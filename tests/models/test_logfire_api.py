"""Tests for Pydantic models."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from logfire_cli.models.logfire_api import Dashboard, DashboardMetadata, ListDashboardItem, ListDashboards


class TestDashboardModels:
    """Tests for dashboard models."""

    def test_dashboard_metadata(self) -> None:
        """Test DashboardMetadata model."""
        metadata = DashboardMetadata(name='test-dashboard', project='my-project')
        assert metadata.name == 'test-dashboard'
        assert metadata.project == 'my-project'
        assert metadata.version is None

    def test_dashboard_metadata_with_alias(self) -> None:
        """Test DashboardMetadata with field aliases."""
        metadata = DashboardMetadata(
            name='test',
            createdAt='2024-01-01T00:00:00Z',
            updatedAt='2024-01-02T00:00:00Z',
        )
        assert metadata.created_at == '2024-01-01T00:00:00Z'
        assert metadata.updated_at == '2024-01-02T00:00:00Z'

    def test_list_dashboard_item(self) -> None:
        """Test ListDashboardItem model."""
        item = ListDashboardItem(
            id=uuid4(),
            project_id=uuid4(),
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            updated_at=datetime(2024, 1, 2, tzinfo=UTC),
            created_by_name='test-user',
            updated_by_name='test-user',
            dashboard_name='My Dashboard',
            dashboard_slug='my-dashboard',
        )
        assert item.dashboard_slug == 'my-dashboard'
        assert item.dashboard_name == 'My Dashboard'
        assert isinstance(item.created_at, datetime)

    def test_list_dashboards(self) -> None:
        """Test ListDashboards root model."""
        items = [
            {
                'id': str(uuid4()),
                'project_id': str(uuid4()),
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-02T00:00:00Z',
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
        dashboards = ListDashboards.model_validate(items)
        assert len(dashboards.root) == 2
        assert dashboards.root[0].dashboard_slug == 'dashboard-1'
        assert dashboards.root[1].dashboard_slug == 'dashboard-2'

    def test_full_dashboard(self, sample_dashboard: dict[str, Any]) -> None:
        """Test full Dashboard model."""
        dashboard = Dashboard.model_validate(sample_dashboard)
        assert dashboard.kind == 'Dashboard'
        assert dashboard.metadata.name == 'test-dashboard'
        assert dashboard.spec.display.name == 'Test Dashboard'
        assert dashboard.spec.duration == '1h'
        assert 'TestPanel' in dashboard.spec.panels
