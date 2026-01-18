"""Pydantic models for Logfire dashboard API interactions.

This module defines the data models used for representing Perses dashboards
and their components when interacting with the Logfire API.
"""

from datetime import datetime
from typing import Any, ClassVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, RootModel


class DashboardMetadata(BaseModel):
    """Metadata for a Perses dashboard."""

    name: str = Field(..., description='Dashboard name/identifier')
    project: str | None = Field(default=None, description='Project the dashboard belongs to')
    version: int | None = Field(default=None, description='Dashboard version number')
    created_at: str | None = Field(default=None, alias='createdAt', description='Creation timestamp')
    updated_at: str | None = Field(default=None, alias='updatedAt', description='Last update timestamp')

    model_config: ClassVar[ConfigDict] = ConfigDict(populate_by_name=True)


class DashboardDisplay(BaseModel):
    """Display settings for a dashboard."""

    name: str = Field(..., description='Display name shown in the UI')
    description: str | None = Field(default=None, description='Dashboard description')


class DashboardSpec(BaseModel):
    """Specification for a Perses dashboard."""

    display: DashboardDisplay = Field(..., description='Display settings')
    datasources: dict[str, Any] = Field(default_factory=dict, description='Datasource definitions')
    panels: dict[str, Any] = Field(default_factory=dict, description='Panel definitions')
    layouts: list[Any] = Field(default_factory=list, description='Layout definitions')
    variables: list[Any] = Field(default_factory=list, description='Dashboard variables')
    duration: str = Field(default='1h', description='Default time range duration')
    refresh_interval: str = Field(default='0s', alias='refreshInterval', description='Auto-refresh interval')

    model_config: ClassVar[ConfigDict] = ConfigDict(populate_by_name=True)


class Dashboard(BaseModel):
    """A Perses dashboard definition.

    This model represents the full structure of a Perses dashboard as used
    by Logfire. It follows the Perses dashboard schema with Logfire-specific
    query plugins.
    """

    kind: str = Field(default='Dashboard', description='Resource kind (always "Dashboard")')
    metadata: DashboardMetadata = Field(..., description='Dashboard metadata')
    spec: DashboardSpec = Field(..., description='Dashboard specification')

    model_config: ClassVar[ConfigDict] = ConfigDict(populate_by_name=True)


class PreconfiguredBaseModel(BaseModel):
    """A pre-configured BaseModel for deserializing Logfire responses."""

    model_config: ClassVar[ConfigDict] = ConfigDict(populate_by_name=True, extra='forbid', frozen=True, use_attribute_docstrings=True)


class PreconfiguredRootModel(RootModel[Any]):
    """A pre-configured RootModel for deserializing Logfire responses."""

    model_config: ClassVar[ConfigDict] = ConfigDict(populate_by_name=True, frozen=True, use_attribute_docstrings=True)


class ListDashboardItem(PreconfiguredBaseModel):
    """A single dashboard item from the list dashboards API response.

    {
        "id": "d87a3b26-4100-4026-9b42-ee4bbffe215e",
        "project_id": "4fbc915c-7847-4088-8516-05a1026b2b47",
        "created_at": "2025-12-16T04:37:26.837478Z",
        "updated_at": "2026-01-18T02:00:59.541420Z",
        "created_by_name": "strawgate",
        "updated_by_name": "strawgate",
        "dashboard_name": "my test dashboard",
        "dashboard_slug": "my-test-dashboard"
    }
    """

    id: UUID = Field(..., description='Dashboard ID')
    project_id: UUID = Field(..., description='Project ID')
    created_at: datetime = Field(..., description='Creation timestamp')
    updated_at: datetime | None = Field(default=None, description='Last update timestamp')
    created_by_name: str = Field(..., description='Created by name')
    updated_by_name: str | None = Field(..., description='Updated by name')
    dashboard_name: str = Field(..., description='Dashboard name')
    dashboard_slug: str = Field(..., description='Dashboard slug')


class ListDashboards(PreconfiguredRootModel):
    """A list of dashboard items from the list dashboards API response."""

    root: list[ListDashboardItem]

class GetDashboardResponse(PreconfiguredBaseModel):
    """API response wrapper for a single dashboard."""

    dashboard: Dashboard = Field(..., description='Dashboard definition')

class DashboardResponse(PreconfiguredBaseModel):
    """API response wrapper for a single dashboard.

    The API returns dashboards wrapped in this structure:
    {
        "id": "b08a77b8-0761-4bab-9efe-8b6f82997903",
        "project_id": "4fbc915c-7847-4088-8516-05a1026b2b47",
        "created_at": "2026-01-18T20:45:30.305002Z",
        "updated_at": null,
        "created_by_name": "strawgate",
        "updated_by_name": null,
        "dashboard_name": "test-create",
        "dashboard_slug": "test-create",
        "definition": {
            "kind": "Dashboard",
            ...
        }
    }
    """

    id: UUID = Field(..., description='Dashboard ID')
    project_id: UUID = Field(..., description='Project ID')
    created_at: datetime = Field(..., description='Creation timestamp')
    updated_at: datetime | None = Field(default=None, description='Last update timestamp')
    created_by_name: str = Field(..., description='Created by name')
    updated_by_name: str | None = Field(default=None, description='Updated by name')
    dashboard_name: str = Field(..., description='Dashboard name')
    dashboard_slug: str = Field(..., description='Dashboard slug')
    definition: Dashboard = Field(..., description='Dashboard definition')


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
