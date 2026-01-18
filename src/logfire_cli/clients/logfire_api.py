"""HTTP client for interacting with the Logfire dashboard API.

This module provides a client class for communicating with Logfire's
undocumented ui-api endpoints for dashboard management.
"""

import json
from types import TracebackType
from typing import Any, TypeGuard

import aiohttp
from pydantic import BaseModel

from logfire_cli.models.logfire_api import Dashboard, DashboardResponse, GetDashboardResponse, ListDashboards

# Default Logfire API base URL
DEFAULT_BASE_URL = 'https://logfire-us.pydantic.dev'


class LogfireClientError(Exception):
    """Base exception for Logfire client errors."""


class LogfireAuthenticationError(LogfireClientError):
    """Raised when authentication fails."""


class LogfireNotFoundError(LogfireClientError):
    """Raised when a requested resource is not found."""


# Define the specific type we expect
JsonDict = dict[str, Any]


def is_json_dict(val: Any) -> TypeGuard[JsonDict]:  # pyright: ignore[reportAny]
    """Checks if a value is a dictionary and all keys are strings."""
    if not isinstance(val, dict):
        return False
    return all(isinstance(key, str) for key in val)  # pyright: ignore[reportUnknownVariableType]


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
        self.token: str = token
        self.organization: str = organization
        self.project: str = project
        self.base_url: str = base_url.rstrip('/')
        self.timeout: aiohttp.ClientTimeout = aiohttp.ClientTimeout(total=timeout)
        self._session: aiohttp.ClientSession | None = None

    @property
    def _headers(self) -> dict[str, str]:
        """Get authentication headers."""
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.2 Safari/605.1.15'
            ),
        }

    @property
    def session(self) -> aiohttp.ClientSession:
        """Get the aiohttp session."""
        if self._session is None:
            msg = 'Session not initialized. Enter the async context manager first.'
            raise RuntimeError(msg)
        return self._session

    def _build_url(self, *parts: str | None) -> str:
        """Build a URL from the base URL and parts."""
        return '/'.join(part for part in parts if part is not None and part != '')

    def _build_ui_api_url(self, *parts: str | None) -> str:
        """Build a UI API URL from the base URL and parts."""
        return self._build_url(f'/ui-api/organizations/{self.organization}/projects/{self.project}', *parts)

    async def _handle_response[T: BaseModel](self, response: aiohttp.ClientResponse, model: type[T]) -> T:
        """Handle API response and raise appropriate exceptions.

        Args:
            response: The HTTP response to handle.
            model: The model to use for deserialization.

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
            msg = 'Not found'
            raise LogfireNotFoundError(msg)
        if not response.ok:
            text = await response.text()
            msg = f'API request failed with status {response.status}: {text}'
            raise LogfireClientError(msg)

        json_data = await response.json()  # pyright: ignore[reportAny]
        return model.model_validate(json_data)

    async def _get[T: BaseModel](self, url: str, model: type[T]) -> T:
        """Get a resource from the API.

        Args:
            url: The URL to get the resource from.
            model: The model to use for deserialization.

        Returns:
            The resource.
        """
        async with self.session.get(url) as response:
            return await self._handle_response(response, model)

    async def _post[T: BaseModel](self, url: str, data: dict[str, Any], model: type[T]) -> T:
        """Post a resource to the API.

        Args:
            url: The URL to post the resource to.
            data: The data to post to the resource.
            model: The model to use for deserialization.
        """
        async with self.session.post(url, data=json.dumps(data)) as response:
            return await self._handle_response(response, model)

    async def _put[T: BaseModel](self, url: str, data: dict[str, Any], model: type[T]) -> T:
        """Put a resource to the API.

        Args:
            url: The URL to put the resource to.
            data: The data to put to the resource.
            model: The model to use for deserialization.
        """
        async with self.session.put(url, data=json.dumps(data)) as response:
            return await self._handle_response(response, model)

    async def _delete(self, url: str) -> None:
        """Delete a resource from the API.

        Args:
            url: The URL to delete the resource from.
        """
        async with self.session.delete(url) as response:
            if response.status != 204:  # noqa: PLR2004
                msg = f'Failed to delete resource: {response.status}'
                raise LogfireClientError(msg)

    async def list_dashboards(self) -> ListDashboards:
        """List all dashboards in the project.

        Returns:
            A list of dashboard items.

        Raises:
            LogfireClientError: If the request fails.
        """
        url = self._build_ui_api_url('dashboards') + '/'
        return await self._get(url, ListDashboards)

    async def get_dashboard(self, slug: str) -> Dashboard:
        """Get a dashboard by slug.

        Args:
            slug: The dashboard slug/identifier.

        Returns:
            The Perses dashboard definition.

        Raises:
            LogfireNotFoundError: If the dashboard doesn't exist.
            LogfireClientError: If the request fails.
        """
        url = self._build_ui_api_url('dashboards', slug) + '/'
        response = await self._get(url, GetDashboardResponse)
        return response.dashboard

    async def create_dashboard(self, slug: str, dashboard: Dashboard) -> Dashboard:
        """Create a dashboard.

        Args:
            slug: The dashboard slug/identifier.
            dashboard: The Perses dashboard definition.

        Returns:
            The created dashboard.

        Raises:
            LogfireClientError: If the request fails.
            ValueError: If slug doesn't match dashboard.metadata.name.
        """
        # POST to create - slug comes from metadata.name in the body
        url = self._build_ui_api_url('dashboards') + '/'
        # Use model_dump with by_alias=True to ensure camelCase fields are used
        data = {
            'definition': dashboard.model_dump(mode='json', by_alias=True, exclude_none=True),
            'slug': slug,
            'name': dashboard.metadata.name,
        }
        response = await self._post(url, data=data, model=DashboardResponse)
        return response.definition

    async def update_dashboard(self, slug: str, dashboard: Dashboard) -> Dashboard:
        """Create or update a dashboard.

        Args:
            slug: The dashboard slug/identifier. Should match dashboard.metadata.name.
            dashboard: The Perses dashboard definition.

        Returns:
            The created or updated dashboard.

        Raises:
            LogfireClientError: If the request fails.
            ValueError: If slug doesn't match dashboard.metadata.name.
        """
        url = self._build_ui_api_url('dashboards', slug) + '/'
        # Use model_dump with by_alias=True to ensure camelCase fields are used
        data = {
            'definition': dashboard.model_dump(mode='json', by_alias=True, exclude_none=True),
            'slug': slug,
            'name': dashboard.metadata.name,
        }
        response = await self._put(url, data=data, model=DashboardResponse)
        return response.definition

    async def delete_dashboard(self, slug: str) -> None:
        """Delete a dashboard.

        Args:
            slug: The dashboard slug/identifier.

        Raises:
            LogfireNotFoundError: If the dashboard doesn't exist.
            LogfireClientError: If the request fails.
        """
        url = self._build_ui_api_url('dashboards', slug) + '/'
        return await self._delete(url)

    # async def pull(self, slug: str, output_path: Path) -> None:
    #     """Export a dashboard to a YAML file.

    #     Args:
    #         slug: The dashboard slug to export.
    #         output_path: Path to write the YAML file.

    #     Raises:
    #         LogfireNotFoundError: If the dashboard doesn't exist.
    #         LogfireClientError: If the request fails.
    #     """
    #     definition = await self._get(
    #         self._build_url(
    #             self._ui_api_project_path(),
    #             'dashboards',
    #             slug,
    #         ),
    #     )
    #     with output_path.open('w') as f:
    #         yaml.dump(definition, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    # async def push(self, yaml_path: Path, slug: str | None = None) -> dict[str, Any]:
    #     """Import a dashboard from a YAML file.

    #     Args:
    #         yaml_path: Path to the YAML file.
    #         slug: Optional slug override. If not provided, derived from metadata.name.

    #     Returns:
    #         The API response.

    #     Raises:
    #         LogfireClientError: If the request fails.
    #         TypeError: If the YAML is not a dictionary.
    #         ValueError: If the YAML is missing required fields.
    #     """
    #     with yaml_path.open() as f:
    #         definition = yaml.safe_load(f)

    #     if not isinstance(definition, dict):
    #         msg = 'Invalid dashboard YAML: expected a dictionary'
    #         raise TypeError(msg)

    #     # Derive slug from metadata.name if not provided
    #     if slug is None:
    #         metadata = definition.get('metadata', {})
    #         name = metadata.get('name')
    #         if not name:
    #             msg = 'Dashboard must have metadata.name or provide explicit slug'
    #             raise ValueError(msg)
    #         derived_slug: str = name.lower().replace(' ', '-').replace('_', '-')
    #         return await self.put_dashboard(derived_slug, definition)

    #     return await self.put_dashboard(slug, definition)

    # async def close(self) -> None:
    #     """Close the aiohttp session."""
    #     if self._session is not None and not self._session.closed:
    #         await self._session.close()
    #         self._session = None

    async def __aenter__(self) -> 'LogfireClient':
        """Enter async context manager."""
        self._session = aiohttp.ClientSession(
            base_url=self.base_url,
            headers=self._headers,
            timeout=self.timeout,
        )
        _ = await self._session.__aenter__()
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        """Exit async context manager."""
        if self._session is not None and not self._session.closed:
            await self._session.__aexit__(exc_type=exc_type, exc_val=exc_val, exc_tb=exc_tb)
            self._session = None
