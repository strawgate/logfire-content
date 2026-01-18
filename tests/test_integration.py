"""Integration tests for the CLI commands against a real Logfire instance.

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
    make test-integration
    # or
    pytest -m integration tests/test_integration.py

    # Update snapshots after API changes
    make test-integration-update
    # or
    pytest -m integration --inline-snapshot=update tests/test_integration.py

    # Skip integration tests (useful in CI)
    pytest -m "not integration"
"""

import os
from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner
from inline_snapshot import snapshot

from logfire_cli.cli import cli


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


@pytest.fixture(scope='session')
def skip_if_no_env(integration_env_vars: dict[str, str] | None) -> dict[str, str]:
    """Skip test if integration env vars are not set."""
    if integration_env_vars is None:
        pytest.skip('Integration tests require LOGFIRE_TOKEN, LOGFIRE_ORGANIZATION, and LOGFIRE_PROJECT env vars')
    return integration_env_vars


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI runner."""
    return CliRunner()


@pytest.mark.integration
class TestIntegration:
    """Integration tests against a real Logfire instance."""

    def test_dashboards_list(self, runner: CliRunner, skip_if_no_env: dict[str, str]) -> None:
        """Test listing dashboards against real API."""
        result = runner.invoke(cli, ['dashboards', 'list'], env=skip_if_no_env)
        assert result.exit_code == 0
        # Snapshot the output to track changes in dashboard list
        # Update snapshots with: pytest --inline-snapshot=update tests/test_integration.py
        assert result.output == snapshot("""\
                                 Dashboards                                 \n\
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Slug              ┃ Name              ┃ Updated                          ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ my-test-dashboard │ my test dashboard │ 2026-01-18T19:20:25.310030+00:00 │
└───────────────────┴───────────────────┴──────────────────────────────────┘
""")

    def test_dashboards_list_empty_output(self, runner: CliRunner, skip_if_no_env: dict[str, str]) -> None:
        """Test listing dashboards - check output structure."""
        result = runner.invoke(cli, ['dashboards', 'list'], env=skip_if_no_env)
        assert result.exit_code == 0
        # Check that output contains expected structure (table headers)
        assert 'Slug' in result.output or 'No dashboards found' in result.output

    def test_dashboards_get_nonexistent(self, runner: CliRunner, skip_if_no_env: dict[str, str]) -> None:
        """Test getting a nonexistent dashboard."""
        result = runner.invoke(cli, ['dashboards', 'get', 'nonexistent-dashboard-12345'], env=skip_if_no_env)
        assert result.exit_code != 0
        assert 'Not found' in result.output or '404' in result.output or 'error' in result.output.lower()

    def test_dashboards_init(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test creating a dashboard template."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ['dashboards', 'init', 'Integration Test Dashboard'])
            assert result.exit_code == 0
            assert Path('integration-test-dashboard.yaml').exists()

            # Check file contents
            with Path('integration-test-dashboard.yaml').open() as f:
                content = yaml.safe_load(f)  # pyright: ignore[reportAny]
                assert content['kind'] == 'Dashboard'
                assert content['metadata']['name'] == 'integration-test-dashboard'
                assert content['spec']['display']['name'] == 'Integration Test Dashboard'

    def test_dashboards_import_and_export(
        self,
        runner: CliRunner,
        skip_if_no_env: dict[str, str],
        tmp_path: Path,
    ) -> None:
        """Test importing and exporting a dashboard."""
        # Create a test dashboard
        test_dashboard: dict[str, Any] = {
            'kind': 'Dashboard',
            'metadata': {
                'name': 'integration-test-dashboard',
                'project': skip_if_no_env['LOGFIRE_PROJECT'],
            },
            'spec': {
                'display': {
                    'name': 'Integration Test Dashboard',
                },
                'panels': {
                    'TestPanel': {
                        'kind': 'Panel',
                        'spec': {
                            'display': {
                                'name': 'Test Panel',
                            },
                            'plugin': {
                                'kind': 'TimeSeriesChart',
                                'spec': {},
                            },
                            'queries': [
                                {
                                    'kind': 'TimeSeriesQuery',
                                    'spec': {
                                        'plugin': {
                                            'kind': 'LogfireTimeSeriesQuery',
                                            'spec': {
                                                'query': (
                                                    'SELECT time_bucket($resolution, start_timestamp) AS x, '
                                                    'count(1) as y FROM records GROUP BY x ORDER BY x'
                                                ),
                                            },
                                        },
                                    },
                                },
                            ],
                        },
                    },
                },
                'layouts': [
                    {
                        'kind': 'Grid',
                        'spec': {
                            'items': [
                                {
                                    'x': 0,
                                    'y': 0,
                                    'width': 12,
                                    'height': 6,
                                    'content': {'$ref': '#/spec/panels/TestPanel'},
                                },
                            ],
                        },
                    },
                ],
                'duration': '1h',
                'refreshInterval': '0s',
            },
        }

        dashboard_file = tmp_path / 'test-dashboard.yaml'
        with dashboard_file.open('w') as f:
            yaml.dump(test_dashboard, f)

        # Import the dashboard
        import_result = runner.invoke(
            cli,
            ['dashboards', 'import', str(dashboard_file)],
            env=skip_if_no_env,
        )
        assert import_result.exit_code == 0
        assert 'imported successfully' in import_result.output.lower()

        # Export the dashboard back
        exported_file = tmp_path / 'exported-dashboard.yaml'
        export_result = runner.invoke(
            cli,
            ['dashboards', 'export', 'integration-test-dashboard', '-o', str(exported_file)],
            env=skip_if_no_env,
        )
        assert export_result.exit_code == 0
        assert exported_file.exists()

        # Verify the exported dashboard structure
        with exported_file.open() as f:
            exported_content = yaml.safe_load(f)  # pyright: ignore[reportAny]
            assert exported_content['kind'] == 'Dashboard'
            assert exported_content['metadata']['name'] == 'integration-test-dashboard'
            assert exported_content['spec']['display']['name'] == 'Integration Test Dashboard'

        # Get the dashboard via get command
        get_result = runner.invoke(
            cli,
            ['dashboards', 'get', 'integration-test-dashboard'],
            env=skip_if_no_env,
        )
        assert get_result.exit_code == 0
        get_content = yaml.safe_load(get_result.output)  # pyright: ignore[reportAny]
        assert get_content['kind'] == 'Dashboard'
        assert get_content['metadata']['name'] == 'integration-test-dashboard'

        # Snapshot the YAML output structure (normalized)
        normalized_content = {
            'kind': get_content['kind'],
            'metadata': {
                'name': get_content['metadata']['name'],
                'project': get_content['metadata'].get('project'),  # pyright: ignore[reportAny]
            },
            'spec': {
                'display': get_content['spec']['display'],
                'panels_count': len(get_content['spec'].get('panels', {})),  # pyright: ignore[reportAny]
                'layouts_count': len(get_content['spec'].get('layouts', [])),  # pyright: ignore[reportAny]
            },
        }
        assert normalized_content == snapshot()

        # Clean up: delete the dashboard
        delete_result = runner.invoke(
            cli,
            ['dashboards', 'delete', 'integration-test-dashboard', '-y'],
            env=skip_if_no_env,
        )
        assert delete_result.exit_code == 0

    def test_dashboards_get_existing(self, runner: CliRunner, skip_if_no_env: dict[str, str]) -> None:
        """Test getting an existing dashboard (if any exist)."""
        # First, list dashboards to see if any exist
        list_result = runner.invoke(cli, ['dashboards', 'list'], env=skip_if_no_env)
        assert list_result.exit_code == 0

        # If there are dashboards, try to get the first one
        # This is a bit fragile, but we'll extract a slug from the output if possible
        if 'No dashboards found' not in list_result.output:
            # Try to find a dashboard slug in the output
            # The output is a table, so we need to parse it
            lines = list_result.output.split('\n')
            # Look for lines that might contain dashboard slugs (non-header, non-empty lines)
            for line in lines:
                # Skip empty lines and headers
                if not line.strip() or 'Slug' in line or '─' in line or '│' not in line:
                    continue
                # Try to extract slug (first column in table)
                parts = [p.strip() for p in line.split('│') if p.strip()]
                if parts:
                    slug = parts[0]
                    # Get this dashboard
                    get_result = runner.invoke(
                        cli,
                        ['dashboards', 'get', slug],
                        env=skip_if_no_env,
                    )
                    assert get_result.exit_code == 0
                    # Verify it's valid YAML
                    content = yaml.safe_load(get_result.output)  # pyright: ignore[reportAny]
                    assert content['kind'] == 'Dashboard'
                    assert 'metadata' in content
                    assert 'spec' in content
                    break
