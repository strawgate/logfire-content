"""Tests for the LogfireClient."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from aioresponses import aioresponses

if TYPE_CHECKING:
    from pathlib import Path

from logfire_cli.client import (
    LogfireAuthenticationError,
    LogfireClient,
    LogfireNotFoundError,
)


class TestLogfireClient:
    """Tests for LogfireClient."""

    @pytest.fixture
    def client(self) -> LogfireClient:
        """Create a test client."""
        return LogfireClient(
            token='test-token',
            organization='test-org',
            project='test-project',
        )

    async def test_list_dashboards(self, client: LogfireClient) -> None:
        """Test listing dashboards."""
        dashboards = [
            {'slug': 'dashboard-1', 'name': 'Dashboard 1'},
            {'slug': 'dashboard-2', 'name': 'Dashboard 2'},
        ]
        with aioresponses() as m:
            m.get(
                'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/',
                payload=dashboards,
            )

            async with client:
                result = await client.list_dashboards()
            assert result == dashboards

    async def test_get_dashboard(self, client: LogfireClient, sample_dashboard: dict) -> None:
        """Test getting a specific dashboard."""
        with aioresponses() as m:
            m.get(
                'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/my-dashboard/',
                payload={'definition': sample_dashboard},
            )

            async with client:
                result = await client.get_dashboard('my-dashboard')
            assert result == sample_dashboard

    async def test_put_dashboard(self, client: LogfireClient, sample_dashboard: dict) -> None:
        """Test creating/updating a dashboard."""
        with aioresponses() as m:
            m.put(
                'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/my-dashboard/',
                payload={'slug': 'my-dashboard', 'definition': sample_dashboard},
            )

            async with client:
                result = await client.put_dashboard('my-dashboard', sample_dashboard)
            assert result['slug'] == 'my-dashboard'

    async def test_delete_dashboard(self, client: LogfireClient) -> None:
        """Test deleting a dashboard."""
        with aioresponses() as m:
            m.delete(
                'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/my-dashboard/',
                status=204,
            )

            async with client:
                await client.delete_dashboard('my-dashboard')

    async def test_authentication_error(self, client: LogfireClient) -> None:
        """Test handling of authentication errors."""
        with aioresponses() as m:
            m.get(
                'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/',
                status=401,
                payload={'error': 'Unauthorized'},
            )

            with pytest.raises(LogfireAuthenticationError):
                async with client:
                    await client.list_dashboards()

    async def test_not_found_error(self, client: LogfireClient) -> None:
        """Test handling of not found errors."""
        with aioresponses() as m:
            m.get(
                'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/nonexistent/',
                status=404,
                payload={'error': 'Not found'},
            )

            with pytest.raises(LogfireNotFoundError):
                async with client:
                    await client.get_dashboard('nonexistent')

    async def test_pull(self, client: LogfireClient, sample_dashboard: dict, tmp_path: Path) -> None:
        """Test pulling a dashboard to a file."""
        with aioresponses() as m:
            m.get(
                'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/my-dashboard/',
                payload={'definition': sample_dashboard},
            )

            output_path = tmp_path / 'output.yaml'
            async with client:
                await client.pull('my-dashboard', output_path)

            assert output_path.exists()
            import yaml

            with output_path.open() as f:
                content = yaml.safe_load(f)
            assert content['metadata']['name'] == 'test-dashboard'

    async def test_push(self, client: LogfireClient, temp_yaml_file: Path) -> None:
        """Test pushing a dashboard from a file."""
        with aioresponses() as m:
            m.put(
                'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/test-dashboard/',
                payload={'slug': 'test-dashboard'},
            )

            async with client:
                result = await client.push(temp_yaml_file)
            assert result['slug'] == 'test-dashboard'

    async def test_push_with_explicit_slug(self, client: LogfireClient, temp_yaml_file: Path) -> None:
        """Test pushing a dashboard with an explicit slug override."""
        with aioresponses() as m:
            m.put(
                'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/custom-slug/',
                payload={'slug': 'custom-slug'},
            )

            async with client:
                result = await client.push(temp_yaml_file, slug='custom-slug')
            assert result['slug'] == 'custom-slug'

    async def test_context_manager(self) -> None:
        """Test async context manager protocol."""
        async with LogfireClient(
            token='test-token',
            organization='test-org',
            project='test-project',
        ) as client:
            assert client.token == 'test-token'

    async def test_push_invalid_yaml(self, client: LogfireClient, tmp_path: Path) -> None:
        """Test pushing invalid YAML (not a dictionary)."""
        bad_file = tmp_path / 'bad.yaml'
        bad_file.write_text('[1, 2, 3]')

        with pytest.raises(TypeError, match='expected a dictionary'):
            async with client:
                await client.push(bad_file)

    async def test_push_missing_name(self, client: LogfireClient, tmp_path: Path) -> None:
        """Test pushing YAML missing metadata.name."""
        bad_file = tmp_path / 'bad.yaml'
        bad_file.write_text('kind: Dashboard\nmetadata: {}\nspec: {}')

        with pytest.raises(ValueError, match=r'metadata\.name'):
            async with client:
                await client.push(bad_file)
