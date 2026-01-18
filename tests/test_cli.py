"""Tests for the CLI commands."""

from __future__ import annotations

from pathlib import Path

import pytest
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
            {'slug': 'dashboard-1', 'name': 'Dashboard 1', 'updatedAt': '2024-01-01'},
            {'slug': 'dashboard-2', 'name': 'Dashboard 2', 'updatedAt': '2024-01-02'},
        ]
        with aioresponses() as m:
            m.get(
                'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/',
                payload=dashboards,
            )

            result = runner.invoke(cli, ['list'], env=env_vars)
            assert result.exit_code == 0
            assert 'dashboard-1' in result.output
            assert 'Dashboard 1' in result.output

    def test_list_empty(self, runner: CliRunner, env_vars: dict[str, str]) -> None:
        """Test listing when no dashboards exist."""
        with aioresponses() as m:
            m.get(
                'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/',
                payload=[],
            )

            result = runner.invoke(cli, ['list'], env=env_vars)
            assert result.exit_code == 0
            assert 'No dashboards found' in result.output

    def test_pull(self, runner: CliRunner, env_vars: dict[str, str], sample_dashboard: dict, tmp_path: Path) -> None:
        """Test pulling a dashboard to a file."""
        with aioresponses() as m:
            m.get(
                'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/my-dashboard/',
                payload={'definition': sample_dashboard},
            )

            output_file = tmp_path / 'output.yaml'
            result = runner.invoke(cli, ['pull', 'my-dashboard', '-o', str(output_file)], env=env_vars)
            assert result.exit_code == 0
            assert output_file.exists()

    def test_push(self, runner: CliRunner, env_vars: dict[str, str], temp_yaml_file: Path) -> None:
        """Test pushing a dashboard from a file."""
        with aioresponses() as m:
            m.put(
                'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/test-dashboard/',
                payload={'slug': 'test-dashboard'},
            )

            result = runner.invoke(cli, ['push', str(temp_yaml_file)], env=env_vars)
            assert result.exit_code == 0
            assert 'pushed successfully' in result.output

    def test_get(self, runner: CliRunner, env_vars: dict[str, str], sample_dashboard: dict) -> None:
        """Test getting dashboard details."""
        with aioresponses() as m:
            m.get(
                'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/my-dashboard/',
                payload={'definition': sample_dashboard},
            )

            result = runner.invoke(cli, ['get', 'my-dashboard'], env=env_vars)
            assert result.exit_code == 0
            assert 'kind: Dashboard' in result.output

    def test_delete_with_confirmation(self, runner: CliRunner, env_vars: dict[str, str]) -> None:
        """Test deleting a dashboard with confirmation flag."""
        with aioresponses() as m:
            m.delete(
                'https://logfire-us.pydantic.dev/ui-api/organizations/test-org/projects/test-project/dashboards/my-dashboard/',
                status=204,
            )

            result = runner.invoke(cli, ['delete', 'my-dashboard', '-y'], env=env_vars)
            assert result.exit_code == 0
            assert 'deleted' in result.output

    def test_init(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test creating a new dashboard template."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ['init', 'My New Dashboard'])
            assert result.exit_code == 0
            assert Path('my-new-dashboard.yaml').exists()

    def test_lint_valid(self, runner: CliRunner, temp_yaml_file: Path) -> None:
        """Test linting a valid dashboard file."""
        result = runner.invoke(cli, ['lint', str(temp_yaml_file)])
        assert result.exit_code == 0
        assert 'Valid' in result.output

    def test_lint_invalid(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test linting an invalid dashboard file."""
        bad_file = tmp_path / 'bad.yaml'
        bad_file.write_text('not: a dashboard')

        result = runner.invoke(cli, ['lint', str(bad_file)])
        assert result.exit_code == 1
        assert 'Validation failed' in result.output

    def test_missing_token(self, runner: CliRunner) -> None:
        """Test error when token is missing."""
        result = runner.invoke(cli, ['list'])
        assert result.exit_code != 0
        assert 'Missing option' in result.output or 'required' in result.output.lower()
