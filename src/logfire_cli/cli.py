"""Command-line interface for the Logfire CLI.

This module provides the main CLI commands for managing Logfire dashboards.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import rich_click as click
from rich.console import Console
from rich.table import Table

from logfire_cli import __version__
from logfire_cli.client import (
    LogfireAuthenticationError,
    LogfireClient,
    LogfireClientError,
    LogfireNotFoundError,
)

if TYPE_CHECKING:
    from collections.abc import Callable

# Configure rich-click styling
click.rich_click.USE_RICH_MARKUP = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True

console = Console()
error_console = Console(stderr=True)


def get_client_from_context(ctx: click.Context) -> LogfireClient:
    """Get the LogfireClient from the click context.

    Args:
        ctx: Click context with client parameters.

    Returns:
        Configured LogfireClient instance.

    Raises:
        click.UsageError: If required authentication parameters are missing.
    """
    token = ctx.obj.get('token')
    organization = ctx.obj.get('organization')
    project = ctx.obj.get('project')
    base_url = ctx.obj.get('base_url', 'https://logfire-us.pydantic.dev')

    if not token:
        msg = 'Missing required option: --token or LOGFIRE_TOKEN environment variable'
        raise click.UsageError(msg)
    if not organization:
        msg = 'Missing required option: --organization or LOGFIRE_ORGANIZATION environment variable'
        raise click.UsageError(msg)
    if not project:
        msg = 'Missing required option: --project or LOGFIRE_PROJECT environment variable'
        raise click.UsageError(msg)

    return LogfireClient(
        token=token,
        organization=organization,
        project=project,
        base_url=base_url,
    )


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
            error_console.print(f'[red]Authentication error:[/red] {e}')
            error_console.print('[dim]Check your LOGFIRE_TOKEN environment variable.[/dim]')
            sys.exit(1)
        except LogfireNotFoundError as e:
            error_console.print(f'[red]Not found:[/red] {e}')
            sys.exit(1)
        except LogfireClientError as e:
            error_console.print(f'[red]Error:[/red] {e}')
            sys.exit(1)
        except FileNotFoundError as e:
            error_console.print(f'[red]File not found:[/red] {e}')
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
    ctx.ensure_object(dict)
    ctx.obj['token'] = token
    ctx.obj['organization'] = organization
    ctx.obj['project'] = project
    ctx.obj['base_url'] = base_url


@cli.command('list')
@click.pass_context
@handle_errors
def list_dashboards(ctx: click.Context) -> None:
    """List all dashboards in the project."""
    with get_client_from_context(ctx) as client:
        dashboards = client.list_dashboards()

    if not dashboards:
        console.print('[yellow]No dashboards found.[/yellow]')
        return

    table = Table(title='Dashboards')
    table.add_column('Slug', style='cyan')
    table.add_column('Name', style='green')
    table.add_column('Updated', style='dim')

    for dashboard in dashboards:
        table.add_row(
            dashboard.get('slug', 'N/A'),
            dashboard.get('name', 'N/A'),
            dashboard.get('updatedAt', dashboard.get('updated_at', 'N/A')),
        )

    console.print(table)


@cli.command('pull')
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

    with get_client_from_context(ctx) as client:
        client.pull(slug, output)

    console.print(f'[green]Dashboard exported to:[/green] {output}')


@cli.command('push')
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
    with get_client_from_context(ctx) as client:
        result = client.push(file, slug)

    dashboard_slug = result.get('slug', slug or 'unknown')
    console.print(f'[green]Dashboard pushed successfully:[/green] {dashboard_slug}')


@cli.command('delete')
@click.argument('slug')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt.')
@click.pass_context
@handle_errors
def delete(ctx: click.Context, slug: str, yes: bool) -> None:
    """Delete a dashboard.

    SLUG is the dashboard identifier to delete.
    """
    if not yes:
        click.confirm(f'Are you sure you want to delete dashboard "{slug}"?', abort=True)

    with get_client_from_context(ctx) as client:
        client.delete_dashboard(slug)

    console.print(f'[green]Dashboard deleted:[/green] {slug}')


@cli.command('get')
@click.argument('slug')
@click.pass_context
@handle_errors
def get_dashboard(ctx: click.Context, slug: str) -> None:
    """Get dashboard details and print to stdout.

    SLUG is the dashboard identifier.
    """
    import yaml

    with get_client_from_context(ctx) as client:
        definition = client.get_dashboard(slug)

    console.print(yaml.dump(definition, default_flow_style=False, sort_keys=False, allow_unicode=True))


@cli.command('lint')
@click.argument('files', nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option('--strict', is_flag=True, help='Treat warnings as errors.')
def lint(files: tuple[Path, ...], strict: bool) -> None:  # noqa: ARG001
    """Validate dashboard YAML files.

    FILES are the paths to YAML dashboard files to validate.

    This command wraps percli lint if available, otherwise performs
    basic YAML validation.

    Note: The strict flag is reserved for future use with percli warnings.
    """
    if not files:
        error_console.print('[yellow]No files specified.[/yellow]')
        sys.exit(0)

    # Check if percli is available
    percli_available = _check_percli()

    has_errors = False

    for file_path in files:
        console.print(f'[dim]Validating:[/dim] {file_path}')

        if percli_available:
            # Use percli for full Perses validation
            result = subprocess.run(  # noqa: S603
                ['percli', 'lint', '-f', str(file_path)],  # noqa: S607
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                has_errors = True
                error_console.print(f'[red]Validation failed:[/red] {file_path}')
                if result.stderr:
                    error_console.print(result.stderr)
                if result.stdout:
                    console.print(result.stdout)
            else:
                console.print(f'[green]Valid:[/green] {file_path}')
        else:
            # Fall back to basic YAML validation
            try:
                _validate_yaml_structure(file_path)
                console.print(f'[green]Valid:[/green] {file_path}')
            except ValueError as e:
                has_errors = True
                error_console.print(f'[red]Validation failed:[/red] {file_path}')
                error_console.print(f'  {e}')

    if has_errors:
        sys.exit(1)


def _check_percli() -> bool:
    """Check if percli is available on the system.

    Returns:
        True if percli is available, False otherwise.
    """
    try:
        result = subprocess.run(
            ['percli', 'version'],  # noqa: S607
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        return False
    else:
        return result.returncode == 0


def _validate_yaml_structure(path: Path) -> None:
    """Perform basic YAML structure validation.

    Args:
        path: Path to the YAML file.

    Raises:
        ValueError: If the YAML structure is invalid.
    """
    import yaml

    with path.open() as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        msg = 'Dashboard must be a YAML mapping/dictionary'
        raise TypeError(msg)

    if data.get('kind') != 'Dashboard':
        msg = 'Dashboard must have kind: Dashboard'
        raise ValueError(msg)

    if 'metadata' not in data:
        msg = 'Dashboard must have metadata section'
        raise ValueError(msg)

    if 'spec' not in data:
        msg = 'Dashboard must have spec section'
        raise ValueError(msg)

    metadata = data['metadata']
    if not isinstance(metadata, dict) or 'name' not in metadata:
        msg = 'Dashboard metadata must include name'
        raise ValueError(msg)


@cli.command('init')
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
    import yaml

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

    with output.open('w') as f:
        yaml.dump(template, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    console.print(f'[green]Dashboard template created:[/green] {output}')
    console.print('[dim]Edit the file and use "logfire-cli push" to upload it.[/dim]')


if __name__ == '__main__':
    cli()
