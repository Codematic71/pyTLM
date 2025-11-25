# PyTLM API Reference

PyTLM (Python Terminal Library Manager) is a lightweight library for building terminal user interfaces using the `curses` module. It provides classes for managing windows, widgets, and handling user input in a terminal environment.

This documentation covers the main classes, methods, and functions provided by the library.

## Table of Contents

- [Color Management](#color-management)
- [Base Classes](#base-classes)
  - [Widget](#widget)
  - [Window](#window)
  - [WindowManager](#windowmanager)
- [Widgets](#widgets)
  - [Button](#button)
  - [StatusLabel](#statuslabel)
  - [ProgressBar](#progressbar)

## Color Management

The library includes a lazy color manager for handling foreground, background, and attribute combinations in `curses`.

### Constants

- `_COLOR_MAP`: A dictionary mapping color names to `curses` color constants. Supported colors include:
  - "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"
  - "bright_black", "bright_red", etc. (mapped to -1 for default terminal bright colors)
  - "default", "gray", "grey" (mapped to black or default)

- `_ATTR_MAP`: A dictionary mapping attribute names to `curses` attribute constants. Supported attributes include:
  - "bold", "underline", "reverse", "blink", "dim", "bright", "standout", "normal", "default"

### Functions

#### `cm(fg: str = "default", bg: str = "default", att: str = "default") -> int`

- **Description**: Returns a `curses` color pair with the specified foreground, background, and attribute. Lazily initializes color pairs as needed.
- **Parameters**:
  - `fg`: Foreground color name (default: "default").
  - `bg`: Background color name (default: "default").
  - `att`: Attribute name (default: "default").
- **Returns**: An integer representing the color pair combined with the attribute.
- **Example**:
  ```python
  style = cm("white", "blue", "bold")
  ```

## Base Classes

### Widget

Base class for all UI widgets.

#### `__init__(self, x: int, y: int, width: int, height: int = 1, **kwargs)`

- **Parameters**:
  - `x`: Horizontal position.
  - `y`: Vertical position.
  - `width`: Width of the widget.
  - `height`: Height of the widget (default: 1).
  - `name`: Optional name for the widget (str).

- **Attributes**:
  - `x`, `y`, `width`, `height`: Position and dimensions.
  - `name`: Widget name.
  - `parent`: Parent Window (set via `set_parent`).
  - `visible`: Visibility flag (bool, default: True).
  - `focused`: Focus state (bool, default: False).

#### Methods

- `set_parent(self, parent: "Window") -> None`: Sets the parent window.
- `request_repaint(self) -> None`: Requests a repaint from the parent window.
- `paint(self, win) -> None`: Paints the widget on the given `curses` window (override in subclasses).
- `contains(self, x: int, y: int) -> bool`: Checks if the point (x, y) is within the widget's bounds.
- `handle_key(self, key: int) -> bool`: Handles keyboard input (override in subclasses; returns True if handled).
- `handle_mouse(self, x: int, y: int, button: int) -> bool`: Handles mouse input (override in subclasses; returns True if handled).

### Window

Represents a window in the terminal UI, managing widgets and input.

#### `__init__(self, x: int, y: int, width: int, height: int, **kwargs)`

- **Parameters**:
  - `x`, `y`, `width`, `height`: Position and dimensions.
  - `title`: Window title (str, default: "").
  - `name`: Window name (str, optional).
  - `title_foreground`, `title_background`, `title_attribute`: Title styling (defaults: "default", "default", "reverse").
  - `border_foreground`, `border_background`, `border_attribute`: Border styling (defaults: "default", "default", "default").
  - `border_style`: Border style ("single", "double", "solid", "none"; default: "single").
  - `active_foreground`, `active_background`, `active_attribute`: Active window indicator styling (defaults: "default", "default", "default").

- **Attributes**:
  - `x`, `y`, `width`, `height`: Position and dimensions.
  - `title`: Window title.
  - `name`: Window name.
  - `win`: Underlying `curses` window.
  - `panel`: `curses.panel` for the window.
  - `active`: Active state (bool).
  - `widgets`: List of child widgets.
  - `widget_names`: Dictionary of widgets by name.
  - `focused_widget`: Currently focused widget.
  - `needs_repaint`: Repaint flag (bool).
  - `window_manager`: Parent WindowManager.

#### Methods

- `get_manager(self) -> WindowManager`: Returns the parent WindowManager.
- `add_widget(self, w: Widget) -> Widget`: Adds a widget to the window.
- `set_focus(self, w: Optional[Widget]) -> None`: Sets focus to a widget.
- `next_focus(self) -> None`: Cycles focus to the next widget.
- `prev_focus(self) -> None`: Cycles focus to the previous widget.
- `request_repaint(self) -> None`: Marks the window for repainting.
- `resize(self, width: int, height: int) -> None`: Resizes the window.
- `move(self, x: int, y: int) -> int`: Moves the window; returns `curses` result.
- `paint(self) -> None`: Paints the window, border, title, and widgets.
- `handle_key(self, key: int) -> bool`: Handles key input, including tab navigation.
- `handle_mouse(self, local_x: int, local_y: int, button: int) -> bool`: Dispatches mouse events to widgets.
- `handle_resize(self, width: int, height: int) -> None`: Handles terminal resize (stub; override if needed).

### WindowManager

Manages multiple windows, input loop, and repainting.

#### `__init__(self, stdscr)`

- **Parameters**:
  - `stdscr`: Standard `curses` screen.

- **Attributes**:
  - `stdscr`: Standard screen.
  - `windows`: List of managed windows.
  - `active_window`: Currently active window.
  - `window_names`: Dictionary of windows by name.
  - `height`, `width`: Terminal dimensions.
  - `running`: Loop running flag (bool).

#### Methods

- `get_window_byName(self, name: str) -> Window`: Retrieves a window by name.
- `get_widget_byName(self, name: str) -> Widget`: Retrieves a widget by "window/widget" name.
- `add_window(self, win: Window) -> Window`: Adds a window and activates it.
- `set_active_window(self, win: Window) -> None`: Activates a window and brings it to top.
- `get_window_at(self, x: int, y: int) -> Optional[Window]`: Finds window at coordinates.
- `event_loop(self) -> None`: Runs the main event loop (handles keys, mouse, resize, repaint at 60 FPS).

## Widgets

### Button

A clickable button widget.

#### `__init__(self, x: int, y: int, width: int, **kwargs)`

- Inherits from [Widget](#widget).
- **Parameters**:
  - `text`: Button text (str, default: "").
  - `on_click`, `on_press`, `on_release`: Callback functions (default: no-op).
  - `toggle`: Toggle behavior (bool, default: False; not fully implemented).
  - `normal_foreground`, `normal_background`, `normal_attribute`: Normal styling (defaults: "white", "default", "reverse").
  - `pressed_foreground`, `pressed_background`, `pressed_attribute`: Pressed styling (defaults: "white", "default", "default").
  - `active_foreground`, `active_background`, `active_attribute`: Active styling (defaults: "white", "red", "default").

- **Attributes**:
  - `text`: Button label.
  - `state`: Internal state (0: idle, 1: pressed).

#### Methods

- `set_text(self, text: str) -> None`: Updates the button text.
- `paint(self, win) -> None`: Draws the button with centered text.
- `handle_key(self, key: int) -> bool`: Handles Enter/Space for click if focused.
- `handle_mouse(self, x: int, y: int, button: int) -> bool`: Handles mouse press/release/click.

### StatusLabel

A label that displays a value and can change style based on thresholds.

#### `__init__(self, x: int, y: int, width: int, **kwargs)`

- Inherits from [Widget](#widget).
- **Parameters**:
  - `units`: Units suffix (str, default: "").
  - `value`: Initial value (any, default: "0").
  - `normal_foreground`, `normal_background`, `normal_attribute`: Normal styling (defaults: "white", "default", "default").
  - `fault_foreground`, `fault_background`, `fault_attribute`: Fault styling (defaults: "white", "default", "default").
  - `threshold`: Comparison threshold (str).
  - `comparison`: Operator ("LT", "LTE", "GT", "GTE", or equality; default: equality).
  - `format`: Format string for value (str, default: "").

#### Methods

- `set_value(self, value: Any) -> None`: Updates the value.
- `get_value(self) -> Any`: Returns the current value.
- `paint(self, win) -> None`: Draws the formatted value with normal or fault style based on comparison.

### ProgressBar

A progress bar widget with threshold-based coloring.

#### `__init__(self, x: int, y: int, width: int, **kwargs)`

- Inherits from [Widget](#widget).
- **Parameters**:
  - `value`: Initial value (float, default: 0.0).
  - `minimum`, `maximum`: Range (floats, defaults: 0.0, 100.0).
  - `show_value`: Display value text (bool, default: True).
  - `format`: Value format string (str, default: "").
  - `warning_threshold`, `critical_threshold`: Thresholds for coloring (defaults: 50, 75).
  - `invert_threshold`: Invert threshold logic (bool, default: False).
  - `fill_char`, `empty_char`: Bar characters (defaults: "█", "░").
  - `normal_foreground`, `normal_background`, `normal_attribute`: Normal styling (defaults: "green", "black", "default").
  - `warning_foreground`, `warning_background`, `warning_attribute`: Warning styling (defaults: "yellow", "black", "default").
  - `critical_foreground`, `critical_background`, `critical_attribute`: Critical styling (defaults: "red", "black", "default").

#### Methods

- `set_value(self, value: float) -> None`: Updates and clamps the value.
- `paint(self, win) -> None`: Draws the bar with appropriate color based on thresholds.

## Usage Example

```python
import curses
from pytlm import WindowManager, Window, Button

def main(stdscr):
    wm = WindowManager(stdscr)
    win = Window(0, 0, 40, 10, title="Example")
    wm.add_window(win)
    button = Button(2, 2, 10, text="Click Me", on_click=lambda b: print("Clicked!"))
    win.add_widget(button)
    wm.event_loop()

curses.wrapper(main)
```

For more details, refer to the source code.

**SOURCES:**  
[^1]: Provided code from `pytlm.py` (inline document).
