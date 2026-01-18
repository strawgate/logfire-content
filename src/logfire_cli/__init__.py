"""Logfire CLI - A tool for managing Pydantic Logfire dashboards.

This package provides a CLI for interacting with Logfire's dashboard API,
allowing users to pull, push, list, and validate Perses YAML dashboards.
"""

from logfire_cli.clients.logfire_api import LogfireClient

__version__ = '0.1.0'
__all__ = ['LogfireClient', '__version__']
