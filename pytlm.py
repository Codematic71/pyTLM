#!/usr/bin/env python3

import curses
import curses.panel
import time
import threading
from typing import List, Optional, Callable, Any


# ----------------------------------------------------------------------
# Lazy colour manager
# ----------------------------------------------------------------------

    
_COLOR_MAP = {
        "black":          curses.COLOR_BLACK,
        "red":            curses.COLOR_RED,
        "green":          curses.COLOR_GREEN,
        "yellow":         curses.COLOR_YELLOW,
        "blue":           curses.COLOR_BLUE,
        "magenta":        curses.COLOR_MAGENTA,
        "cyan":           curses.COLOR_CYAN,
        "white":          curses.COLOR_WHITE,
        "bright_black":   -1,
        "bright_red":     -1,
        "bright_green":   -1,
        "bright_yellow":  -1,
        "bright_blue":    -1,
        "bright_magenta": -1,
        "bright_cyan":    -1,
        "bright_white":   -1,
        "default":        -1,
        "gray":           curses.COLOR_BLACK,
        "grey":           curses.COLOR_BLACK,
    }

_ATTR_MAP = {
        "bold":       curses.A_BOLD,
        "underline":  curses.A_UNDERLINE,
        "reverse":    curses.A_REVERSE,
        "blink":      curses.A_BLINK,
        "dim":        curses.A_DIM,
        "bright":     curses.A_STANDOUT,
        "standout":   curses.A_STANDOUT,
        "normal":     curses.A_NORMAL,
        "default":    curses.A_NORMAL
    }

_color_pairs: dict[tuple[int, int, int], int] = {}    

def cm(fg: str = "default", bg: str = "default", att: str = "default") -> int:

    fore = _COLOR_MAP[fg]
    back = _COLOR_MAP[bg]
    attr = _ATTR_MAP[att]
    
    key = (fore, back, attr)

    if key not in _color_pairs:

        idx = len(_color_pairs) + 1
        curses.init_pair(idx, fore, back)
        _color_pairs[key] = curses.color_pair(idx) | attr

    return _color_pairs[key]

# ----------------------------------------------------------------------
# Base Widget
# ----------------------------------------------------------------------

class Widget:

    def __init__(self, x: int, y: int, width: int, height: int = 1, **kwargs):
        
        self.x      = x
        self.y      = y
        self.width  = width
        self.height = height

        self.name   = kwargs.get("name", None)

        self.parent: Optional["Window"] = None
                 
        self.visible = True
        self.focused = False
        
    def set_parent(self, parent: "Window") -> None:
        self.parent = parent

    def box(self, win, x, y, w, h, style) :

        h -= 1
        
        win.hline(y, x, curses.ACS_HLINE, w, style)        
        win.hline(y + h, x, curses.ACS_HLINE, w, style)
        
        win.vline(y, x, curses.ACS_VLINE, h, style)
        win.vline(y, x + w, curses.ACS_VLINE, h, style)

        win.addch(y, x, curses.ACS_ULCORNER, style)
        win.addch(y + h, x, curses.ACS_LLCORNER, style)
        win.addch(y, x + w, curses.ACS_URCORNER, style)
        win.addch(y + h, x + w, curses.ACS_LRCORNER, style)
        
    def request_repaint(self) :
        if self.parent :
            self.parent.request_repaint()
            
    def paint(self, win) -> None:
        pass

    def contains(self, x: int, y: int) -> bool:
        return (self.x <= x < self.x + self.width and
                self.y <= y < self.y + self.height)

    def handle_key(self, key: int) -> bool:
        return False
    
    def handle_mouse(self, x: int, y: int, button: int) -> bool:
        return False

    def handle_tick(self) :
        return False
    
# ----------------------------------------------------------------------
# Container - Used to make composite wiget patterns
# ----------------------------------------------------------------------

