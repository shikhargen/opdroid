"""Skill text for agents that use opdroid through MCP."""

ANDROID_USE_SKILL = """# Android Use with opdroid

Use opdroid when you need to inspect or operate a connected Android device.

## Workflow

1. Call `get_screen` before taking visual actions.
2. Read the returned screenshot and the interactive UI elements list.
3. Prefer an element's `position` value when it is available.
4. Use grid cells for actions: columns are letters from left to right and rows are numbers from top to bottom.
5. After every action that changes the screen, call `get_screen` again before deciding the next action.

## Tools

- `get_screen`: capture a gridded screenshot and UI element list.
- `tap`: tap one grid cell, for example `{ "cell": "E10" }`.
- `tap_sequence`: tap multiple cells in order.
- `swipe`: swipe between two grid cells.
- `input_text`: type into the currently focused field.
- `press_home`, `press_back`, `press_enter`, `press_recent_apps`: Android navigation keys.
- `launch_app`: start an app by Android package name.
- `wait`: wait for loading or animation.
- `list_devices`: list connected devices.

## Operating Rules

- Never guess raw pixel coordinates. Use grid cells.
- If text entry fails because a field is not focused, tap the field and retry.
- If the keyboard covers content, use `press_back` to hide it.
- If the device state is uncertain, call `get_screen`.
- Stop when the requested device state is achieved, or report the concrete blocker.
"""


def get_android_use_skill() -> str:
    """Return the recommended skill text for agents using opdroid."""
    return ANDROID_USE_SKILL
