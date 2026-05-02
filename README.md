# opdroid

Android device control through MCP and a deterministic CLI.

opdroid exposes a connected Android device as a set of practical tools:
capture a gridded screen, inspect UI hierarchy, tap cells, swipe, type text,
press Android navigation keys, and launch apps. Bring your own MCP-capable
agent.

## Requirements

- Python 3.10+
- ADB installed and running
- Android device or emulator with USB debugging enabled

## Installation

```bash
pip install opdroid
```

For local development:

```bash
uv sync
uv run opdroid --help
```

## MCP Server

Run the MCP server over stdio:

```bash
opdroid mcp
```

Target a specific device:

```bash
opdroid mcp --serial emulator-5554
```

Print a ready-to-copy MCP config snippet:

```bash
opdroid mcp-config
```

Example config:

```json
{
  "mcpServers": {
    "opdroid": {
      "command": "opdroid",
      "args": ["mcp"]
    }
  }
}
```

## Agent Skill

Print the recommended skill text for another agent:

```bash
opdroid skill
```

The MCP server also exposes this through `get_android_use_skill`.

## CLI

List devices:

```bash
opdroid devices
```

Capture the current screen with a grid and UI hierarchy:

```bash
opdroid screen --output artifacts/screen.png
```

Operate the device:

```bash
opdroid tap E10
opdroid tap-sequence B16 E16 H16
opdroid swipe E18 E6
opdroid input-text "hello world"
opdroid press back
opdroid launch-app com.android.settings
```

## MCP Tools

- `get_screen`: returns a gridded screenshot and compact interactive element list.
- `tap`: tap a grid cell.
- `tap_sequence`: tap multiple grid cells.
- `swipe`: swipe between two grid cells.
- `input_text`: type text into the focused field.
- `press_home`, `press_back`, `press_enter`, `press_recent_apps`: Android key actions.
- `launch_app`: launch an app by package name.
- `wait`: wait for loading or animation.
- `list_devices`: list connected Android devices.
- `get_android_use_skill`: return the recommended agent skill text.

## Configuration

By default opdroid connects to ADB at `127.0.0.1:5037`.

Environment variables:

- `OPDROID_ADB_HOST`: ADB server host.
- `OPDROID_ADB_PORT`: ADB server port.
- `OPDROID_CELL_SIZE`: grid cell size in analysis screenshots.

Equivalent CLI options are available where device access is needed:

```bash
opdroid devices --adb-host 127.0.0.1 --adb-port 5037
opdroid mcp --adb-host 127.0.0.1 --adb-port 5037
```

## Development Checks

```bash
uv run python -m compileall src tests
uv run opdroid --help
```

## License

MIT