class Container(Widget):
    
    def __init__(self, x: int, y: int, width: int, height: int, **kwargs):

        super().__init__(x, y, width, height, **kwargs)

        self.children       = []
        self.child_names    = {}
        self.focused_child  = None

        # Optional background/fill properties for the container itself
        self.base_foreground  = kwargs.get("base_foreground", "default")
        self.base_background  = kwargs.get("base_background", "default")
        self.base_attribute   = kwargs.get("base_attribute",  "default")
        self.base_color       = None


        self.border_fg   = kwargs.get("border_foreground", "cyan")
        self.border_bg   = kwargs.get("border_background", "default")
        self.border_att  = kwargs.get("border_attribute",  "default")
        self.border_color = None

        
    def add_widget(self, w: Widget) -> Widget:

        # Set the child's parent to the same window as this container
        if self.parent:
            w.set_parent(self.parent)

        self.children.append(w)

        if w.name:
            self.child_names[w.name] = w

        self.request_repaint()
        return w

    def remove_widget(self, w: Widget) -> None:
        if w in self.children:
            self.children.remove(w)
            if w.name and w.name in self.child_names:
                del self.child_names[w.name]
            if self.focused_child == w:
                self.focused_child = None
            self.request_repaint()

    def get_child_by_name(self, name: str) -> Optional[Widget]:
        return self.child_names.get(name)

    def set_focus(self, w: Optional[Widget]) -> None:
        if self.focused_child:
            self.focused_child.focused = False
        self.focused_child = w
        if w:
            w.focused = True
        self.request_repaint()

    def next_focus(self) -> None:
        if not self.children:
            return
        i = (self.children.index(self.focused_child) + 1) % len(self.children) if self.focused_child else 0
        self.set_focus(self.children[i])

    def prev_focus(self) -> None:
        if not self.children:
            return
        i = (self.children.index(self.focused_child) - 1) % len(self.children) if self.focused_child else -1
        self.set_focus(self.children[i])

    def paint(self, win) -> None:

        # One time init colors
        
        if self.base_color is None:
            self.base_color = cm(self.base_foreground, self.base_background, self.base_attribute)

        if self.border_color is None :
            self.border_color = cm(self.border_fg, self.border_bg, self.border_att)
            
        # Paint Background
        
        try:
            for dy in range(self.height):
                win.addstr(self.y + dy, self.x, " " * self.width, self.base_color)
        except curses.error:
            pass

        # Paint box if requested...
        
        self.box(win, self.x, self.y, self.width, self.height, self.border_color)
        
        #
        # Because these child  widgets aren't based on a curses window, 
        # we need to simulate the window based coordinates that widgets 
        # expect, so paint the children with a temporary absolute offset.
        # 

        for child in self.children:
            if child.visible:
                orig_x, orig_y = child.x, child.y
                child.x += self.x
                child.y += self.y
                child.paint(win)
                child.x, child.y = orig_x, orig_y

    def contains(self, x: int, y: int) -> bool:
        # Check if point is within container or any child (with relative coords)
        if not (self.x <= x < self.x + self.width and self.y <= y < self.y + self.height):
            return False
        rel_x = x - self.x
        rel_y = y - self.y
        return any(child.contains(rel_x, rel_y) for child in self.children)

    def handle_key(self, key: int) -> bool:
        # Handle tab navigation within container
        if key == ord('\t'):
            self.next_focus()
            return True
        if key == curses.KEY_BTAB:
            self.prev_focus()
            return True

        # Delegate to focused child first
        if self.focused_child and self.focused_child.handle_key(key):
            return True

        # Then try all children in reverse (top-to-bottom)
        for child in reversed(self.children):
            if child.handle_key(key):
                return True

        return False

    def handle_mouse(self, x: int, y: int, button: int) -> bool:
        # Check if within container
        if not (self.x <= x < self.x + self.width and self.y <= y < self.y + self.height):
            return False

        # Compute relative coordinates
        rel_x = x - self.x
        rel_y = y - self.y

        # Delegate to children in reverse order (top-most first)
        for child in reversed(self.children):
            if child.contains(rel_x, rel_y) and child.handle_mouse(rel_x, rel_y, button):
                # Optionally set focus to the clicked child if it handles the event
                if button & curses.BUTTON1_PRESSED:
                    self.set_focus(child)
                return True

        # Container itself doesn't handle mouse by default
        return False
    
