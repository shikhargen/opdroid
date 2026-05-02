"""Android control tool execution shared by the CLI and MCP server."""

from __future__ import annotations

import time
from typing import Any, Callable, Optional

from opdroid.client import AndroidController
from opdroid.grid import CELL_SIZE, grid_cell_to_pixels
from opdroid.utils import resize_image


class ToolExecutor:
    """Executes Android control tools against an AndroidController."""

    def __init__(self, controller: AndroidController):
        self.controller = controller
        self._tool_map: dict[str, Callable[..., str]] = {
            "tap": self._tap,
            "tap_sequence": self._tap_sequence,
            "swipe": self._swipe,
            "input_text": self._input_text,
            "press_home": self._press_home,
            "press_back": self._press_back,
            "press_enter": self._press_enter,
            "press_recent_apps": self._press_recent_apps,
            "launch_app": self._launch_app,
            "wait": self._wait,
        }
        self.original_size: Optional[tuple[int, int]] = None
        self.resized_size: Optional[tuple[int, int]] = None

    @property
    def tool_names(self) -> tuple[str, ...]:
        """Return executable tool names."""
        return tuple(self._tool_map)

    def set_screen_geometry(
        self,
        original_size: tuple[int, int],
        resized_size: tuple[int, int],
    ) -> None:
        """Set the coordinate conversion geometry from a captured screen."""
        self.original_size = original_size
        self.resized_size = resized_size

    def refresh_screen_geometry(self, max_size: int = 1024) -> tuple[int, int]:
        """Capture a screenshot and update geometry used for grid coordinates."""
        screenshot = self.controller.get_screenshot()
        resized = resize_image(screenshot, max_size=max_size)
        self.set_screen_geometry(screenshot.size, resized.size)
        return resized.size

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Execute a tool by name with given arguments."""
        if tool_name not in self._tool_map:
            raise ValueError(f"Unknown tool: {tool_name}")
        coerced_args = self._coerce_arguments(tool_name, arguments)
        return self._tool_map[tool_name](**coerced_args)

    def _coerce_arguments(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Coerce common MCP/JSON string values into the expected Python types."""
        coerced = arguments.copy()
        numeric_params = {
            "swipe": ["duration_ms"],
            "tap_sequence": ["delay_ms"],
            "wait": ["seconds"],
        }
        for param in numeric_params.get(tool_name, []):
            if param in coerced and isinstance(coerced[param], str):
                try:
                    coerced[param] = float(coerced[param])
                except ValueError:
                    pass
        return coerced

    def _cell_to_device_pixels(self, cell: str) -> tuple[int, int]:
        """Convert a grid cell to device pixel coordinates."""
        if self.original_size is None or self.resized_size is None:
            self.refresh_screen_geometry()

        resized_x, resized_y = grid_cell_to_pixels(cell, CELL_SIZE)
        assert self.original_size is not None
        assert self.resized_size is not None

        scale_x = self.original_size[0] / self.resized_size[0]
        scale_y = self.original_size[1] / self.resized_size[1]
        return int(resized_x * scale_x), int(resized_y * scale_y)

    def _tap(self, cell: str) -> str:
        x, y = self._cell_to_device_pixels(cell)
        return self.controller.tap(x, y)

    def _tap_sequence(self, cells: list[str], delay_ms: float = 500) -> str:
        if not cells:
            raise ValueError("cells must contain at least one grid cell")
        tapped = []
        for index, cell in enumerate(cells):
            x, y = self._cell_to_device_pixels(cell)
            self.controller.tap(x, y)
            tapped.append(cell)
            if index < len(cells) - 1:
                time.sleep(float(delay_ms) / 1000)
        return f"Tapped sequence: {' -> '.join(tapped)}"

    def _swipe(self, start_cell: str, end_cell: str, duration_ms: float = 300) -> str:
        start_x, start_y = self._cell_to_device_pixels(start_cell)
        end_x, end_y = self._cell_to_device_pixels(end_cell)
        return self.controller.swipe(start_x, start_y, end_x, end_y, int(duration_ms))

    def _input_text(self, text: str) -> str:
        return self.controller.input_text(text)

    def _press_home(self) -> str:
        return self.controller.press_home()

    def _press_back(self) -> str:
        return self.controller.press_back()

    def _press_enter(self) -> str:
        return self.controller.press_enter()

    def _press_recent_apps(self) -> str:
        return self.controller.press_recent_apps()

    def _launch_app(self, package: str) -> str:
        return self.controller.launch_app(package)

    def _wait(self, seconds: float) -> str:
        time.sleep(float(seconds))
        return f"Waited {seconds} seconds"
