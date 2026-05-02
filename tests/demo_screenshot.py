#!/usr/bin/env python3
"""Capture a gridded Android screenshot and UI hierarchy for manual inspection."""

from pathlib import Path

from opdroid.client import AndroidController
from opdroid.grid import CELL_SIZE, get_column_label, grid_cell_to_pixels, overlay_grid
from opdroid.ui_hierarchy import parse_ui_hierarchy
from opdroid.utils import resize_image


def main() -> None:
    artifacts = Path("artifacts")
    artifacts.mkdir(exist_ok=True)

    print("Connecting to device...")
    controller = AndroidController()

    print("Capturing screenshot...")
    screenshot = controller.get_screenshot()
    original_size = screenshot.size
    resized = resize_image(screenshot, max_size=1024)
    resized_size = resized.size
    gridded, cols, rows = overlay_grid(resized)

    print(f"Original: {original_size[0]}x{original_size[1]}")
    print(f"Analysis image: {resized_size[0]}x{resized_size[1]}")
    print(f"Grid: {cols}x{rows} cells ({CELL_SIZE}px)")

    demo_cell = f"{get_column_label(cols // 2)}{rows // 2}"
    px, py = grid_cell_to_pixels(demo_cell)
    orig_x = int(px * original_size[0] / resized_size[0])
    orig_y = int(py * original_size[1] / resized_size[1])
    print(f"Example: {demo_cell} -> analysis ({px}, {py}) -> device ({orig_x}, {orig_y})")

    try:
        xml_raw = controller.get_ui_hierarchy()
        ui_hierarchy = parse_ui_hierarchy(xml_raw, original_size, resized_size)
        (artifacts / "ui_hierarchy.xml").write_text(xml_raw)
        (artifacts / "ui_hierarchy_minified.txt").write_text(ui_hierarchy)
        print("\nInteractive UI Elements\n")
        print(ui_hierarchy)
    except Exception as exc:
        print(f"Could not capture UI hierarchy: {exc}")

    screenshot.save(artifacts / "screenshot_original.png")
    resized.save(artifacts / "screenshot_resized.png")
    gridded.save(artifacts / "screenshot_gridded.png")
    print(f"\nSaved artifacts under {artifacts.absolute()}")


if __name__ == "__main__":
    main()
