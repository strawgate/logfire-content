"""HTTP client for interacting with the Logfire dashboard API.

This module provides a client class for communicating with Logfire's
undocumented ui-api endpoints for dashboard management.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import aiohttp
import yaml

if TYPE_CHECKING:
    from pathlib import Path

# Default Logfire API base URL
DEFAULT_BASE_URL = 'https://logfire-us.pydantic.dev'


class LogfireClientError(Exception):
    """Base exception for Logfire client errors."""


class LogfireAuthenticationError(LogfireClientError):
    """Raised when authentication fails."""


class LogfireNotFoundError(LogfireClientError):
    """Raised when a requested resource is not found."""


class LogfireClient:
    """Async client for interacting with the Logfire dashboard API.

    This client provides methods for managing Perses dashboards through
    Logfire's ui-api endpoints.

    Args:
        token: Authentication token for the Logfire API.
        organization: Organization slug.
        project: Project slug.
        base_url: Base URL for the Logfire API (defaults to US region).
        timeout: Request timeout in seconds.

    Example:
        >>> async with LogfireClient(
        ...     token="your-token",
        ...     organization="my-org",
        ...     project="my-project",
        ... ) as client:
        ...     dashboards = await client.list_dashboards()
    """

    def __init__(
        self,
        token: str,
        organization: str,
        project: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the Logfire client."""
        self.token = token
        self.organization = organization
        self.project = project
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: aiohttp.ClientSession | None = None

    @property
    def _headers(self) -> dict[str, str]:
        """Get authentication headers."""
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                base_url=self.base_url,
                headers=self._headers,
                timeout=self.timeout,
            )
        return self._session

    def _dashboard_url(self, slug: str | None = None) -> str:
        """Build the URL for dashboard operations.

        Args:
            slug: Optional dashboard slug for specific dashboard operations.

        Returns:
            The constructed URL path.
        """
        base = f'/ui-api/organizations/{self.organization}/projects/{self.project}/dashboards'
        if slug:
            return f'{base}/{slug}/'
        return f'{base}/'

    async def _handle_response(self, response: aiohttp.ClientResponse) -> dict[str, Any]:
        """Handle API response and raise appropriate exceptions.

        Args:
            response: The HTTP response to handle.

        Returns:
            The parsed JSON response.

        Raises:
            LogfireAuthenticationError: If authentication fails.
            LogfireNotFoundError: If the resource is not found.
            LogfireClientError: For other HTTP errors.
        """
        if response.status == 401:  # noqa: PLR2004
            msg = 'Invalid or expired authentication token'
            raise LogfireAuthenticationError(msg)
        if response.status == 403:  # noqa: PLR2004
            msg = 'Access denied to this resource'
            raise LogfireAuthenticationError(msg)
        if response.status == 404:  # noqa: PLR2004
            msg = 'Dashboard not found'
            raise LogfireNotFoundError(msg)
        if not response.ok:
            text = await response.text()
            msg = f'API request failed with status {response.status}: {text}'
            raise LogfireClientError(msg)
        return await response.json()

    async def list_dashboards(self) -> list[dict[str, Any]]:
        """List all dashboards in the project.

        Returns:
            List of dashboard summary objects.

        Raises:
            LogfireClientError: If the request fails.
        """
        session = await self._get_session()
        async with session.get(self._dashboard_url()) as response:
            result = await self._handle_response(response)
        # The API returns a list of dashboards
        if isinstance(result, list):
            return result
        return [result]

    async def get_dashboard(self, slug: str) -> dict[str, Any]:
        """Get a dashboard by slug.

        Args:
            slug: The dashboard slug/identifier.

        Returns:
            The Perses dashboard definition.

        Raises:
            LogfireNotFoundError: If the dashboard doesn't exist.
            LogfireClientError: If the request fails.
        """
        session = await self._get_session()
        async with session.get(self._dashboard_url(slug)) as response:
            data = await self._handle_response(response)
        # Extract the Perses definition from the response
        return data.get('definition', data)

    async def put_dashboard(self, slug: str, definition: dict[str, Any]) -> dict[str, Any]:
        """Create or update a dashboard.

        Args:
            slug: The dashboard slug/identifier.
            definition: The Perses dashboard definition.

        Returns:
            The API response.

        Raises:
            LogfireClientError: If the request fails.
        """
        session = await self._get_session()
        async with session.put(
            self._dashboard_url(slug),
            data=json.dumps({'definition': definition}),
        ) as response:
            return await self._handle_response(response)

    async def delete_dashboard(self, slug: str) -> None:
        """Delete a dashboard.

        Args:
            slug: The dashboard slug/identifier.

        Raises:
            LogfireNotFoundError: If the dashboard doesn't exist.
            LogfireClientError: If the request fails.
        """
        session = await self._get_session()
        async with session.delete(self._dashboard_url(slug)) as response:
            if response.status != 204:  # noqa: PLR2004
                await self._handle_response(response)

    async def pull(self, slug: str, output_path: Path) -> None:
        """Export a dashboard to a YAML file.

        Args:
            slug: The dashboard slug to export.
            output_path: Path to write the YAML file.

        Raises:
            LogfireNotFoundError: If the dashboard doesn't exist.
            LogfireClientError: If the request fails.
        """
        definition = await self.get_dashboard(slug)
        with output_path.open('w') as f:
            yaml.dump(definition, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    async def push(self, yaml_path: Path, slug: str | None = None) -> dict[str, Any]:
        """Import a dashboard from a YAML file.

        Args:
            yaml_path: Path to the YAML file.
            slug: Optional slug override. If not provided, derived from metadata.name.

        Returns:
            The API response.

        Raises:
            LogfireClientError: If the request fails.
            TypeError: If the YAML is not a dictionary.
            ValueError: If the YAML is missing required fields.
        """
        with yaml_path.open() as f:
            definition = yaml.safe_load(f)

        if not isinstance(definition, dict):
            msg = 'Invalid dashboard YAML: expected a dictionary'
            raise TypeError(msg)

        # Derive slug from metadata.name if not provided
        if slug is None:
            metadata = definition.get('metadata', {})
            name = metadata.get('name')
            if not name:
                msg = 'Dashboard must have metadata.name or provide explicit slug'
                raise ValueError(msg)
            derived_slug: str = name.lower().replace(' ', '-').replace('_', '-')
            return await self.put_dashboard(derived_slug, definition)

        return await self.put_dashboard(slug, definition)

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session is not None and not self._session.closed:
            await self._session.close()
            self._session = None

    async def __aenter__(self) -> LogfireClient:
        """Enter async context manager."""
        return self

    async def __aexit__(self, *_: object) -> None:
        """Exit async context manager."""
        await self.close()
