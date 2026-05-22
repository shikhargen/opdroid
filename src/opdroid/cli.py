"""Typer CLI for opdroid."""

from __future__ import annotations

import json
import time
from importlib.metadata import version as package_version
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from opdroid.client import AndroidController, list_connected_devices
from opdroid.grid import overlay_grid
from opdroid.mcp_server import main as run_mcp_server
from opdroid.skills import get_android_use_skill
from opdroid.tools import ToolExecutor
from opdroid.ui_hierarchy import parse_ui_hierarchy
from opdroid.utils import resize_image


app = typer.Typer(
    name="opdroid",
    help="Android device control through MCP and deterministic CLI commands.",
    add_completion=False,
    rich_markup_mode="rich",
    no_args_is_help=True,
)
console = Console()


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(
        False,
        "--version",
        is_eager=True,
        help="Show the installed opdroid version.",
    ),
) -> None:
    """Android device control through MCP and deterministic CLI commands."""
    if version:
        typer.echo(f"opdroid {package_version('opdroid')}")
        raise typer.Exit()


def _controller(serial: Optional[str], host: Optional[str], port: Optional[int]) -> AndroidController:
    return AndroidController(serial=serial, host=host, port=port)


def _executor_with_fresh_geometry(
    controller: AndroidController,
    max_size: int = 1024,
) -> ToolExecutor:
    executor = ToolExecutor(controller)
    executor.refresh_screen_geometry(max_size=max_size)
    return executor


@app.command()
def mcp(
    serial: Optional[str] = typer.Option(None, "--serial", "-s", help="Target device serial."),
    host: Optional[str] = typer.Option(None, "--adb-host", help="ADB server host."),
    port: Optional[int] = typer.Option(None, "--adb-port", help="ADB server port."),
) -> None:
    """Run the MCP server over stdio."""
    run_mcp_server(serial=serial, host=host, port=port)


@app.command()
def devices(
    host: Optional[str] = typer.Option(None, "--adb-host", help="ADB server host."),
    port: Optional[int] = typer.Option(None, "--adb-port", help="ADB server port."),
) -> None:
    """List connected Android devices."""
    try:
        serials = list_connected_devices(host=host, port=port)
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(1) from exc

    if not serials:
        console.print("No Android devices connected.")
        return

    table = Table("Serial")
    for serial in serials:
        table.add_row(serial)
    console.print(table)


@app.command()
def screen(
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Optional path for the gridded screenshot.",
    ),
    raw_output: Optional[Path] = typer.Option(
        None,
        "--raw-output",
        help="Optional path for the raw screenshot.",
    ),
    serial: Optional[str] = typer.Option(None, "--serial", "-s", help="Target device serial."),
    host: Optional[str] = typer.Option(None, "--adb-host", help="ADB server host."),
    port: Optional[int] = typer.Option(None, "--adb-port", help="ADB server port."),
    max_size: int = typer.Option(1024, "--max-size", help="Maximum screenshot analysis size."),
) -> None:
    """Capture the current screen, grid overlay, and UI element list."""
    try:
        controller = _controller(serial, host, port)
        screenshot = controller.get_screenshot()
        resized = resize_image(screenshot, max_size=max_size)
        gridded, cols, rows = overlay_grid(resized)

        if raw_output:
            raw_output.parent.mkdir(parents=True, exist_ok=True)
            screenshot.save(raw_output)
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            gridded.save(output)

        try:
            ui_xml = controller.get_ui_hierarchy()
            ui_elements = parse_ui_hierarchy(ui_xml, screenshot.size, resized.size)
        except Exception as exc:
            ui_elements = f"(Unable to parse UI hierarchy: {exc})"

        console.print(
            f"Screen: {screenshot.size[0]}x{screenshot.size[1]} "
            f"(analysis image: {resized.size[0]}x{resized.size[1]}, grid: {cols}x{rows})"
        )
        if output:
            console.print(f"Gridded screenshot: {output}")
        if raw_output:
            console.print(f"Raw screenshot: {raw_output}")
        console.print("\n[bold]Interactive UI Elements[/bold]\n")
        console.print(ui_elements)
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(1) from exc


@app.command()
def tap(
    cell: str = typer.Argument(..., help="Grid cell to tap, for example E10."),
    serial: Optional[str] = typer.Option(None, "--serial", "-s", help="Target device serial."),
    host: Optional[str] = typer.Option(None, "--adb-host", help="ADB server host."),
    port: Optional[int] = typer.Option(None, "--adb-port", help="ADB server port."),
) -> None:
    """Tap a grid cell."""
    _run_tool("tap", {"cell": cell}, serial, host, port)


