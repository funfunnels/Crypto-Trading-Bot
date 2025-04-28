import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import asyncio
import json
import os
from datetime import datetime
import time
from typing import Dict, Any, List, Optional, Callable

# This will be imported from the actual modules in the real implementation
from src.utils.models import TradingSignal, Portfolio, RiskLevel, TradingSignalType
from src.strategy.trading_strategy import TradingStrategy
from src.risk.risk_manager import RiskManager
from src.analysis.signal_generator import SignalAggregator

class AsyncTkApp:
    """Helper class to run asyncio tasks in tkinter"""
    
    def __init__(self, root):
        self.root = root
        self.loop = asyncio.new_event_loop()
        self.tasks = []
        
    def start(self):
        """Start the asyncio event loop in a separate thread"""
        threading.Thread(target=self._start_loop, daemon=True).start()
        
    def _start_loop(self):
        """Run the asyncio event loop"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
        
    def stop(self):
        """Stop the asyncio event loop"""
        for task in self.tasks:
            task.cancel()
        self.loop.call_soon_threadsafe(self.loop.stop)
        
    def run_coroutine(self, coroutine, callback=None):
        """
        Run a coroutine in the asyncio event loop and call the callback with the result
        
        Args:
            coroutine: The coroutine to run
            callback: Optional callback function to call with the result
        """
        async def _run_and_callback():
            try:
                result = await coroutine
                if callback:
                    self.root.after(0, lambda: callback(result))
                return result
            except Exception as e:
                if callback:
                    self.root.after(0, lambda: callback(None, e))
                return None
                
        task = self.loop.create_task(_run_and_callback())
        self.tasks.append(task)
        return task
        
    def run_coroutine_periodically(self, coroutine_factory, interval, callback=None):
        """
        Run a coroutine periodically in the asyncio event loop
        
        Args:
            coroutine_factory: Function that returns the coroutine to run
            interval: Interval in seconds between runs
            callback: Optional callback function to call with the result
        """
        async def _run_periodically():
            while True:
                try:
                    result = await coroutine_factory()
                    if callback:
                        self.root.after(0, lambda: callback(result))
                except Exception as e:
                    if callback:
                        self.root.after(0, lambda: callback(None, e))
                await asyncio.sleep(interval)
                
        task = self.loop.create_task(_run_periodically())
        self.tasks.append(task)
        return task


class TradingBotUI:
    """Main UI class for the trading bot"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Solana Meme Coin Trading Bot")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Set theme
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Configure colors
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0")
        self.style.configure("TButton", background="#4a86e8", foreground="white")
        self.style.configure("Green.TButton", background="#4caf50", foreground="white")
        self.style.configure("Red.TButton", background="#f44336", foreground="white")
        self.style.configure("TNotebook", background="#f0f0f0")
        self.style.configure("TNotebook.Tab", background="#e0e0e0", padding=[10, 5])
        self.style.map("TNotebook.Tab", background=[("selected", "#4a86e8")], foreground=[("selected", "white")])
        
        # Create asyncio helper
        self.async_app = AsyncTkApp(root)
        self.async_app.start()
        
        # Create trading strategy and risk manager
        self.strategy = TradingStrategy(initial_capital=200.0, target_value=10000.0, days_remaining=10)
        self.risk_manager = RiskManager(self.strategy)
        
        # Create UI components
        self.create_menu()
        self.create_main_frame()
        
        # Start periodic updates
        self.async_app.run_coroutine_periodically(
            lambda: self.strategy.update_portfolio(),
            interval=30,  # Update every 30 seconds
            callback=self.update_portfolio_display
        )
        
        self.async_app.run_coroutine_periodically(
            lambda: self.risk_manager.get_risk_report(),
            interval=60,  # Update every 60 seconds
            callback=self.update_risk_display
        )
        
        self.async_app.run_coroutine_periodically(
            lambda: self.strategy.get_recommended_actions(),
            interval=120,  # Update every 2 minutes
            callback=self.update_signals_display
        )
        
        # Initial data load
        self.load_initial_data()
        
    def create_menu(self):
        """Create the menu bar"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load Configuration", command=self.load_config)
        file_menu.add_command(label="Save Configuration", command=self.save_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Trading menu
        trading_menu = tk.Menu(menubar, tearoff=0)
        trading_menu.add_command(label="Refresh Signals", command=self.refresh_signals)
        trading_menu.add_command(label="Update Portfolio", command=self.refresh_portfolio)
        trading_menu.add_separator()
        trading_menu.add_command(label="Add Tracked Wallet", command=self.add_wallet)
        menubar.add_cascade(label="Trading", menu=trading_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
        
    def create_main_frame(self):
        """Create the main frame with tabs"""
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Dashboard tab
        self.dashboard_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        self.create_dashboard()
        
        # Trading Signals tab
        self.signals_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.signals_frame, text="Trading Signals")
        self.create_signals_tab()
        
        # Portfolio tab
        self.portfolio_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.portfolio_frame, text="Portfolio")
        self.create_portfolio_tab()
        
        # Risk Management tab
        self.risk_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.risk_frame, text="Risk Management")
        self.create_risk_tab()
        
        # Settings tab
        self.settings_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.settings_frame, text="Settings")
        self.create_settings_tab()
        
        # Status bar
        self.status_bar = ttk.Label(self.main_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def create_dashboard(self):
        """Create the dashboard tab"""
        # Top section - Key metrics
        metrics_frame = ttk.LabelFrame(self.dashboard_frame, text="Key Metrics", padding=10)
        metrics_frame.pack(fill=tk.X, pady=5)
        
        # Create a grid for metrics
        for i in range(3):
            metrics_frame.columnconfigure(i, weight=1)
            
        # Portfolio value
        ttk.Label(metrics_frame, text="Portfolio Value:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.portfolio_value_label = ttk.Label(metrics_frame, text="$200.00")
        self.portfolio_value_label.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # Profit/Loss
        ttk.Label(metrics_frame, text="Profit/Loss:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.profit_loss_label = ttk.Label(metrics_frame, text="$0.00 (0.00%)")
        self.profit_loss_label.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # Available Capital
        ttk.Label(metrics_frame, text="Available Capital:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.available_capital_label = ttk.Label(metrics_frame, text="$200.00")
        self.available_capital_label.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # Target Progress
        ttk.Label(metrics_frame, text="Progress to $10,000:").grid(row=0, column=2, sticky=tk.W, pady=2)
        self.progress_label = ttk.Label(metrics_frame, text="2.00%")
        self.progress_label.grid(row=0, column=3, sticky=tk.W, pady=2)
        
        # Days Remaining
        ttk.Label(metrics_frame, text="Days Remaining:").grid(row=1, column=2, sticky=tk.W, pady=2)
        self.days_remaining_label = ttk.Label(metrics_frame, text="10")
        self.days_remaining_label.grid(row=1, column=3, sticky=tk.W, pady=2)
        
        # Required Daily Growth
        ttk.Label(metrics_frame, text="Required Daily Growth:").grid(row=2, column=2, sticky=tk.W, pady=2)
        self.required_growth_label = ttk.Label(metrics_frame, text="47.50%")
        self.required_growth_label.grid(row=2, column=3, sticky=tk.W, pady=2)
        
        # Middle section - Active Holdings
        holdings_frame = ttk.LabelFrame(self.dashboard_frame, text="Active Holdings", padding=10)
        holdings_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create treeview for holdings
        self.holdings_tree = ttk.Treeview(holdings_frame, columns=("token", "quantity", "value", "profit_loss", "actions"))
        self.holdings_tree.heading("#0", text="")
        self.holdings_tree.heading("token", text="Token")
        self.holdings_tree.heading("quantity", text="Quantity")
        self.holdings_tree.heading("value", text="Value")
        self.holdings_tree.heading("profit_loss", text="Profit/Loss")
        self.holdings_tree.heading("actions", text="Actions")
        
        self.holdings_tree.column("#0", width=0, stretch=tk.NO)
        self.holdings_tree.column("token", width=150)
        self.holdings_tree.column("quantity", width=150)
        self.holdings_tree.column("value", width=150)
        self.holdings_tree.column("profit_loss", width=150)
        self.holdings_tree.column("actions", width=150)
        
        self.holdings_tree.pack(fill=tk.BOTH, expand=True)
        
        # Bottom section - Recent Signals
        signals_frame = ttk.LabelFrame(self.dashboard_frame, text="Recent Trading Signals", padding=10)
        signals_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create treeview for signals
        self.signals_tree = ttk.Treeview(signals_frame, columns=("token", "signal", "confidence", "price", "actions"))
        self.signals_tree.heading("#0", text="")
        self.signals_tree.heading("token", text="Token")
        self.signals_tree.heading("signal", text="Signal")
        self.signals_tree.heading("confidence", text="Confidence")
        self.signals_tree.heading("price", text="Price")
        self.signals_tree.heading("actions", text="Actions")
        
        self.signals_tree.column("#0", width=0, stretch=tk.NO)
        self.signals_tree.column("token", width=150)
        self.signals_tree.column("signal", width=100)
        self.signals_tree.column("confidence", width=100)
        self.signals_tree.column("price", width=100)
        self.signals_tree.column("actions", width=200)
        
        self.signals_tree.pack(fill=tk.BOTH, expand=True)
        
        # Action buttons
        actions_frame = ttk.Frame(self.dashboard_frame, padding=10)
        actions_frame.pack(fill=tk.X, pady=5)
        
        refresh_button = ttk.Button(actions_frame, text="Refresh Dashboard", command=self.refresh_dashboard)
        refresh_button.pack(side=tk.LEFT, padx=5)
        
        self.auto_refresh_var = tk.BooleanVar(value=True)
        auto_refresh_check = ttk.Checkbutton(actions_frame, text="Auto-refresh", variable=self.auto_refresh_var)
        auto_refresh_check.pack(side=tk.LEFT, padx=5)
        
    def create_signals_tab(self):
        """Create the trading signals tab"""
        # Top section - Controls
        controls_frame = ttk.Frame(self.signals_frame, padding=10)
        controls_frame.pack(fill=tk.X, pady=5)
        
        refresh_button = ttk.Button(controls_frame, text="Refresh Signals", command=self.refresh_signals)
        refresh_button.pack(side=tk.LEFT, padx=5)
        
        # Filter options
        ttk.Label(controls_frame, text="Filter:").pack(side=tk.LEFT, padx=5)
        
        self.signal_filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(controls_frame, textvariable=self.signal_filter_var, 
                                    values=["All", "Buy", "Sell", "High Confidence"])
        filter_combo.pack(side=tk.LEFT, padx=5)
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_signals())
        
        # Main section - Signals list
        signals_frame = ttk.Frame(self.signals_frame, padding=10)
        signals_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create treeview for signals
        self.detailed_signals_tree = ttk.Treeview(signals_frame, 
                                                 columns=("token", "signal", "confidence", "entry", "target", "stop", "risk", "actions"))
        self.detailed_signals_tree.heading("#0", text="")
        self.detailed_signals_tree.heading("token", text="Token")
        self.detailed_signals_tree.heading("signal", text="Signal")
        self.detailed_signals_tree.heading("confidence", text="Confidence")
        self.detailed_signals_tree.heading("entry", text="Entry Price")
        self.detailed_signals_tree.heading("target", text="Target Price")
        self.detailed_signals_tree.heading("stop", text="Stop Loss")
        self.detailed_signals_tree.heading("risk", text="Risk Level")
        self.detailed_signals_tree.heading("actions", text="Actions")
        
        self.detailed_signals_tree.column("#0", width=0, stretch=tk.NO)
        self.detailed_signals_tree.column("token", width=150)
        self.detailed_signals_tree.column("signal", width=80)
        self.detailed_signals_tree.column("confidence", width=100)
        self.detailed_signals_tree.column("entry", width=100)
        self.detailed_signals_tree.column("target", width=100)
        self.detailed_signals_tree.column("stop", width=100)
        self.detailed_signals_tree.column("risk", width=100)
        self.detailed_signals_tree.column("actions", width=150)
        
        self.detailed_signals_tree.pack(fill=tk.BOTH, expand=True)
        self.detailed_signals_tree.bind("<Double-1>", self.show_signal_details)
        
        # Bottom section - Signal details
        details_frame = ttk.LabelFrame(self.signals_frame, text="Signal Details", padding=10)
        details_frame.pack(fill=tk.X, pady=5)
        
        self.signal_details_text = scrolledtext.ScrolledText(details_frame, height=8)
        self.signal_details_text.pack(fill=tk.BOTH, expand=True)
        self.signal_details_text.config(state=tk.DISABLED)
        
    def create_portfolio_tab(self):
        """Create the portfolio tab"""
        # Top section - Summary
        summary_frame = ttk.LabelFrame(self.portfolio_frame, text="Portfolio Summary", padding=10)
        summary_frame.pack(fill=tk.X, pady=5)
        
        # Create a grid for summary
        for i in range(3):
            summary_frame.columnconfigure(i, weight=1)
            
        # Initial Capital
        ttk.Label(summary_frame, text="Initial Capital:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.initial_capital_label = ttk.Label(summary_frame, text="$200.00")
        self.initial_capital_label.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # Current Value
        ttk.Label(summary_frame, text="Current Value:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.current_value_label = ttk.Label(summary_frame, text="$200.00")
        self.current_value_label.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # Profit/Loss
        ttk.Label(summary_frame, text="Total Profit/Loss:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.total_pl_label = ttk.Label(summary_frame, text="$0.00 (0.00%)")
        self.total_pl_label.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # Available Capital
        ttk.Label(summary_frame, text="Available Capital:").grid(row=0, column=2, sticky=tk.W, pady=2)
        self.avail_capital_label = ttk.Label(summary_frame, text="$200.00")
        self.avail_capital_label.grid(row=0, column=3, sticky=tk.W, pady=2)
        
        # Holdings Value
        ttk.Label(summary_frame, text="Holdings Value:").grid(row=1, column=2, sticky=tk.W, pady=2)
        self.holdings_value_label = ttk.Label(summary_frame, text="$0.00")
        self.holdings_value_label.grid(row=1, column=3, sticky=tk.W, pady=2)
        
        # Last Updated
        ttk.Label(summary_frame, text="Last Updated:").grid(row=2, column=2, sticky=tk.W, pady=2)
        self.last_updated_label = ttk.Label(summary_frame, text="Never")
        self.last_updated_label.grid(row=2, column=3, sticky=tk.W, pady=2)
        
        # Middle section - Holdings
        holdings_frame = ttk.LabelFrame(self.portfolio_frame, text="Current Holdings", padding=10)
        holdings_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create treeview for holdings
        self.portfolio_holdings_tree = ttk.Treeview(holdings_frame, 
                                                  columns=("token", "quantity", "avg_price", "current_price", "value", "pl", "pl_pct", "actions"))
        self.portfolio_holdings_tree.heading("#0", text="")
        self.portfolio_holdings_tree.heading("token", text="Token")
        self.portfolio_holdings_tree.heading("quantity", text="Quantity")
        self.portfolio_holdings_tree.heading("avg_price", text="Avg Price")
        self.portfolio_holdings_tree.heading("current_price", text="Current Price")
        self.portfolio_holdings_tree.heading("value", text="Value")
        self.portfolio_holdings_tree.heading("pl", text="Profit/Loss")
        self.portfolio_holdings_tree.heading("pl_pct", text="P/L %")
        self.portfolio_holdings_tree.heading("actions", text="Actions")
        
        self.portfolio_holdings_tree.column("#0", width=0, stretch=tk.NO)
        self.portfolio_holdings_tree.column("token", width=120)
        self.portfolio_holdings_tree.column("quantity", width=100)
        self.portfolio_holdings_tree.column("avg_price", width=100)
        self.portfolio_holdings_tree.column("current_price", width=100)
        self.portfolio_holdings_tree.column("value", width=100)
        self.portfolio_holdings_tree.column("pl", width=100)
        self.portfolio_holdings_tree.column("pl_pct", width=80)
        self.portfolio_holdings_tree.column("actions", width=150)
        
        self.portfolio_holdings_tree.pack(fill=tk.BOTH, expand=True)
        
        # Bottom section - Trade History
        history_frame = ttk.LabelFrame(self.portfolio_frame, text="Trade History", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create treeview for trade history
        self.trade_history_tree = ttk.Treeview(history_frame, 
                                             columns=("date", "token", "type", "quantity", "price", "amount", "status"))
        self.trade_history_tree.heading("#0", text="")
        self.trade_history_tree.heading("date", text="Date/Time")
        self.trade_history_tree.heading("token", text="Token")
        self.trade_history_tree.heading("type", text="Type")
        self.trade_history_tree.heading("quantity", text="Quantity")
        self.trade_history_tree.heading("price", text="Price")
        self.trade_history_tree.heading("amount", text="Amount")
        self.trade_history_tree.heading("status", text="Status")
        
        self.trade_history_tree.column("#0", width=0, stretch=tk.NO)
        self.trade_history_tree.column("date", width=150)
        self.trade_history_tree.column("token", width=120)
        self.trade_history_tree.column("type", width=80)
        self.trade_history_tree.column("quantity", width=100)
        self.trade_history_tree.column("price", width=100)
        self.trade_history_tree.column("amount", width=100)
        self.trade_history_tree.column("status", width=100)
        
        self.trade_history_tree.pack(fill=tk.BOTH, expand=True)
        
        # Action buttons
        actions_frame = ttk.Frame(self.portfolio_frame, padding=10)
        actions_frame.pack(fill=tk.X, pady=5)
        
        refresh_button = ttk.Button(actions_frame, text="Refresh Portfolio", command=self.refresh_portfolio)
        refresh_button.pack(side=tk.LEFT, padx=5)
        
        export_button = ttk.Button(actions_frame, text="Export Trade History", command=self.export_trade_history)
        export_button.pack(side=tk.LEFT, padx=5)
        
    def create_risk_tab(self):
        """Create the risk management tab"""
        # Top section - Risk Metrics
        metrics_frame = ttk.LabelFrame(self.risk_frame, text="Risk Metrics", padding=10)
        metrics_frame.pack(fill=tk.X, pady=5)
        
        # Create a grid for metrics
        for i in range(3):
            metrics_frame.columnconfigure(i, weight=1)
            
        # Daily Drawdown
        ttk.Label(metrics_frame, text="Daily Drawdown:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.daily_drawdown_label = ttk.Label(metrics_frame, text="0.00%")
        self.daily_drawdown_label.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # Max Drawdown
        ttk.Label(metrics_frame, text="Max Drawdown:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.max_drawdown_label = ttk.Label(metrics_frame, text="0.00%")
        self.max_drawdown_label.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # Daily P&L
        ttk.Label(metrics_frame, text="Daily P&L:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.daily_pl_label = ttk.Label(metrics_frame, text="$0.00 (0.00%)")
        self.daily_pl_label.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # Portfolio Risk
        ttk.Label(metrics_frame, text="Portfolio Risk:").grid(row=0, column=2, sticky=tk.W, pady=2)
        self.portfolio_risk_label = ttk.Label(metrics_frame, text="0.00%")
        self.portfolio_risk_label.grid(row=0, column=3, sticky=tk.W, pady=2)
        
        # Required Growth
        ttk.Label(metrics_frame, text="Required Daily Growth:").grid(row=1, column=2, sticky=tk.W, pady=2)
        self.req_growth_label = ttk.Label(metrics_frame, text="47.50%")
        self.req_growth_label.grid(row=1, column=3, sticky=tk.W, pady=2)
        
        # Risk Budget
        ttk.Label(metrics_frame, text="Risk Budget:").grid(row=2, column=2, sticky=tk.W, pady=2)
        self.risk_budget_label = ttk.Label(metrics_frame, text="15.00%")
        self.risk_budget_label.grid(row=2, column=3, sticky=tk.W, pady=2)
        
        # Middle section - Risk Status
        status_frame = ttk.LabelFrame(self.risk_frame, text="Risk Status", padding=10)
        status_frame.pack(fill=tk.X, pady=5)
        
        # Create a grid for status
        for i in range(2):
            status_frame.columnconfigure(i, weight=1)
            
        # Daily Loss Limit
        ttk.Label(status_frame, text="Daily Loss Limit:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.daily_loss_status_label = ttk.Label(status_frame, text="OK")
        self.daily_loss_status_label.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # Drawdown Limit
        ttk.Label(status_frame, text="Drawdown Limit:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.drawdown_status_label = ttk.Label(status_frame, text="OK")
        self.drawdown_status_label.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # Portfolio Risk Status
        ttk.Label(status_frame, text="Portfolio Risk:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.risk_status_label = ttk.Label(status_frame, text="OK")
        self.risk_status_label.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # Position Size Adjustment
        ttk.Label(status_frame, text="Position Size Adjustment:").grid(row=0, column=2, sticky=tk.W, pady=2)
        self.position_adjustment_label = ttk.Label(status_frame, text="NORMAL")
        self.position_adjustment_label.grid(row=0, column=3, sticky=tk.W, pady=2)
        
        # Suggested Max Position
        ttk.Label(status_frame, text="Suggested Max Position:").grid(row=1, column=2, sticky=tk.W, pady=2)
        self.max_position_label = ttk.Label(status_frame, text="$30.00")
        self.max_position_label.grid(row=1, column=3, sticky=tk.W, pady=2)
        
        # Performance Metrics
        ttk.Label(status_frame, text="Win Rate:").grid(row=2, column=2, sticky=tk.W, pady=2)
        self.win_rate_label = ttk.Label(status_frame, text="0.00%")
        self.win_rate_label.grid(row=2, column=3, sticky=tk.W, pady=2)
        
        # Bottom section - Risk Settings
        settings_frame = ttk.LabelFrame(self.risk_frame, text="Risk Settings", padding=10)
        settings_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create a grid for settings
        for i in range(2):
            settings_frame.columnconfigure(i, weight=1)
            
        # Max Daily Loss
        ttk.Label(settings_frame, text="Max Daily Loss:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.max_daily_loss_var = tk.StringVar(value="20.0")
        max_daily_loss_entry = ttk.Entry(settings_frame, textvariable=self.max_daily_loss_var, width=10)
        max_daily_loss_entry.grid(row=0, column=1, sticky=tk.W, pady=2)
        ttk.Label(settings_frame, text="%").grid(row=0, column=2, sticky=tk.W, pady=2)
        
        # Max Drawdown
        ttk.Label(settings_frame, text="Max Drawdown:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.max_drawdown_var = tk.StringVar(value="30.0")
        max_drawdown_entry = ttk.Entry(settings_frame, textvariable=self.max_drawdown_var, width=10)
        max_drawdown_entry.grid(row=1, column=1, sticky=tk.W, pady=2)
        ttk.Label(settings_frame, text="%").grid(row=1, column=2, sticky=tk.W, pady=2)
        
        # Max Risk Per Trade
        ttk.Label(settings_frame, text="Max Risk Per Trade:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.max_risk_per_trade_var = tk.StringVar(value="15.0")
        max_risk_entry = ttk.Entry(settings_frame, textvariable=self.max_risk_per_trade_var, width=10)
        max_risk_entry.grid(row=2, column=1, sticky=tk.W, pady=2)
        ttk.Label(settings_frame, text="%").grid(row=2, column=2, sticky=tk.W, pady=2)
        
        # Max Portfolio Risk
        ttk.Label(settings_frame, text="Max Portfolio Risk:").grid(row=0, column=3, sticky=tk.W, pady=2)
        self.max_portfolio_risk_var = tk.StringVar(value="50.0")
        max_portfolio_risk_entry = ttk.Entry(settings_frame, textvariable=self.max_portfolio_risk_var, width=10)
        max_portfolio_risk_entry.grid(row=0, column=4, sticky=tk.W, pady=2)
        ttk.Label(settings_frame, text="%").grid(row=0, column=5, sticky=tk.W, pady=2)
        
        # Default Stop Loss
        ttk.Label(settings_frame, text="Default Stop Loss:").grid(row=1, column=3, sticky=tk.W, pady=2)
        self.default_stop_loss_var = tk.StringVar(value="15.0")
        default_stop_loss_entry = ttk.Entry(settings_frame, textvariable=self.default_stop_loss_var, width=10)
        default_stop_loss_entry.grid(row=1, column=4, sticky=tk.W, pady=2)
        ttk.Label(settings_frame, text="%").grid(row=1, column=5, sticky=tk.W, pady=2)
        
        # Default Take Profit
        ttk.Label(settings_frame, text="Default Take Profit:").grid(row=2, column=3, sticky=tk.W, pady=2)
        self.default_take_profit_var = tk.StringVar(value="50.0")
        default_take_profit_entry = ttk.Entry(settings_frame, textvariable=self.default_take_profit_var, width=10)
        default_take_profit_entry.grid(row=2, column=4, sticky=tk.W, pady=2)
        ttk.Label(settings_frame, text="%").grid(row=2, column=5, sticky=tk.W, pady=2)
        
        # Action buttons
        actions_frame = ttk.Frame(self.risk_frame, padding=10)
        actions_frame.pack(fill=tk.X, pady=5)
        
        save_button = ttk.Button(actions_frame, text="Save Risk Settings", command=self.save_risk_settings)
        save_button.pack(side=tk.LEFT, padx=5)
        
        refresh_button = ttk.Button(actions_frame, text="Refresh Risk Metrics", command=self.refresh_risk)
        refresh_button.pack(side=tk.LEFT, padx=5)
        
    def create_settings_tab(self):
        """Create the settings tab"""
        # API Settings
        api_frame = ttk.LabelFrame(self.settings_frame, text="API Settings", padding=10)
        api_frame.pack(fill=tk.X, pady=5)
        
        # Solana Private Key
        ttk.Label(api_frame, text="Solana Private Key:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.private_key_var = tk.StringVar()
        private_key_entry = ttk.Entry(api_frame, textvariable=self.private_key_var, width=50, show="*")
        private_key_entry.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        show_key_var = tk.BooleanVar(value=False)
        show_key_check = ttk.Checkbutton(api_frame, text="Show", variable=show_key_var, 
                                         command=lambda: private_key_entry.config(show="" if show_key_var.get() else "*"))
        show_key_check.grid(row=0, column=2, sticky=tk.W, pady=2)
        
        # Trading Settings
        trading_frame = ttk.LabelFrame(self.settings_frame, text="Trading Settings", padding=10)
        trading_frame.pack(fill=tk.X, pady=5)
        
        # Initial Capital
        ttk.Label(trading_frame, text="Initial Capital:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.initial_capital_var = tk.StringVar(value="200.0")
        ttk.Entry(trading_frame, textvariable=self.initial_capital_var, width=10).grid(row=0, column=1, sticky=tk.W, pady=2)
        ttk.Label(trading_frame, text="USD").grid(row=0, column=2, sticky=tk.W, pady=2)
        
        # Target Value
        ttk.Label(trading_frame, text="Target Value:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.target_value_var = tk.StringVar(value="10000.0")
        ttk.Entry(trading_frame, textvariable=self.target_value_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=2)
        ttk.Label(trading_frame, text="USD").grid(row=1, column=2, sticky=tk.W, pady=2)
        
        # Days Remaining
        ttk.Label(trading_frame, text="Days Remaining:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.days_remaining_var = tk.StringVar(value="10")
        ttk.Entry(trading_frame, textvariable=self.days_remaining_var, width=10).grid(row=2, column=1, sticky=tk.W, pady=2)
        ttk.Label(trading_frame, text="days").grid(row=2, column=2, sticky=tk.W, pady=2)
        
        # Max Concurrent Trades
        ttk.Label(trading_frame, text="Max Concurrent Trades:").grid(row=0, column=3, sticky=tk.W, pady=2)
        self.max_trades_var = tk.StringVar(value="2")
        ttk.Entry(trading_frame, textvariable=self.max_trades_var, width=10).grid(row=0, column=4, sticky=tk.W, pady=2)
        
        # Trading Mode
        ttk.Label(trading_frame, text="Trading Mode:").grid(row=1, column=3, sticky=tk.W, pady=2)
        self.trading_mode_var = tk.StringVar(value="Semi-Automated")
        ttk.Combobox(trading_frame, textvariable=self.trading_mode_var, 
                    values=["Semi-Automated", "Manual"], width=15).grid(row=1, column=4, sticky=tk.W, pady=2)
        
        # Wallet Tracking
        wallet_frame = ttk.LabelFrame(self.settings_frame, text="Wallet Tracking", padding=10)
        wallet_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create treeview for wallets
        self.wallets_tree = ttk.Treeview(wallet_frame, columns=("name", "address", "performance", "actions"))
        self.wallets_tree.heading("#0", text="")
        self.wallets_tree.heading("name", text="Name")
        self.wallets_tree.heading("address", text="Address")
        self.wallets_tree.heading("performance", text="Performance")
        self.wallets_tree.heading("actions", text="Actions")
        
        self.wallets_tree.column("#0", width=0, stretch=tk.NO)
        self.wallets_tree.column("name", width=150)
        self.wallets_tree.column("address", width=300)
        self.wallets_tree.column("performance", width=100)
        self.wallets_tree.column("actions", width=150)
        
        self.wallets_tree.pack(fill=tk.BOTH, expand=True)
        
        # Add wallet controls
        add_wallet_frame = ttk.Frame(wallet_frame, padding=5)
        add_wallet_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(add_wallet_frame, text="Name:").pack(side=tk.LEFT, padx=2)
        self.wallet_name_var = tk.StringVar()
        ttk.Entry(add_wallet_frame, textvariable=self.wallet_name_var, width=15).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(add_wallet_frame, text="Address:").pack(side=tk.LEFT, padx=2)
        self.wallet_address_var = tk.StringVar()
        ttk.Entry(add_wallet_frame, textvariable=self.wallet_address_var, width=40).pack(side=tk.LEFT, padx=2)
        
        add_wallet_button = ttk.Button(add_wallet_frame, text="Add Wallet", command=self.add_wallet)
        add_wallet_button.pack(side=tk.LEFT, padx=5)
        
        # Action buttons
        actions_frame = ttk.Frame(self.settings_frame, padding=10)
        actions_frame.pack(fill=tk.X, pady=5)
        
        save_button = ttk.Button(actions_frame, text="Save Settings", command=self.save_settings)
        save_button.pack(side=tk.LEFT, padx=5)
        
        reset_button = ttk.Button(actions_frame, text="Reset to Defaults", command=self.reset_settings)
        reset_button.pack(side=tk.LEFT, padx=5)
        
    def load_initial_data(self):
        """Load initial data for the UI"""
        # Set status
        self.status_bar.config(text="Loading initial data...")
        
        # Load portfolio data
        self.async_app.run_coroutine(
            self.strategy.update_portfolio(),
            callback=self.update_portfolio_display
        )
        
        # Load risk data
        self.async_app.run_coroutine(
            self.risk_manager.get_risk_report(),
            callback=self.update_risk_display
        )
        
        # Load signals data
        self.async_app.run_coroutine(
            self.strategy.get_recommended_actions(),
            callback=self.update_signals_display
        )
        
        # Add sample wallets
        self.async_app.run_coroutine(
            self.strategy.add_tracked_wallet("5ZWj7a1f8tWkjBESHKgrLmZhGh7yBR8Cmjw6aQGhRTMQ", "Whale 1")
        )
        
        self.async_app.run_coroutine(
            self.strategy.add_tracked_wallet("7NsngNMtXJNdHgeK4znQDZ5PJ19ykVvQvEF7BT5KFjMv", "Whale 2")
        )
        
        # Update status
        self.status_bar.config(text="Ready")
        
    def update_portfolio_display(self, portfolio, error=None):
        """Update the portfolio display with new data"""
        if error:
            messagebox.showerror("Error", f"Failed to update portfolio: {error}")
            return
            
        if not portfolio:
            return
            
        # Update dashboard labels
        self.portfolio_value_label.config(text=f"${portfolio.total_value_usd:.2f}")
        self.profit_loss_label.config(text=f"${portfolio.profit_loss:.2f} ({portfolio.profit_loss_percentage:.2f}%)")
        self.available_capital_label.config(text=f"${portfolio.available_capital:.2f}")
        
        progress = (portfolio.total_value_usd / self.strategy.target_value) * 100
        self.progress_label.config(text=f"{progress:.2f}%")
        self.days_remaining_label.config(text=f"{self.strategy.days_remaining}")
        
        # Calculate required daily growth
        if self.strategy.days_remaining > 0 and portfolio.total_value_usd > 0:
            required_growth = ((self.strategy.target_value / portfolio.total_value_usd) ** (1 / self.strategy.days_remaining) - 1) * 100
        else:
            required_growth = 0
        self.required_growth_label.config(text=f"{required_growth:.2f}%")
        
        # Update portfolio tab labels
        self.initial_capital_label.config(text=f"${portfolio.initial_capital:.2f}")
        self.current_value_label.config(text=f"${portfolio.total_value_usd:.2f}")
        self.total_pl_label.config(text=f"${portfolio.profit_loss:.2f} ({portfolio.profit_loss_percentage:.2f}%)")
        self.avail_capital_label.config(text=f"${portfolio.available_capital:.2f}")
        
        holdings_value = portfolio.total_value_usd - portfolio.available_capital
        self.holdings_value_label.config(text=f"${holdings_value:.2f}")
        self.last_updated_label.config(text=f"{portfolio.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Update holdings treeview
        for item in self.holdings_tree.get_children():
            self.holdings_tree.delete(item)
            
        for item in self.portfolio_holdings_tree.get_children():
            self.portfolio_holdings_tree.delete(item)
            
        for holding in portfolio.holdings:
            # Add to dashboard holdings
            self.holdings_tree.insert("", "end", values=(
                f"{holding['token_symbol']} ({holding['token_name']})",
                f"{holding['quantity']:.8f}",
                f"${holding['current_value']:.2f}",
                f"${holding['profit_loss']:.2f} ({holding['profit_loss_percentage']:.2f}%)",
                "Sell"
            ))
            
            # Add to portfolio holdings
            self.portfolio_holdings_tree.insert("", "end", values=(
                f"{holding['token_symbol']} ({holding['token_name']})",
                f"{holding['quantity']:.8f}",
                f"${holding['average_price']:.8f}",
                f"${holding['current_price']:.8f}",
                f"${holding['current_value']:.2f}",
                f"${holding['profit_loss']:.2f}",
                f"{holding['profit_loss_percentage']:.2f}%",
                "Sell"
            ))
            
        # Update trade history treeview
        for item in self.trade_history_tree.get_children():
            self.trade_history_tree.delete(item)
            
        for trade in portfolio.trade_history:
            self.trade_history_tree.insert("", 0, values=(
                trade.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                f"{trade.token.symbol}",
                trade.trade_type.value,
                f"{trade.quantity:.8f}",
                f"${trade.price:.8f}",
                f"${trade.amount_usd:.2f}",
                trade.status
            ))
            
        # Update status
        self.status_bar.config(text=f"Portfolio updated at {datetime.now().strftime('%H:%M:%S')}")
        
    def update_risk_display(self, report, error=None):
        """Update the risk display with new data"""
        if error:
            messagebox.showerror("Error", f"Failed to update risk metrics: {error}")
            return
            
        if not report:
            return
            
        # Update risk metrics labels
        self.daily_drawdown_label.config(text=f"{report['risk_metrics']['daily_drawdown']:.2f}%")
        self.max_drawdown_label.config(text=f"{report['risk_metrics']['max_drawdown']:.2f}%")
        self.daily_pl_label.config(text=f"${report['risk_metrics']['daily_pl']:.2f} ({report['risk_metrics']['daily_pl_percentage']:.2f}%)")
        self.portfolio_risk_label.config(text=f"{report['risk_metrics']['portfolio_risk_percentage']:.2f}%")
        self.req_growth_label.config(text=f"{report['risk_metrics']['required_daily_growth']:.2f}%")
        self.risk_budget_label.config(text=f"{report['risk_metrics']['risk_budget']:.2f}%")
        
        # Update risk status labels
        self.daily_loss_status_label.config(text=report['risk_status']['daily_loss_limit_status'])
        self.drawdown_status_label.config(text=report['risk_status']['drawdown_limit_status'])
        self.risk_status_label.config(text=report['risk_status']['portfolio_risk_status'])
        
        # Color code status labels
        for label, status in [
            (self.daily_loss_status_label, report['risk_status']['daily_loss_limit_status']),
            (self.drawdown_status_label, report['risk_status']['drawdown_limit_status']),
            (self.risk_status_label, report['risk_status']['portfolio_risk_status'])
        ]:
            if status == "OK":
                label.config(foreground="green")
            else:
                label.config(foreground="red")
                
        # Update recommendations
        self.position_adjustment_label.config(text=report['recommendations']['position_size_adjustment'])
        self.max_position_label.config(text=f"${report['recommendations']['suggested_max_position']:.2f}")
        self.win_rate_label.config(text=f"{report['performance_metrics']['win_rate']:.2f}%")
        
        # Color code position adjustment
        if report['recommendations']['position_size_adjustment'] == "REDUCE":
            self.position_adjustment_label.config(foreground="red")
        elif report['recommendations']['position_size_adjustment'] == "INCREASE":
            self.position_adjustment_label.config(foreground="green")
        else:
            self.position_adjustment_label.config(foreground="black")
            
        # Update status
        self.status_bar.config(text=f"Risk metrics updated at {datetime.now().strftime('%H:%M:%S')}")
        
    def update_signals_display(self, recommendations, error=None):
        """Update the signals display with new data"""
        if error:
            messagebox.showerror("Error", f"Failed to update signals: {error}")
            return
            
        if not recommendations:
            return
            
        # Update signals treeview
        for item in self.signals_tree.get_children():
            self.signals_tree.delete(item)
            
        for item in self.detailed_signals_tree.get_children():
            self.detailed_signals_tree.delete(item)
            
        # Get buy signals
        buy_signals = recommendations.get("buy_signals", [])
        
        for signal in buy_signals:
            # Add to dashboard signals
            self.signals_tree.insert("", "end", values=(
                f"{signal.token.symbol} ({signal.token.name})",
                signal.signal_type.value,
                f"{signal.confidence:.2f}",
                f"${signal.entry_price:.8f}",
                "Buy"
            ))
            
            # Add to detailed signals
            self.detailed_signals_tree.insert("", "end", values=(
                f"{signal.token.symbol} ({signal.token.name})",
                signal.signal_type.value,
                f"{signal.confidence:.2f}",
                f"${signal.entry_price:.8f}",
                f"${signal.target_price:.8f}",
                f"${signal.stop_loss:.8f}",
                signal.risk_level.value,
                "Buy"
            ))
            
        # Get sell recommendations
        sell_recommendations = recommendations.get("sell_recommendations", [])
        
        for holding, reason in sell_recommendations:
            # Add to detailed signals
            self.detailed_signals_tree.insert("", "end", values=(
                f"{holding['token_symbol']} ({holding['token_name']})",
                "SELL",
                "0.90",
                f"${holding['average_price']:.8f}",
                f"${holding['current_price']:.8f}",
                f"${holding['average_price'] * 0.85:.8f}",
                "MEDIUM",
                "Sell"
            ))
            
        # Update status
        self.status_bar.config(text=f"Signals updated at {datetime.now().strftime('%H:%M:%S')}")
        
    def refresh_dashboard(self):
        """Refresh all dashboard data"""
        self.status_bar.config(text="Refreshing dashboard...")
        
        # Refresh portfolio
        self.async_app.run_coroutine(
            self.strategy.update_portfolio(),
            callback=self.update_portfolio_display
        )
        
        # Refresh signals
        self.async_app.run_coroutine(
            self.strategy.get_recommended_actions(),
            callback=self.update_signals_display
        )
        
        self.status_bar.config(text=f"Dashboard refreshed at {datetime.now().strftime('%H:%M:%S')}")
        
    def refresh_signals(self):
        """Refresh trading signals"""
        self.status_bar.config(text="Refreshing trading signals...")
        
        self.async_app.run_coroutine(
            self.strategy.get_recommended_actions(),
            callback=self.update_signals_display
        )
        
    def refresh_portfolio(self):
        """Refresh portfolio data"""
        self.status_bar.config(text="Refreshing portfolio...")
        
        self.async_app.run_coroutine(
            self.strategy.update_portfolio(),
            callback=self.update_portfolio_display
        )
        
    def refresh_risk(self):
        """Refresh risk metrics"""
        self.status_bar.config(text="Refreshing risk metrics...")
        
        self.async_app.run_coroutine(
            self.risk_manager.get_risk_report(),
            callback=self.update_risk_display
        )
        
    def show_signal_details(self, event):
        """Show details for a selected signal"""
        # Get selected item
        selection = self.detailed_signals_tree.selection()
        if not selection:
            return
            
        # Get values
        values = self.detailed_signals_tree.item(selection, "values")
        
        # Format details
        details = f"Token: {values[0]}\n"
        details += f"Signal Type: {values[1]}\n"
        details += f"Confidence: {values[2]}\n"
        details += f"Entry Price: {values[3]}\n"
        details += f"Target Price: {values[4]}\n"
        details += f"Stop Loss: {values[5]}\n"
        details += f"Risk Level: {values[6]}\n\n"
        
        # Add reasoning (simulated)
        if values[1] == "BUY":
            details += "Reasoning: This token shows strong momentum with increasing volume and positive price action. "
            details += "Recent wallet tracking indicates accumulation by successful traders. "
            details += "Technical indicators suggest potential for significant upside in the short term."
        else:
            details += "Reasoning: Take profit target has been reached. "
            details += "Consider securing profits as the token has shown signs of slowing momentum. "
            details += "Risk/reward ratio no longer favorable at current price levels."
            
        # Update details text
        self.signal_details_text.config(state=tk.NORMAL)
        self.signal_details_text.delete(1.0, tk.END)
        self.signal_details_text.insert(tk.END, details)
        self.signal_details_text.config(state=tk.DISABLED)
        
    def add_wallet(self):
        """Add a wallet to track"""
        name = self.wallet_name_var.get()
        address = self.wallet_address_var.get()
        
        if not address:
            messagebox.showerror("Error", "Wallet address is required")
            return
            
        if not name:
            name = f"Wallet-{len(self.wallets_tree.get_children()) + 1}"
            
        # Add wallet to strategy
        self.async_app.run_coroutine(
            self.strategy.add_tracked_wallet(address, name),
            callback=lambda result, error=None: self.wallet_added(result, error, name, address)
        )
        
    def wallet_added(self, result, error, name, address):
        """Callback when wallet is added"""
        if error:
            messagebox.showerror("Error", f"Failed to add wallet: {error}")
            return
            
        # Add to wallets treeview
        self.wallets_tree.insert("", "end", values=(
            name,
            address,
            "Pending",
            "Remove"
        ))
        
        # Clear entry fields
        self.wallet_name_var.set("")
        self.wallet_address_var.set("")
        
        # Update status
        self.status_bar.config(text=f"Added wallet {name} at {datetime.now().strftime('%H:%M:%S')}")
        
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists("config/config.json"):
                with open("config/config.json", "r") as f:
                    config = json.load(f)
                    
                # Update settings
                self.private_key_var.set(config.get("private_key", ""))
                self.initial_capital_var.set(str(config.get("initial_capital", 200.0)))
                self.target_value_var.set(str(config.get("target_value", 10000.0)))
                self.days_remaining_var.set(str(config.get("days_remaining", 10)))
                self.max_trades_var.set(str(config.get("max_concurrent_trades", 2)))
                self.trading_mode_var.set(config.get("trading_mode", "Semi-Automated"))
                
                # Update risk settings
                self.max_daily_loss_var.set(str(config.get("max_daily_loss", 20.0)))
                self.max_drawdown_var.set(str(config.get("max_drawdown", 30.0)))
                self.max_risk_per_trade_var.set(str(config.get("max_risk_per_trade", 15.0)))
                self.max_portfolio_risk_var.set(str(config.get("max_portfolio_risk", 50.0)))
                self.default_stop_loss_var.set(str(config.get("default_stop_loss", 15.0)))
                self.default_take_profit_var.set(str(config.get("default_take_profit", 50.0)))
                
                # Update wallets
                for item in self.wallets_tree.get_children():
                    self.wallets_tree.delete(item)
                    
                for wallet in config.get("wallets", []):
                    self.wallets_tree.insert("", "end", values=(
                        wallet.get("name", "Unknown"),
                        wallet.get("address", ""),
                        "Pending",
                        "Remove"
                    ))
                    
                messagebox.showinfo("Success", "Configuration loaded successfully")
                self.status_bar.config(text=f"Configuration loaded at {datetime.now().strftime('%H:%M:%S')}")
            else:
                messagebox.showinfo("Info", "No configuration file found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {e}")
            
    def save_config(self):
        """Save configuration to file"""
        try:
            # Create config directory if it doesn't exist
            os.makedirs("config", exist_ok=True)
            
            # Get wallets
            wallets = []
            for item in self.wallets_tree.get_children():
                values = self.wallets_tree.item(item, "values")
                wallets.append({
                    "name": values[0],
                    "address": values[1]
                })
                
            # Create config
            config = {
                "private_key": self.private_key_var.get(),
                "initial_capital": float(self.initial_capital_var.get()),
                "target_value": float(self.target_value_var.get()),
                "days_remaining": int(self.days_remaining_var.get()),
                "max_concurrent_trades": int(self.max_trades_var.get()),
                "trading_mode": self.trading_mode_var.get(),
                "max_daily_loss": float(self.max_daily_loss_var.get()),
                "max_drawdown": float(self.max_drawdown_var.get()),
                "max_risk_per_trade": float(self.max_risk_per_trade_var.get()),
                "max_portfolio_risk": float(self.max_portfolio_risk_var.get()),
                "default_stop_loss": float(self.default_stop_loss_var.get()),
                "default_take_profit": float(self.default_take_profit_var.get()),
                "wallets": wallets
            }
            
            # Save config
            with open("config/config.json", "w") as f:
                json.dump(config, f, indent=4)
                
            messagebox.showinfo("Success", "Configuration saved successfully")
            self.status_bar.config(text=f"Configuration saved at {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
            
    def save_risk_settings(self):
        """Save risk settings"""
        try:
            # Update risk manager
            self.risk_manager.max_daily_loss = float(self.max_daily_loss_var.get()) / 100
            self.risk_manager.max_drawdown = float(self.max_drawdown_var.get()) / 100
            self.risk_manager.max_risk_per_trade = float(self.max_risk_per_trade_var.get()) / 100
            self.risk_manager.max_portfolio_risk = float(self.max_portfolio_risk_var.get()) / 100
            
            messagebox.showinfo("Success", "Risk settings saved successfully")
            self.status_bar.config(text=f"Risk settings saved at {datetime.now().strftime('%H:%M:%S')}")
            
            # Refresh risk metrics
            self.refresh_risk()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save risk settings: {e}")
            
    def save_settings(self):
        """Save all settings"""
        try:
            # Update strategy
            self.strategy.initial_capital = float(self.initial_capital_var.get())
            self.strategy.target_value = float(self.target_value_var.get())
            self.strategy.days_remaining = int(self.days_remaining_var.get())
            
            # Set private key
            self.strategy.set_private_key(self.private_key_var.get())
            
            # Save config
            self.save_config()
            
            # Refresh data
            self.refresh_dashboard()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
            
    def reset_settings(self):
        """Reset settings to defaults"""
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to reset all settings to defaults?"):
            # Reset settings
            self.private_key_var.set("")
            self.initial_capital_var.set("200.0")
            self.target_value_var.set("10000.0")
            self.days_remaining_var.set("10")
            self.max_trades_var.set("2")
            self.trading_mode_var.set("Semi-Automated")
            
            # Reset risk settings
            self.max_daily_loss_var.set("20.0")
            self.max_drawdown_var.set("30.0")
            self.max_risk_per_trade_var.set("15.0")
            self.max_portfolio_risk_var.set("50.0")
            self.default_stop_loss_var.set("15.0")
            self.default_take_profit_var.set("50.0")
            
            # Clear wallets
            for item in self.wallets_tree.get_children():
                self.wallets_tree.delete(item)
                
            messagebox.showinfo("Success", "Settings reset to defaults")
            self.status_bar.config(text=f"Settings reset at {datetime.now().strftime('%H:%M:%S')}")
            
    def export_trade_history(self):
        """Export trade history to CSV"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs("data", exist_ok=True)
            
            # Get portfolio
            portfolio = self.strategy.portfolio_manager.get_portfolio()
            
            # Create CSV
            filename = f"data/trade_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(filename, "w") as f:
                f.write("Date,Token,Type,Quantity,Price,Amount,Status,Transaction Hash\n")
                
                for trade in portfolio.trade_history:
                    f.write(f"{trade.timestamp.strftime('%Y-%m-%d %H:%M:%S')},")
                    f.write(f"{trade.token.symbol},")
                    f.write(f"{trade.trade_type.value},")
                    f.write(f"{trade.quantity:.8f},")
                    f.write(f"{trade.price:.8f},")
                    f.write(f"{trade.amount_usd:.2f},")
                    f.write(f"{trade.status},")
                    f.write(f"{trade.transaction_hash}\n")
                    
            messagebox.showinfo("Success", f"Trade history exported to {filename}")
            self.status_bar.config(text=f"Trade history exported at {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export trade history: {e}")
            
    def show_documentation(self):
        """Show documentation"""
        doc_text = """
        Solana Meme Coin Trading Bot Documentation
        
        This trading bot is designed to help you trade meme coins on the Solana blockchain
        with the goal of turning $200 into $10,000 in 10 days.
        
        Key Features:
        - Market analysis to find trending meme coins
        - Copy trading from successful wallets
        - Risk management to protect your capital
        - Semi-automated trading with user approval
        
        Dashboard:
        - Shows key metrics and active holdings
        - Displays recent trading signals
        
        Trading Signals:
        - Lists buy and sell signals with confidence levels
        - Provides detailed information about each signal
        
        Portfolio:
        - Tracks your holdings and trade history
        - Calculates profit/loss for each position
        
        Risk Management:
        - Monitors risk metrics like drawdown and exposure
        - Adjusts position sizes based on risk factors
        
        Settings:
        - Configure API keys and trading parameters
        - Manage tracked wallets for copy trading
        
        Getting Started:
        1. Enter your Solana private key in Settings
        2. Add wallets to track for copy trading signals
        3. Configure risk parameters to match your preferences
        4. Monitor trading signals and approve trades
        
        Warning: Trading meme coins carries significant risk.
        Only trade with funds you can afford to lose.
        """
        
        doc_window = tk.Toplevel(self.root)
        doc_window.title("Documentation")
        doc_window.geometry("600x500")
        
        text = scrolledtext.ScrolledText(doc_window, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert(tk.END, doc_text)
        text.config(state=tk.DISABLED)
        
    def show_about(self):
        """Show about dialog"""
        about_text = """
        Solana Meme Coin Trading Bot
        Version 1.0.0
        
        A semi-automated trading bot designed to trade meme coins
        on the Solana blockchain using Jupiter Exchange.
        
        Goal: Turn $200 into $10,000 in 10 days
        
        This software is for educational purposes only.
        Trading cryptocurrencies involves significant risk.
        
        © 2025 All Rights Reserved
        """
        
        messagebox.showinfo("About", about_text)
        
    def on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            # Stop asyncio loop
            self.async_app.stop()
            
            # Destroy window
            self.root.destroy()


def main():
    """Main function"""
    root = tk.Tk()
    app = TradingBotUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
