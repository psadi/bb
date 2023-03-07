# -*- coding: utf-8 -*-

"""
bb: auth - validates and configures the auth details
"""

import typer
from bb.utils.ini import _setup, BB_CONFIG_FILE, parse, is_config_present
from bb.utils.validate import validate_config, error_tip, state
from bb.utils.richprint import traceback_to_console, console

_auth = typer.Typer(add_completion=False)
bold_red: str = "bold red"


@_auth.command()
def setup():
    """Configure bbcli to work with bitbucket"""
    try:
        if is_config_present():
            console.print(
                "Configuration file found, Run 'bb auth status' for more information"
            )
        _setup(
            typer.prompt("> bitbucket_host"),
            typer.prompt("> username"),
            typer.prompt("> token"),
        )
        typer.echo(
            f"Configuration written at '{BB_CONFIG_FILE}',"
            + "Please re-run 'bb auth test' to validate"
        )
    except Exception as err:
        console.print(f"ERROR: {err}", style=bold_red)
        if state["verbose"]:
            traceback_to_console()
        else:
            error_tip()


@_auth.command()
def test():
    """Test configuration & connection"""
    try:
        validate_config()
    except Exception as err:
        console.print(f"ERROR: {err}", style=bold_red)
        if state["verbose"]:
            traceback_to_console()
        else:
            error_tip()


@_auth.command()
def status(token: bool = typer.Option(False, help="Display auth token")):
    """View authentication config status"""
    try:
        if is_config_present():
            hcm: str = "[bold green]:heavy_check_mark:[/bold green]"
            console.print(
                f"{hcm} Configuration found at [bold cyan]{BB_CONFIG_FILE}[/bold cyan]"
            )
            username, _token, bitbucket_host = parse()
            console.print(
                f"{hcm} Will connect to [bold]{bitbucket_host}[/bold] as [bold]{username}[/bold]"
            )
            console.print(f"{hcm} Token: {'*' * len(_token) if not token else _token}")
        else:
            console.print("Configuration missing, run 'bb auth setup'")
            raise typer.Exit(code=1)
    except Exception as err:
        console.print(f"ERROR: {err}", style=bold_red)
        if state["verbose"]:
            traceback_to_console()
        else:
            error_tip()
