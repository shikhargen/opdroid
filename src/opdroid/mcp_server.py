"""MCP server for Android device control."""

from __future__ import annotations

import asyncio
import logging
import sys
from typing import Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import ImageContent, TextContent, Tool

from opdroid.client import AndroidController, list_connected_devices
from opdroid.grid import overlay_grid
from opdroid.skills import get_android_use_skill
from opdroid.tools import ToolExecutor
from opdroid.ui_hierarchy import parse_ui_hierarchy
from opdroid.utils import encode_image_base64, resize_image


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger("opdroid.mcp")

_controller: Optional[AndroidController] = None
_executor: Optional[ToolExecutor] = None
_device_serial: Optional[str] = None
_adb_host: Optional[str] = None
_adb_port: Optional[int] = None


def configure_device(
    serial: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
) -> None:
    """Configure the target ADB endpoint and reset cached connections."""
    global _device_serial, _adb_host, _adb_port, _controller, _executor
    _device_serial = serial
    _adb_host = host
    _adb_port = port
    _controller = None
    _executor = None


def get_controller() -> AndroidController:
    """Get or create the AndroidController instance."""
    global _controller
    if _controller is None:
        target = _device_serial or "first connected device"
        logger.info("Connecting to %s...", target)
        _controller = AndroidController(
            serial=_device_serial,
            host=_adb_host,
            port=_adb_port,
        )
        logger.info("Connected to device: %s", _controller.serial)
    return _controller


def get_executor() -> ToolExecutor:
    """Get or create the ToolExecutor instance."""
    global _executor
    if _executor is None:
        _executor = ToolExecutor(get_controller())
    return _executor


MCP_TOOLS = [
    Tool(
        name="get_screen",
        description=(
            "Capture the current Android screen. Returns a screenshot with a labeled grid "
            "and a compact list of interactive UI elements with grid positions."
        ),
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="tap",
        description="Tap a grid cell from the latest get_screen result, for example E10.",
        inputSchema={
            "type": "object",
            "properties": {"cell": {"type": "string", "description": "Grid cell to tap."}},
            "required": ["cell"],
        },
    ),
    Tool(
        name="tap_sequence",
        description="Tap multiple grid cells in order.",
        inputSchema={
            "type": "object",
            "properties": {
                "cells": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Grid cells to tap in order.",
                },
                "delay_ms": {
                    "type": "number",
                    "description": "Delay between taps in milliseconds.",
                    "default": 500,
                },
            },
            "required": ["cells"],
        },
    ),
    Tool(
        name="swipe",
        description="Swipe from one grid cell to another.",
        inputSchema={
            "type": "object",
            "properties": {
                "start_cell": {"type": "string", "description": "Starting grid cell."},
                "end_cell": {"type": "string", "description": "Ending grid cell."},
                "duration_ms": {
                    "type": "number",
                    "description": "Swipe duration in milliseconds.",
                    "default": 300,
                },
            },
            "required": ["start_cell", "end_cell"],
        },
    ),
    Tool(
        name="input_text",
        description="Type text into the currently focused input field.",
        inputSchema={
            "type": "object",
            "properties": {"text": {"type": "string", "description": "Text to type."}},
            "required": ["text"],
        },
    ),
    Tool(
        name="press_home",
        description="Press the Android HOME key.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="press_back",
        description="Press the Android BACK key.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="press_enter",
        description="Press the Android ENTER key.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="press_recent_apps",
        description="Open Android recent apps.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="launch_app",
        description="Launch an installed app by package name.",
        inputSchema={
            "type": "object",
            "properties": {
                "package": {
                    "type": "string",
                    "description": "Android package name, for example com.android.settings.",
                }
            },
            "required": ["package"],
        },
    ),
    Tool(
        name="wait",
        description="Wait for loading, animation, or device state changes.",
        inputSchema={
            "type": "object",
            "properties": {"seconds": {"type": "number", "description": "Seconds to wait."}},
            "required": ["seconds"],
        },
    ),
    Tool(
        name="list_devices",
        description="List connected Android device serial numbers.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_android_use_skill",
        description="Return the recommended skill text for agents that use opdroid.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
]


def capture_screen_state() -> tuple[str, str, tuple[int, int], tuple[int, int], int, int]:
    """Capture screenshot, grid overlay, and UI hierarchy text."""
    controller = get_controller()
    executor = get_executor()

    screenshot = controller.get_screenshot()
    original_size = screenshot.size
    resized = resize_image(screenshot, max_size=1024)
    resized_size = resized.size
    executor.set_screen_geometry(original_size, resized_size)

    gridded_image, cols, rows = overlay_grid(resized)
    image_b64 = encode_image_base64(gridded_image, format="PNG")

    try:
        ui_xml = controller.get_ui_hierarchy()
        ui_elements = parse_ui_hierarchy(ui_xml, original_size, resized_size)
    except Exception as exc:
        ui_elements = f"(Unable to parse UI hierarchy: {exc})"

    return image_b64, ui_elements, original_size, resized_size, cols, rows


def create_server() -> Server:
    """Create and configure the MCP server."""
    server = Server("opdroid")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return MCP_TOOLS

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent]:
        logger.info("tool %s(%s)", name, arguments if arguments else "")

        if name == "get_screen":
            try:
                image_b64, ui_elements, original, resized, cols, rows = await asyncio.to_thread(
                    capture_screen_state
                )
                text = (
                    f"Screen: {original[0]}x{original[1]} "
                    f"(analysis image: {resized[0]}x{resized[1]}, grid: {cols}x{rows})\n\n"
                    f"## Interactive UI Elements\n\n{ui_elements}\n\n"
                    "Use the position value from an element when possible."
                )
                return [
                    ImageContent(type="image", data=image_b64, mimeType="image/png"),
                    TextContent(type="text", text=text),
                ]
            except Exception as exc:
                logger.exception("screen capture failed")
                return [TextContent(type="text", text=f"Error capturing screen: {exc}")]

        if name == "list_devices":
            try:
                devices = await asyncio.to_thread(
                    list_connected_devices,
                    _adb_host,
                    _adb_port,
                )
                if not devices:
                    return [TextContent(type="text", text="No Android devices connected.")]
                return [TextContent(type="text", text="\n".join(f"- {d}" for d in devices))]
            except Exception as exc:
                return [TextContent(type="text", text=f"Error listing devices: {exc}")]

        if name == "get_android_use_skill":
            return [TextContent(type="text", text=get_android_use_skill())]

        try:
            result = await asyncio.to_thread(get_executor().execute, name, arguments)
            return [TextContent(type="text", text=result)]
        except ValueError:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
        except Exception as exc:
            logger.exception("tool execution failed")
            return [TextContent(type="text", text=f"Error executing {name}: {exc}")]

    return server


async def run_server(
    serial: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
) -> None:
    """Run the MCP server over stdio."""
    configure_device(serial=serial, host=host, port=port)
    logger.info("opdroid MCP server starting")
    if serial:
        logger.info("target device: %s", serial)

    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main(
    serial: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
) -> None:
    """Entry point for the MCP server."""
    asyncio.run(run_server(serial=serial, host=host, port=port))


if __name__ == "__main__":
    main()
