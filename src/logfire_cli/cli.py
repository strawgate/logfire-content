"""Command-line interface for the Logfire CLI.

This module provides the main CLI commands for managing Logfire dashboards.
"""

import asyncio
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import rich_click as click
from pydantic import BaseModel
from rich.table import Table

from logfire_cli import __version__
from logfire_cli.clients.logfire_api import (
    LogfireAuthenticationError,
    LogfireClient,
    LogfireClientError,
    LogfireNotFoundError,
)
from logfire_cli.models.logfire_api import Dashboard, ListDashboards
from logfire_cli.utilities.console import (
    get_console,
    get_error_console,
    print_error,
    print_console,
    print_success,
    print_table,
    print_warning,
)
from logfire_cli.utilities.file import dump_model_to_yaml, dump_model_to_yaml_file, load_model_from_yaml

# Configure rich-click styling
click.rich_click.TEXT_MARKUP = 'rich'
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True


class CLIContext(BaseModel):
    """Context for the CLI."""

    token: str | None = None
    organization: str | None = None
    project: str | None = None
    base_url: str = 'https://logfire-us.pydantic.dev'

    def to_client(self) -> LogfireClient:
        """Convert the context to a Logfire client."""
        if self.token is None:
            msg = 'Missing required option: --token or LOGFIRE_TOKEN environment variable'
            raise click.UsageError(msg)
        if self.organization is None:
            msg = 'Missing required option: --organization or LOGFIRE_ORGANIZATION environment variable'
            raise click.UsageError(msg)
        if self.project is None:
            msg = 'Missing required option: --project or LOGFIRE_PROJECT environment variable'
            raise click.UsageError(msg)
        return LogfireClient(
            token=self.token,
            organization=self.organization,
            project=self.project,
            base_url=self.base_url,
        )


def _get_client_from_context(ctx: click.Context) -> LogfireClient:
    if not isinstance(ctx.obj, CLIContext):  # pyright: ignore[reportAny]
        msg = 'Context object is not a CLIContext'
        raise click.UsageError(msg)
    return ctx.obj.to_client()


def handle_errors(func: Callable[..., None]) -> Callable[..., None]:
    """Decorator to handle common client errors.

    Args:
        func: The CLI command function to wrap.

    Returns:
        Wrapped function with error handling.
    """

    def wrapper(*args: object, **kwargs: object) -> None:
        try:
            func(*args, **kwargs)
        except LogfireAuthenticationError as e:
            print_error(message='Authentication error', extra_message=str(e), help_message='Check your LOGFIRE_TOKEN environment variable.')
            sys.exit(1)
        except LogfireNotFoundError as e:
            print_error(message='Not found', extra_message=str(e))
            sys.exit(1)
        except LogfireClientError as e:
            print_error(message='Error', extra_message=str(e))
            sys.exit(1)
        except FileNotFoundError as e:
            print_error(message='File not found', extra_message=str(e))
            sys.exit(1)

    return wrapper


@click.group()
@click.version_option(version=__version__, prog_name='logfire-cli')
@click.option(
    '--token',
    envvar='LOGFIRE_TOKEN',
    help='Logfire API token. Can also be set via LOGFIRE_TOKEN env var.',
)
@click.option(
    '--organization',
    '-o',
    envvar='LOGFIRE_ORGANIZATION',
    help='Logfire organization slug. Can also be set via LOGFIRE_ORGANIZATION env var.',
)
@click.option(
    '--project',
    '-p',
    envvar='LOGFIRE_PROJECT',
    help='Logfire project slug. Can also be set via LOGFIRE_PROJECT env var.',
)
@click.option(
    '--base-url',
    envvar='LOGFIRE_BASE_URL',
    default='https://logfire-us.pydantic.dev',
    help='Logfire API base URL.',
)
@click.pass_context
def cli(
    ctx: click.Context,
    token: str | None,
    organization: str | None,
    project: str | None,
    base_url: str,
) -> None:
    """Logfire CLI - Manage Pydantic Logfire dashboards.

    A CLI tool for interacting with Logfire's dashboard API to pull, push,
    list, and validate Perses YAML dashboards.

    [bold]Configuration:[/bold]

    Set these environment variables to avoid passing them every time:

      LOGFIRE_TOKEN         Your Logfire API token
      LOGFIRE_ORGANIZATION  Your organization slug
      LOGFIRE_PROJECT       Your project slug
    """
    ctx.obj = CLIContext(
        token=token,
        organization=organization,
        project=project,
        base_url=base_url,
    )


@cli.group('dashboards')
def dashboards_group() -> None:
    """Manage Logfire dashboards."""


@dashboards_group.command('list')
@click.pass_context
@handle_errors
def list_dashboards(ctx: click.Context) -> None:
    """List all dashboards in the project."""
    asyncio.run(_async_list_dashboards(ctx=ctx))


def _print_dashboards(dashboards: ListDashboards) -> None:
    table = Table(title='Dashboards')
    table.add_column('Slug', style='cyan')
    table.add_column('Name', style='green')
    table.add_column('Updated', style='dim')

    for dashboard in dashboards.root:
        row_slug = dashboard.dashboard_slug
        row_name = dashboard.dashboard_name
        row_updated = dashboard.updated_at.isoformat() if dashboard.updated_at else ''
        table.add_row(row_slug, row_name, row_updated)

    print_table(table=table)


async def _async_list_dashboards(ctx: click.Context) -> None:
    async with _get_client_from_context(ctx) as client:
        dashboards: ListDashboards = await client.list_dashboards()

    if len(dashboards.root) == 0:
        print_warning(message='No dashboards found.')
        return

    _print_dashboards(dashboards=dashboards)


