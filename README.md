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
uv add opdroid
```

You can also run it without installing into the current environment:

```bash
uvx opdroid --help
uvx opdroid devices
```

For local development:

```bash
uv sync
uv run opdroid --help
```

## Agent Skill

`opdroid` is built to be **skill-native** according to the [agentskills.io](https://agentskills.io) open standard. You can install it directly into your AI coding assistant (like Claude Code or Cursor) using the Vercel Skills CLI:

```bash
npx skills add shikhargen/opdroid
```

Alternatively, you can print the recommended skill instructions for manually pasting or configuring other agents using the CLI:

```bash
opdroid skill
```

The MCP server also exposes this through the `get_android_use_skill` tool.

## MCP Server

Run the MCP server over stdio:

```bash
opdroid mcp
```

Run it directly from PyPI with `uvx`:

```bash
uvx opdroid mcp
```

Target a specific device:

```bash
opdroid mcp --serial emulator-5554
uvx opdroid mcp --serial emulator-5554
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

Alternative config that runs through `uvx` without a prior install:

```json
{
  "mcpServers": {
    "opdroid": {
      "command": "uvx",
      "args": ["opdroid", "mcp"]
    }
  }
}
```

Project-local Codex config example in `.codex/config.toml`:

```toml
[mcp_servers.opdroid]
command = "uvx"
args = ["opdroid", "mcp"]
enabled = true
```

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
