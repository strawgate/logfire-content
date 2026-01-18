"""Tests for the LogfireClient."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import pytest
import respx

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

    @respx.mock
    def test_list_dashboards(self, client: LogfireClient) -> None:
        dashboards = [
            {'slug': 'dashboard-1', 'name': 'Dashboard 1'},
            {'slug': 'dashboard-2', 'name': 'Dashboard 2'},
        ]
        respx.get('https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/').mock(
            return_value=httpx.Response(200, json=dashboards)
        )

        result = client.list_dashboards()
        assert result == dashboards

    @respx.mock
    def test_get_dashboard(self, client: LogfireClient, sample_dashboard: dict) -> None:
        respx.get('https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/my-dashboard/').mock(
            return_value=httpx.Response(200, json={'definition': sample_dashboard})
        )

        result = client.get_dashboard('my-dashboard')
        assert result == sample_dashboard

    @respx.mock
    def test_put_dashboard(self, client: LogfireClient, sample_dashboard: dict) -> None:
        respx.put('https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/my-dashboard/').mock(
            return_value=httpx.Response(200, json={'slug': 'my-dashboard', 'definition': sample_dashboard})
        )

        result = client.put_dashboard('my-dashboard', sample_dashboard)
        assert result['slug'] == 'my-dashboard'

    @respx.mock
    def test_delete_dashboard(self, client: LogfireClient) -> None:
        respx.delete('https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/my-dashboard/').mock(
            return_value=httpx.Response(204)
        )

        client.delete_dashboard('my-dashboard')

    @respx.mock
    def test_authentication_error(self, client: LogfireClient) -> None:
        respx.get('https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/').mock(
            return_value=httpx.Response(401, json={'error': 'Unauthorized'})
        )

        with pytest.raises(LogfireAuthenticationError):
            client.list_dashboards()

    @respx.mock
    def test_not_found_error(self, client: LogfireClient) -> None:
        respx.get('https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/nonexistent/').mock(
            return_value=httpx.Response(404, json={'error': 'Not found'})
        )

        with pytest.raises(LogfireNotFoundError):
            client.get_dashboard('nonexistent')

    @respx.mock
    def test_pull(self, client: LogfireClient, sample_dashboard: dict, tmp_path: Path) -> None:
        respx.get('https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/my-dashboard/').mock(
            return_value=httpx.Response(200, json={'definition': sample_dashboard})
        )

        output_path = tmp_path / 'output.yaml'
        client.pull('my-dashboard', output_path)

        assert output_path.exists()
        import yaml

        with output_path.open() as f:
            content = yaml.safe_load(f)
        assert content['metadata']['name'] == 'test-dashboard'

    @respx.mock
    def test_push(self, client: LogfireClient, temp_yaml_file: Path) -> None:
        respx.put('https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/test-dashboard/').mock(
            return_value=httpx.Response(200, json={'slug': 'test-dashboard'})
        )

        result = client.push(temp_yaml_file)
        assert result['slug'] == 'test-dashboard'

    @respx.mock
    def test_push_with_explicit_slug(self, client: LogfireClient, temp_yaml_file: Path) -> None:
        respx.put('https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/custom-slug/').mock(
            return_value=httpx.Response(200, json={'slug': 'custom-slug'})
        )

        result = client.push(temp_yaml_file, slug='custom-slug')
        assert result['slug'] == 'custom-slug'

    def test_context_manager(self) -> None:
        with LogfireClient(
            token='test-token',
            organization='test-org',
            project='test-project',
        ) as client:
            assert client.token == 'test-token'

    def test_push_invalid_yaml(self, client: LogfireClient, tmp_path: Path) -> None:
        bad_file = tmp_path / 'bad.yaml'
        bad_file.write_text('[1, 2, 3]')

        with pytest.raises(TypeError, match='expected a dictionary'):
            client.push(bad_file)

    def test_push_missing_name(self, client: LogfireClient, tmp_path: Path) -> None:
        bad_file = tmp_path / 'bad.yaml'
        bad_file.write_text('kind: Dashboard\nmetadata: {}\nspec: {}')

        with pytest.raises(ValueError, match=r'metadata\.name'):
            client.push(bad_file)
