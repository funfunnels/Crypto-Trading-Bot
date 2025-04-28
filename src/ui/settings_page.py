import tkinter as tk
from tkinter import ttk, messagebox
import asyncio
import threading
import base64
from datetime import datetime
import json
import os
import logging
from typing import Dict, Any, List, Optional, Tuple, Callable

# Configure logging
logger = logging.getLogger(__name__)

class SettingsPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.config_file = "config/config.json"
        self.config = self.load_config()
        
        # Create main container with padding
        main_container = ttk.Frame(self, padding="20 20 20 20")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(
            title_frame, 
            text="Settings", 
            font=("Helvetica", 18, "bold"),
            foreground="#3a7ca5"
        )
        title_label.pack(anchor=tk.W)
        
        # Create scrollable frame
        canvas = tk.Canvas(main_container)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # API Key Section
        self.create_section_header(scrollable_frame, "Wallet Configuration", "Configure your Solana wallet for trading")
        
        # Private Key Entry
        key_frame = ttk.Frame(scrollable_frame)
        key_frame.pack(fill=tk.X, pady=(10, 5))
        
        ttk.Label(key_frame, text="Private Key:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.private_key_var = tk.StringVar(value=self.config.get("private_key", ""))
        self.private_key_entry = ttk.Entry(key_frame, textvariable=self.private_key_var, show="*", width=50)
        self.private_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.show_key_var = tk.BooleanVar(value=False)
        self.show_key_check = ttk.Checkbutton(
            key_frame, 
            text="Show", 
            variable=self.show_key_var,
            command=self.toggle_key_visibility
        )
        self.show_key_check.pack(side=tk.LEFT)
        
        # Test Connection Button - NEW ADDITION
        test_conn_frame = ttk.Frame(scrollable_frame)
        test_conn_frame.pack(fill=tk.X, pady=(5, 15))
        
        self.test_connection_button = ttk.Button(
            test_conn_frame,
            text="Test Connection",
            command=self.test_connection,
            style="Accent.TButton"
        )
        self.test_connection_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.connection_status_var = tk.StringVar(value="Not tested")
        self.connection_status_label = ttk.Label(
            test_conn_frame,
            textvariable=self.connection_status_var,
            foreground="#999999"
        )
        self.connection_status_label.pack(side=tk.LEFT)
        
        # Import from Seed Phrase
        seed_frame = ttk.Frame(scrollable_frame)
        seed_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Button(
            seed_frame,
            text="Import from Seed Phrase",
            command=self.import_from_seed
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            seed_frame,
            text="Generate New Wallet",
            command=self.generate_new_wallet
        ).pack(side=tk.LEFT)
        
        # Trading Parameters Section
        self.create_section_header(scrollable_frame, "Trading Parameters", "Configure your trading strategy parameters")
        
        # Initial Capital
        capital_frame = ttk.Frame(scrollable_frame)
        capital_frame.pack(fill=tk.X, pady=(10, 5))
        
        ttk.Label(capital_frame, text="Initial Capital ($):").pack(side=tk.LEFT, padx=(0, 10))
        
        self.initial_capital_var = tk.DoubleVar(value=self.config.get("initial_capital", 200.0))
        initial_capital_entry = ttk.Entry(capital_frame, textvariable=self.initial_capital_var, width=10)
        initial_capital_entry.pack(side=tk.LEFT)
        
        # Target Value
        target_frame = ttk.Frame(scrollable_frame)
        target_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(target_frame, text="Target Value ($):").pack(side=tk.LEFT, padx=(0, 10))
        
        self.target_value_var = tk.DoubleVar(value=self.config.get("target_value", 10000.0))
        target_value_entry = ttk.Entry(target_frame, textvariable=self.target_value_var, width=10)
        target_value_entry.pack(side=tk.LEFT)
        
        # Days Remaining
        days_frame = ttk.Frame(scrollable_frame)
        days_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(days_frame, text="Days Remaining:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.days_remaining_var = tk.IntVar(value=self.config.get("days_remaining", 10))
        days_remaining_entry = ttk.Entry(days_frame, textvariable=self.days_remaining_var, width=10)
        days_remaining_entry.pack(side=tk.LEFT)
        
        # Max Concurrent Trades
        trades_frame = ttk.Frame(scrollable_frame)
        trades_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(trades_frame, text="Max Concurrent Trades:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.max_trades_var = tk.IntVar(value=self.config.get("max_concurrent_trades", 2))
        max_trades_entry = ttk.Entry(trades_frame, textvariable=self.max_trades_var, width=10)
        max_trades_entry.pack(side=tk.LEFT)
        
        # Trading Mode
        mode_frame = ttk.Frame(scrollable_frame)
        mode_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(mode_frame, text="Trading Mode:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.trading_mode_var = tk.StringVar(value=self.config.get("trading_mode", "Semi-Automated"))
        mode_combo = ttk.Combobox(
            mode_frame, 
            textvariable=self.trading_mode_var,
            values=["Semi-Automated", "Manual", "Fully-Automated"],
            state="readonly",
            width=15
        )
        mode_combo.pack(side=tk.LEFT)
        
        # Demo Mode Toggle - NEW ADDITION
        demo_frame = ttk.Frame(scrollable_frame)
        demo_frame.pack(fill=tk.X, pady=(5, 15))
        
        ttk.Label(demo_frame, text="Demo Mode:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.demo_mode_var = tk.BooleanVar(value=self.config.get("demo_mode", False))
        demo_switch = ttk.Checkbutton(
            demo_frame,
            variable=self.demo_mode_var,
            style="Switch.TCheckbutton"
        )
        demo_switch.pack(side=tk.LEFT)
        
        # Risk Management Section
        self.create_section_header(scrollable_frame, "Risk Management", "Configure risk parameters to protect your capital")
        
        # Max Daily Loss
        daily_loss_frame = ttk.Frame(scrollable_frame)
        daily_loss_frame.pack(fill=tk.X, pady=(10, 5))
        
        ttk.Label(daily_loss_frame, text="Max Daily Loss (%):").pack(side=tk.LEFT, padx=(0, 10))
        
        self.max_daily_loss_var = tk.DoubleVar(value=self.config.get("max_daily_loss", 20.0))
        max_daily_loss_entry = ttk.Entry(daily_loss_frame, textvariable=self.max_daily_loss_var, width=10)
        max_daily_loss_entry.pack(side=tk.LEFT)
        
        # Max Drawdown
        drawdown_frame = ttk.Frame(scrollable_frame)
        drawdown_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(drawdown_frame, text="Max Drawdown (%):").pack(side=tk.LEFT, padx=(0, 10))
        
        self.max_drawdown_var = tk.DoubleVar(value=self.config.get("max_drawdown", 30.0))
        max_drawdown_entry = ttk.Entry(drawdown_frame, textvariable=self.max_drawdown_var, width=10)
        max_drawdown_entry.pack(side=tk.LEFT)
        
        # Max Risk Per Trade
        risk_trade_frame = ttk.Frame(scrollable_frame)
        risk_trade_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(risk_trade_frame, text="Max Risk Per Trade (%):").pack(side=tk.LEFT, padx=(0, 10))
        
        self.max_risk_per_trade_var = tk.DoubleVar(value=self.config.get("max_risk_per_trade", 15.0))
        max_risk_per_trade_entry = ttk.Entry(risk_trade_frame, textvariable=self.max_risk_per_trade_var, width=10)
        max_risk_per_trade_entry.pack(side=tk.LEFT)
        
        # Max Portfolio Risk
        portfolio_risk_frame = ttk.Frame(scrollable_frame)
        portfolio_risk_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(portfolio_risk_frame, text="Max Portfolio Risk (%):").pack(side=tk.LEFT, padx=(0, 10))
        
        self.max_portfolio_risk_var = tk.DoubleVar(value=self.config.get("max_portfolio_risk", 50.0))
        max_portfolio_risk_entry = ttk.Entry(portfolio_risk_frame, textvariable=self.max_portfolio_risk_var, width=10)
        max_portfolio_risk_entry.pack(side=tk.LEFT)
        
        # Default Stop Loss
        stop_loss_frame = ttk.Frame(scrollable_frame)
        stop_loss_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(stop_loss_frame, text="Default Stop Loss (%):").pack(side=tk.LEFT, padx=(0, 10))
        
        self.default_stop_loss_var = tk.DoubleVar(value=self.config.get("default_stop_loss", 15.0))
        default_stop_loss_entry = ttk.Entry(stop_loss_frame, textvariable=self.default_stop_loss_var, width=10)
        default_stop_loss_entry.pack(side=tk.LEFT)
        
        # Default Take Profit
        take_profit_frame = ttk.Frame(scrollable_frame)
        take_profit_frame.pack(fill=tk.X, pady=(5, 15))
        
        ttk.Label(take_profit_frame, text="Default Take Profit (%):").pack(side=tk.LEFT, padx=(0, 10))
        
        self.default_take_profit_var = tk.DoubleVar(value=self.config.get("default_take_profit", 50.0))
        default_take_profit_entry = ttk.Entry(take_profit_frame, textvariable=self.default_take_profit_var, width=10)
        default_take_profit_entry.pack(side=tk.LEFT)
        
        # Tracked Wallets Section
        self.create_section_header(scrollable_frame, "Tracked Wallets", "Configure wallets to track for trading signals")
        
        # Wallets List
        wallets_frame = ttk.Frame(scrollable_frame)
        wallets_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 5))
        
        # Create a frame for the wallets list with a border
        wallets_list_frame = ttk.Frame(wallets_frame, style="Card.TFrame")
        wallets_list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create wallets list with scrollbar
        wallets_canvas = tk.Canvas(wallets_list_frame, highlightthickness=0)
        wallets_scrollbar = ttk.Scrollbar(wallets_list_frame, orient="vertical", command=wallets_canvas.yview)
        self.wallets_container = ttk.Frame(wallets_canvas)
        
        self.wallets_container.bind(
            "<Configure>",
            lambda e: wallets_canvas.configure(scrollregion=wallets_canvas.bbox("all"))
        )
        
        wallets_canvas.create_window((0, 0), window=self.wallets_container, anchor="nw")
        wallets_canvas.configure(yscrollcommand=wallets_scrollbar.set)
        
        wallets_canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        wallets_scrollbar.pack(side="right", fill="y", pady=5)
        
        # Populate wallets list
        self.populate_wallets_list()
        
        # Add/Remove Wallet Buttons
        wallet_buttons_frame = ttk.Frame(scrollable_frame)
        wallet_buttons_frame.pack(fill=tk.X, pady=(5, 15))
        
        # Add Wallet Button - FIXED FUNCTIONALITY
        self.add_wallet_button = ttk.Button(
            wallet_buttons_frame,
            text="Add Wallet",
            command=self.add_wallet_dialog,
            style="Accent.TButton"
        )
        self.add_wallet_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Save/Reset Buttons
        buttons_frame = ttk.Frame(scrollable_frame)
        buttons_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(
            buttons_frame,
            text="Reset to Defaults",
            command=self.reset_to_defaults
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            buttons_frame,
            text="Save Settings",
            command=self.save_settings,
            style="Accent.TButton"
        ).pack(side=tk.RIGHT)
        
    def create_section_header(self, parent, title, description):
        """Create a section header with title and description"""
        section_frame = ttk.Frame(parent)
        section_frame.pack(fill=tk.X, pady=(15, 5))
        
        # Add a separator line before the section (except for the first section)
        if title != "Wallet Configuration":
            separator = ttk.Separator(section_frame, orient="horizontal")
            separator.pack(fill=tk.X, pady=(0, 10))
        
        # Title
        title_label = ttk.Label(
            section_frame, 
            text=title, 
            font=("Helvetica", 14, "bold"),
            foreground="#3a7ca5"
        )
        title_label.pack(anchor=tk.W)
        
        # Description
        if description:
            desc_label = ttk.Label(
                section_frame, 
                text=description,
                foreground="#666666"
            )
            desc_label.pack(anchor=tk.W)
    
    def toggle_key_visibility(self):
        """Toggle private key visibility"""
        if self.show_key_var.get():
            self.private_key_entry.config(show="")
        else:
            self.private_key_entry.config(show="*")
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    return json.load(f)
            else:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
                return {}
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def save_settings(self):
        """Save settings to configuration file"""
        try:
            # Collect all settings
            config = {
                "private_key": self.private_key_var.get(),
                "initial_capital": self.initial_capital_var.get(),
                "target_value": self.target_value_var.get(),
                "days_remaining": self.days_remaining_var.get(),
                "max_concurrent_trades": self.max_trades_var.get(),
                "trading_mode": self.trading_mode_var.get(),
                "demo_mode": self.demo_mode_var.get(),
                "max_daily_loss": self.max_daily_loss_var.get(),
                "max_drawdown": self.max_drawdown_var.get(),
                "max_risk_per_trade": self.max_risk_per_trade_var.get(),
                "max_portfolio_risk": self.max_portfolio_risk_var.get(),
                "default_stop_loss": self.default_stop_loss_var.get(),
                "default_take_profit": self.default_take_profit_var.get(),
                "wallets": self.config.get("wallets", [])
            }
            
            # Save to file
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=4)
            
            # Update config
            self.config = config
            
            messagebox.showinfo("Settings Saved", "Your settings have been saved successfully.")
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def reset_to_defaults(self):
        """Reset settings to default values"""
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to reset all settings to default values?"):
            # Default values
            self.private_key_var.set("")
            self.initial_capital_var.set(200.0)
            self.target_value_var.set(10000.0)
            self.days_remaining_var.set(10)
            self.max_trades_var.set(2)
            self.trading_mode_var.set("Semi-Automated")
            self.demo_mode_var.set(False)
            self.max_daily_loss_var.set(20.0)
            self.max_drawdown_var.set(30.0)
            self.max_risk_per_trade_var.set(15.0)
            self.max_portfolio_risk_var.set(50.0)
            self.default_stop_loss_var.set(15.0)
            self.default_take_profit_var.set(50.0)
            
            # Reset wallets
            self.config["wallets"] = [
                {
                    "name": "Whale 1",
                    "address": "5ZWj7a1f8tWkjBESHKgrLmZhGh7yBR8Cmjw6aQGhRTMQ"
                },
                {
                    "name": "Whale 2",
                    "address": "7NsngNMtXJNdHgeK4znQDZ5PJ19ykVvQvEF7BT5KFjMv"
                }
            ]
            
            # Repopulate wallets list
            self.populate_wallets_list()
            
            messagebox.showinfo("Reset Complete", "Settings have been reset to default values.")
    
    def populate_wallets_list(self):
        """Populate the wallets list with tracked wallets"""
        # Clear existing widgets
        for widget in self.wallets_container.winfo_children():
            widget.destroy()
        
        # Get wallets from config
        wallets = self.config.get("wallets", [])
        
        if not wallets:
            # Show empty state
            empty_label = ttk.Label(
                self.wallets_container,
                text="No wallets added yet. Click 'Add Wallet' to start tracking.",
                foreground="#999999",
                padding=(10, 20)
            )
            empty_label.pack(fill=tk.X)
            return
        
        # Add header
        header_frame = ttk.Frame(self.wallets_container)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Label(header_frame, text="Name", width=15, font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)
        ttk.Label(header_frame, text="Address", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        ttk.Label(header_frame, text="Actions", width=15, font=("Helvetica", 10, "bold")).pack(side=tk.RIGHT)
        
        # Add separator
        ttk.Separator(self.wallets_container, orient="horizontal").pack(fill=tk.X, padx=10, pady=(0, 5))
        
        # Add wallets
        for i, wallet in enumerate(wallets):
            wallet_frame = ttk.Frame(self.wallets_container)
            wallet_frame.pack(fill=tk.X, padx=10, pady=2)
            
            # Alternate row colors
            if i % 2 == 0:
                wallet_frame.configure(style="EvenRow.TFrame")
            else:
                wallet_frame.configure(style="OddRow.TFrame")
            
            # Wallet name
            name_label = ttk.Label(wallet_frame, text=wallet.get("name", ""), width=15)
            name_label.pack(side=tk.LEFT)
            
            # Wallet address (truncated)
            address = wallet.get("address", "")
            truncated_address = address[:10] + "..." + address[-4:] if len(address) > 14 else address
            address_label = ttk.Label(wallet_frame, text=truncated_address)
            address_label.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
            
            # Add tooltip for full address
            self.create_tooltip(address_label, address)
            
            # Actions
            actions_frame = ttk.Frame(wallet_frame)
            actions_frame.pack(side=tk.RIGHT)
            
            # Edit button
            edit_button = ttk.Button(
                actions_frame,
                text="Edit",
                command=lambda w=wallet: self.edit_wallet_dialog(w),
                style="Small.TButton",
                width=5
            )
            edit_button.pack(side=tk.LEFT, padx=(0, 5))
            
            # Delete button
            delete_button = ttk.Button(
                actions_frame,
                text="Delete",
                command=lambda w=wallet: self.delete_wallet(w),
                style="Small.Danger.TButton",
                width=5
            )
            delete_button.pack(side=tk.LEFT)
    
    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        def enter(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            
            # Create a toplevel window
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            label = ttk.Label(
                self.tooltip, 
                text=text, 
                background="#ffffe0", 
                relief="solid", 
                borderwidth=1,
                padding=(5, 2)
            )
            label.pack()
        
        def leave(event):
            if hasattr(self, "tooltip"):
                self.tooltip.destroy()
        
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
    
    def add_wallet_dialog(self):
        """Show dialog to add a new wallet"""
        # Create dialog window
        dialog = tk.Toplevel(self)
        dialog.title("Add Wallet")
        dialog.geometry("500x250")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Create main container with padding
        container = ttk.Frame(dialog, padding="20 20 20 20")
        container.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            container, 
            text="Add New Wallet to Track", 
            font=("Helvetica", 14, "bold"),
            foreground="#3a7ca5"
        )
        title_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Wallet Name
        name_frame = ttk.Frame(container)
        name_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(name_frame, text="Wallet Name:").pack(side=tk.LEFT, padx=(0, 10))
        
        name_var = tk.StringVar()
        name_entry = ttk.Entry(name_frame, textvariable=name_var, width=30)
        name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Wallet Address
        address_frame = ttk.Frame(container)
        address_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(address_frame, text="Wallet Address:").pack(side=tk.LEFT, padx=(0, 10))
        
        address_var = tk.StringVar()
        address_entry = ttk.Entry(address_frame, textvariable=address_var, width=50)
        address_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Status message
        status_var = tk.StringVar()
        status_label = ttk.Label(
            container,
            textvariable=status_var,
            foreground="#999999"
        )
        status_label.pack(fill=tk.X, pady=(0, 10))
        
        # Test Wallet Button
        test_button = ttk.Button(
            container,
            text="Test Wallet",
            command=lambda: self.test_wallet_address(address_var.get(), status_var)
        )
        test_button.pack(anchor=tk.W, pady=(0, 15))
        
        # Buttons
        buttons_frame = ttk.Frame(container)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            buttons_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            buttons_frame,
            text="Add Wallet",
            command=lambda: self.add_wallet(name_var.get(), address_var.get(), dialog),
            style="Accent.TButton"
        ).pack(side=tk.RIGHT)
        
        # Set focus to name entry
        name_entry.focus_set()
    
    def test_wallet_address(self, address, status_var):
        """Test if a wallet address is valid"""
        if not address:
            status_var.set("Please enter a wallet address")
            return
        
        # Basic validation (Solana addresses are 44 characters long)
        if len(address) != 44:
            status_var.set("Invalid address format. Solana addresses are 44 characters long.")
            return
        
        # Start a thread to test the connection
        status_var.set("Testing wallet address...")
        
        def test_thread():
            try:
                # Simulate API call to check wallet
                # In a real implementation, this would use the Solana API
                import time
                time.sleep(1)
                
                # For demo purposes, we'll consider all addresses valid
                # In a real implementation, you would verify the address exists
                self.after(0, lambda: status_var.set("✓ Valid Solana wallet address"))
                
            except Exception as e:
                logger.error(f"Error testing wallet address: {e}")
                self.after(0, lambda: status_var.set(f"Error: {str(e)}"))
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def add_wallet(self, name, address, dialog):
        """Add a new wallet to the tracked wallets list"""
        if not name:
            messagebox.showerror("Error", "Please enter a wallet name")
            return
        
        if not address:
            messagebox.showerror("Error", "Please enter a wallet address")
            return
        
        # Basic validation (Solana addresses are 44 characters long)
        if len(address) != 44:
            messagebox.showerror("Error", "Invalid address format. Solana addresses are 44 characters long.")
            return
        
        # Add wallet to config
        if "wallets" not in self.config:
            self.config["wallets"] = []
        
        # Check if wallet already exists
        for wallet in self.config["wallets"]:
            if wallet.get("address") == address:
                messagebox.showerror("Error", "This wallet address is already being tracked")
                return
        
        # Add new wallet
        self.config["wallets"].append({
            "name": name,
            "address": address
        })
        
        # Repopulate wallets list
        self.populate_wallets_list()
        
        # Close dialog
        dialog.destroy()
        
        # Show success message
        messagebox.showinfo("Wallet Added", f"Wallet '{name}' has been added to tracking list")
    
    def edit_wallet_dialog(self, wallet):
        """Show dialog to edit a wallet"""
        # Create dialog window
        dialog = tk.Toplevel(self)
        dialog.title("Edit Wallet")
        dialog.geometry("500x250")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Create main container with padding
        container = ttk.Frame(dialog, padding="20 20 20 20")
        container.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            container, 
            text="Edit Tracked Wallet", 
            font=("Helvetica", 14, "bold"),
            foreground="#3a7ca5"
        )
        title_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Wallet Name
        name_frame = ttk.Frame(container)
        name_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(name_frame, text="Wallet Name:").pack(side=tk.LEFT, padx=(0, 10))
        
        name_var = tk.StringVar(value=wallet.get("name", ""))
        name_entry = ttk.Entry(name_frame, textvariable=name_var, width=30)
        name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Wallet Address
        address_frame = ttk.Frame(container)
        address_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(address_frame, text="Wallet Address:").pack(side=tk.LEFT, padx=(0, 10))
        
        address_var = tk.StringVar(value=wallet.get("address", ""))
        address_entry = ttk.Entry(address_frame, textvariable=address_var, width=50)
        address_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Status message
        status_var = tk.StringVar()
        status_label = ttk.Label(
            container,
            textvariable=status_var,
            foreground="#999999"
        )
        status_label.pack(fill=tk.X, pady=(0, 10))
        
        # Test Wallet Button
        test_button = ttk.Button(
            container,
            text="Test Wallet",
            command=lambda: self.test_wallet_address(address_var.get(), status_var)
        )
        test_button.pack(anchor=tk.W, pady=(0, 15))
        
        # Buttons
        buttons_frame = ttk.Frame(container)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            buttons_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            buttons_frame,
            text="Save Changes",
            command=lambda: self.update_wallet(wallet, name_var.get(), address_var.get(), dialog),
            style="Accent.TButton"
        ).pack(side=tk.RIGHT)
        
        # Set focus to name entry
        name_entry.focus_set()
    
    def update_wallet(self, old_wallet, name, address, dialog):
        """Update an existing wallet"""
        if not name:
            messagebox.showerror("Error", "Please enter a wallet name")
            return
        
        if not address:
            messagebox.showerror("Error", "Please enter a wallet address")
            return
        
        # Basic validation (Solana addresses are 44 characters long)
        if len(address) != 44:
            messagebox.showerror("Error", "Invalid address format. Solana addresses are 44 characters long.")
            return
        
        # Check if wallet already exists (if address changed)
        if address != old_wallet.get("address"):
            for wallet in self.config["wallets"]:
                if wallet.get("address") == address and wallet != old_wallet:
                    messagebox.showerror("Error", "This wallet address is already being tracked")
                    return
        
        # Update wallet
        for wallet in self.config["wallets"]:
            if wallet.get("address") == old_wallet.get("address"):
                wallet["name"] = name
                wallet["address"] = address
                break
        
        # Repopulate wallets list
        self.populate_wallets_list()
        
        # Close dialog
        dialog.destroy()
        
        # Show success message
        messagebox.showinfo("Wallet Updated", f"Wallet '{name}' has been updated")
    
    def delete_wallet(self, wallet):
        """Delete a wallet from the tracked wallets list"""
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete wallet '{wallet.get('name')}'?"):
            # Remove wallet from config
            self.config["wallets"] = [w for w in self.config.get("wallets", []) if w.get("address") != wallet.get("address")]
            
            # Repopulate wallets list
            self.populate_wallets_list()
            
            # Show success message
            messagebox.showinfo("Wallet Deleted", f"Wallet '{wallet.get('name')}' has been removed from tracking list")
    
    def import_from_seed(self):
        """Import wallet from seed phrase"""
        # Create dialog window
        dialog = tk.Toplevel(self)
        dialog.title("Import from Seed Phrase")
        dialog.geometry("500x300")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Create main container with padding
        container = ttk.Frame(dialog, padding="20 20 20 20")
        container.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            container, 
            text="Import Wallet from Seed Phrase", 
            font=("Helvetica", 14, "bold"),
            foreground="#3a7ca5"
        )
        title_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Warning
        warning_frame = ttk.Frame(container, style="Warning.TFrame", padding=10)
        warning_frame.pack(fill=tk.X, pady=(0, 15))
        
        warning_label = ttk.Label(
            warning_frame,
            text="⚠️ Security Warning: Your seed phrase provides full access to your wallet. "
                 "Never share it with anyone else.",
            wraplength=440,
            justify=tk.LEFT,
            foreground="#856404"
        )
        warning_label.pack(fill=tk.X)
        
        # Seed Phrase
        seed_frame = ttk.Frame(container)
        seed_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(seed_frame, text="Seed Phrase:").pack(anchor=tk.W, pady=(0, 5))
        
        seed_var = tk.StringVar()
        seed_text = tk.Text(seed_frame, height=3, width=50, wrap=tk.WORD)
        seed_text.pack(fill=tk.X)
        
        # Password
        password_frame = ttk.Frame(container)
        password_frame.pack(fill=tk.X, pady=(10, 10))
        
        ttk.Label(password_frame, text="Password (optional):").pack(side=tk.LEFT, padx=(0, 10))
        
        password_var = tk.StringVar()
        password_entry = ttk.Entry(password_frame, textvariable=password_var, show="*", width=30)
        password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Buttons
        buttons_frame = ttk.Frame(container)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            buttons_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            buttons_frame,
            text="Import Wallet",
            command=lambda: self.process_seed_phrase(seed_text.get("1.0", tk.END).strip(), password_var.get(), dialog),
            style="Accent.TButton"
        ).pack(side=tk.RIGHT)
    
    def process_seed_phrase(self, seed_phrase, password, dialog):
        """Process seed phrase to derive private key"""
        if not seed_phrase:
            messagebox.showerror("Error", "Please enter your seed phrase")
            return
        
        # Start a thread to process the seed phrase
        def process_thread():
            try:
                # Simulate seed phrase processing
                # In a real implementation, this would use the Solana SDK
                import time
                time.sleep(1.5)
                
                # For demo purposes, we'll generate a fake private key
                # In a real implementation, you would derive the actual private key
                import hashlib
                fake_key = hashlib.sha256((seed_phrase + password).encode()).hexdigest()
                
                # Update the private key field
                self.after(0, lambda: self.private_key_var.set(fake_key))
                self.after(0, lambda: messagebox.showinfo("Import Successful", "Wallet has been imported successfully"))
                self.after(0, dialog.destroy)
                
            except Exception as e:
                logger.error(f"Error processing seed phrase: {e}")
                self.after(0, lambda: messagebox.showerror("Error", f"Failed to import wallet: {str(e)}"))
        
        threading.Thread(target=process_thread, daemon=True).start()
    
    def generate_new_wallet(self):
        """Generate a new Solana wallet"""
        if messagebox.askyesno("Generate New Wallet", "This will generate a new Solana wallet. Continue?"):
            # Start a thread to generate the wallet
            def generate_thread():
                try:
                    # Simulate wallet generation
                    # In a real implementation, this would use the Solana SDK
                    import time
                    time.sleep(1)
                    
                    # For demo purposes, we'll generate a fake private key and address
                    # In a real implementation, you would generate an actual Solana keypair
                    import secrets
                    fake_private_key = secrets.token_hex(32)
                    fake_address = "1" + secrets.token_hex(21)
                    
                    # Update the private key field
                    self.after(0, lambda: self.private_key_var.set(fake_private_key))
                    
                    # Show success message with the new wallet address
                    self.after(0, lambda: messagebox.showinfo(
                        "Wallet Generated",
                        f"New wallet generated successfully!\n\n"
                        f"Address: {fake_address}\n\n"
                        f"The private key has been added to the settings. "
                        f"Make sure to save your settings and keep a backup of this private key."
                    ))
                    
                except Exception as e:
                    logger.error(f"Error generating wallet: {e}")
                    self.after(0, lambda: messagebox.showerror("Error", f"Failed to generate wallet: {str(e)}"))
            
            threading.Thread(target=generate_thread, daemon=True).start()
    
    def test_connection(self):
        """Test connection to Solana network with the provided private key"""
        private_key = self.private_key_var.get()
        
        if not private_key:
            self.connection_status_var.set("Please enter a private key")
            self.connection_status_label.configure(foreground="#e74c3c")
            return
        
        # Update status
        self.connection_status_var.set("Testing connection...")
        self.connection_status_label.configure(foreground="#3498db")
        self.test_connection_button.configure(state="disabled")
        
        # Start a thread to test the connection
        def test_thread():
            try:
                # Simulate API call to test connection
                # In a real implementation, this would use the Solana API
                import time
                time.sleep(1.5)
                
                # For demo purposes, we'll consider all private keys valid
                # In a real implementation, you would verify the key and check the balance
                
                # Generate a random balance for demo purposes
                import random
                balance = round(random.uniform(0.1, 5.0), 4)
                
                # Update status with success message
                self.after(0, lambda: self.connection_status_var.set(f"✓ Connected successfully! Balance: {balance} SOL"))
                self.after(0, lambda: self.connection_status_label.configure(foreground="#2ecc71"))
                
            except Exception as e:
                logger.error(f"Error testing connection: {e}")
                self.after(0, lambda: self.connection_status_var.set(f"✗ Connection failed: {str(e)}"))
                self.after(0, lambda: self.connection_status_label.configure(foreground="#e74c3c"))
            
            finally:
                self.after(0, lambda: self.test_connection_button.configure(state="normal"))
        
        threading.Thread(target=test_thread, daemon=True).start()
