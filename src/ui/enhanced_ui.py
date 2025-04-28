import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
import logging
from typing import Dict, Any, List, Optional, Callable
import threading
import asyncio
import time
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

class ModernUITheme:
    """Modern UI theme with customized styles for the trading bot"""
    
    # Color palette
    PRIMARY = "#3a7ca5"
    SECONDARY = "#16a085"
    ACCENT = "#e74c3c"
    BACKGROUND = "#f5f5f5"
    CARD_BG = "#ffffff"
    TEXT_PRIMARY = "#2c3e50"
    TEXT_SECONDARY = "#7f8c8d"
    SUCCESS = "#2ecc71"
    WARNING = "#f39c12"
    ERROR = "#e74c3c"
    BORDER = "#dcdde1"
    
    # Font settings
    FONT_FAMILY = "Helvetica"
    FONT_SIZE_SMALL = 9
    FONT_SIZE_NORMAL = 10
    FONT_SIZE_LARGE = 12
    FONT_SIZE_XLARGE = 14
    FONT_SIZE_XXLARGE = 18
    
    @classmethod
    def apply_theme(cls, root):
        """Apply the modern theme to the root window and all widgets"""
        style = ttk.Style()
        
        # Configure basic styles
        style.configure(".", 
            font=(cls.FONT_FAMILY, cls.FONT_SIZE_NORMAL),
            background=cls.BACKGROUND,
            foreground=cls.TEXT_PRIMARY,
            troughcolor=cls.BORDER,
            focuscolor=cls.PRIMARY,
            borderwidth=1,
            bordercolor=cls.BORDER
        )
        
        # Configure TFrame
        style.configure("TFrame", background=cls.BACKGROUND)
        style.configure("Card.TFrame", background=cls.CARD_BG, relief="flat", borderwidth=0)
        
        # Configure TLabel
        style.configure("TLabel", 
            background=cls.BACKGROUND, 
            foreground=cls.TEXT_PRIMARY,
            font=(cls.FONT_FAMILY, cls.FONT_SIZE_NORMAL)
        )
        style.configure("Card.TLabel", background=cls.CARD_BG)
        style.configure("Title.TLabel", 
            font=(cls.FONT_FAMILY, cls.FONT_SIZE_XLARGE, "bold"),
            foreground=cls.PRIMARY
        )
        style.configure("Subtitle.TLabel", 
            font=(cls.FONT_FAMILY, cls.FONT_SIZE_LARGE),
            foreground=cls.TEXT_SECONDARY
        )
        style.configure("Success.TLabel", foreground=cls.SUCCESS)
        style.configure("Warning.TLabel", foreground=cls.WARNING)
        style.configure("Error.TLabel", foreground=cls.ERROR)
        
        # Configure TButton
        style.configure("TButton", 
            font=(cls.FONT_FAMILY, cls.FONT_SIZE_NORMAL),
            background=cls.PRIMARY,
            foreground="white",
            borderwidth=0,
            focusthickness=0,
            focuscolor=cls.PRIMARY,
            padding=(10, 5)
        )
        style.map("TButton",
            background=[("active", cls.PRIMARY), ("disabled", cls.BORDER)],
            foreground=[("disabled", cls.TEXT_SECONDARY)]
        )
        
        # Accent button style
        style.configure("Accent.TButton", 
            background=cls.ACCENT,
            foreground="white"
        )
        style.map("Accent.TButton",
            background=[("active", cls.ACCENT), ("disabled", cls.BORDER)]
        )
        
        # Success button style
        style.configure("Success.TButton", 
            background=cls.SUCCESS,
            foreground="white"
        )
        style.map("Success.TButton",
            background=[("active", cls.SUCCESS), ("disabled", cls.BORDER)]
        )
        
        # Secondary button style
        style.configure("Secondary.TButton", 
            background=cls.SECONDARY,
            foreground="white"
        )
        style.map("Secondary.TButton",
            background=[("active", cls.SECONDARY), ("disabled", cls.BORDER)]
        )
        
        # Small button style
        style.configure("Small.TButton", 
            font=(cls.FONT_FAMILY, cls.FONT_SIZE_SMALL),
            padding=(5, 2)
        )
        
        # Configure TEntry
        style.configure("TEntry", 
            fieldbackground=cls.CARD_BG,
            foreground=cls.TEXT_PRIMARY,
            borderwidth=1,
            padding=(5, 2)
        )
        style.map("TEntry",
            fieldbackground=[("disabled", cls.BACKGROUND)],
            foreground=[("disabled", cls.TEXT_SECONDARY)]
        )
        
        # Configure TCombobox
        style.configure("TCombobox", 
            fieldbackground=cls.CARD_BG,
            background=cls.PRIMARY,
            foreground=cls.TEXT_PRIMARY,
            arrowcolor=cls.PRIMARY,
            borderwidth=1,
            padding=(5, 2)
        )
        style.map("TCombobox",
            fieldbackground=[("disabled", cls.BACKGROUND)],
            foreground=[("disabled", cls.TEXT_SECONDARY)]
        )
        
        # Configure TCheckbutton
        style.configure("TCheckbutton", 
            background=cls.BACKGROUND,
            foreground=cls.TEXT_PRIMARY
        )
        
        # Configure TRadiobutton
        style.configure("TRadiobutton", 
            background=cls.BACKGROUND,
            foreground=cls.TEXT_PRIMARY
        )
        
        # Configure TNotebook
        style.configure("TNotebook", 
            background=cls.BACKGROUND,
            tabmargins=[2, 5, 2, 0]
        )
        style.configure("TNotebook.Tab", 
            background=cls.BACKGROUND,
            foreground=cls.TEXT_SECONDARY,
            padding=[10, 5],
            font=(cls.FONT_FAMILY, cls.FONT_SIZE_NORMAL)
        )
        style.map("TNotebook.Tab",
            background=[("selected", cls.CARD_BG)],
            foreground=[("selected", cls.PRIMARY)],
            expand=[("selected", [1, 1, 1, 0])]
        )
        
        # Configure Treeview
        style.configure("Treeview", 
            background=cls.CARD_BG,
            foreground=cls.TEXT_PRIMARY,
            fieldbackground=cls.CARD_BG,
            borderwidth=0,
            font=(cls.FONT_FAMILY, cls.FONT_SIZE_NORMAL)
        )
        style.configure("Treeview.Heading", 
            background=cls.PRIMARY,
            foreground="white",
            font=(cls.FONT_FAMILY, cls.FONT_SIZE_NORMAL, "bold"),
            relief="flat",
            borderwidth=0
        )
        style.map("Treeview.Heading",
            background=[("active", cls.PRIMARY)]
        )
        
        # Configure Progressbar
        style.configure("TProgressbar", 
            background=cls.PRIMARY,
            troughcolor=cls.BACKGROUND,
            borderwidth=0,
            thickness=10
        )
        
        # Configure Scrollbar
        style.configure("TScrollbar", 
            background=cls.BACKGROUND,
            troughcolor=cls.BACKGROUND,
            borderwidth=0,
            arrowsize=13
        )
        
        # Configure Separator
        style.configure("TSeparator", 
            background=cls.BORDER
        )
        
        # Configure LabelFrame
        style.configure("TLabelframe", 
            background=cls.CARD_BG,
            foreground=cls.TEXT_PRIMARY,
            borderwidth=1,
            relief="solid",
            bordercolor=cls.BORDER
        )
        style.configure("TLabelframe.Label", 
            background=cls.CARD_BG,
            foreground=cls.PRIMARY,
            font=(cls.FONT_FAMILY, cls.FONT_SIZE_NORMAL, "bold")
        )
        
        # Configure Panedwindow
        style.configure("TPanedwindow", 
            background=cls.BACKGROUND,
            sashwidth=4,
            sashrelief="flat",
            sashcolor=cls.BORDER
        )
        
        # Configure Scale
        style.configure("TScale", 
            background=cls.BACKGROUND,
            troughcolor=cls.BORDER,
            sliderrelief="flat",
            sliderlength=15
        )
        
        # Set theme for the root window
        root.configure(background=cls.BACKGROUND)
        
        return style

