"""Integration tests for the LogfireClient against a real Logfire instance.

These tests require environment variables to be set:
- LOGFIRE_TOKEN: Your Logfire API token
- LOGFIRE_ORGANIZATION: Your organization slug
- LOGFIRE_PROJECT: Your project slug

Tests are automatically skipped if these variables are not set.

Usage:
    # Set environment variables
    export LOGFIRE_TOKEN="your-token"
    export LOGFIRE_ORGANIZATION="your-org"
    export LOGFIRE_PROJECT="your-project"

    # Run integration tests
    pytest -m integration tests/test_client_integration.py

    # Update snapshots after API changes
    pytest -m integration --inline-snapshot=update tests/test_client_integration.py

    # Skip integration tests (useful in CI)
    pytest -m "not integration"
"""

import contextlib
import os
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from dirty_equals import IsStr
from inline_snapshot import snapshot

from logfire_cli.clients.logfire_api import LogfireClient, LogfireNotFoundError
from logfire_cli.models.logfire_api import Dashboard, ListDashboards


@pytest.fixture(scope='session')
def integration_env_vars() -> dict[str, str | None] | None:
    """Get integration test environment variables.

    Returns:
        Dictionary of env vars if all required vars are set, None otherwise.
    """
    token = os.environ.get('LOGFIRE_TOKEN')
    organization = os.environ.get('LOGFIRE_ORGANIZATION')
    project = os.environ.get('LOGFIRE_PROJECT')

    if not all([token, organization, project]):
        return None

    return {
        'LOGFIRE_TOKEN': token,
        'LOGFIRE_ORGANIZATION': organization,
        'LOGFIRE_PROJECT': project,
    }


@pytest.fixture(scope='session', autouse=True)
def skip_if_no_env(integration_env_vars: dict[str, str | None] | None) -> dict[str, str]:
    """Skip test if integration env vars are not set."""
    if integration_env_vars is None:
        pytest.skip('Integration tests require LOGFIRE_TOKEN, LOGFIRE_ORGANIZATION, and LOGFIRE_PROJECT env vars')
    # Type narrowing: we know these are not None at this point
    return {
        'token': integration_env_vars['LOGFIRE_TOKEN'] or '',
        'organization': integration_env_vars['LOGFIRE_ORGANIZATION'] or '',
        'project': integration_env_vars['LOGFIRE_PROJECT'] or '',
    }


@pytest.fixture
async def client(skip_if_no_env: dict[str, str]) -> AsyncGenerator[LogfireClient, None]:
    """Create a LogfireClient instance."""
    client_instance = LogfireClient(
        token=skip_if_no_env['token'],
        organization=skip_if_no_env['organization'],
        project=skip_if_no_env['project'],
    )
    async with client_instance:
        yield client_instance


pytestmark = pytest.mark.integration


async def test_list_dashboards(client: LogfireClient) -> None:
    """Test that list_dashboards returns proper structure."""
    result = await client.list_dashboards()
    assert isinstance(result, ListDashboards)

    assert len(result.root) > 0, 'No dashboards found'

    for item in result.root:
        assert isinstance(item.id, UUID), 'Dashboard is missing a valid UUID'
        assert isinstance(item.project_id, UUID), 'Dashboard is missing a valid project ID'
        assert isinstance(item.created_at, datetime), 'Dashboard is missing a valid creation timestamp'
        assert isinstance(item.created_by_name, str), 'Dashboard is missing a valid created by name'
        assert item.updated_at is None or isinstance(item.updated_at, datetime), 'Dashboard is missing a valid update timestamp'
        assert item.updated_by_name is None or isinstance(item.updated_by_name, str), 'Dashboard is missing a valid updated by name'
        assert isinstance(item.dashboard_slug, str), 'Dashboard is missing a valid slug'
        assert isinstance(item.dashboard_name, str), 'Dashboard is missing a valid name'