# ----------------------------------------------------------------------
# Window
# ----------------------------------------------------------------------
class Window:
    
    def __init__(self, x: int, y: int, width: int, height: int, **kwargs):

        self.x             = x        
        self.y             = y
        self.width         = width        
        self.height        = height
        
        self.title         = kwargs.get("title", "")
        self.name          = kwargs.get("name", None)
        
        self.title_fg      = kwargs.get("title_foreground", "default")
        self.title_bg      = kwargs.get("title_background", "default")
        self.title_att     = kwargs.get("title_attribute",  "reverse")
        self.title_color   = None
        
        self.border_fg     = kwargs.get("border_foreground", "default")
        self.border_bg     = kwargs.get("border_background", "default")
        self.border_att    = kwargs.get("border_attribute",  "default")

        self.border_style  = kwargs.get("border_style",      "single") # single, double, solid, none
        self.border_color  = None
        
        self.active_fg     = kwargs.get("active_foreground", "default")
        self.active_bg     = kwargs.get("active_background", "default")
        self.active_att    = kwargs.get("active_attribute",  "default")
        self.active_color  = None
        
        self.win   = curses.newwin(height, width, y, x)
        self.panel = curses.panel.new_panel(self.win)
        
        self.panel.set_userptr(self)
        
        self.active = False     

        self.widgets: List[Widget] = []

        self.widget_names = {}
                 
        self.focused_widget: Optional[Widget] = None
        self.needs_repaint = True

        self.window_manager = None

    def set_title(self, text):
        
        self.title = text
        self.request_repaint()
        
    def get_manager(self) :

        return self.window_manager
    
    def add_widget(self, w: Widget) -> Widget:

        w.set_parent(self)
        
        self.widgets.append(w)
        
        if w.name :
           self.widget_names[w.name] = w
                 
        self.request_repaint()

        return w

    def move_top(self) :
        self.panel.top()

    def move_botton(self) :
        self.panel.bottom()

    def move_forwared(self) :
        self.panel.forward()

    def move_backward(self) :
        self.panel.backward()

    def hide(self) :
        self.panel.hide()

    def show(self) :
        self.panel.show()
        
    def set_focus(self, w: Optional[Widget]) -> None:

        if self.focused_widget:
            self.focused_widget.focused = False

        self.focused_widget = w

        if w:
            w.focused = True

        self.request_repaint()

    def next_focus(self) -> None:

        if not self.widgets:
            return
        
        i = (self.widgets.index(self.focused_widget) + 1) % len(self.widgets) if self.focused_widget else 0

        self.set_focus(self.widgets[i])

    def prev_focus(self) -> None:

        if not self.widgets: return
        i = (self.widgets.index(self.focused_widget) - 1) % len(self.widgets) if self.focused_widget else -1

        self.set_focus(self.widgets[i])

    def request_repaint(self) -> None:
        self.needs_repaint = True

    def resize(self, width: int, height: int) :

        self.win.resize(height, width)        
        self.panel.replace(self.win)        
        self.request_repaint()

    def move(self, x, y) :

        result = curses.ERR
        
        if x != self.x or y != self.y :

            try :
                result = self.win.mvwin(y, x)                
            except Exception as e :
                pass
                
            self.x = x
            self.y = y            
            self.request_repaint()

        return result
    
    def paint(self) -> None:

        if not self.needs_repaint:
            return

        w = self.win
        
        w.erase()

        if self.border_style != None :
            
            if self.border_color == None :
                self.border_color = cm(self.border_fg, self.border_bg, self.border_att)
            
            w.attron(self.border_color)
            w.border()
            w.attroff(self.border_color)
        
        if self.title:

            t = f" {self.title} "
            
            if self.title_color == None :
               self.title_color = cm(self.title_fg, self.title_bg, self.title_att)

            w.addstr(0, 2, t, self.title_color)

        if self.active:

            if self.active_color == None :
                self.active_color = cm(self.active_fg, self.active_bg, self.active_att)

            w.addstr(0, 1, "*", self.active_color)

        for widget in self.widgets:
            if widget.visible:
                widget.paint(w)

        self.needs_repaint = False

    # ---- input ------------------------------------------------------------

    def handle_key(self, key: int) -> bool:

        if key == ord('\t'):
            self.next_focus(); return True

        if key == curses.KEY_BTAB:
            self.prev_focus(); return True

        if self.focused_widget and self.focused_widget.handle_key(key):
            return True

        for widget in reversed(self.widgets):
            if widget.handle_key(key):
                return True

    def handle_mouse(self, local_x: int, local_y: int, button: int) -> bool:

        for widget in reversed(self.widgets):
            if widget.handle_mouse(local_x, local_y, button):
                return True

    def handle_tick(self) :

        for widget in reversed(self.widgets) :
            widget.handle_tick()            
    
    def handle_resize(self, width, height) :        
        pass
    