class AnimatedButton(ttk.Button):
    """Button with hover and click animations"""
    
    def __init__(self, master=None, **kwargs):
        self.style_name = kwargs.pop('style', 'TButton')
        self.hover_style = kwargs.pop('hover_style', None)
        self.click_style = kwargs.pop('click_style', None)
        
        super().__init__(master, style=self.style_name, **kwargs)
        
        # Create hover and click styles if not provided
        if not self.hover_style:
            self.hover_style = f"{self.style_name}.Hover"
        
        if not self.click_style:
            self.click_style = f"{self.style_name}.Click"
        
        # Bind events
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
    
    def _on_enter(self, event):
        self.configure(style=self.hover_style)
    
    def _on_leave(self, event):
        self.configure(style=self.style_name)
    
    def _on_press(self, event):
        self.configure(style=self.click_style)
    
    def _on_release(self, event):
        self.configure(style=self.hover_style)
        # Schedule return to normal style
        self.after(100, lambda: self.configure(style=self.style_name))

class CardFrame(ttk.Frame):
    """A frame styled as a card with optional shadow effect"""
    
    def __init__(self, master=None, title=None, **kwargs):
        self.shadow = kwargs.pop('shadow', True)
        self.padding = kwargs.pop('padding', 10)
        
        # Create shadow frame if needed
        if self.shadow:
            self.shadow_frame = ttk.Frame(master, style="Shadow.TFrame")
            self.shadow_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
            super().__init__(self.shadow_frame, style="Card.TFrame", padding=self.padding, **kwargs)
        else:
            super().__init__(master, style="Card.TFrame", padding=self.padding, **kwargs)
        
        # Add title if provided
        if title:
            self.title_label = ttk.Label(self, text=title, style="Title.TLabel")
            self.title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Pack the frame
        self.pack(fill=tk.BOTH, expand=True)

