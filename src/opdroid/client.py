"""Low-level ADB wrapper for Android device control."""

from typing import Optional
from PIL import Image
import os
import shlex

from adbutils import AdbClient, AdbDevice


DEFAULT_ADB_HOST = "127.0.0.1"
DEFAULT_ADB_PORT = 5037


def _adb_host() -> str:
    return os.getenv("OPDROID_ADB_HOST", DEFAULT_ADB_HOST)


def _adb_port() -> int:
    value = os.getenv("OPDROID_ADB_PORT")
    if not value:
        return DEFAULT_ADB_PORT
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError("OPDROID_ADB_PORT must be an integer") from exc


def list_connected_devices(host: Optional[str] = None, port: Optional[int] = None) -> list[str]:
    """Return serial numbers for connected Android devices."""
    client = AdbClient(host=host or _adb_host(), port=port or _adb_port())
    return [device.serial for device in client.device_list()]


class AndroidController:
    """Wrapper around adbutils for controlling an Android device via ADB.

    Provides high-level methods for tapping, swiping, text input, and
    capturing screenshots from a connected Android device.
    """

    def __init__(
        self,
        serial: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
    ):
        """Initialize the Android controller.

        Args:
            serial: Optional device serial number. If None, auto-connects
                    to the first available device.

        Raises:
            RuntimeError: If no device is found.
        """
        self.host = host or _adb_host()
        self.port = port or _adb_port()
        self._client = AdbClient(host=self.host, port=self.port)
        self._device: Optional[AdbDevice] = None
        self._connect(serial)

    def _connect(self, serial: Optional[str] = None) -> None:
        """Connect to an Android device via ADB.

        Args:
            serial: Optional device serial. If None, uses first available device.

        Raises:
            RuntimeError: If no device is found or connection fails.
        """
        devices = self._client.device_list()

        if not devices:
            raise RuntimeError(
                f"No Android devices found through ADB at {self.host}:{self.port}. "
                "Ensure ADB is running and a device is connected."
            )

        if serial:
            for device in devices:
                if device.serial == serial:
                    self._device = device
                    break
            if not self._device:
                raise RuntimeError(f"Device with serial '{serial}' not found.")
        else:
            self._device = devices[0]

    @property
    def device(self) -> AdbDevice:
        """Get the connected ADB device."""
        if not self._device:
            raise RuntimeError("No device connected.")
        return self._device

    @property
    def serial(self) -> str:
        """Get the serial number of the connected device."""
        return self.device.serial

    def tap(self, x: int, y: int) -> str:
        """Simulate a finger tap at the specified coordinates.

        Args:
            x: X coordinate (0 = left edge).
            y: Y coordinate (0 = top edge).

        Returns:
            Status message confirming the tap.
        """
        self.device.shell(f"input tap {int(x)} {int(y)}")
        return f"Tapped at ({x}, {y})"

    def swipe(
        self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int = 300
    ) -> str:
        """Simulate a swipe gesture.

        Args:
            start_x: Starting X coordinate.
            start_y: Starting Y coordinate.
            end_x: Ending X coordinate.
            end_y: Ending Y coordinate.
            duration_ms: Duration of swipe in milliseconds.

        Returns:
            Status message confirming the swipe.
        """
        self.device.shell(
            "input swipe "
            f"{int(start_x)} {int(start_y)} {int(end_x)} {int(end_y)} {int(duration_ms)}"
        )
        return f"Swiped from ({start_x}, {start_y}) to ({end_x}, {end_y})"

    def input_text(self, text: str) -> str:
        """Input text into the currently focused field.

        The text is sanitized to prevent shell injection issues.
        Spaces are converted to '%s' for ADB compatibility.

        Args:
            text: The text to input.

        Returns:
            Status message confirming the text input.
        """
        # Android's input command uses %s for spaces. Quote the full argument so
        # punctuation is not interpreted by the device shell.
        encoded = text.replace(" ", "%s")
        self.device.shell(f"input text {shlex.quote(encoded)}")
        return f"Entered text: '{text}'"

    def press_key(self, keycode: int) -> str:
        """Press a key by its Android keycode.

        Args:
            keycode: Android keycode (e.g., 3 for HOME, 4 for BACK).

        Returns:
            Status message confirming the key press.
        """
        self.device.shell(f"input keyevent {int(keycode)}")
        return f"Pressed key: {keycode}"

    def press_home(self) -> str:
        """Press the HOME button.

        Returns:
            Status message confirming the action.
        """
        return self.press_key(3)  # KEYCODE_HOME

    def press_back(self) -> str:
        """Press the BACK button.

        Returns:
            Status message confirming the action.
        """
        return self.press_key(4)  # KEYCODE_BACK

    def press_enter(self) -> str:
        """Press the ENTER key.

        Returns:
            Status message confirming the action.
        """
        return self.press_key(66)  # KEYCODE_ENTER

    def press_recent_apps(self) -> str:
        """Press the RECENT APPS button.

        Returns:
            Status message confirming the action.
        """
        return self.press_key(187)  # KEYCODE_APP_SWITCH

    def get_screenshot(self) -> Image.Image:
        """Capture a screenshot from the device.

        Returns:
            PIL Image object containing the screenshot.
        """
        # adbutils.screenshot() returns PIL.Image directly
        return self.device.screenshot()

    def get_screen_size(self) -> tuple[int, int]:
        """Get the screen resolution of the device.

        Returns:
            Tuple of (width, height) in pixels.
        """
        output = self.device.shell("wm size")
        for line in output.splitlines():
            if "Physical size:" in line:
                size_str = line.split("Physical size:", 1)[1].strip()
                width, height = map(int, size_str.split("x"))
                return width, height
        raise RuntimeError(f"Could not parse screen size from adb output: {output!r}")

    def launch_app(self, package: str) -> str:
        """Launch an app by its package name.

        Args:
            package: The package name (e.g., 'com.android.settings').

        Returns:
            Status message confirming the launch.
        """
        if not package or any(char.isspace() for char in package):
            raise ValueError("Package name must be a non-empty identifier without spaces.")
        self.device.shell(
            "monkey -p "
            f"{shlex.quote(package)} -c android.intent.category.LAUNCHER 1"
        )
        return f"Launched app: {package}"

    def get_ui_hierarchy(self) -> str:
        """Dump the UI hierarchy XML from the device.

        Uses uiautomator to capture the current UI tree structure.

        Returns:
            Raw XML string of the UI hierarchy.
        """
        # Dump directly to stdout to avoid file permission issues
        output = self.device.shell("uiautomator dump /dev/tty")

        # Extract only the XML part (between <?xml ... </hierarchy>)
        xml_start = output.find("<?xml")
        xml_end = output.find("</hierarchy>")

        if xml_start != -1 and xml_end != -1:
            output = output[xml_start : xml_end + len("</hierarchy>")]

        return output.strip()
