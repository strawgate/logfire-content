"""Tests for the LogfireClient."""

import contextlib
from collections.abc import Generator
from typing import Any
from uuid import uuid4

import pytest
from aioresponses import aioresponses

from logfire_cli.clients.logfire_api import (
    LogfireAuthenticationError,
    LogfireClient,
    LogfireClientError,
    LogfireNotFoundError,
)
from logfire_cli.models.logfire_api import Dashboard, ListDashboards


@contextlib.contextmanager
def mock_get(url: str, payload: dict[str, Any] | list[dict[str, Any]], status: int = 200) -> Generator[None, None, None]:
    with aioresponses() as m:
        m.get(url, payload=payload, status=status)  # pyright: ignore[reportUnknownMemberType]
        yield


@contextlib.contextmanager
def mock_put(url: str, payload: dict[str, Any] | list[dict[str, Any]], status: int = 200) -> Generator[None, None, None]:
    with aioresponses() as m:
        m.put(url, payload=payload, status=status)  # pyright: ignore[reportUnknownMemberType]
        yield


@contextlib.contextmanager
def mock_delete(url: str, status: int = 204) -> Generator[None, None, None]:
    with aioresponses() as m:
        m.delete(url, status=status)  # pyright: ignore[reportUnknownMemberType]
        yield


@pytest.fixture
def client() -> LogfireClient:
    """Create a test client."""
    return LogfireClient(
        token='test-token',
        organization='test-org',
        project='test-project',
    )


async def test_list_dashboards(client: LogfireClient) -> None:
    """Test listing dashboards."""
    dashboards = [
        {
            'id': str(uuid4()),
            'project_id': str(uuid4()),
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z',
            'created_by_name': 'test-user',
            'updated_by_name': 'test-user',
            'dashboard_name': 'Dashboard 1',
            'dashboard_slug': 'dashboard-1',
        },
        {
            'id': str(uuid4()),
            'project_id': str(uuid4()),
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-02T00:00:00Z',
            'created_by_name': 'test-user',
            'updated_by_name': 'test-user',
            'dashboard_name': 'Dashboard 2',
            'dashboard_slug': 'dashboard-2',
        },
    ]
    with mock_get(
        'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/',
        dashboards,
    ):
        async with client:
            result = await client.list_dashboards()
        assert isinstance(result, ListDashboards)
        assert len(result.root) == 2
        assert result.root[0].dashboard_slug == 'dashboard-1'
        assert result.root[1].dashboard_slug == 'dashboard-2'


async def test_get_dashboard(client: LogfireClient, sample_dashboard: dict[str, Any]) -> None:
    """Test getting a specific dashboard."""
    # GetDashboardResponse uses 'dashboard' field, not 'definition'
    get_response = {
        'dashboard': sample_dashboard,
    }
    with mock_get(
        'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/test-dashboard/',
        get_response,
    ):
        async with client:
            result = await client.get_dashboard('test-dashboard')
        assert isinstance(result, Dashboard)
        assert result.kind == 'Dashboard'
        assert result.metadata.name == 'test-dashboard'
        assert result.spec.display.name == 'Test Dashboard'


async def test_update_dashboard(client: LogfireClient, sample_dashboard: dict[str, Any]) -> None:
    """Test updating a dashboard."""
    dashboard = Dashboard.model_validate(sample_dashboard)
    wrapped_response: dict[str, Any] = {
        'id': str(uuid4()),
        'project_id': str(uuid4()),
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-01-02T00:00:00Z',
        'created_by_name': 'test-user',
        'updated_by_name': 'test-user',
        'dashboard_name': 'test-dashboard',
        'dashboard_slug': 'test-dashboard',
        'definition': sample_dashboard,
    }

    with mock_put(
        'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/test-dashboard/',
        wrapped_response,
    ):
        async with client:
            result = await client.update_dashboard('test-dashboard', dashboard)
        assert isinstance(result, Dashboard)
        assert result.kind == 'Dashboard'
        assert result.metadata.name == 'test-dashboard'


async def test_delete_dashboard(client: LogfireClient) -> None:
    """Test deleting a dashboard."""
    with mock_delete(
        'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/my-dashboard/',
    ):
        async with client:
            await client.delete_dashboard('my-dashboard')


async def test_authentication_error(client: LogfireClient) -> None:
    """Test handling of authentication errors."""
    with (
        mock_get(
            'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/',
            {'error': 'Unauthorized'},
            status=401,
        ),
        pytest.raises(LogfireAuthenticationError),
    ):
        async with client:
            _ = await client.list_dashboards()


async def test_not_found_error(client: LogfireClient) -> None:
    """Test handling of not found errors."""
    with mock_get(
        'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/nonexistent/',
        {'error': 'Not found'},
        status=404,
    ):
        async with client:
            with pytest.raises(LogfireNotFoundError):
                _ = await client.get_dashboard('nonexistent')


async def test_get_dashboard_wrapped_response(client: LogfireClient, sample_dashboard: dict[str, Any]) -> None:
    """Test getting a dashboard when API returns it wrapped in GetDashboardResponse."""
    # GetDashboardResponse uses 'dashboard' field, not 'definition'
    get_response = {
        'dashboard': sample_dashboard,
    }
    with mock_get(
        'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/test-dashboard/',
        get_response,
    ):
        async with client:
            result = await client.get_dashboard('test-dashboard')

    assert isinstance(result, Dashboard)
    assert result.kind == 'Dashboard'
    assert result.metadata.name == 'test-dashboard'


async def test_context_manager() -> None:
    """Test async context manager protocol."""
    async with LogfireClient(
        token='test-token',
        organization='test-org',
        project='test-project',
    ) as client:
        assert client.token == 'test-token'


async def test_update_dashboard_api_error(client: LogfireClient, sample_dashboard: dict[str, Any]) -> None:
    """Test handling API errors when updating dashboard."""
    dashboard = Dashboard.model_validate(sample_dashboard)

    with mock_put(
        'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/test-dashboard/',
        {'error': 'Invalid dashboard'},
        status=422,
    ):
        async with client:
            with pytest.raises(LogfireClientError):
                _ = await client.update_dashboard('test-dashboard', dashboard)