# ----------------------------------------------------------------------
# WindowManager (panels + global repaint)
# ----------------------------------------------------------------------
class WindowManager:
    
    def __init__(self, stdscr):

        self.stdscr = stdscr        
        self.window = {}
        self.active_window = None
        self.last_tick    = 0.0
        
        (self.height, self.width) = stdscr.getmaxyx()
        
        curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
        curses.mouseinterval(0)

    def get_window_byName(self, name: str) -> Window :

        result = None
    
        if name in self.window :
            result = self.window[name]

        return result
    
        
    def get_widget_byName(self, name: str) -> Widget :

        window = None
        widget = None
        
        (window_str, widget_str) = name.split("/")
        
        if window_str and widget_str :                            
            window = self.get_window_byName(window_str)
            
            if window :        
                if widget_str in window.widget_names :
                   widget = window.widget_names[widget_str]
        
        return widget
    
                   
    def add_window(self, win: Window) -> Window:
        
        if win.name :           
           self.window[win.name] = win
           
        self.set_active_window(win)

        # Store a quick link to the window manager.
        win.window_manager = self
        
        return win

    def set_active_window(self, win: Window) -> None:        

        if self.active_window == win:
            return

        if self.active_window:
            self.active_window.active = False
            self.active_window.request_repaint()

        self.active_window = win
        win.active = True
        win.request_repaint()        
        win.panel.top()

    def get_window_at(self, x: int, y: int) -> Optional[Window]:

        panel = curses.panel.top_panel()

        while panel:
            
            win_obj = panel.userptr()

            if win_obj and isinstance(win_obj, Window):
                win = win_obj
                if (win.y <= y < win.y + win.height and
                    win.x <= x < win.x + win.width):
                    return win
                
            panel = panel.below()

        return None
    
    def event_loop(self) -> None:

        self.stdscr.nodelay(True)
        curses.curs_set(0)
        self.running = True

        while self.running:
            
            frame_start = time.monotonic()
            
            key = self.stdscr.getch()

            while key != -1:

                #
                # MOUSE EVENTS
                #
                # Determine which window the X,Y Coordinates occurred, by 
                # searching Top to bottom of the panel stack.. then
                # subtract the windows x, y and pass the relative coordinates
                # into the windows handle_mouse interface.
                #
                
                if key == curses.KEY_MOUSE:                
                    try:
                        _, mx, my, _, bstate = curses.getmouse()
                        win = self.get_window_at(mx, my)
                        if win:
                            self.set_active_window(win)
                            local_x = mx - win.x
                            local_y = my - win.y
                            win.handle_mouse(local_x, local_y, bstate)

                    except curses.error:
                        # Invalid mouse event — ignore but KEEP DRAINING
                        pass

                #
                # TERMINAL RESIZE
                #
                # Get the new size, and interate through the panel stack
                # from bottom to top, and call their resize handlers.
                #
                
                if key == curses.KEY_RESIZE :
                    
                    self.height, self.width = self.stdscr.getmaxyx()

                    panel = curses.panel.bottom_panel()       # start at true bottom

                    while panel:
                        
                        win_obj = panel.userptr()

                        if win_obj and isinstance(win_obj, Window):
                            win_obj.handle_resize(self.width, self.height)

                        panel = panel.above()

                #
                # EVERY OTHER KEY
                #
                
                elif self.active_window:
                    self.active_window.handle_key(key)
                    
                # Always get next key — even after error
                key = self.stdscr.getch()

                
            # Call all the paint routines.
            
            panel = curses.panel.bottom_panel()

            while panel :
                win = panel.userptr()
                if win :
                   win.paint()
                panel = panel.above()
                
            # Refresh the actual screen.
            curses.panel.update_panels()

            self.stdscr.noutrefresh()
            curses.doupdate()

            #
            # Time for a system Tick 1/10 sec
            #
            
            if (time.monotonic() - self.last_tick) >= (0.100) :
                self.last_tick = time.monotonic()
                panel = curses.panel.bottom_panel()
                while panel :
                    win = panel.userptr()
                    if win :
                        win.handle_tick()
                    panel = panel.above()

             # === 4. FPS LIMIT ===
            elapsed = time.monotonic() - frame_start
            target = 1.0 / 60.0

            if elapsed < target:
                time.sleep(target - elapsed)

