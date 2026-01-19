"""Tests for the CLI commands."""

from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
import yaml
from aioresponses import aioresponses
from click.testing import CliRunner

from logfire_cli.cli import cli


class TestCLI:
    """Tests for CLI commands."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner."""
        return CliRunner()

    @pytest.fixture
    def env_vars(self) -> dict[str, str]:
        """Environment variables for testing."""
        return {
            'LOGFIRE_TOKEN': 'test-token',
            'LOGFIRE_ORGANIZATION': 'test-org',
            'LOGFIRE_PROJECT': 'test-project',
        }

    def test_version(self, runner: CliRunner) -> None:
        """Test version command."""
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert 'logfire-cli' in result.output

    def test_help(self, runner: CliRunner) -> None:
        """Test help output."""
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Logfire CLI' in result.output

    def test_list_dashboards(self, runner: CliRunner, env_vars: dict[str, str]) -> None:
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
        with aioresponses() as m:
            m.get(  # pyright: ignore[reportUnknownMemberType]
                'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/',
                payload=dashboards,
            )

            result = runner.invoke(cli, ['dashboards', 'list'], env=env_vars)
            assert result.exit_code == 0
            assert 'dashboard-1' in result.output
            assert 'Dashboard 1' in result.output

    def test_list_empty(self, runner: CliRunner, env_vars: dict[str, str]) -> None:
        """Test listing when no dashboards exist."""
        with aioresponses() as m:
            m.get(  # pyright: ignore[reportUnknownMemberType]
                'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/',
                payload=[],
            )

            result = runner.invoke(cli, ['dashboards', 'list'], env=env_vars)
            assert result.exit_code == 0
            assert 'No dashboards found' in result.output

    def test_export(self, runner: CliRunner, env_vars: dict[str, str], sample_dashboard: dict[str, Any], tmp_path: Path) -> None:
        """Test exporting a dashboard to a file."""
        wrapped_response = {
            'dashboard': sample_dashboard,
        }
        with aioresponses() as m:
            m.get(  # pyright: ignore[reportUnknownMemberType]
                'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/test-dashboard/',
                payload=wrapped_response,
            )

            output_file = tmp_path / 'output.yaml'
            result = runner.invoke(cli, ['dashboards', 'export', 'test-dashboard', '-o', str(output_file)], env=env_vars)
            assert result.exit_code == 0
            assert output_file.exists()

            # Verify file contents
            with output_file.open() as f:
                content: dict[str, Any] = yaml.safe_load(f)  # pyright: ignore[reportAny]
                assert content['kind'] == 'Dashboard'
                assert content['metadata']['name'] == 'test-dashboard'

    def test_import(self, runner: CliRunner, env_vars: dict[str, str], temp_yaml_file: Path) -> None:
        """Test importing a dashboard from a file."""
        # Read the dashboard to get the expected response structure
        with temp_yaml_file.open() as f:
            dashboard_data: dict[str, Any] = yaml.safe_load(f)  # pyright: ignore[reportAny]

        wrapped_response = {
            'id': str(uuid4()),
            'project_id': str(uuid4()),
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-02T00:00:00Z',
            'created_by_name': 'test-user',
            'updated_by_name': 'test-user',
            'dashboard_name': 'test-dashboard',
            'dashboard_slug': 'test-dashboard',
            'definition': dashboard_data,
        }
        with aioresponses() as m:
            m.put(  # pyright: ignore[reportUnknownMemberType]
                'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/test-dashboard/',
                payload=wrapped_response,
            )

            result = runner.invoke(cli, ['dashboards', 'import', str(temp_yaml_file)], env=env_vars)
            assert result.exit_code == 0
            assert 'imported successfully' in result.output.lower()

    def test_get(self, runner: CliRunner, env_vars: dict[str, str], sample_dashboard: dict[str, Any]) -> None:
        """Test getting dashboard details."""
        wrapped_response = {
            'dashboard': sample_dashboard,
        }
        with aioresponses() as m:
            m.get(  # pyright: ignore[reportUnknownMemberType]
                'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/test-dashboard/',
                payload=wrapped_response,
            )

            result = runner.invoke(cli, ['dashboards', 'get', 'test-dashboard'], env=env_vars)
            assert result.exit_code == 0
            # Verify key fields are present in output
            assert 'kind: Dashboard' in result.output or 'kind: "Dashboard"' in result.output
            assert 'test-dashboard' in result.output
            assert 'Test Dashboard' in result.output

    def test_delete_with_confirmation(self, runner: CliRunner, env_vars: dict[str, str]) -> None:
        """Test deleting a dashboard with confirmation flag."""
        with aioresponses() as m:
            m.delete(  # pyright: ignore[reportUnknownMemberType]
                'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/my-dashboard/',
                status=204,
            )

            result = runner.invoke(cli, ['dashboards', 'delete', 'my-dashboard', '-y'], env=env_vars)
            assert result.exit_code == 0
            assert 'deleted' in result.output

    def test_init(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test creating a new dashboard template."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ['dashboards', 'init', 'My New Dashboard'])
            assert result.exit_code == 0
            assert Path('my-new-dashboard.yaml').exists()

    def test_missing_token(self, runner: CliRunner) -> None:
        """Test error when token is missing."""
        with runner.isolation(env={'LOGFIRE_TOKEN': ''}):
            result = runner.invoke(cli, ['dashboards', 'list'])
        assert result.exit_code != 0
        assert 'Missing option' in result.output or 'required' in result.output.lower()