@dashboards_group.command('pull')
@click.argument('slug')
@click.option(
    '--output',
    '-o',
    type=click.Path(path_type=Path),
    help='Output file path. Defaults to <slug>.yaml',
)
@click.pass_context
@handle_errors
def pull(ctx: click.Context, slug: str, output: Path | None) -> None:
    """Export a dashboard to a Perses YAML file.

    SLUG is the dashboard identifier to export.
    """
    if output is None:
        output = Path(f'{slug}.yaml')

    asyncio.run(_async_pull(ctx=ctx, slug=slug, output=output))
    get_console().print(f'[green]Dashboard exported to:[/green] {output}')


async def _async_pull(ctx: click.Context, slug: str, output: Path) -> None:
    """Async implementation of pull command."""
    import yaml

    async with _get_client_from_context(ctx) as client:
        dashboard: Dashboard = await client.get_dashboard(slug)

    # Convert Dashboard model to dict for YAML serialization
    dashboard_dict = dashboard.model_dump(mode='json', exclude_none=True, by_alias=True)

    with output.open('w') as f:
        yaml.dump(dashboard_dict, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


@dashboards_group.command('push')
@click.argument('file', type=click.Path(exists=True, path_type=Path))
@click.option(
    '--slug',
    '-s',
    help='Override the dashboard slug. Defaults to metadata.name from YAML.',
)
@click.pass_context
@handle_errors
def push(ctx: click.Context, file: Path, slug: str | None) -> None:
    """Import a Perses YAML dashboard to Logfire.

    FILE is the path to the YAML dashboard file.
    """
    dashboard_slug = asyncio.run(_async_push(ctx=ctx, file=file, slug=slug))
    get_console().print(f'[green]Dashboard pushed successfully:[/green] {dashboard_slug}')


async def _async_push(ctx: click.Context, file: Path, slug: str | None) -> str:
    """Async implementation of push command."""
    dashboard = load_model_from_yaml(path=file, model=Dashboard)

    # Determine slug: use provided slug, or derive from metadata.name
    if slug is None:
        slug = dashboard.metadata.name

    # Push dashboard (create or update)
    async with _get_client_from_context(ctx) as client:
        _ = await client.update_dashboard(slug, dashboard)

    return slug


@dashboards_group.command('delete')
@click.argument('slug')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt.')
@click.pass_context
@handle_errors
def delete(ctx: click.Context, slug: str, yes: bool) -> None:
    """Delete a dashboard.

    SLUG is the dashboard identifier to delete.
    """
    if not yes:
        _ = click.confirm(f'Are you sure you want to delete dashboard "{slug}"?', abort=True)

    asyncio.run(_async_delete(ctx=ctx, slug=slug))
    get_console().print(f'[green]Dashboard deleted:[/green] {slug}')


async def _async_delete(ctx: click.Context, slug: str) -> None:
    """Async implementation of delete command."""
    async with _get_client_from_context(ctx) as client:
        await client.delete_dashboard(slug)


@dashboards_group.command('get')
@click.argument('slug')
@click.pass_context
@handle_errors
def get_dashboard(ctx: click.Context, slug: str) -> None:
    """Get dashboard details and print to stdout.

    SLUG is the dashboard identifier.
    """
    asyncio.run(_async_get_dashboard(ctx=ctx, slug=slug))


async def _async_get_dashboard(ctx: click.Context, slug: str) -> None:
    """Async implementation of get command."""
    async with _get_client_from_context(ctx) as client:
        dashboard: Dashboard = await client.get_dashboard(slug)

    get_console().print(dump_model_to_yaml(model=dashboard))


@dashboards_group.command('init')
@click.argument('name')
@click.option(
    '--output',
    '-o',
    type=click.Path(path_type=Path),
    help='Output file path. Defaults to <name>.yaml',
)
def init(name: str, output: Path | None) -> None:
    """Create a new dashboard template.

    NAME is the display name for the new dashboard.
    """
    if output is None:
        slug = name.lower().replace(' ', '-').replace('_', '-')
        output = Path(f'{slug}.yaml')

    template = {
        'kind': 'Dashboard',
        'metadata': {
            'name': name.lower().replace(' ', '-'),
            'project': os.environ.get('LOGFIRE_PROJECT', 'your-project'),
        },
        'spec': {
            'display': {
                'name': name,
            },
            'panels': {
                'ExamplePanel': {
                    'kind': 'Panel',
                    'spec': {
                        'display': {
                            'name': 'Example Panel',
                        },
                        'plugin': {
                            'kind': 'TimeSeriesChart',
                            'spec': {
                                'legend': {
                                    'position': 'bottom',
                                },
                            },
                        },
                        'queries': [
                            {
                                'kind': 'TimeSeriesQuery',
                                'spec': {
                                    'plugin': {
                                        'kind': 'LogfireTimeSeriesQuery',
                                        'spec': {
                                            'query': 'SELECT\n'
                                            '  time_bucket($resolution, start_timestamp) AS x,\n'
                                            '  count(1) as y\n'
                                            'FROM records\n'
                                            'GROUP BY x\n'
                                            'ORDER BY x',
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
                                'content': {
                                    '$ref': '#/spec/panels/ExamplePanel',
                                },
                            },
                        ],
                    },
                },
            ],
            'duration': '1h',
            'refreshInterval': '0s',
        },
    }

    dump_model_to_yaml_file(model=Dashboard.model_validate(template), path=output)

    print_success(message='Dashboard template created', extra_message=str(output))
    print_console(message='Edit the file and use "logfire-cli dashboards push" to upload it.')


if __name__ == '__main__':
    cli()