# ----------------------------------------------------------------------
# Widget Button
# ----------------------------------------------------------------------

class Button(Widget):

    def __init__(self, x: int, y: int, width: int, **kwargs) :

        super().__init__(x, y, width)

        self.text         = kwargs.get("text",               "")

        self.on_click     = kwargs.get("on_click",   lambda *_, **__: None)
        self.on_press     = kwargs.get("on_press",   lambda *_, **__: None)
        self.on_release   = kwargs.get("on_release", lambda *_, **__: None)

        self.toggle       = kwargs.get("toggle",             False)
        
        self.normal_fg    = kwargs.get("normal_foreground",  "white")
        self.normal_bg    = kwargs.get("normal_background",  "default")
        self.normal_att   = kwargs.get("normal_attribute",   "reverse")

        self.pressed_fg   = kwargs.get("pressed_foreground", "white")
        self.pressed_bg   = kwargs.get("pressed_background", "default")
        self.pressed_att  = kwargs.get("pressed_attribute",  "default")

        self.active_fg    = kwargs.get("active_foreground",  "white")
        self.active_bg    = kwargs.get("active_background",  "red")
        self.active_att   = kwargs.get("active_attribute",   "default")
        
        self.normal_color  = None
        self.pressed_color = None
        self.active_color  = None

        self.state         = 0

    def set_text(self, text):
        
        self.text = text
        self.request_repaint()

    def click(self) :
        
        if self.on_click :                      
            self.on_click(button=self)
            
    def paint(self, win):

        if self.normal_color == None :
            self.normal_color = cm(self.normal_fg, self.normal_bg, self.normal_att)

        if self.pressed_color == None :
            self.pressed_color = cm(self.pressed_fg, self.pressed_bg, self.pressed_att)

        if self.active_color == None :
            self.active_color = cm(self.active_fg, self.active_bg, self.active_att)
                    
        label = self.text.center(self.width)

        # Same style for now.
        style = self.normal_color

        try:
            
            win.addstr(self.y, self.x, label, style)

        except curses.error:
            pass

    def handle_key(self, key: int) -> bool:

        if key in (curses.KEY_ENTER, ord('\n'), ord(' ')) and self.focused:
            self.on_click()
            self.request_repaint()
            return True
        return False

    def handle_mouse(self, x: int, y: int, button: int) -> bool:

        result = False
        
        if self.contains(x, y) :
            
            if self.state == 0 :                      # Button is IDLE
                
                if button & curses.BUTTON1_PRESSED :  # New Button is DOWN
                    self.state = 1                    # Transition to down... 
                    self.request_repaint()
                    
                    if self.on_press :
                        self.on_press(button=self)
                        
            elif self.state == 1 :                    # Wait for release
                
                if button & curses.BUTTON1_RELEASED : # Button is released
                    self.state = 0                    # Go back to IDLE
                    self.request_repaint()            # Get repainted for new state.

                    if self.on_release :
                        self.on_release(button=self)   # Process release event...
                    
                    if self.contains(x, y) :           # only fire full click if done inside.
                        if self.on_click :                      
                            self.on_click(button=self) # Process Click event.                                                    
                    result = True
                    
        return result
                        
