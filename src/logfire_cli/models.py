"""Pydantic models for Logfire dashboard API interactions.

This module defines the data models used for representing Perses dashboards
and their components when interacting with the Logfire API.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DashboardMetadata(BaseModel):
    """Metadata for a Perses dashboard."""

    name: str = Field(..., description='Dashboard name/identifier')
    project: str | None = Field(default=None, description='Project the dashboard belongs to')
    version: int | None = Field(default=None, description='Dashboard version number')
    created_at: str | None = Field(default=None, alias='createdAt', description='Creation timestamp')
    updated_at: str | None = Field(default=None, alias='updatedAt', description='Last update timestamp')

    model_config = {'populate_by_name': True}


class DashboardDisplay(BaseModel):
    """Display settings for a dashboard."""

    name: str = Field(..., description='Display name shown in the UI')


class DashboardSpec(BaseModel):
    """Specification for a Perses dashboard."""

    display: DashboardDisplay = Field(..., description='Display settings')
    panels: dict[str, Any] = Field(default_factory=dict, description='Panel definitions')
    layouts: list[Any] = Field(default_factory=list, description='Layout definitions')
    variables: list[Any] = Field(default_factory=list, description='Dashboard variables')
    duration: str = Field(default='1h', description='Default time range duration')
    refresh_interval: str = Field(default='0s', alias='refreshInterval', description='Auto-refresh interval')

    model_config = {'populate_by_name': True}


class Dashboard(BaseModel):
    """A Perses dashboard definition.

    This model represents the full structure of a Perses dashboard as used
    by Logfire. It follows the Perses dashboard schema with Logfire-specific
    query plugins.
    """

    kind: str = Field(default='Dashboard', description='Resource kind (always "Dashboard")')
    metadata: DashboardMetadata = Field(..., description='Dashboard metadata')
    spec: DashboardSpec = Field(..., description='Dashboard specification')

    model_config = {'populate_by_name': True}


class DashboardListItem(BaseModel):
    """Summary information for a dashboard in list responses."""

    slug: str = Field(..., description='URL-safe dashboard identifier')
    name: str = Field(..., description='Display name')
    created_at: str | None = Field(default=None, alias='createdAt', description='Creation timestamp')
    updated_at: str | None = Field(default=None, alias='updatedAt', description='Last update timestamp')

    model_config = {'populate_by_name': True}


class LogfireTimeSeriesQuerySpec(BaseModel):
    """Specification for a Logfire time series query.

    This is the Logfire-specific query plugin that uses SQL against the
    records and metrics tables.
    """

    query: str = Field(..., description='SQL query for the time series data')


class LogfireTimeSeriesQuery(BaseModel):
    """A Logfire time series query plugin.

    This replaces the standard PrometheusTimeSeriesQuery in Perses with
    Logfire-specific SQL queries.
    """

    kind: str = Field(default='LogfireTimeSeriesQuery', description='Plugin kind')
    spec: LogfireTimeSeriesQuerySpec = Field(..., description='Query specification')