async def test_get_dashboard_nonexistent(client: LogfireClient) -> None:
    """Test getting a nonexistent dashboard."""
    with pytest.raises(LogfireNotFoundError):
        _ = await client.get_dashboard('nonexistent-dashboard-integration-test-12345')


async def test_crud_dashboard(
    client: LogfireClient,
) -> None:
    """Test creating, updating, and deleting a dashboard."""

    slug = 'test-create-simple-dashboard-' + str(uuid4())

    with contextlib.suppress(LogfireNotFoundError):
        _ = await client.get_dashboard(slug)
        _ = await client.delete_dashboard(slug)

    # Create a test dashboard
    simple_dashboard_dict: dict[str, Any] = {
        'kind': 'Dashboard',
        'metadata': {
            'name': slug,
            'project': 'starter-project',
        },
        'spec': {
            'display': {'name': slug, 'description': None},
            'datasources': {},
            'variables': [],
            'panels': {},
            'layouts': [],
            'duration': '1h',
            'refreshInterval': '0s',
        },
    }
    simple_dashboard = Dashboard.model_validate(simple_dashboard_dict)

    # Create/update the dashboard
    created = await client.create_dashboard(slug, simple_dashboard)
    assert isinstance(created, Dashboard)
    assert created.kind == 'Dashboard'
    assert created.metadata.name == slug
    assert created.spec.display.name == slug

    # Get the dashboard back
    retrieved = await client.get_dashboard(slug)
    assert isinstance(retrieved, Dashboard)

    assert retrieved.model_dump() == snapshot({
        'kind': 'Dashboard',
        'metadata': {
            'name': 'test-create-simple-dashboard',
            'project': 'starter-project',
            'version': 0,
            'created_at': IsStr(),
            'updated_at': IsStr(),
        },
        'spec': {
            'display': {'name': 'test-create-simple-dashboard', 'description': None},
            'datasources': {},
            'panels': {},
            'layouts': [],
            'variables': [],
            'duration': '1h',
            'refresh_interval': '0s',
        },
    })

    # Update the dashboard
    updated_dashboard_dict: dict[str, Any] = {
        'kind': 'Dashboard',
        'metadata': {
            'name': slug,
            'project': 'starter-project',
        },
        'spec': {
            'display': {'name': slug, 'description': 'my cool description'},
            'datasources': {},
            'variables': [],
            'panels': {},
            'layouts': [],
            'duration': '1h',
            'refreshInterval': '0s',
        },
    }
    updated_dashboard = Dashboard.model_validate(updated_dashboard_dict)
    updated = await client.update_dashboard(slug, updated_dashboard)

    assert updated.model_dump() == snapshot({
        'kind': 'Dashboard',
        'metadata': {
            'name': 'test-create-simple-dashboard',
            'project': 'starter-project',
            'version': 0,
            'created_at': IsStr(),
            'updated_at': IsStr(),
        },
        'spec': {
            'display': {'name': 'test-create-simple-dashboard', 'description': 'my cool description'},
            'datasources': {},
            'panels': {},
            'layouts': [],
            'variables': [],
            'duration': '1h',
            'refresh_interval': '0s',
        },
    })

    # Clean up: delete the dashboard
    await client.delete_dashboard(slug)

    # Verify it's deleted
    with pytest.raises(LogfireNotFoundError):
        _ = await client.get_dashboard(slug)


async def test_context_manager(skip_if_no_env: dict[str, str]) -> None:
    """Test async context manager protocol."""
    async with LogfireClient(
        token=skip_if_no_env['token'],
        organization=skip_if_no_env['organization'],
        project=skip_if_no_env['project'],
    ) as client:
        assert client.token == skip_if_no_env['token']
        assert client.organization == skip_if_no_env['organization']
        assert client.project == skip_if_no_env['project']

        # Test that we can make a call
        dashboards = await client.list_dashboards()
        assert isinstance(dashboards, ListDashboards)
