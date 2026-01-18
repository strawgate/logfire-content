"""Tests for Pydantic models."""

from __future__ import annotations

from logfire_cli.models import Dashboard, DashboardListItem, DashboardMetadata


class TestDashboardModels:
    """Tests for dashboard models."""

    def test_dashboard_metadata(self) -> None:
        metadata = DashboardMetadata(name='test-dashboard', project='my-project')
        assert metadata.name == 'test-dashboard'
        assert metadata.project == 'my-project'
        assert metadata.version is None

    def test_dashboard_metadata_with_alias(self) -> None:
        metadata = DashboardMetadata(
            name='test',
            createdAt='2024-01-01T00:00:00Z',
            updatedAt='2024-01-02T00:00:00Z',
        )
        assert metadata.created_at == '2024-01-01T00:00:00Z'
        assert metadata.updated_at == '2024-01-02T00:00:00Z'

    def test_dashboard_list_item(self) -> None:
        item = DashboardListItem(
            slug='my-dashboard',
            name='My Dashboard',
            createdAt='2024-01-01T00:00:00Z',
        )
        assert item.slug == 'my-dashboard'
        assert item.name == 'My Dashboard'
        assert item.created_at == '2024-01-01T00:00:00Z'

    def test_full_dashboard(self, sample_dashboard: dict) -> None:
        dashboard = Dashboard.model_validate(sample_dashboard)
        assert dashboard.kind == 'Dashboard'
        assert dashboard.metadata.name == 'test-dashboard'
        assert dashboard.spec.display.name == 'Test Dashboard'
        assert dashboard.spec.duration == '1h'
        assert 'TestPanel' in dashboard.spec.panels
