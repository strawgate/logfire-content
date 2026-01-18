"""Pytest configuration and fixtures for logfire-cli tests."""

from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def sample_dashboard() -> dict[str, Any]:
    """Provide a sample dashboard definition for testing."""
    return {
        'kind': 'Dashboard',
        'metadata': {
            'name': 'test-dashboard',
            'project': 'test-project',
        },
        'spec': {
            'display': {
                'name': 'Test Dashboard',
            },
            'datasources': {},
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
                                            'query': """
                                            SELECT time_bucket($resolution, start_timestamp) AS x, count(1) as y
                                            FROM records
                                            GROUP BY x
                                            ORDER BY x
                                            """
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


@pytest.fixture
def temp_yaml_file(tmp_path: Path, sample_dashboard: dict[str, Any]) -> Path:
    """Create a temporary YAML file with a sample dashboard."""
    import yaml

    file_path = tmp_path / 'test-dashboard.yaml'
    with file_path.open('w') as f:
        yaml.dump(sample_dashboard, f)
    return file_path
