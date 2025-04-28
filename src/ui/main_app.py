import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import logging
import threading
import asyncio
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import UI components
from src.ui.enhanced_ui import ModernUITheme, EnhancedUI, ToastNotification
from src.ui.settings_page import SettingsPage
from src.ui.demo_mode import DemoModePage, DemoModeManager
from src.utils.config import initialize_app
from src.ui.enhanced_ui import StatusIndicator
from src.analysis.market_analyzer import MarketAnalyzer
from src.strategy.trading_strategy import TradingStrategy
from src.risk.risk_manager import RiskManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('trading_bot.log')
    ]
)
logger = logging.getLogger(__name__)

class TradingBotApp:
    """Main application class for the Solana Meme Coin Trading Bot"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Solana Meme Coin Trading Bot")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Initialize config
        self.config = initialize_app()
        
        # Initialize demo mode manager
        self.demo_manager = DemoModeManager()
        
        # Apply modern UI theme
        self.style = ModernUITheme.apply_theme(root)
        
        # Create main container
        self.main_container = ttk.Frame(root)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create header
        self.create_header()
        
        # Create main content area
        self.content_frame = ttk.Frame(self.main_container)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_trading_tab()
        self.create_portfolio_tab()
        self.create_analysis_tab()
        self.create_settings_tab()
        self.create_demo_mode_tab()
        
        # Create status bar
        self.status_bar, self.status_var, self.time_var = EnhancedUI.create_status_bar(self.main_container)
        
        # Initialize components
        self.initialize_components()
        
        # Bind events
        self.bind_events()
        
        # Schedule periodic updates
        self.schedule_updates()
    
    def create_header(self):
        """Create the application header"""
        header_frame = ttk.Frame(self.main_container, style="Card.TFrame", padding=10)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Logo and title
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side=tk.LEFT)
        
        title_label = ttk.Label(
            title_frame, 
            text="Solana Meme Coin Trading Bot",
            style="Title.TLabel"
        )
        title_label.pack(anchor=tk.W)
        
        subtitle_label = ttk.Label(
            title_frame,
            text="Turn $200 into $10,000 in 10 days",
            style="Subtitle.TLabel"
        )
        subtitle_label.pack(anchor=tk.W)
        
        # Connection status
        self.connection_frame = ttk.Frame(header_frame)
        self.connection_frame.pack(side=tk.RIGHT)
        
        self.connection_status = tk.StringVar(value="Disconnected")
        self.connection_indicator = StatusIndicator(
            self.connection_frame,
            text="Status: Disconnected",
            status="error"
        )
        self.connection_indicator.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Balance display
        self.balance_var = tk.StringVar(value="Balance: $0.00")
        balance_label = ttk.Label(
            self.connection_frame,
            textvariable=self.balance_var,
            font=(ModernUITheme.FONT_FAMILY, ModernUITheme.FONT_SIZE_LARGE, "bold")
        )
        balance_label.pack(side=tk.RIGHT, padx=(0, 20))
    
    def create_dashboard_tab(self):
        """Create the dashboard tab"""
        dashboard_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(dashboard_frame, text="Dashboard")
        
        # Split into left and right panes
        dashboard_panes = ttk.PanedWindow(dashboard_frame, orient=tk.HORIZONTAL)
        dashboard_panes.pack(fill=tk.BOTH, expand=True)
        
        # Left pane - Portfolio summary and performance
        left_frame = ttk.Frame(dashboard_panes, padding=10)
        dashboard_panes.add(left_frame, weight=1)
        
        # Portfolio summary card
        portfolio_card = ttk.LabelFrame(left_frame, text="Portfolio Summary", padding=10)
        portfolio_card.pack(fill=tk.X, pady=(0, 10))
        
        # Portfolio summary content
        summary_frame = ttk.Frame(portfolio_card)
        summary_frame.pack(fill=tk.X)
        
        # Initial investment
        initial_frame, initial_label = EnhancedUI.create_data_row(
            summary_frame, "Initial Investment:", "$200.00"
        )
        
        # Current value
        self.current_value_var = tk.StringVar(value="$0.00")
        current_frame, current_label = EnhancedUI.create_data_row(
            summary_frame, "Current Value:", value_var=self.current_value_var
        )
        
        # Profit/Loss
        self.profit_loss_var = tk.StringVar(value="$0.00 (0.00%)")
        profit_frame, self.profit_label = EnhancedUI.create_data_row(
            summary_frame, "Profit/Loss:", value_var=self.profit_loss_var
        )
        
        # Target
        target_frame, target_label = EnhancedUI.create_data_row(
            summary_frame, "Target:", "$10,000.00"
        )
        
        # Progress to target
        progress_frame = ttk.Frame(portfolio_card)
        progress_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(progress_frame, text="Progress to Target:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.progress_var = tk.DoubleVar(value=0)
        progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            length=400,
            mode="determinate",
            maximum=100
        )
        progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.progress_label = ttk.Label(progress_frame, text="0.00%")
        self.progress_label.pack(side=tk.LEFT)
        
        # Performance chart card
        performance_card = ttk.LabelFrame(left_frame, text="Performance Chart", padding=10)
        performance_card.pack(fill=tk.BOTH, expand=True)
        
        # Placeholder for chart
        chart_placeholder = ttk.Label(
            performance_card,
            text="Performance chart will be displayed here",
            anchor=tk.CENTER
        )
        chart_placeholder.pack(fill=tk.BOTH, expand=True)
        
        # Right pane - Trading signals and activity
        right_frame = ttk.Frame(dashboard_panes, padding=10)
        dashboard_panes.add(right_frame, weight=1)
        
        # Trading signals card
        signals_card = ttk.LabelFrame(right_frame, text="Trading Signals", padding=10)
        signals_card.pack(fill=tk.X, pady=(0, 10))
        
        # Create signals table with scrollbar
        signals_container = ttk.Frame(signals_card)
        signals_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10), height=200)
        
        columns = ("token", "signal", "price", "confidence", "time")
        self.signals_tree = ttk.Treeview(
            signals_container,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=8
        )
        
        # Define headings
        self.signals_tree.heading("token", text="Token")
        self.signals_tree.heading("signal", text="Signal")
        self.signals_tree.heading("price", text="Price ($)")
        self.signals_tree.heading("confidence", text="Confidence")
        self.signals_tree.heading("time", text="Time")
        
        # Define columns
        self.signals_tree.column("token", width=80, anchor=tk.W)
        self.signals_tree.column("signal", width=80, anchor=tk.CENTER)
        self.signals_tree.column("price", width=100, anchor=tk.E)
        self.signals_tree.column("confidence", width=100, anchor=tk.CENTER)
        self.signals_tree.column("time", width=120, anchor=tk.W)
        
        # Add scrollbar
        signals_scrollbar = ttk.Scrollbar(signals_container, orient="vertical", command=self.signals_tree.yview)
        self.signals_tree.configure(yscrollcommand=signals_scrollbar.set)
        
        self.signals_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        signals_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add sample data
        for i in range(5):
            if i % 2 == 0:
                signal = "BUY"
                tag = "buy"
            else:
                signal = "SELL"
                tag = "sell"
            
            item_id = self.signals_tree.insert(
                "", "end", 
                values=(f"TOKEN{i}", signal, f"{0.00123 * (i+1):.8f}", f"{70 + i*5}%", "2025-04-27 12:30:00"),
                tags=(tag,)
            )
        
        # Configure tags
        self.signals_tree.tag_configure("buy", foreground=ModernUITheme.SUCCESS)
        self.signals_tree.tag_configure("sell", foreground=ModernUITheme.ACCENT)
        
        # Recent activity card
        activity_card = ttk.LabelFrame(right_frame, text="Recent Activity", padding=10)
        activity_card.pack(fill=tk.BOTH, expand=True)
        
        # Create activity table with scrollbar
        activity_container = ttk.Frame(activity_card)
        activity_container.pack(fill=tk.BOTH, expand=True)
        
        columns = ("time", "type", "description", "status")
        self.activity_tree = ttk.Treeview(
            activity_container,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # Define headings
        self.activity_tree.heading("time", text="Time")
        self.activity_tree.heading("type", text="Type")
        self.activity_tree.heading("description", text="Description")
        self.activity_tree.heading("status", text="Status")
        
        # Define columns
        self.activity_tree.column("time", width=120, anchor=tk.W)
        self.activity_tree.column("type", width=80, anchor=tk.CENTER)
        self.activity_tree.column("description", width=250, anchor=tk.W)
        self.activity_tree.column("status", width=80, anchor=tk.CENTER)
        
        # Add scrollbar
        activity_scrollbar = ttk.Scrollbar(activity_container, orient="vertical", command=self.activity_tree.yview)
        self.activity_tree.configure(yscrollcommand=activity_scrollbar.set)
        
        self.activity_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        activity_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add sample data
        for i in range(10):
            if i % 3 == 0:
                activity_type = "TRADE"
                status = "COMPLETED"
                tag = "completed"
            elif i % 3 == 1:
                activity_type = "SCAN"
                status = "COMPLETED"
                tag = "completed"
            else:
                activity_type = "ALERT"
                status = "NEW"
                tag = "new"
            
            item_id = self.activity_tree.insert(
                "", 0,  # Insert at the beginning (newest first)
                values=(f"2025-04-27 {12-i}:30:00", activity_type, f"Sample activity description {i}", status),
                tags=(tag,)
            )
        
        # Configure tags
        self.activity_tree.tag_configure("completed", foreground=ModernUITheme.SUCCESS)
        self.activity_tree.tag_configure("new", foreground=ModernUITheme.PRIMARY)
    
    def create_trading_tab(self):
        """Create the trading tab"""
        trading_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(trading_frame, text="Trading")
        
        # Split into left and right panes
        trading_panes = ttk.PanedWindow(trading_frame, orient=tk.HORIZONTAL)
        trading_panes.pack(fill=tk.BOTH, expand=True)
        
        # Left pane - Token list
        left_frame = ttk.Frame(trading_panes, padding=10)
        trading_panes.add(left_frame, weight=1)
        
        # Search frame
        search_frame, self.search_var, search_entry = EnhancedUI.create_search_box(
            left_frame, self.search_tokens, "Search tokens..."
        )
        
        # Token list card
        token_list_card = ttk.LabelFrame(left_frame, text="Available Tokens", padding=10)
        token_list_card.pack(fill=tk.BOTH, expand=True)
        
        # Create token list with scrollbar
        token_list_container = ttk.Frame(token_list_card)
        token_list_container.pack(fill=tk.BOTH, expand=True)
        
        columns = ("symbol", "name", "price", "change_24h", "volume")
        self.token_tree = ttk.Treeview(
            token_list_container,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # Define headings
        self.token_tree.heading("symbol", text="Symbol")
        self.token_tree.heading("name", text="Name")
        self.token_tree.heading("price", text="Price ($)")
        self.token_tree.heading("change_24h", text="24h Change (%)")
        self.token_tree.heading("volume", text="Volume ($)")
        
        # Define columns
        self.token_tree.column("symbol", width=80, anchor=tk.W)
        self.token_tree.column("name", width=150, anchor=tk.W)
        self.token_tree.column("price", width=100, anchor=tk.E)
        self.token_tree.column("change_24h", width=100, anchor=tk.E)
        self.token_tree.column("volume", width=100, anchor=tk.E)
        
        # Add scrollbar
        token_scrollbar = ttk.Scrollbar(token_list_container, orient="vertical", command=self.token_tree.yview)
        self.token_tree.configure(yscrollcommand=token_scrollbar.set)
        
        self.token_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        token_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add sample data
        for i in range(20):
            price = 0.00001 * (i + 1)
            change = (i % 10) - 5  # Range from -5 to 4
            volume = 10000 * (i + 1)
            
            # Format values
            if price < 0.000001:
                price_str = f"{price:.10f}"
            elif price < 0.0001:
                price_str = f"{price:.8f}"
            elif price < 0.01:
                price_str = f"{price:.6f}"
            elif price < 1:
                price_str = f"{price:.4f}"
            else:
                price_str = f"{price:.2f}"
            
            change_str = f"{change:.2f}"
            
            if volume >= 1_000_000:
                volume_str = f"{volume/1_000_000:.2f}M"
            elif volume >= 1_000:
                volume_str = f"{volume/1_000:.2f}K"
            else:
                volume_str = f"{volume:.2f}"
            
            # Insert into tree
            item_id = self.token_tree.insert(
                "", "end", 
                values=(f"TOKEN{i}", f"Token Name {i}", price_str, change_str, volume_str)
            )
            
            # Apply color to change column
            if change > 0:
                self.token_tree.item(item_id, tags=("positive",))
            elif change < 0:
                self.token_tree.item(item_id, tags=("negative",))
        
        # Configure tags
        self.token_tree.tag_configure("positive", foreground=ModernUITheme.SUCCESS)
        self.token_tree.tag_configure("negative", foreground=ModernUITheme.ERROR)
        
        # Bind selection event
        self.token_tree.bind("<<TreeviewSelect>>", self.on_token_select)
        
        # Right pane - Token details and trading
        right_frame = ttk.Frame(trading_panes, padding=10)
        trading_panes.add(right_frame, weight=1)
        
        # Token details card
        self.token_details_card = ttk.LabelFrame(right_frame, text="Token Details", padding=10)
        self.token_details_card.pack(fill=tk.X, pady=(0, 10))
        
        # Token details content
        self.token_symbol_var = tk.StringVar()
        self.token_name_var = tk.StringVar()
        self.token_price_var = tk.StringVar()
        self.token_change_var = tk.StringVar()
        self.token_volume_var = tk.StringVar()
        self.token_liquidity_var = tk.StringVar()
        
        # Symbol and name
        header_frame = ttk.Frame(self.token_details_card)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.token_symbol_label = ttk.Label(
            header_frame,
            textvariable=self.token_symbol_var,
            font=(ModernUITheme.FONT_FAMILY, ModernUITheme.FONT_SIZE_XLARGE, "bold"),
            foreground=ModernUITheme.PRIMARY
        )
        self.token_symbol_label.pack(side=tk.LEFT)
        
        self.token_name_label = ttk.Label(
            header_frame,
            textvariable=self.token_name_var,
            font=(ModernUITheme.FONT_FAMILY, ModernUITheme.FONT_SIZE_LARGE),
            foreground=ModernUITheme.TEXT_SECONDARY
        )
        self.token_name_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Price and change
        price_frame = ttk.Frame(self.token_details_card)
        price_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(price_frame, text="Price:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.token_price_label = ttk.Label(
            price_frame,
            textvariable=self.token_price_var,
            font=(ModernUITheme.FONT_FAMILY, ModernUITheme.FONT_SIZE_LARGE, "bold")
        )
        self.token_price_label.pack(side=tk.LEFT)
        
        ttk.Label(price_frame, text="24h Change:").pack(side=tk.LEFT, padx=(20, 10))
        
        self.token_change_label = ttk.Label(
            price_frame,
            textvariable=self.token_change_var,
            font=(ModernUITheme.FONT_FAMILY, ModernUITheme.FONT_SIZE_LARGE, "bold")
        )
        self.token_change_label.pack(side=tk.LEFT)
        
        # Volume and liquidity
        stats_frame = ttk.Frame(self.token_details_card)
        stats_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(stats_frame, text="24h Volume:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.token_volume_label = ttk.Label(
            stats_frame,
            textvariable=self.token_volume_var
        )
        self.token_volume_label.pack(side=tk.LEFT)
        
        ttk.Label(stats_frame, text="Liquidity:").pack(side=tk.LEFT, padx=(20, 10))
        
        self.token_liquidity_label = ttk.Label(
            stats_frame,
            textvariable=self.token_liquidity_var
        )
        self.token_liquidity_label.pack(side=tk.LEFT)
        
        # Trading card
        trading_card = ttk.LabelFrame(right_frame, text="Execute Trade", padding=10)
        trading_card.pack(fill=tk.BOTH, expand=True)
        
        # Trade type
        type_frame = ttk.Frame(trading_card)
        type_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(type_frame, text="Trade Type:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.trade_type_var = tk.StringVar(value="BUY")
        buy_radio = ttk.Radiobutton(
            type_frame,
            text="Buy",
            variable=self.trade_type_var,
            value="BUY",
            command=self.update_trade_form
        )
        buy_radio.pack(side=tk.LEFT, padx=(0, 10))
        
        sell_radio = ttk.Radiobutton(
            type_frame,
            text="Sell",
            variable=self.trade_type_var,
            value="SELL",
            command=self.update_trade_form
        )
        sell_radio.pack(side=tk.LEFT)
        
        # Amount frame
        self.amount_frame = ttk.Frame(trading_card)
        self.amount_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(self.amount_frame, text="Amount ($):").pack(side=tk.LEFT, padx=(0, 10))
        
        self.amount_var = tk.DoubleVar(value=10.0)
        amount_entry = ttk.Entry(self.amount_frame, textvariable=self.amount_var, width=10)
        amount_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # Percentage buttons for buy
        self.percentage_frame = ttk.Frame(self.amount_frame)
        self.percentage_frame.pack(side=tk.LEFT)
        
        for pct in [10, 25, 50, 100]:
            pct_button = ttk.Button(
                self.percentage_frame,
                text=f"{pct}%",
                command=lambda p=pct: self.set_percentage(p),
                style="Small.TButton",
                width=4
            )
            pct_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Quantity frame for sell
        self.quantity_frame = ttk.Frame(trading_card)
        
        ttk.Label(self.quantity_frame, text="Quantity:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.quantity_var = tk.DoubleVar(value=0)
        quantity_entry = ttk.Entry(self.quantity_frame, textvariable=self.quantity_var, width=15)
        quantity_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # Percentage buttons for sell
        self.sell_percentage_frame = ttk.Frame(self.quantity_frame)
        self.sell_percentage_frame.pack(side=tk.LEFT)
        
        for pct in [10, 25, 50, 100]:
            pct_button = ttk.Button(
                self.sell_percentage_frame,
                text=f"{pct}%",
                command=lambda p=pct: self.set_sell_percentage(p),
                style="Small.TButton",
                width=4
            )
            pct_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Summary frame
        summary_frame = ttk.Frame(trading_card)
        summary_frame.pack(fill=tk.X, pady=(10, 10))
        
        ttk.Label(summary_frame, text="Trade Summary:").pack(anchor=tk.W)
        
        self.summary_text = tk.Text(summary_frame, height=5, width=40, wrap=tk.WORD, state=tk.DISABLED)
        self.summary_text.pack(fill=tk.X, pady=(5, 0))
        
        # Execute button
        button_frame = ttk.Frame(trading_card)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.execute_button = ttk.Button(
            button_frame,
            text="Execute Trade",
            command=self.execute_trade,
            style="Accent.TButton"
        )
        self.execute_button.pack(side=tk.RIGHT)
        
        # Initially hide quantity frame (buy is default)
        self.update_trade_form()
    
    def create_portfolio_tab(self):
        """Create the portfolio tab"""
        portfolio_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(portfolio_frame, text="Portfolio")
        
        # Split into top and bottom sections
        portfolio_panes = ttk.PanedWindow(portfolio_frame, orient=tk.VERTICAL)
        portfolio_panes.pack(fill=tk.BOTH, expand=True)
        
        # Top section - Holdings
        top_frame = ttk.Frame(portfolio_panes, padding=10)
        portfolio_panes.add(top_frame, weight=2)
        
        # Holdings card
        holdings_card = ttk.LabelFrame(top_frame, text="Current Holdings", padding=10)
        holdings_card.pack(fill=tk.BOTH, expand=True)
        
        # Create holdings table with scrollbar
        holdings_container = ttk.Frame(holdings_card)
        holdings_container.pack(fill=tk.BOTH, expand=True)
        
        columns = ("symbol", "quantity", "avg_price", "current_price", "value", "profit_loss", "profit_loss_pct", "actions")
        self.holdings_tree = ttk.Treeview(
            holdings_container,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # Define headings
        self.holdings_tree.heading("symbol", text="Symbol")
        self.holdings_tree.heading("quantity", text="Quantity")
        self.holdings_tree.heading("avg_price", text="Avg Price ($)")
        self.holdings_tree.heading("current_price", text="Current Price ($)")
        self.holdings_tree.heading("value", text="Value ($)")
        self.holdings_tree.heading("profit_loss", text="Profit/Loss ($)")
        self.holdings_tree.heading("profit_loss_pct", text="P/L (%)")
        self.holdings_tree.heading("actions", text="Actions")
        
        # Define columns
        self.holdings_tree.column("symbol", width=80, anchor=tk.W)
        self.holdings_tree.column("quantity", width=100, anchor=tk.E)
        self.holdings_tree.column("avg_price", width=100, anchor=tk.E)
        self.holdings_tree.column("current_price", width=100, anchor=tk.E)
        self.holdings_tree.column("value", width=100, anchor=tk.E)
        self.holdings_tree.column("profit_loss", width=100, anchor=tk.E)
        self.holdings_tree.column("profit_loss_pct", width=80, anchor=tk.E)
        self.holdings_tree.column("actions", width=100, anchor=tk.CENTER)
        
        # Add scrollbar
        holdings_scrollbar = ttk.Scrollbar(holdings_container, orient="vertical", command=self.holdings_tree.yview)
        self.holdings_tree.configure(yscrollcommand=holdings_scrollbar.set)
        
        self.holdings_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        holdings_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add sample data
        for i in range(5):
            symbol = f"TOKEN{i}"
            quantity = 1000 * (i + 1)
            avg_price = 0.00001 * (i + 1)
            current_price = avg_price * (1 + (i % 5 - 2) / 10)  # +/- 20% from avg price
            value = quantity * current_price
            profit_loss = value - (quantity * avg_price)
            profit_loss_pct = (profit_loss / (quantity * avg_price)) * 100
            
            # Format values
            quantity_str = f"{quantity:.2f}"
            avg_price_str = f"{avg_price:.8f}"
            current_price_str = f"{current_price:.8f}"
            value_str = f"{value:.2f}"
            
            # Format profit/loss with color tag
            if profit_loss > 0:
                profit_loss_str = f"+{profit_loss:.2f}"
                profit_loss_pct_str = f"+{profit_loss_pct:.2f}"
                tag = "positive"
            elif profit_loss < 0:
                profit_loss_str = f"{profit_loss:.2f}"
                profit_loss_pct_str = f"{profit_loss_pct:.2f}"
                tag = "negative"
            else:
                profit_loss_str = f"{profit_loss:.2f}"
                profit_loss_pct_str = f"{profit_loss_pct:.2f}"
                tag = ""
            
            # Insert into tree
            item_id = self.holdings_tree.insert(
                "", "end", 
                values=(symbol, quantity_str, avg_price_str, current_price_str, value_str, profit_loss_str, profit_loss_pct_str, "Sell"),
                tags=(tag,)
            )
        
        # Configure tags
        self.holdings_tree.tag_configure("positive", foreground=ModernUITheme.SUCCESS)
        self.holdings_tree.tag_configure("negative", foreground=ModernUITheme.ERROR)
        
        # Bottom section - Trade history
        bottom_frame = ttk.Frame(portfolio_panes, padding=10)
        portfolio_panes.add(bottom_frame, weight=1)
        
        # Trade history card
        history_card = ttk.LabelFrame(bottom_frame, text="Trade History", padding=10)
        history_card.pack(fill=tk.BOTH, expand=True)
        
        # Create history table with scrollbar
        history_container = ttk.Frame(history_card)
        history_container.pack(fill=tk.BOTH, expand=True)
        
        columns = ("id", "timestamp", "type", "symbol", "quantity", "price", "amount", "status")
        self.history_tree = ttk.Treeview(
            history_container,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # Define headings
        self.history_tree.heading("id", text="ID")
        self.history_tree.heading("timestamp", text="Timestamp")
        self.history_tree.heading("type", text="Type")
        self.history_tree.heading("symbol", text="Symbol")
        self.history_tree.heading("quantity", text="Quantity")
        self.history_tree.heading("price", text="Price ($)")
        self.history_tree.heading("amount", text="Amount ($)")
        self.history_tree.heading("status", text="Status")
        
        # Define columns
        self.history_tree.column("id", width=50, anchor=tk.CENTER)
        self.history_tree.column("timestamp", width=150, anchor=tk.W)
        self.history_tree.column("type", width=80, anchor=tk.CENTER)
        self.history_tree.column("symbol", width=80, anchor=tk.W)
        self.history_tree.column("quantity", width=100, anchor=tk.E)
        self.history_tree.column("price", width=100, anchor=tk.E)
        self.history_tree.column("amount", width=100, anchor=tk.E)
        self.history_tree.column("status", width=100, anchor=tk.CENTER)
        
        # Add scrollbar
        history_scrollbar = ttk.Scrollbar(history_container, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=history_scrollbar.set)
        
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add sample data
        for i in range(10):
            trade_id = i + 1
            timestamp = f"2025-04-27 {12-i}:30:00"
            trade_type = "BUY" if i % 2 == 0 else "SELL"
            symbol = f"TOKEN{i % 5}"
            quantity = 1000 * (i % 5 + 1)
            price = 0.00001 * (i % 5 + 1)
            amount = quantity * price
            status = "COMPLETED"
            
            # Format values
            quantity_str = f"{quantity:.2f}"
            price_str = f"{price:.8f}"
            amount_str = f"{amount:.2f}"
            
            # Insert into tree with color tag
            tag = "buy" if trade_type == "BUY" else "sell"
            
            item_id = self.history_tree.insert(
                "", 0,  # Insert at the beginning (newest first)
                values=(trade_id, timestamp, trade_type, symbol, quantity_str, price_str, amount_str, status),
                tags=(tag,)
            )
        
        # Configure tags
        self.history_tree.tag_configure("buy", foreground=ModernUITheme.PRIMARY)
        self.history_tree.tag_configure("sell", foreground=ModernUITheme.ACCENT)
    
    def create_analysis_tab(self):
        """Create the analysis tab"""
        analysis_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(analysis_frame, text="Analysis")
        
        # Split into left and right panes
        analysis_panes = ttk.PanedWindow(analysis_frame, orient=tk.HORIZONTAL)
        analysis_panes.pack(fill=tk.BOTH, expand=True)
        
        # Left pane - Market overview
        left_frame = ttk.Frame(analysis_panes, padding=10)
        analysis_panes.add(left_frame, weight=1)
        
        # Market overview card
        market_card = ttk.LabelFrame(left_frame, text="Market Overview", padding=10)
        market_card.pack(fill=tk.X, pady=(0, 10))
        
        # Market stats
        stats_frame = ttk.Frame(market_card)
        stats_frame.pack(fill=tk.X)
        
        # Create data rows
        EnhancedUI.create_data_row(stats_frame, "Total Market Cap:", "$1.23B")
        EnhancedUI.create_data_row(stats_frame, "24h Volume:", "$456.78M")
        EnhancedUI.create_data_row(stats_frame, "Active Tokens:", "1,234")
        EnhancedUI.create_data_row(stats_frame, "Market Sentiment:", "Bullish")
        
        # Trending tokens card
        trending_card = ttk.LabelFrame(left_frame, text="Trending Tokens", padding=10)
        trending_card.pack(fill=tk.BOTH, expand=True)
        
        # Create trending tokens table with scrollbar
        trending_container = ttk.Frame(trending_card)
        trending_container.pack(fill=tk.BOTH, expand=True)
        
        columns = ("rank", "symbol", "name", "price", "change_24h")
        self.trending_tree = ttk.Treeview(
            trending_container,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # Define headings
        self.trending_tree.heading("rank", text="#")
        self.trending_tree.heading("symbol", text="Symbol")
        self.trending_tree.heading("name", text="Name")
        self.trending_tree.heading("price", text="Price ($)")
        self.trending_tree.heading("change_24h", text="24h Change (%)")
        
        # Define columns
        self.trending_tree.column("rank", width=40, anchor=tk.CENTER)
        self.trending_tree.column("symbol", width=80, anchor=tk.W)
        self.trending_tree.column("name", width=150, anchor=tk.W)
        self.trending_tree.column("price", width=100, anchor=tk.E)
        self.trending_tree.column("change_24h", width=100, anchor=tk.E)
        
        # Add scrollbar
        trending_scrollbar = ttk.Scrollbar(trending_container, orient="vertical", command=self.trending_tree.yview)
        self.trending_tree.configure(yscrollcommand=trending_scrollbar.set)
        
        self.trending_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        trending_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add sample data
        for i in range(10):
            rank = i + 1
            symbol = f"TOKEN{i}"
            name = f"Token Name {i}"
            price = 0.00001 * (10 - i)
            change = 20 - i * 2  # Range from 20 to 2
            
            # Format values
            price_str = f"{price:.8f}"
            change_str = f"+{change:.2f}"
            
            # Insert into tree
            item_id = self.trending_tree.insert(
                "", "end", 
                values=(rank, symbol, name, price_str, change_str),
                tags=("positive",)
            )
        
        # Configure tags
        self.trending_tree.tag_configure("positive", foreground=ModernUITheme.SUCCESS)
        
        # Right pane - Token analysis
        right_frame = ttk.Frame(analysis_panes, padding=10)
        analysis_panes.add(right_frame, weight=1)
        
        # Token analysis card
        analysis_card = ttk.LabelFrame(right_frame, text="Token Analysis", padding=10)
        analysis_card.pack(fill=tk.BOTH, expand=True)
        
        # Token selection
        selection_frame = ttk.Frame(analysis_card)
        selection_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(selection_frame, text="Select Token:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.analysis_token_var = tk.StringVar()
        token_combo = ttk.Combobox(selection_frame, textvariable=self.analysis_token_var, width=15)
        token_combo['values'] = tuple(f"TOKEN{i}" for i in range(10))
        token_combo.current(0)
        token_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        analyze_button = ttk.Button(
            selection_frame,
            text="Analyze",
            command=self.analyze_token
        )
        analyze_button.pack(side=tk.LEFT)
        
        # Analysis tabs
        analysis_notebook = ttk.Notebook(analysis_card)
        analysis_notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Price chart tab
        price_tab = ttk.Frame(analysis_notebook, padding=10)
        analysis_notebook.add(price_tab, text="Price Chart")
        
        # Placeholder for chart
        chart_placeholder = ttk.Label(
            price_tab,
            text="Price chart will be displayed here",
            anchor=tk.CENTER
        )
        chart_placeholder.pack(fill=tk.BOTH, expand=True)
        
        # Technical indicators tab
        indicators_tab = ttk.Frame(analysis_notebook, padding=10)
        analysis_notebook.add(indicators_tab, text="Technical Indicators")
        
        # Create indicators table with scrollbar
        indicators_container = ttk.Frame(indicators_tab)
        indicators_container.pack(fill=tk.BOTH, expand=True)
        
        columns = ("indicator", "value", "signal")
        self.indicators_tree = ttk.Treeview(
            indicators_container,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # Define headings
        self.indicators_tree.heading("indicator", text="Indicator")
        self.indicators_tree.heading("value", text="Value")
        self.indicators_tree.heading("signal", text="Signal")
        
        # Define columns
        self.indicators_tree.column("indicator", width=150, anchor=tk.W)
        self.indicators_tree.column("value", width=100, anchor=tk.CENTER)
        self.indicators_tree.column("signal", width=100, anchor=tk.CENTER)
        
        # Add scrollbar
        indicators_scrollbar = ttk.Scrollbar(indicators_container, orient="vertical", command=self.indicators_tree.yview)
        self.indicators_tree.configure(yscrollcommand=indicators_scrollbar.set)
        
        self.indicators_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        indicators_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add sample data
        indicators = [
            ("RSI (14)", "65.42", "Neutral"),
            ("MACD", "0.00012", "Bullish"),
            ("Stochastic", "75.30", "Bullish"),
            ("Bollinger Bands", "Upper", "Neutral"),
            ("Moving Average (50)", "0.00123", "Bullish"),
            ("Moving Average (200)", "0.00100", "Bullish"),
            ("Volume", "Increasing", "Bullish")
        ]
        
        for indicator, value, signal in indicators:
            tag = "bullish" if signal == "Bullish" else "neutral" if signal == "Neutral" else "bearish"
            
            item_id = self.indicators_tree.insert(
                "", "end", 
                values=(indicator, value, signal),
                tags=(tag,)
            )
        
        # Configure tags
        self.indicators_tree.tag_configure("bullish", foreground=ModernUITheme.SUCCESS)
        self.indicators_tree.tag_configure("neutral", foreground=ModernUITheme.TEXT_PRIMARY)
        self.indicators_tree.tag_configure("bearish", foreground=ModernUITheme.ERROR)
        
        # Social sentiment tab
        sentiment_tab = ttk.Frame(analysis_notebook, padding=10)
        analysis_notebook.add(sentiment_tab, text="Social Sentiment")
        
        # Sentiment stats
        sentiment_frame = ttk.Frame(sentiment_tab)
        sentiment_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create data rows
        EnhancedUI.create_data_row(sentiment_frame, "Overall Sentiment:", "Positive")
        EnhancedUI.create_data_row(sentiment_frame, "Twitter Mentions:", "1,234")
        EnhancedUI.create_data_row(sentiment_frame, "Reddit Mentions:", "567")
        EnhancedUI.create_data_row(sentiment_frame, "Telegram Activity:", "High")
        EnhancedUI.create_data_row(sentiment_frame, "Discord Activity:", "Medium")
        
        # Sentiment chart placeholder
        sentiment_chart_frame = ttk.Frame(sentiment_tab)
        sentiment_chart_frame.pack(fill=tk.BOTH, expand=True)
        
        sentiment_chart_placeholder = ttk.Label(
            sentiment_chart_frame,
            text="Sentiment chart will be displayed here",
            anchor=tk.CENTER
        )
        sentiment_chart_placeholder.pack(fill=tk.BOTH, expand=True)
    
    def create_settings_tab(self):
        """Create the settings tab"""
        self.settings_page = SettingsPage(self.notebook, self)
        self.notebook.add(self.settings_page, text="Settings")
    
    def create_demo_mode_tab(self):
        """Create the demo mode tab"""
        self.demo_page = DemoModePage(self.notebook, self)
        self.notebook.add(self.demo_page, text="Demo Mode")
    
    def initialize_components(self):
        """Initialize components and load data"""
        # Set initial connection status
        self.update_connection_status("Disconnected", "error")
        
        # Load initial data
        self.load_initial_data()
    
    def bind_events(self):
        """Bind events to widgets"""
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def schedule_updates(self):
        """Schedule periodic updates"""
        # Update UI every second
        self.root.after(1000, self.update_ui)
    
    def load_initial_data(self):
        """Load initial data for the UI"""
        # This would normally load data from APIs or local storage
        pass
    
    def update_ui(self):
        """Update UI elements periodically"""
        # Update time in status bar
        self.time_var.set(datetime.now().strftime("%H:%M:%S"))
        
        # Schedule next update
        self.root.after(1000, self.update_ui)
    
    def update_connection_status(self, status_text, status_type):
        """Update the connection status indicator"""
        self.connection_status.set(status_text)
        self.connection_indicator.set_status(status_type, f"Status: {status_text}")
    
    def search_tokens(self, search_text):
        """Search for tokens based on search text"""
        # This would normally search through token data
        if search_text:
            EnhancedUI.show_toast(self.root, f"Searching for: {search_text}", "info")
    
    def on_token_select(self, event):
        """Handle token selection event"""
        # Get selected item
        selection = self.token_tree.selection()
        if not selection:
            return
        
        # Get token data
        item = self.token_tree.item(selection[0])
        values = item["values"]
        
        if not values or len(values) < 5:
            return
        
        symbol = values[0]
        name = values[1]
        price_str = values[2]
        change_str = values[3]
        volume_str = values[4]
        
        # Update token details
        self.token_symbol_var.set(symbol)
        self.token_name_var.set(name)
        self.token_price_var.set(f"${price_str}")
        
        # Set change color
        try:
            change = float(change_str)
            if change > 0:
                self.token_change_var.set(f"+{change_str}%")
                self.token_change_label.configure(foreground=ModernUITheme.SUCCESS)
            elif change < 0:
                self.token_change_var.set(f"{change_str}%")
                self.token_change_label.configure(foreground=ModernUITheme.ERROR)
            else:
                self.token_change_var.set(f"{change_str}%")
                self.token_change_label.configure(foreground=ModernUITheme.TEXT_SECONDARY)
        except ValueError:
            self.token_change_var.set(change_str)
        
        self.token_volume_var.set(volume_str)
        self.token_liquidity_var.set("$50.00K")  # Placeholder
        
        # Update trade form
        self.update_trade_form()
    
    def update_trade_form(self):
        """Update trade form based on trade type"""
        trade_type = self.trade_type_var.get()
        
        if trade_type == "BUY":
            # Show amount frame, hide quantity frame
            self.quantity_frame.pack_forget()
            self.amount_frame.pack(fill=tk.X, pady=(0, 10))
            
            # Update summary
            self.update_trade_summary()
        else:  # SELL
            # Show quantity frame, hide amount frame
            self.amount_frame.pack_forget()
            self.quantity_frame.pack(fill=tk.X, pady=(0, 10))
            
            # Update quantity based on holdings
            self.update_sell_quantity()
            
            # Update summary
            self.update_trade_summary()
    
    def update_sell_quantity(self):
        """Update sell quantity based on holdings"""
        symbol = self.token_symbol_var.get()
        if not symbol:
            return
        
        # This would normally get holdings from portfolio data
        # For now, just set a placeholder value
        self.quantity_var.set(1000)
    
    def set_percentage(self, percentage):
        """Set amount as percentage of available capital"""
        # This would normally calculate based on available balance
        # For now, just set a placeholder value
        available_capital = 200.0
        amount = available_capital * (percentage / 100)
        self.amount_var.set(round(amount, 2))
        
        # Update summary
        self.update_trade_summary()
    
    def set_sell_percentage(self, percentage):
        """Set sell quantity as percentage of holdings"""
        symbol = self.token_symbol_var.get()
        if not symbol:
            return
        
        # This would normally calculate based on holdings
        # For now, just set a placeholder value
        holding_quantity = 1000
        quantity = holding_quantity * (percentage / 100)
        self.quantity_var.set(quantity)
        
        # Update summary
        self.update_trade_summary()
    
    def update_trade_summary(self):
        """Update trade summary based on current form values"""
        symbol = self.token_symbol_var.get()
        if not symbol:
            return
        
        trade_type = self.trade_type_var.get()
        
        # Get token price from UI
        price_str = self.token_price_var.get().replace("$", "")
        try:
            price = float(price_str)
        except ValueError:
            price = 0.0
        
        # Enable text widget for editing
        self.summary_text.configure(state=tk.NORMAL)
        self.summary_text.delete("1.0", tk.END)
        
        if trade_type == "BUY":
            # Get amount
            amount = self.amount_var.get()
            
            # Calculate quantity
            quantity = amount / price if price > 0 else 0
            
            # Format summary
            summary = f"Buy {symbol}\n"
            summary += f"Amount: ${amount:.2f}\n"
            summary += f"Price: ${price:.8f}\n"
            summary += f"Quantity: {quantity:.8f}\n"
            
            # Check if amount is valid
            available_capital = 200.0  # Placeholder
            if amount > available_capital:
                summary += f"\nWARNING: Insufficient funds (${available_capital:.2f} available)"
        else:  # SELL
            # Get quantity
            quantity = self.quantity_var.get()
            
            # Calculate amount
            amount = quantity * price
            
            # Format summary
            summary = f"Sell {symbol}\n"
            summary += f"Quantity: {quantity:.8f}\n"
            summary += f"Price: ${price:.8f}\n"
            summary += f"Amount: ${amount:.2f}\n"
            
            # Check if quantity is valid
            holding_quantity = 1000  # Placeholder
            if quantity > holding_quantity:
                summary += f"\nWARNING: Insufficient quantity ({holding_quantity:.8f} available)"
        
        # Update summary text
        self.summary_text.insert(tk.END, summary)
        
        # Disable text widget
        self.summary_text.configure(state=tk.DISABLED)
    
    def execute_trade(self):
        """Execute the trade"""
        symbol = self.token_symbol_var.get()
        if not symbol:
            messagebox.showerror("Error", "No token selected")
            return
        
        trade_type = self.trade_type_var.get()
        
        try:
            if trade_type == "BUY":
                # Get amount
                amount = self.amount_var.get()
                
                # This would normally execute the buy order
                # For now, just show a success message
                EnhancedUI.show_toast(
                    self.root, 
                    f"Buy order for {symbol} executed successfully", 
                    "success"
                )
                
                # Update UI
                self.update_portfolio_data()
            else:  # SELL
                # Get quantity
                quantity = self.quantity_var.get()
                
                # This would normally execute the sell order
                # For now, just show a success message
                EnhancedUI.show_toast(
                    self.root, 
                    f"Sell order for {symbol} executed successfully", 
                    "success"
                )
                
                # Update UI
                self.update_portfolio_data()
        
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            messagebox.showerror("Error", f"Failed to execute trade: {str(e)}")
    
    def update_portfolio_data(self):
        """Update portfolio data after a trade"""
        # This would normally update portfolio data from API
        # For now, just update the UI with placeholder data
        self.current_value_var.set("$250.00")
        self.profit_loss_var.set("+$50.00 (+25.00%)")
        self.profit_label.configure(foreground=ModernUITheme.SUCCESS)
        
        # Update progress
        progress_pct = 2.5  # 250 / 10000 * 100
        self.progress_var.set(progress_pct)
        self.progress_label.configure(text=f"{progress_pct:.2f}%")
    
    def analyze_token(self):
        """Analyze the selected token"""
        token = self.analysis_token_var.get()
        if not token:
            return
        
        # This would normally perform token analysis
        # For now, just show a message
        EnhancedUI.show_toast(
            self.root, 
            f"Analyzing {token}...", 
            "info"
        )
    
    def on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            # Clean up resources
            if hasattr(self, "demo_page"):
                # Stop demo mode if active
                if hasattr(self.demo_page, "demo_manager") and self.demo_page.demo_manager.is_active():
                    self.demo_page.demo_manager.stop_demo_mode()
            
            self.root.destroy()

def main():
    """Main function to start the application"""
    root = tk.Tk()
    app = TradingBotApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
