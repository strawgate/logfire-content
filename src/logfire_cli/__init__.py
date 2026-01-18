"""Logfire CLI - A tool for managing Pydantic Logfire dashboards.

This package provides a CLI for interacting with Logfire's dashboard API,
allowing users to pull, push, list, and validate Perses YAML dashboards.
"""

from logfire_cli.client import LogfireClient
from logfire_cli.models import Dashboard, DashboardMetadata

__version__ = '0.1.0'
__all__ = ['Dashboard', 'DashboardMetadata', 'LogfireClient', '__version__']