class StatusIndicator(ttk.Frame):
    """A status indicator widget with colored circle and text"""
    
    def __init__(self, master=None, text="Status", status="neutral", **kwargs):
        super().__init__(master, **kwargs)
        
        # Status colors
        self.colors = {
            "success": ModernUITheme.SUCCESS,
            "warning": ModernUITheme.WARNING,
            "error": ModernUITheme.ERROR,
            "neutral": ModernUITheme.TEXT_SECONDARY,
            "active": ModernUITheme.PRIMARY
        }
        
        # Create canvas for circle
        self.canvas = tk.Canvas(self, width=12, height=12, bg=ModernUITheme.BACKGROUND, 
                               highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, padx=(0, 5))
        
        # Create circle
        self.circle = self.canvas.create_oval(2, 2, 10, 10, fill=self.colors.get(status, self.colors["neutral"]))
        
        # Create label
        self.text_var = tk.StringVar(value=text)
        self.label = ttk.Label(self, textvariable=self.text_var)
        self.label.pack(side=tk.LEFT)
        
        # Set initial status
        self.set_status(status)
    
    def set_status(self, status, text=None):
        """Set the status and optionally update the text"""
        color = self.colors.get(status, self.colors["neutral"])
        self.canvas.itemconfig(self.circle, fill=color)
        
        if text:
            self.text_var.set(text)

