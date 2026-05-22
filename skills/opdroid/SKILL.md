---
name: opdroid
description: Inspect and operate a connected Android device or emulator. Use this skill when you need to view the screen, tap buttons, swipe, type text, or press navigation keys on a connected Android device.
---
# Android Control with opdroid

This skill provides powerful, deterministic tools and commands to operate a connected Android device or emulator over ADB.

## Requirements

Before using this skill:
1. Ensure the ADB server is running on the host (`adb start-server`).
2. An Android device or emulator must be connected and authorized via USB debugging.

## How to Run Commands

You can run `opdroid` commands using the `opdroid` command-line utility. If it is not installed in the active environment, run it on-demand via `uvx`:

```bash
uvx opdroid <command>
```

---

## Recommended Workflow

Always follow these steps when interacting with the device:

1.  **Retrieve Visual Context & UI Hierarchy**:
    Capture the screen and get the minified list of interactive elements:
    ```bash
    uvx opdroid screen --output artifacts/screen.png
    ```
    This command prints a minified list of interactive elements with their grid coordinates, and saves the gridded screenshot under `artifacts/screen.png`.

2.  **Locate Target Element**:
    *   Find the target element in the text output of interactive UI elements.
    *   Use the element's `position` value (e.g., `position="E10"`) directly.
    *   If you need visual confirmation, open and inspect the gridded screenshot (`artifacts/screen.png`). Columns are labeled with letters (A, B, C...) and rows are labeled with numbers (1, 2, 3...).

3.  **Perform Action**:
    Use one of the deterministic CLI commands below with grid coordinates rather than guessing raw pixel coordinates.

4.  **Confirm Changes**:
    After every action that modifies the screen state (taps, text input, swipes), **always** capture the screen again (`uvx opdroid screen --output artifacts/screen.png`) to verify the outcome before planning your next action.

---

## Command Reference

### 1. View Screen and UI Hierarchy
```bash
uvx opdroid screen --output artifacts/screen.png
```
Captures the screen, overlays a coordinate grid, prints the list of interactive UI elements, and saves the image to `artifacts/screen.png`.

### 2. Tap a Grid Cell
```bash
uvx opdroid tap E10
```
Taps the center of the specified grid cell (e.g. cell `E10`).

### 3. Tap a Sequence of Cells
```bash
uvx opdroid tap-sequence B16 E16 H16 --delay-ms 500
```
Taps multiple grid cells in order, with an optional delay in milliseconds between taps.

### 4. Swipe Between Cells
```bash
uvx opdroid swipe E18 E6 --duration-ms 300
```
Performs a swipe gesture from the start cell center to the end cell center with an optional duration in milliseconds.

### 5. Input Text
```bash
uvx opdroid input-text "hello world"
```
Types the text into the currently focused input field.
*   *Rule:* If text entry fails or does not appear, make sure to `tap` the input field first to focus it, then retry.

### 6. Press Device Buttons
```bash
uvx opdroid press home
uvx opdroid press back
uvx opdroid press enter
uvx opdroid press recent-apps
```
Simulates pressing physical/software keys on the device.
*   *Rule:* If the on-screen keyboard is covering content, use `uvx opdroid press back` to hide it.

### 7. Launch an App
```bash
uvx opdroid launch-app com.android.settings
```
Launches an application using its Android package name.

### 8. Wait/Pause
```bash
uvx opdroid wait 2.5
```
Waits for the specified duration in seconds. Use this to allow transition animations, screen loading, or network requests to complete.

### 9. List Connected Devices
```bash
uvx opdroid devices
```
Lists the serial numbers of all connected Android devices/emulators.

---

## Operating Guidelines

*   **Never Guess Pixels**: Always convert interactions to grid cells or use the `position` coordinate provided in the interactive element list.
*   **Handle Uncertain States**: If you are unsure what is on the screen or if an action succeeded, run the `screen` command to refresh your view.
*   **Focus Before Typing**: Always tap an input field first to ensure focus before calling `input-text`.
*   **Hide Keyboard**: If the virtual keyboard obscures part of the screen, run `uvx opdroid press back` to dismiss it.
