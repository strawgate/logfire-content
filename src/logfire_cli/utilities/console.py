from functools import lru_cache

from rich.console import Console
from rich.table import Table


@lru_cache(maxsize=1)
def get_console(stderr: bool = False) -> Console:
    """Get a console instance."""
    return Console(stderr=stderr)


@lru_cache(maxsize=1)
def get_error_console() -> Console:
    """Get an error console instance."""
    return Console(stderr=True)


def _print_normal(message: str, console: Console | None = None) -> None:
    """Print a message in normal."""
    console = console or get_console()
    console.print(message)


def _print_red(message: str, extra_message: str | None = None, console: Console | None = None) -> None:
    """Print a message in red."""
    console = console or get_console()
    console.print(f'[red]{message}[/red] {extra_message}')


def _print_green(message: str, extra_message: str | None = None, console: Console | None = None) -> None:
    """Print a message in green."""
    console = console or get_console()
    console.print(f'[green]{message}[/green] {extra_message}')


def _print_yellow(message: str, extra_message: str | None = None, console: Console | None = None) -> None:
    """Print a message in yellow."""
    console = console or get_console()
    console.print(f'[yellow]{message}[/yellow] {extra_message}')


def _print_dim(message: str, extra_message: str | None = None, console: Console | None = None) -> None:
    """Print a message in dim."""
    console = console or get_console()
    console.print(f'[dim]{message}[/dim] {extra_message}')


def print_error(message: str, extra_message: str | None = None, help_message: str | None = None) -> None:
    """Print an error message."""
    _print_red(message, extra_message=extra_message, console=get_error_console())
    if help_message:
        _print_dim(help_message, console=get_error_console())


def print_success(message: str, extra_message: str | None = None) -> None:
    """Print a success message."""
    _print_green(message, extra_message=extra_message, console=get_console())


def print_console(message: str) -> None:
    """Print a message to the console."""
    _print_normal(message, console=get_console())


def print_warning(message: str, extra_message: str | None = None) -> None:
    """Print a warning message."""
    _print_yellow(message, extra_message=extra_message, console=get_console())


def print_table(table: Table) -> None:
    """Print a table to the console."""
    get_console().print(table)