class LoadingSpinner(ttk.Frame):
    """A loading spinner animation widget"""
    
    def __init__(self, master=None, size=20, thickness=2, color=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.size = size
        self.thickness = thickness
        self.color = color or ModernUITheme.PRIMARY
        self.spinning = False
        self.angle = 0
        
        # Create canvas
        self.canvas = tk.Canvas(self, width=size, height=size, bg=ModernUITheme.BACKGROUND,
                               highlightthickness=0)
        self.canvas.pack()
        
        # Create arc
        self.arc = self.canvas.create_arc(
            self.thickness, self.thickness, 
            size - self.thickness, size - self.thickness,
            start=0, extent=270, outline=self.color, width=self.thickness,
            style=tk.ARC
        )
    
    def start(self):
        """Start the spinning animation"""
        self.spinning = True
        self.spin()
    
    def stop(self):
        """Stop the spinning animation"""
        self.spinning = False
    
    def spin(self):
        """Update the spinner animation"""
        if not self.spinning:
            return
        
        self.angle = (self.angle + 10) % 360
        self.canvas.itemconfig(self.arc, start=self.angle)
        self.after(50, self.spin)

class ToastNotification:
    """Toast notification that appears and disappears automatically"""
    
    def __init__(self, master, message, duration=3000, type="info"):
        self.master = master
        self.message = message
        self.duration = duration
        
        # Determine colors based on type
        if type == "success":
            bg_color = ModernUITheme.SUCCESS
        elif type == "warning":
            bg_color = ModernUITheme.WARNING
        elif type == "error":
            bg_color = ModernUITheme.ERROR
        else:  # info
            bg_color = ModernUITheme.PRIMARY
        
        # Create toast frame
        self.toast = tk.Frame(master, bg=bg_color, padx=10, pady=5)
        
        # Add message label
        self.label = tk.Label(self.toast, text=message, bg=bg_color, fg="white",
                             font=(ModernUITheme.FONT_FAMILY, ModernUITheme.FONT_SIZE_NORMAL))
        self.label.pack(pady=5)
        
        # Position at the bottom of the window
        self.toast.place(relx=0.5, rely=0.9, anchor="center")
        
        # Schedule removal
        self.master.after(duration, self.remove)
    
    def remove(self):
        """Remove the toast notification"""
        self.toast.destroy()

class EnhancedUI:
    """Helper class with methods to create enhanced UI elements"""
    
    @staticmethod
    def create_tooltip(widget, text):
        """Create a tooltip for a widget"""
        
        def enter(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            
            # Create a toplevel window
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{x}+{y}")
            
            # Create label
            label = ttk.Label(tooltip, text=text, background=ModernUITheme.PRIMARY,
                             foreground="white", padding=(5, 3))
            label.pack()
            
            # Store tooltip reference
            widget.tooltip = tooltip
        
        def leave(event):
            if hasattr(widget, "tooltip"):
                widget.tooltip.destroy()
                del widget.tooltip
        
        # Bind events
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
    
    @staticmethod
    def create_section_header(parent, text, with_line=True):
        """Create a section header with optional separator line"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=(15, 5))
        
        label = ttk.Label(frame, text=text, style="Title.TLabel")
        label.pack(side=tk.LEFT, anchor=tk.W)
        
        if with_line:
            separator = ttk.Separator(frame, orient=tk.HORIZONTAL)
            separator.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0), pady=5)
        
        return frame
    
    @staticmethod
    def create_info_box(parent, title, content, type="info"):
        """Create an information box with icon"""
        
        # Determine colors based on type
        if type == "success":
            bg_color = "#d5f5e3"  # Light green
            fg_color = ModernUITheme.SUCCESS
        elif type == "warning":
            bg_color = "#fef9e7"  # Light yellow
            fg_color = ModernUITheme.WARNING
        elif type == "error":
            bg_color = "#fadbd8"  # Light red
            fg_color = ModernUITheme.ERROR
        else:  # info
            bg_color = "#d6eaf8"  # Light blue
            fg_color = ModernUITheme.PRIMARY
        
        # Create frame
        frame = tk.Frame(parent, bg=bg_color, padx=10, pady=10)
        frame.pack(fill=tk.X, pady=5)
        
        # Add title
        if title:
            title_label = tk.Label(frame, text=title, bg=bg_color, fg=fg_color,
                                 font=(ModernUITheme.FONT_FAMILY, ModernUITheme.FONT_SIZE_NORMAL, "bold"))
            title_label.pack(anchor=tk.W)
        
        # Add content
        content_label = tk.Label(frame, text=content, bg=bg_color, fg=ModernUITheme.TEXT_PRIMARY,
                               font=(ModernUITheme.FONT_FAMILY, ModernUITheme.FONT_SIZE_NORMAL),
                               justify=tk.LEFT, wraplength=400)
        content_label.pack(anchor=tk.W, pady=(5, 0))
        
        return frame
    
    @staticmethod
    def create_data_row(parent, label_text, value_text=None, value_var=None):
        """Create a row with label and value for displaying data"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=2)
        
        label = ttk.Label(frame, text=label_text, width=20, anchor=tk.E)
        label.pack(side=tk.LEFT, padx=(0, 10))
        
        if value_var:
            value = ttk.Label(frame, textvariable=value_var)
        else:
            value = ttk.Label(frame, text=value_text or "")
        
        value.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        return frame, value
    
    @staticmethod
    def create_input_row(parent, label_text, input_var, input_type="entry", **kwargs):
        """Create a row with label and input field"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)
        
        label = ttk.Label(frame, text=label_text, width=20, anchor=tk.E)
        label.pack(side=tk.LEFT, padx=(0, 10))
        
        if input_type == "entry":
            input_widget = ttk.Entry(frame, textvariable=input_var, **kwargs)
        elif input_type == "combobox":
            input_widget = ttk.Combobox(frame, textvariable=input_var, **kwargs)
        elif input_type == "spinbox":
            input_widget = ttk.Spinbox(frame, textvariable=input_var, **kwargs)
        elif input_type == "checkbutton":
            input_widget = ttk.Checkbutton(frame, variable=input_var, **kwargs)
        else:
            input_widget = ttk.Entry(frame, textvariable=input_var, **kwargs)
        
        input_widget.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        return frame, input_widget
    
    @staticmethod
    def create_button_group(parent, buttons, side=tk.RIGHT, padx=5, pady=10):
        """Create a group of buttons"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=pady)
        
        for btn_config in reversed(buttons):  # Reverse to maintain order when using side=tk.RIGHT
            btn = ttk.Button(
                frame,
                text=btn_config.get("text", "Button"),
                command=btn_config.get("command"),
                style=btn_config.get("style", "TButton")
            )
            btn.pack(side=side, padx=padx)
            
            # Add tooltip if provided
            if "tooltip" in btn_config:
                EnhancedUI.create_tooltip(btn, btn_config["tooltip"])
        
        return frame
    
    @staticmethod
    def show_toast(master, message, type="info", duration=3000):
        """Show a toast notification"""
        return ToastNotification(master, message, duration, type)
    
    @staticmethod
    def create_loading_indicator(parent, text="Loading...", show_spinner=True):
        """Create a loading indicator with optional spinner"""
        frame = ttk.Frame(parent)
        
        if show_spinner:
            spinner = LoadingSpinner(frame, size=20)
            spinner.pack(side=tk.LEFT, padx=(0, 10))
            spinner.start()
        
        label = ttk.Label(frame, text=text)
        label.pack(side=tk.LEFT)
        
        return frame, spinner if show_spinner else None
    
    @staticmethod
    def create_search_box(parent, search_command, placeholder="Search..."):
        """Create a search box with icon and clear button"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)
        
        # Search variable
        search_var = tk.StringVar()
        
        # Search entry
        search_entry = ttk.Entry(frame, textvariable=search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Set placeholder
        search_entry.insert(0, placeholder)
        search_entry.config(foreground=ModernUITheme.TEXT_SECONDARY)
        
        def on_entry_click(event):
            if search_entry.get() == placeholder:
                search_entry.delete(0, tk.END)
                search_entry.config(foreground=ModernUITheme.TEXT_PRIMARY)
        
        def on_focus_out(event):
            if search_entry.get() == "":
                search_entry.insert(0, placeholder)
                search_entry.config(foreground=ModernUITheme.TEXT_SECONDARY)
        
        search_entry.bind("<FocusIn>", on_entry_click)
        search_entry.bind("<FocusOut>", on_focus_out)
        
        # Search button
        search_button = ttk.Button(
            frame,
            text="Search",
            command=lambda: search_command(search_var.get())
        )
        search_button.pack(side=tk.LEFT)
        
        # Bind Enter key
        search_entry.bind("<Return>", lambda event: search_command(search_var.get()))
        
        return frame, search_var, search_entry
    
    @staticmethod
    def create_status_bar(parent):
        """Create a status bar at the bottom of the window"""
        frame = ttk.Frame(parent, relief=tk.SUNKEN, padding=(5, 2))
        frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Status message
        status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(frame, textvariable=status_var)
        status_label.pack(side=tk.LEFT)
        
        # Current time
        time_var = tk.StringVar()
        time_label = ttk.Label(frame, textvariable=time_var)
        time_label.pack(side=tk.RIGHT)
        
        # Update time
        def update_time():
            time_var.set(datetime.now().strftime("%H:%M:%S"))
            frame.after(1000, update_time)
        
        update_time()
        
        return frame, status_var, time_var
    
    @staticmethod
    def create_tab_view(parent, tabs):
        """Create a tabbed view with the provided tabs"""
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tab_frames = {}
        
        for tab_id, tab_config in tabs.items():
            frame = ttk.Frame(notebook, padding=10)
            notebook.add(frame, text=tab_config.get("title", tab_id))
            tab_frames[tab_id] = frame
        
        return notebook, tab_frames