# ----------------------------------------------------------------------
# Widget StatusLabel
# ----------------------------------------------------------------------

class StatusLabel(Widget):
    
    def __init__(self, x: int, y: int, width: int, **kwargs) :                         

        super().__init__(x, y, width, **kwargs)
        
        self.units        = kwargs.get("units",   "")
        self.value        = kwargs.get("value",  0.0)
        
        self.normal_fg    = kwargs.get("normal_foreground", "default")
        self.normal_bg    = kwargs.get("normal_background", "default")
        self.normal_att   = kwargs.get("normal_attribute",  "default")
        
        self.fault_fg     = kwargs.get("fault_foreground",  "default")
        self.fault_bg     = kwargs.get("fault_background",  "default")
        self.fault_att    = kwargs.get("fault_attribute",   "default")

        self.units_fg     = kwargs.get("units_foreground",  "default")
        self.units_bg     = kwargs.get("units_background",  "default")
        self.units_att    = kwargs.get("units_attribute",   "default")
        
        self.threshold    = kwargs.get("threshold",   "")        
        self.comparison   = kwargs.get("comparison",  "")
        self.fmt          = kwargs.get("format",      "")

        self.scale          = kwargs.get("on_display",   "")
        
        self.normal_color = None
        self.fault_color  = None
        self.units_color  = None
        
    def set_value(self, value):

        if isinstance(value, (int)) :
            self.value = int(value)
        elif isinstance(value, (float)) :
            self.value = float(value)
        elif isinstance(value, (str)) :
            self.value = str(value)
            
        self.request_repaint()

    def set_units(self, value) :
        self.units = value
        
    def get_value(self) :
        return self.value

    def _compare_values(self) :

        faulted = False

        # &= BAE  Bitwise AND and Equal
        # |= BOE  Bitwise OR and equal
        #
        # Faulted text, normal text
        #
        
        if isinstance(self.value, (int, float)) :

            if self.comparison == "LT" or self.comparison == "<" :
                faulted = float(self.value) < float(self.threshold)

            elif self.comparison == "LTE" or self.comparison == "<=" :
                faulted = float(self.value) <= float(self.threshold)
                
            elif self.comparison == "GT" or self.comparison == ">" :
                faulted = float(self.value) > float(self.threshold)

            elif self.comparison == "GTE" or self.comparison == ">=" :
                faulted = float(self.value) >= float(self.threshold)
                
            else :
                faulted = self.value == self.threshold

        return faulted

    
    def paint(self, win):

        # Set Value...
        txt = f"{self.value:{self.fmt}}"

        # detect fault.

        faulted = self._compare_values()
        
        # First Time Color Init
        
        if self.fault_color == None :
            self.fault_color = cm(self.fault_fg, self.fault_bg, self.fault_att)

        if self.normal_color == None :
            self.normal_color = cm(self.normal_fg, self.normal_bg, self.normal_att)

        if self.units_color == None :
            self.units_color = cm(self.units_fg, self.units_bg, self.units_att)
            
        # Get Style

        if faulted :
            style = self.fault_color
        else :
            style = self.normal_color

        try:

            win.addstr(self.y, self.x, txt, style)
            win.addstr(self.y, self.x + len(txt), f"{self.units}", self.units_color)
            
        except curses.error:
            pass