@app.command("tap-sequence")
def tap_sequence(
    cells: list[str] = typer.Argument(..., help="Grid cells to tap in order."),
    delay_ms: float = typer.Option(500, "--delay-ms", help="Delay between taps."),
    serial: Optional[str] = typer.Option(None, "--serial", "-s", help="Target device serial."),
    host: Optional[str] = typer.Option(None, "--adb-host", help="ADB server host."),
    port: Optional[int] = typer.Option(None, "--adb-port", help="ADB server port."),
) -> None:
    """Tap multiple grid cells in order."""
    _run_tool("tap_sequence", {"cells": cells, "delay_ms": delay_ms}, serial, host, port)


@app.command()
def swipe(
    start_cell: str = typer.Argument(..., help="Starting grid cell."),
    end_cell: str = typer.Argument(..., help="Ending grid cell."),
    duration_ms: float = typer.Option(300, "--duration-ms", help="Swipe duration."),
    serial: Optional[str] = typer.Option(None, "--serial", "-s", help="Target device serial."),
    host: Optional[str] = typer.Option(None, "--adb-host", help="ADB server host."),
    port: Optional[int] = typer.Option(None, "--adb-port", help="ADB server port."),
) -> None:
    """Swipe between two grid cells."""
    _run_tool(
        "swipe",
        {"start_cell": start_cell, "end_cell": end_cell, "duration_ms": duration_ms},
        serial,
        host,
        port,
    )


@app.command("input-text")
def input_text(
    text: str = typer.Argument(..., help="Text to type into the focused field."),
    serial: Optional[str] = typer.Option(None, "--serial", "-s", help="Target device serial."),
    host: Optional[str] = typer.Option(None, "--adb-host", help="ADB server host."),
    port: Optional[int] = typer.Option(None, "--adb-port", help="ADB server port."),
) -> None:
    """Type text into the focused input field."""
    _run_tool("input_text", {"text": text}, serial, host, port)


@app.command("press")
def press_key(
    key: str = typer.Argument(..., help="One of: home, back, enter, recent-apps."),
    serial: Optional[str] = typer.Option(None, "--serial", "-s", help="Target device serial."),
    host: Optional[str] = typer.Option(None, "--adb-host", help="ADB server host."),
    port: Optional[int] = typer.Option(None, "--adb-port", help="ADB server port."),
) -> None:
    """Press an Android navigation key."""
    mapping = {
        "home": "press_home",
        "back": "press_back",
        "enter": "press_enter",
        "recent-apps": "press_recent_apps",
        "recent": "press_recent_apps",
    }
    tool = mapping.get(key)
    if tool is None:
        console.print("[bold red]Error:[/bold red] key must be one of home, back, enter, recent-apps")
        raise typer.Exit(2)
    _run_tool(tool, {}, serial, host, port, refresh_geometry=False)


@app.command("launch-app")
def launch_app(
    package: str = typer.Argument(..., help="Android package name."),
    serial: Optional[str] = typer.Option(None, "--serial", "-s", help="Target device serial."),
    host: Optional[str] = typer.Option(None, "--adb-host", help="ADB server host."),
    port: Optional[int] = typer.Option(None, "--adb-port", help="ADB server port."),
) -> None:
    """Launch an app by package name."""
    _run_tool("launch_app", {"package": package}, serial, host, port, refresh_geometry=False)


@app.command()
def wait(
    seconds: float = typer.Argument(..., help="Seconds to wait."),
) -> None:
    """Wait locally for a number of seconds."""
    time.sleep(float(seconds))
    console.print(f"Waited {seconds} seconds")


@app.command()
def skill() -> None:
    """Print the recommended Android-use skill for other agents."""
    typer.echo(get_android_use_skill())


@app.command("mcp-config")
def mcp_config(
    command: str = typer.Option("opdroid", "--command", help="Command used to start opdroid."),
    serial: Optional[str] = typer.Option(None, "--serial", "-s", help="Optional target serial."),
) -> None:
    """Print a JSON MCP server config snippet."""
    args = ["mcp"]
    if serial:
        args.extend(["--serial", serial])
    config = {"mcpServers": {"opdroid": {"command": command, "args": args}}}
    typer.echo(json.dumps(config, indent=2))


def _run_tool(
    name: str,
    arguments: dict,
    serial: Optional[str],
    host: Optional[str],
    port: Optional[int],
    refresh_geometry: bool = True,
) -> None:
    try:
        controller = _controller(serial, host, port)
        executor = ToolExecutor(controller)
        if refresh_geometry:
            executor.refresh_screen_geometry()
        result = executor.execute(name, arguments)
        console.print(result)
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(1) from exc


if __name__ == "__main__":
    app()