# ----------------------------------------------------------------------
# Widget ProgressBar
# ----------------------------------------------------------------------

class ProgressBar(Widget):
    
    def __init__(self, x: int, y: int, width: int, **kwargs):
        
        super().__init__(x, y, width, **kwargs)
        
        self.value         = kwargs.get("value",   0.0)
        self.minimum       = kwargs.get("minimum", 0.0)
        self.maximum       = kwargs.get("maximum", 100.0)

        self.show_value    = kwargs.get("show_value", True)
        self.fmt           = kwargs.get("format",     "")
        
        self.warning_threshold   = kwargs.get("warning_threshold",  50)
        self.critical_threshold  = kwargs.get("critical_threshold", 75)
        self.invert_threshold    = kwargs.get("invert_threshold",   False)
        
        self.fill_char     = kwargs.get("fill_char", "█")
        self.empty_char    = kwargs.get("empty_char", "░")

        self.normal_fg     = kwargs.get("normal_foreground",  "green")
        self.normal_bg     = kwargs.get("normal_background",  "black")
        self.normal_att    = kwargs.get("normal_attribute",   "default")
        self.normal_color  = None
        
        self.warning_fg    = kwargs.get("warning_foreground", "yellow")
        self.warning_bg    = kwargs.get("warning_background", "black")
        self.warning_att   = kwargs.get("warning_attribute",  "default")
        self.warning_color = None
        
        self.critical_fg    = kwargs.get("critical_foreground", "red")
        self.critical_bg    = kwargs.get("critical_background", "black")
        self.critical_att   = kwargs.get("critical_attribute",  "default")
        self.critical_color = None
        
    def set_value(self, value: float):
        
        self.value = max(self.minimum, min(self.maximum, value))
        self.request_repaint()

    def paint(self, win):

        # Clamp value to range
        work_value = max(self.minimum, min(self.value, self.maximum))

        # Compute Relative, abs value range...
        relative_range = self.maximum - self.minimum

        # Adjust for Text if needed.        
        if self.show_value :
            bar_text  = f" {self.value:{self.fmt}} "
            bar_width = self.width - len(bar_text)
        else :
            bar_text  = ""
            bar_width = self.width
            
        # Get bar relative value
        bar_value = (work_value - self.minimum) / relative_range
        
        # Convert fraction to number of filled characters
        filled_length = round(bar_value * bar_width)
        
        # Build the bar
        filled  = self.fill_char * filled_length
        empty   = self.empty_char * (bar_width - filled_length)

        bar = filled + empty + bar_text
        
        #
        # Init the colors on first pass
        #
        
        if self.normal_color == None :
           self.normal_color = cm(self.normal_fg, self.normal_bg, self.normal_att)

        if self.warning_color == None :
           self.warning_color = cm(self.warning_fg, self.warning_bg, self.warning_att)

        if self.critical_color == None :
           self.critical_color = cm(self.critical_fg, self.critical_bg, self.critical_att)
           
        #
        # Select the proper Color
        #

        if self.invert_threshold :
            if self.value < self.critical_threshold :        
                style = self.critical_color
            elif self.value < self.warning_threshold :
                style = self.warning_color
            else :
                style = self.normal_color
        else :                
            if self.value >= self.critical_threshold :        
                style = self.critical_color
            elif self.value >= self.warning_threshold :
                style = self.warning_color
            else :
                style = self.normal_color

        #
        # Do the draw...
        #
        
        try:            
            win.addstr(self.y, self.x, bar, style)
            
        except curses.error:
            pass
                     
