import tkinter as tk
from tkinter import ttk, messagebox
import asyncio
import threading
import json
import os
import logging
from datetime import datetime, timedelta
import random
from typing import Dict, Any, List, Optional, Tuple, Callable

# Configure logging
logger = logging.getLogger(__name__)

class DemoModeManager:
    """Manager class for demo trading mode functionality"""
    
    def __init__(self, initial_capital=200.0):
        self.active = False
        self.initial_capital = initial_capital
        self.available_capital = initial_capital
        self.holdings = []
        self.trade_history = []
        self.start_time = None
        self.virtual_tokens = self._generate_virtual_tokens()
        self.price_update_thread = None
        self.stop_thread = False
    
    def _generate_virtual_tokens(self, count=50):
        """Generate a list of virtual tokens for demo trading"""
        token_prefixes = ["MOON", "DOGE", "SHIB", "PEPE", "FLOKI", "QUOKKA", "ROCKET", "STAR", 
                         "COSMIC", "GALAXY", "ASTRO", "LUNAR", "ORBIT", "NOVA", "COMET", "METEOR"]
        token_suffixes = ["INU", "MOON", "ROCKET", "COIN", "TOKEN", "SWAP", "CASH", "FINANCE", 
                         "PROTOCOL", "NETWORK", "DAO", "VERSE", "WORLD", "UNIVERSE", "CHAIN"]
        
        tokens = []
        for i in range(count):
            prefix = random.choice(token_prefixes)
            suffix = random.choice(token_suffixes)
            
            # Ensure we don't have duplicate names
            while any(t["symbol"] == f"{prefix}{suffix}" for t in tokens):
                prefix = random.choice(token_prefixes)
                suffix = random.choice(token_suffixes)
            
            # Generate random token data
            price = round(random.uniform(0.000001, 0.1), random.randint(6, 10))
            market_cap = price * random.randint(1000000, 1000000000)
            volume = market_cap * random.uniform(0.05, 0.5)
            
            tokens.append({
                "symbol": f"{prefix}{suffix}",
                "name": f"{prefix} {suffix}",
                "price_usd": price,
                "price_change_24h": round(random.uniform(-30, 50), 2),
                "volume_24h": volume,
                "market_cap": market_cap,
                "liquidity": volume * random.uniform(0.1, 0.5),
                "holders": random.randint(100, 10000),
                "created_at": (datetime.now() - timedelta(days=random.randint(1, 60))).isoformat(),
                "contract": "".join(random.choice("0123456789abcdef") for _ in range(40)),
                "volatility": random.uniform(0.5, 3.0)
            })
        
        return tokens
    
    def start_demo_mode(self, initial_capital=None):
        """Start demo trading mode"""
        if initial_capital is not None:
            self.initial_capital = initial_capital
            self.available_capital = initial_capital
        
        self.active = True
        self.holdings = []
        self.trade_history = []
        self.start_time = datetime.now()
        
        # Start price update thread
        self.stop_thread = False
        self.price_update_thread = threading.Thread(target=self._update_prices_thread, daemon=True)
        self.price_update_thread.start()
        
        logger.info(f"Demo mode started with {self.initial_capital} initial capital")
        return True
    
    def stop_demo_mode(self):
        """Stop demo trading mode"""
        if not self.active:
            return False
        
        self.active = False
        self.stop_thread = True
        
        if self.price_update_thread and self.price_update_thread.is_alive():
            self.price_update_thread.join(timeout=1.0)
        
        logger.info("Demo mode stopped")
        return True
    
    def reset_demo_mode(self, initial_capital=None):
        """Reset demo trading mode to initial state"""
        was_active = self.active
        
        # Stop if active
        if was_active:
            self.stop_demo_mode()
        
        # Reset state
        if initial_capital is not None:
            self.initial_capital = initial_capital
        
        self.available_capital = self.initial_capital
        self.holdings = []
        self.trade_history = []
        
        # Regenerate tokens
        self.virtual_tokens = self._generate_virtual_tokens()
        
        # Restart if it was active
        if was_active:
            self.start_demo_mode()
        
        logger.info(f"Demo mode reset with {self.initial_capital} initial capital")
        return True
    
    def _update_prices_thread(self):
        """Background thread to update token prices periodically"""
        while not self.stop_thread:
            try:
                # Update token prices
                for token in self.virtual_tokens:
                    # Calculate price change based on volatility
                    volatility = token.get("volatility", 1.0)
                    change_pct = random.normalvariate(0, volatility)
                    
                    # Apply change to price
                    old_price = token["price_usd"]
                    new_price = old_price * (1 + (change_pct / 100))
                    
                    # Ensure price doesn't go negative or too low
                    token["price_usd"] = max(new_price, 0.0000000001)
                    
                    # Update 24h change
                    token["price_change_24h"] = round(
                        0.8 * token["price_change_24h"] + 0.2 * change_pct, 2
                    )
                
                # Update holdings values
                for holding in self.holdings:
                    token_symbol = holding["token_symbol"]
                    token = next((t for t in self.virtual_tokens if t["symbol"] == token_symbol), None)
                    
                    if token:
                        holding["current_price"] = token["price_usd"]
                        holding["current_value"] = holding["quantity"] * token["price_usd"]
                        holding["profit_loss"] = holding["current_value"] - holding["cost_basis"]
                        holding["profit_loss_pct"] = (
                            (holding["current_value"] / holding["cost_basis"] - 1) * 100 
                            if holding["cost_basis"] > 0 else 0
                        )
                
                # Sleep for a short time
                import time
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in price update thread: {e}")
                time.sleep(10)  # Sleep longer on error
    
    def get_portfolio_summary(self):
        """Get a summary of the current portfolio"""
        holdings_value = sum(holding["current_value"] for holding in self.holdings)
        total_value = self.available_capital + holdings_value
        
        profit_loss = total_value - self.initial_capital
        profit_loss_pct = (total_value / self.initial_capital - 1) * 100 if self.initial_capital > 0 else 0
        
        return {
            "initial_capital": self.initial_capital,
            "available_capital": self.available_capital,
            "holdings_value": holdings_value,
            "total_value": total_value,
            "profit_loss": profit_loss,
            "profit_loss_pct": profit_loss_pct,
            "holdings_count": len(self.holdings),
            "trade_count": len(self.trade_history),
            "start_time": self.start_time,
            "duration": (datetime.now() - self.start_time) if self.start_time else timedelta(0)
        }
    
    def get_available_tokens(self, count=10, filter_text=None):
        """Get a list of available tokens for trading"""
        tokens = self.virtual_tokens
        
        # Apply filter if provided
        if filter_text:
            filter_text = filter_text.lower()
            tokens = [
                t for t in tokens 
                if filter_text in t["symbol"].lower() or filter_text in t["name"].lower()
            ]
        
        # Sort by market cap (descending)
        tokens = sorted(tokens, key=lambda t: t.get("market_cap", 0), reverse=True)
        
        # Return requested number of tokens
        return tokens[:count]
    
    def get_trending_tokens(self, count=5):
        """Get a list of trending tokens based on price change"""
        # Sort by 24h price change (descending)
        tokens = sorted(self.virtual_tokens, key=lambda t: t.get("price_change_24h", 0), reverse=True)
        
        # Return requested number of tokens
        return tokens[:count]
    
    def execute_buy(self, token_symbol, amount_usd):
        """Execute a buy order in demo mode"""
        if not self.active:
            return {"success": False, "error": "Demo mode is not active"}
        
        if amount_usd <= 0:
            return {"success": False, "error": "Amount must be greater than zero"}
        
        if amount_usd > self.available_capital:
            return {"success": False, "error": "Insufficient funds"}
        
        # Find token
        token = next((t for t in self.virtual_tokens if t["symbol"] == token_symbol), None)
        if not token:
            return {"success": False, "error": f"Token {token_symbol} not found"}
        
        # Calculate quantity
        price = token["price_usd"]
        quantity = amount_usd / price
        
        # Update available capital
        self.available_capital -= amount_usd
        
        # Check if we already have this token
        existing_holding = next((h for h in self.holdings if h["token_symbol"] == token_symbol), None)
        
        if existing_holding:
            # Update existing holding
            new_quantity = existing_holding["quantity"] + quantity
            new_cost_basis = existing_holding["cost_basis"] + amount_usd
            
            existing_holding["quantity"] = new_quantity
            existing_holding["cost_basis"] = new_cost_basis
            existing_holding["avg_price"] = new_cost_basis / new_quantity
            existing_holding["current_price"] = price
            existing_holding["current_value"] = new_quantity * price
            existing_holding["profit_loss"] = existing_holding["current_value"] - new_cost_basis
            existing_holding["profit_loss_pct"] = (
                (existing_holding["current_value"] / new_cost_basis - 1) * 100 
                if new_cost_basis > 0 else 0
            )
            existing_holding["last_updated"] = datetime.now().isoformat()
        else:
            # Create new holding
            self.holdings.append({
                "token_symbol": token_symbol,
                "token_name": token["name"],
                "quantity": quantity,
                "avg_price": price,
                "cost_basis": amount_usd,
                "current_price": price,
                "current_value": amount_usd,
                "profit_loss": 0,
                "profit_loss_pct": 0,
                "purchase_date": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            })
        
        # Add to trade history
        trade_id = len(self.trade_history) + 1
        self.trade_history.append({
            "id": trade_id,
            "type": "BUY",
            "token_symbol": token_symbol,
            "token_name": token["name"],
            "quantity": quantity,
            "price": price,
            "amount_usd": amount_usd,
            "timestamp": datetime.now().isoformat(),
            "status": "COMPLETED",
            "transaction_hash": f"demo_tx_{trade_id}"
        })
        
        logger.info(f"Demo mode: Bought {quantity} {token_symbol} for ${amount_usd}")
        
        return {
            "success": True,
            "trade_id": trade_id,
            "token_symbol": token_symbol,
            "quantity": quantity,
            "price": price,
            "amount_usd": amount_usd,
            "transaction_hash": f"demo_tx_{trade_id}"
        }
    
    def execute_sell(self, token_symbol, quantity=None, percent=None):
        """Execute a sell order in demo mode"""
        if not self.active:
            return {"success": False, "error": "Demo mode is not active"}
        
        # Find holding
        holding = next((h for h in self.holdings if h["token_symbol"] == token_symbol), None)
        if not holding:
            return {"success": False, "error": f"No holdings found for {token_symbol}"}
        
        # Determine quantity to sell
        available_quantity = holding["quantity"]
        
        if quantity is not None:
            sell_quantity = min(quantity, available_quantity)
        elif percent is not None:
            sell_quantity = available_quantity * (percent / 100)
        else:
            sell_quantity = available_quantity
        
        if sell_quantity <= 0:
            return {"success": False, "error": "Sell quantity must be greater than zero"}
        
        # Find token
        token = next((t for t in self.virtual_tokens if t["symbol"] == token_symbol), None)
        if not token:
            return {"success": False, "error": f"Token {token_symbol} not found"}
        
        # Calculate amount
        price = token["price_usd"]
        amount_usd = sell_quantity * price
        
        # Update available capital
        self.available_capital += amount_usd
        
        # Update holding
        if sell_quantity >= available_quantity * 0.9999:  # Allow for floating point imprecision
            # Remove holding if selling all
            self.holdings = [h for h in self.holdings if h["token_symbol"] != token_symbol]
        else:
            # Update holding if selling partial
            sell_ratio = sell_quantity / available_quantity
            cost_basis_sold = holding["cost_basis"] * sell_ratio
            
            holding["quantity"] -= sell_quantity
            holding["cost_basis"] -= cost_basis_sold
            holding["current_value"] = holding["quantity"] * price
            holding["profit_loss"] = holding["current_value"] - holding["cost_basis"]
            holding["profit_loss_pct"] = (
                (holding["current_value"] / holding["cost_basis"] - 1) * 100 
                if holding["cost_basis"] > 0 else 0
            )
            holding["last_updated"] = datetime.now().isoformat()
        
        # Add to trade history
        trade_id = len(self.trade_history) + 1
        self.trade_history.append({
            "id": trade_id,
            "type": "SELL",
            "token_symbol": token_symbol,
            "token_name": token["name"],
            "quantity": sell_quantity,
            "price": price,
            "amount_usd": amount_usd,
            "timestamp": datetime.now().isoformat(),
            "status": "COMPLETED",
            "transaction_hash": f"demo_tx_{trade_id}"
        })
        
        logger.info(f"Demo mode: Sold {sell_quantity} {token_symbol} for ${amount_usd}")
        
        return {
            "success": True,
            "trade_id": trade_id,
            "token_symbol": token_symbol,
            "quantity": sell_quantity,
            "price": price,
            "amount_usd": amount_usd,
            "transaction_hash": f"demo_tx_{trade_id}"
        }
    
    def get_holdings(self):
        """Get current holdings"""
        return self.holdings
    
    def get_trade_history(self, limit=None):
        """Get trade history"""
        history = sorted(self.trade_history, key=lambda t: t["timestamp"], reverse=True)
        
        if limit:
            return history[:limit]
        
        return history
    
    def get_token_price_history(self, token_symbol, days=7):
        """Generate simulated price history for a token"""
        token = next((t for t in self.virtual_tokens if t["symbol"] == token_symbol), None)
        if not token:
            return []
        
        # Generate price history
        current_price = token["price_usd"]
        volatility = token.get("volatility", 1.0)
        
        # Start from current price and work backwards
        prices = [current_price]
        timestamps = [datetime.now()]
        
        # Generate hourly data points
        hours = days * 24
        for i in range(1, hours + 1):
            # More volatility for older prices to create a realistic chart
            time_factor = 1 + (i / hours)
            change_pct = random.normalvariate(0, volatility * time_factor)
            
            # Apply change to previous price
            prev_price = prices[-1]
            new_price = prev_price / (1 + (change_pct / 100))
            
            # Ensure price doesn't go negative or too low
            prices.append(max(new_price, 0.0000000001))
            timestamps.append(datetime.now() - timedelta(hours=i))
        
        # Reverse to get chronological order
        prices.reverse()
        timestamps.reverse()
        
        # Format for return
        return [
            {"timestamp": ts.isoformat(), "price": p}
            for ts, p in zip(timestamps, prices)
        ]
    
    def is_active(self):
        """Check if demo mode is active"""
        return self.active


class DemoModePage(ttk.Frame):
    """Demo Mode Page for the trading bot UI"""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.demo_manager = controller.demo_manager if hasattr(controller, "demo_manager") else DemoModeManager()
        
        # Create main container with padding
        main_container = ttk.Frame(self, padding="20 20 20 20")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(
            title_frame, 
            text="Demo Trading Mode", 
            font=("Helvetica", 18, "bold"),
            foreground="#3a7ca5"
        )
        title_label.pack(side=tk.LEFT)
        
        # Demo Mode Status
        self.status_var = tk.StringVar(value="INACTIVE")
        status_label = ttk.Label(
            title_frame,
            textvariable=self.status_var,
            font=("Helvetica", 12, "bold"),
            foreground="#e74c3c"
        )
        status_label.pack(side=tk.RIGHT)
        
        # Create a notebook for tabs
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.setup_tab = ttk.Frame(self.notebook, padding=10)
        self.trading_tab = ttk.Frame(self.notebook, padding=10)
        self.portfolio_tab = ttk.Frame(self.notebook, padding=10)
        self.history_tab = ttk.Frame(self.notebook, padding=10)
        
        self.notebook.add(self.setup_tab, text="Setup")
        self.notebook.add(self.trading_tab, text="Trading")
        self.notebook.add(self.portfolio_tab, text="Portfolio")
        self.notebook.add(self.history_tab, text="History")
        
        # Setup Tab
        self.create_setup_tab()
        
        # Trading Tab
        self.create_trading_tab()
        
        # Portfolio Tab
        self.create_portfolio_tab()
        
        # History Tab
        self.create_history_tab()
        
        # Update UI based on demo mode status
        self.update_ui_state()
        
        # Start periodic updates
        self.update_id = self.after(1000, self.periodic_update)
    
    def create_setup_tab(self):
        """Create the setup tab content"""
        # Description
        desc_frame = ttk.Frame(self.setup_tab)
        desc_frame.pack(fill=tk.X, pady=(0, 20))
        
        desc_label = ttk.Label(
            desc_frame,
            text="Demo Trading Mode allows you to practice trading with virtual funds. "
                 "You can test strategies and features without risking real money.",
            wraplength=600,
            justify=tk.LEFT
        )
        desc_label.pack(anchor=tk.W)
        
        # Settings
        settings_frame = ttk.LabelFrame(self.setup_tab, text="Demo Settings", padding=10)
        settings_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Initial Capital
        capital_frame = ttk.Frame(settings_frame)
        capital_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(capital_frame, text="Initial Capital ($):").pack(side=tk.LEFT, padx=(0, 10))
        
        self.initial_capital_var = tk.DoubleVar(value=200.0)
        initial_capital_entry = ttk.Entry(capital_frame, textvariable=self.initial_capital_var, width=10)
        initial_capital_entry.pack(side=tk.LEFT)
        
        # Target Value
        target_frame = ttk.Frame(settings_frame)
        target_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(target_frame, text="Target Value ($):").pack(side=tk.LEFT, padx=(0, 10))
        
        self.target_value_var = tk.DoubleVar(value=10000.0)
        target_value_entry = ttk.Entry(target_frame, textvariable=self.target_value_var, width=10)
        target_value_entry.pack(side=tk.LEFT)
        
        # Days Limit
        days_frame = ttk.Frame(settings_frame)
        days_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(days_frame, text="Days Limit:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.days_limit_var = tk.IntVar(value=10)
        days_limit_entry = ttk.Entry(days_frame, textvariable=self.days_limit_var, width=10)
        days_limit_entry.pack(side=tk.LEFT)
        
        # Control Buttons
        buttons_frame = ttk.Frame(self.setup_tab)
        buttons_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.start_button = ttk.Button(
            buttons_frame,
            text="Start Demo Mode",
            command=self.start_demo_mode,
            style="Accent.TButton"
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(
            buttons_frame,
            text="Stop Demo Mode",
            command=self.stop_demo_mode,
            state="disabled"
        )
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.reset_button = ttk.Button(
            buttons_frame,
            text="Reset Demo Mode",
            command=self.reset_demo_mode,
            state="disabled"
        )
        self.reset_button.pack(side=tk.LEFT)
        
        # Features
        features_frame = ttk.LabelFrame(self.setup_tab, text="Demo Mode Features", padding=10)
        features_frame.pack(fill=tk.BOTH, expand=True)
        
        features = [
            "✓ Trade with virtual funds without risk",
            "✓ Real-time market simulation with price movements",
            "✓ Full portfolio tracking and performance metrics",
            "✓ Complete trade history and analytics",
            "✓ Test different trading strategies",
            "✓ Practice using the trading bot interface",
            "✓ Experiment with different risk management settings"
        ]
        
        for feature in features:
            feature_label = ttk.Label(
                features_frame,
                text=feature,
                padding=(5, 3)
            )
            feature_label.pack(anchor=tk.W)
    
    def create_trading_tab(self):
        """Create the trading tab content"""
        # Split into left and right panes
        paned_window = ttk.PanedWindow(self.trading_tab, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Left pane - Token list
        left_frame = ttk.Frame(paned_window, padding=10)
        paned_window.add(left_frame, weight=1)
        
        # Search frame
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Search Tokens:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        search_button = ttk.Button(
            search_frame,
            text="Search",
            command=self.search_tokens
        )
        search_button.pack(side=tk.LEFT)
        
        # Token list frame
        token_list_frame = ttk.LabelFrame(left_frame, text="Available Tokens", padding=10)
        token_list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create token list with scrollbar
        token_list_container = ttk.Frame(token_list_frame)
        token_list_container.pack(fill=tk.BOTH, expand=True)
        
        columns = ("symbol", "name", "price", "change_24h")
        self.token_tree = ttk.Treeview(
            token_list_container,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=15
        )
        
        # Define headings
        self.token_tree.heading("symbol", text="Symbol")
        self.token_tree.heading("name", text="Name")
        self.token_tree.heading("price", text="Price ($)")
        self.token_tree.heading("change_24h", text="24h Change (%)")
        
        # Define columns
        self.token_tree.column("symbol", width=80, anchor=tk.W)
        self.token_tree.column("name", width=150, anchor=tk.W)
        self.token_tree.column("price", width=100, anchor=tk.E)
        self.token_tree.column("change_24h", width=100, anchor=tk.E)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(token_list_container, orient="vertical", command=self.token_tree.yview)
        self.token_tree.configure(yscrollcommand=scrollbar.set)
        
        self.token_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.token_tree.bind("<<TreeviewSelect>>", self.on_token_select)
        
        # Right pane - Token details and trading
        right_frame = ttk.Frame(paned_window, padding=10)
        paned_window.add(right_frame, weight=1)
        
        # Token details frame
        self.token_details_frame = ttk.LabelFrame(right_frame, text="Token Details", padding=10)
        self.token_details_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Token details content
        self.token_symbol_var = tk.StringVar()
        self.token_name_var = tk.StringVar()
        self.token_price_var = tk.StringVar()
        self.token_change_var = tk.StringVar()
        self.token_volume_var = tk.StringVar()
        self.token_liquidity_var = tk.StringVar()
        
        # Symbol and name
        header_frame = ttk.Frame(self.token_details_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.token_symbol_label = ttk.Label(
            header_frame,
            textvariable=self.token_symbol_var,
            font=("Helvetica", 14, "bold"),
            foreground="#3a7ca5"
        )
        self.token_symbol_label.pack(side=tk.LEFT)
        
        self.token_name_label = ttk.Label(
            header_frame,
            textvariable=self.token_name_var,
            font=("Helvetica", 12),
            foreground="#666666"
        )
        self.token_name_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Price and change
        price_frame = ttk.Frame(self.token_details_frame)
        price_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(price_frame, text="Price:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.token_price_label = ttk.Label(
            price_frame,
            textvariable=self.token_price_var,
            font=("Helvetica", 12, "bold")
        )
        self.token_price_label.pack(side=tk.LEFT)
        
        ttk.Label(price_frame, text="24h Change:").pack(side=tk.LEFT, padx=(20, 10))
        
        self.token_change_label = ttk.Label(
            price_frame,
            textvariable=self.token_change_var,
            font=("Helvetica", 12, "bold")
        )
        self.token_change_label.pack(side=tk.LEFT)
        
        # Volume and liquidity
        stats_frame = ttk.Frame(self.token_details_frame)
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
        
        # Trading frame
        trading_frame = ttk.LabelFrame(right_frame, text="Execute Trade", padding=10)
        trading_frame.pack(fill=tk.BOTH, expand=True)
        
        # Trade type
        type_frame = ttk.Frame(trading_frame)
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
        self.amount_frame = ttk.Frame(trading_frame)
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
        self.quantity_frame = ttk.Frame(trading_frame)
        
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
        summary_frame = ttk.Frame(trading_frame)
        summary_frame.pack(fill=tk.X, pady=(10, 10))
        
        ttk.Label(summary_frame, text="Trade Summary:").pack(anchor=tk.W)
        
        self.summary_text = tk.Text(summary_frame, height=5, width=40, wrap=tk.WORD, state=tk.DISABLED)
        self.summary_text.pack(fill=tk.X, pady=(5, 0))
        
        # Execute button
        button_frame = ttk.Frame(trading_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.execute_button = ttk.Button(
            button_frame,
            text="Execute Trade",
            command=self.execute_trade,
            style="Accent.TButton",
            state="disabled"
        )
        self.execute_button.pack(side=tk.RIGHT)
        
        # Initially hide quantity frame (buy is default)
        self.update_trade_form()
    
    def create_portfolio_tab(self):
        """Create the portfolio tab content"""
        # Summary frame
        summary_frame = ttk.LabelFrame(self.portfolio_tab, text="Portfolio Summary", padding=10)
        summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create a grid for summary values
        summary_grid = ttk.Frame(summary_frame)
        summary_grid.pack(fill=tk.X)
        
        # Row 1
        ttk.Label(summary_grid, text="Initial Capital:", anchor=tk.E, width=15).grid(row=0, column=0, padx=(0, 10), pady=2, sticky=tk.E)
        self.initial_capital_label = ttk.Label(summary_grid, text="$0.00", width=15)
        self.initial_capital_label.grid(row=0, column=1, padx=(0, 20), pady=2, sticky=tk.W)
        
        ttk.Label(summary_grid, text="Available Capital:", anchor=tk.E, width=15).grid(row=0, column=2, padx=(0, 10), pady=2, sticky=tk.E)
        self.available_capital_label = ttk.Label(summary_grid, text="$0.00", width=15)
        self.available_capital_label.grid(row=0, column=3, padx=(0, 20), pady=2, sticky=tk.W)
        
        ttk.Label(summary_grid, text="Holdings Value:", anchor=tk.E, width=15).grid(row=0, column=4, padx=(0, 10), pady=2, sticky=tk.E)
        self.holdings_value_label = ttk.Label(summary_grid, text="$0.00", width=15)
        self.holdings_value_label.grid(row=0, column=5, pady=2, sticky=tk.W)
        
        # Row 2
        ttk.Label(summary_grid, text="Total Value:", anchor=tk.E, width=15).grid(row=1, column=0, padx=(0, 10), pady=2, sticky=tk.E)
        self.total_value_label = ttk.Label(summary_grid, text="$0.00", font=("Helvetica", 10, "bold"), width=15)
        self.total_value_label.grid(row=1, column=1, padx=(0, 20), pady=2, sticky=tk.W)
        
        ttk.Label(summary_grid, text="Profit/Loss:", anchor=tk.E, width=15).grid(row=1, column=2, padx=(0, 10), pady=2, sticky=tk.E)
        self.profit_loss_label = ttk.Label(summary_grid, text="$0.00 (0.00%)", width=15)
        self.profit_loss_label.grid(row=1, column=3, padx=(0, 20), pady=2, sticky=tk.W)
        
        ttk.Label(summary_grid, text="Demo Duration:", anchor=tk.E, width=15).grid(row=1, column=4, padx=(0, 10), pady=2, sticky=tk.E)
        self.duration_label = ttk.Label(summary_grid, text="0d 00h 00m", width=15)
        self.duration_label.grid(row=1, column=5, pady=2, sticky=tk.W)
        
        # Progress bar
        progress_frame = ttk.Frame(summary_frame)
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
        
        # Holdings frame
        holdings_frame = ttk.LabelFrame(self.portfolio_tab, text="Current Holdings", padding=10)
        holdings_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create holdings table with scrollbar
        holdings_container = ttk.Frame(holdings_frame)
        holdings_container.pack(fill=tk.BOTH, expand=True)
        
        columns = ("symbol", "quantity", "avg_price", "current_price", "value", "profit_loss", "profit_loss_pct")
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
        
        # Define columns
        self.holdings_tree.column("symbol", width=80, anchor=tk.W)
        self.holdings_tree.column("quantity", width=100, anchor=tk.E)
        self.holdings_tree.column("avg_price", width=100, anchor=tk.E)
        self.holdings_tree.column("current_price", width=100, anchor=tk.E)
        self.holdings_tree.column("value", width=100, anchor=tk.E)
        self.holdings_tree.column("profit_loss", width=100, anchor=tk.E)
        self.holdings_tree.column("profit_loss_pct", width=80, anchor=tk.E)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(holdings_container, orient="vertical", command=self.holdings_tree.yview)
        self.holdings_tree.configure(yscrollcommand=scrollbar.set)
        
        self.holdings_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_history_tab(self):
        """Create the history tab content"""
        # Trade history frame
        history_frame = ttk.LabelFrame(self.history_tab, text="Trade History", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create history table with scrollbar
        history_container = ttk.Frame(history_frame)
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
        scrollbar = ttk.Scrollbar(history_container, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Statistics frame
        stats_frame = ttk.LabelFrame(self.history_tab, text="Trading Statistics", padding=10)
        stats_frame.pack(fill=tk.X)
        
        # Create a grid for statistics
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill=tk.X)
        
        # Row 1
        ttk.Label(stats_grid, text="Total Trades:", anchor=tk.E, width=15).grid(row=0, column=0, padx=(0, 10), pady=2, sticky=tk.E)
        self.total_trades_label = ttk.Label(stats_grid, text="0", width=10)
        self.total_trades_label.grid(row=0, column=1, padx=(0, 20), pady=2, sticky=tk.W)
        
        ttk.Label(stats_grid, text="Buy Trades:", anchor=tk.E, width=15).grid(row=0, column=2, padx=(0, 10), pady=2, sticky=tk.E)
        self.buy_trades_label = ttk.Label(stats_grid, text="0", width=10)
        self.buy_trades_label.grid(row=0, column=3, padx=(0, 20), pady=2, sticky=tk.W)
        
        ttk.Label(stats_grid, text="Sell Trades:", anchor=tk.E, width=15).grid(row=0, column=4, padx=(0, 10), pady=2, sticky=tk.E)
        self.sell_trades_label = ttk.Label(stats_grid, text="0", width=10)
        self.sell_trades_label.grid(row=0, column=5, pady=2, sticky=tk.W)
        
        # Row 2
        ttk.Label(stats_grid, text="Total Volume:", anchor=tk.E, width=15).grid(row=1, column=0, padx=(0, 10), pady=2, sticky=tk.E)
        self.total_volume_label = ttk.Label(stats_grid, text="$0.00", width=10)
        self.total_volume_label.grid(row=1, column=1, padx=(0, 20), pady=2, sticky=tk.W)
        
        ttk.Label(stats_grid, text="Avg. Trade Size:", anchor=tk.E, width=15).grid(row=1, column=2, padx=(0, 10), pady=2, sticky=tk.E)
        self.avg_trade_label = ttk.Label(stats_grid, text="$0.00", width=10)
        self.avg_trade_label.grid(row=1, column=3, padx=(0, 20), pady=2, sticky=tk.W)
        
        ttk.Label(stats_grid, text="Daily P/L:", anchor=tk.E, width=15).grid(row=1, column=4, padx=(0, 10), pady=2, sticky=tk.E)
        self.daily_pl_label = ttk.Label(stats_grid, text="$0.00", width=10)
        self.daily_pl_label.grid(row=1, column=5, pady=2, sticky=tk.W)
    
    def start_demo_mode(self):
        """Start demo trading mode"""
        try:
            initial_capital = self.initial_capital_var.get()
            
            if initial_capital <= 0:
                messagebox.showerror("Error", "Initial capital must be greater than zero")
                return
            
            # Start demo mode
            success = self.demo_manager.start_demo_mode(initial_capital)
            
            if success:
                # Update UI state
                self.status_var.set("ACTIVE")
                self.update_ui_state()
                
                # Load initial data
                self.load_tokens()
                self.update_portfolio_summary()
                self.update_holdings_table()
                self.update_history_table()
                self.update_trading_statistics()
                
                # Show success message
                messagebox.showinfo("Demo Mode", "Demo trading mode started successfully")
                
                # Switch to trading tab
                self.notebook.select(1)  # Index 1 is the trading tab
            else:
                messagebox.showerror("Error", "Failed to start demo mode")
        
        except Exception as e:
            logger.error(f"Error starting demo mode: {e}")
            messagebox.showerror("Error", f"Failed to start demo mode: {str(e)}")
    
    def stop_demo_mode(self):
        """Stop demo trading mode"""
        if messagebox.askyesno("Confirm", "Are you sure you want to stop demo mode? All virtual trades will be preserved."):
            try:
                success = self.demo_manager.stop_demo_mode()
                
                if success:
                    # Update UI state
                    self.status_var.set("INACTIVE")
                    self.update_ui_state()
                    
                    # Show success message
                    messagebox.showinfo("Demo Mode", "Demo trading mode stopped")
                else:
                    messagebox.showerror("Error", "Failed to stop demo mode")
            
            except Exception as e:
                logger.error(f"Error stopping demo mode: {e}")
                messagebox.showerror("Error", f"Failed to stop demo mode: {str(e)}")
    
    def reset_demo_mode(self):
        """Reset demo trading mode"""
        if messagebox.askyesno("Confirm", "Are you sure you want to reset demo mode? All virtual trades will be lost."):
            try:
                initial_capital = self.initial_capital_var.get()
                
                if initial_capital <= 0:
                    messagebox.showerror("Error", "Initial capital must be greater than zero")
                    return
                
                success = self.demo_manager.reset_demo_mode(initial_capital)
                
                if success:
                    # Update UI
                    self.load_tokens()
                    self.update_portfolio_summary()
                    self.update_holdings_table()
                    self.update_history_table()
                    self.update_trading_statistics()
                    
                    # Show success message
                    messagebox.showinfo("Demo Mode", "Demo trading mode reset successfully")
                else:
                    messagebox.showerror("Error", "Failed to reset demo mode")
            
            except Exception as e:
                logger.error(f"Error resetting demo mode: {e}")
                messagebox.showerror("Error", f"Failed to reset demo mode: {str(e)}")
    
    def update_ui_state(self):
        """Update UI state based on demo mode status"""
        is_active = self.demo_manager.is_active()
        
        # Update status label color
        if is_active:
            self.status_var.set("ACTIVE")
            self.status_var.set("ACTIVE")
            for widget in self.winfo_children():
                if isinstance(widget, ttk.Label) and widget.cget("textvariable") == str(self.status_var):
                    widget.configure(foreground="#2ecc71")
        else:
            self.status_var.set("INACTIVE")
            for widget in self.winfo_children():
                if isinstance(widget, ttk.Label) and widget.cget("textvariable") == str(self.status_var):
                    widget.configure(foreground="#e74c3c")
        
        # Update button states
        self.start_button.configure(state="disabled" if is_active else "normal")
        self.stop_button.configure(state="normal" if is_active else "disabled")
        self.reset_button.configure(state="normal" if is_active else "disabled")
        
        # Update trading controls
        self.execute_button.configure(state="normal" if is_active else "disabled")
        
        # Update notebook tabs
        for i in range(1, 4):  # Trading, Portfolio, History tabs
            self.notebook.tab(i, state="normal" if is_active else "disabled")
    
    def load_tokens(self):
        """Load tokens into the token list"""
        if not self.demo_manager.is_active():
            return
        
        # Clear existing items
        for item in self.token_tree.get_children():
            self.token_tree.delete(item)
        
        # Get tokens from demo manager
        tokens = self.demo_manager.get_available_tokens(count=20)
        
        # Add tokens to tree
        for token in tokens:
            symbol = token.get("symbol", "")
            name = token.get("name", "")
            price = token.get("price_usd", 0)
            change = token.get("price_change_24h", 0)
            
            # Format price based on value
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
            
            # Format change with color tag
            change_str = f"{change:.2f}"
            
            # Insert into tree
            item_id = self.token_tree.insert("", "end", values=(symbol, name, price_str, change_str))
            
            # Apply color to change column
            if change > 0:
                self.token_tree.item(item_id, tags=("positive",))
            elif change < 0:
                self.token_tree.item(item_id, tags=("negative",))
        
        # Configure tags
        self.token_tree.tag_configure("positive", foreground="#2ecc71")
        self.token_tree.tag_configure("negative", foreground="#e74c3c")
    
    def search_tokens(self):
        """Search for tokens based on search text"""
        if not self.demo_manager.is_active():
            return
        
        search_text = self.search_var.get()
        
        # Clear existing items
        for item in self.token_tree.get_children():
            self.token_tree.delete(item)
        
        # Get tokens from demo manager with filter
        tokens = self.demo_manager.get_available_tokens(count=20, filter_text=search_text)
        
        # Add tokens to tree
        for token in tokens:
            symbol = token.get("symbol", "")
            name = token.get("name", "")
            price = token.get("price_usd", 0)
            change = token.get("price_change_24h", 0)
            
            # Format price based on value
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
            
            # Format change with color tag
            change_str = f"{change:.2f}"
            
            # Insert into tree
            item_id = self.token_tree.insert("", "end", values=(symbol, name, price_str, change_str))
            
            # Apply color to change column
            if change > 0:
                self.token_tree.item(item_id, tags=("positive",))
            elif change < 0:
                self.token_tree.item(item_id, tags=("negative",))
    
    def on_token_select(self, event):
        """Handle token selection event"""
        if not self.demo_manager.is_active():
            return
        
        # Get selected item
        selection = self.token_tree.selection()
        if not selection:
            return
        
        # Get token data
        item = self.token_tree.item(selection[0])
        values = item["values"]
        
        if not values or len(values) < 4:
            return
        
        symbol = values[0]
        name = values[1]
        price_str = values[2]
        change_str = values[3]
        
        # Get full token data
        tokens = self.demo_manager.get_available_tokens(count=50)
        token = next((t for t in tokens if t["symbol"] == symbol), None)
        
        if not token:
            return
        
        # Update token details
        self.token_symbol_var.set(symbol)
        self.token_name_var.set(name)
        self.token_price_var.set(f"${price_str}")
        
        # Set change color
        change = float(change_str)
        if change > 0:
            self.token_change_var.set(f"+{change_str}%")
            self.token_change_label.configure(foreground="#2ecc71")
        elif change < 0:
            self.token_change_var.set(f"{change_str}%")
            self.token_change_label.configure(foreground="#e74c3c")
        else:
            self.token_change_var.set(f"{change_str}%")
            self.token_change_label.configure(foreground="#666666")
        
        # Format volume and liquidity
        volume = token.get("volume_24h", 0)
        liquidity = token.get("liquidity", 0)
        
        if volume >= 1_000_000:
            volume_str = f"${volume/1_000_000:.2f}M"
        elif volume >= 1_000:
            volume_str = f"${volume/1_000:.2f}K"
        else:
            volume_str = f"${volume:.2f}"
        
        if liquidity >= 1_000_000:
            liquidity_str = f"${liquidity/1_000_000:.2f}M"
        elif liquidity >= 1_000:
            liquidity_str = f"${liquidity/1_000:.2f}K"
        else:
            liquidity_str = f"${liquidity:.2f}"
        
        self.token_volume_var.set(volume_str)
        self.token_liquidity_var.set(liquidity_str)
        
        # Update trade form
        self.update_trade_form()
        
        # Enable execute button
        self.execute_button.configure(state="normal")
    
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
        if not self.demo_manager.is_active():
            return
        
        symbol = self.token_symbol_var.get()
        if not symbol:
            return
        
        # Get holdings
        holdings = self.demo_manager.get_holdings()
        holding = next((h for h in holdings if h["token_symbol"] == symbol), None)
        
        if holding:
            # Set max quantity
            self.quantity_var.set(holding["quantity"])
        else:
            # No holdings for this token
            self.quantity_var.set(0)
    
    def set_percentage(self, percentage):
        """Set amount as percentage of available capital"""
        if not self.demo_manager.is_active():
            return
        
        # Get portfolio summary
        summary = self.demo_manager.get_portfolio_summary()
        available_capital = summary["available_capital"]
        
        # Calculate amount
        amount = available_capital * (percentage / 100)
        
        # Update amount variable
        self.amount_var.set(round(amount, 2))
        
        # Update summary
        self.update_trade_summary()
    
    def set_sell_percentage(self, percentage):
        """Set sell quantity as percentage of holdings"""
        if not self.demo_manager.is_active():
            return
        
        symbol = self.token_symbol_var.get()
        if not symbol:
            return
        
        # Get holdings
        holdings = self.demo_manager.get_holdings()
        holding = next((h for h in holdings if h["token_symbol"] == symbol), None)
        
        if holding:
            # Calculate quantity
            quantity = holding["quantity"] * (percentage / 100)
            
            # Update quantity variable
            self.quantity_var.set(quantity)
            
            # Update summary
            self.update_trade_summary()
    
    def update_trade_summary(self):
        """Update trade summary based on current form values"""
        if not self.demo_manager.is_active():
            return
        
        symbol = self.token_symbol_var.get()
        if not symbol:
            return
        
        trade_type = self.trade_type_var.get()
        
        # Get token price
        tokens = self.demo_manager.get_available_tokens(count=50)
        token = next((t for t in tokens if t["symbol"] == symbol), None)
        
        if not token:
            return
        
        price = token["price_usd"]
        
        # Enable text widget for editing
        self.summary_text.configure(state=tk.NORMAL)
        self.summary_text.delete("1.0", tk.END)
        
        if trade_type == "BUY":
            # Get amount
            amount = self.amount_var.get()
            
            # Calculate quantity
            quantity = amount / price
            
            # Format summary
            summary = f"Buy {symbol}\n"
            summary += f"Amount: ${amount:.2f}\n"
            summary += f"Price: ${price:.8f}\n"
            summary += f"Quantity: {quantity:.8f}\n"
            
            # Check if amount is valid
            portfolio = self.demo_manager.get_portfolio_summary()
            if amount > portfolio["available_capital"]:
                summary += f"\nWARNING: Insufficient funds (${portfolio['available_capital']:.2f} available)"
                self.execute_button.configure(state="disabled")
            else:
                self.execute_button.configure(state="normal")
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
            holdings = self.demo_manager.get_holdings()
            holding = next((h for h in holdings if h["token_symbol"] == symbol), None)
            
            if not holding:
                summary += f"\nWARNING: No holdings for {symbol}"
                self.execute_button.configure(state="disabled")
            elif quantity > holding["quantity"]:
                summary += f"\nWARNING: Insufficient quantity ({holding['quantity']:.8f} available)"
                self.execute_button.configure(state="disabled")
            elif quantity <= 0:
                summary += f"\nWARNING: Quantity must be greater than zero"
                self.execute_button.configure(state="disabled")
            else:
                self.execute_button.configure(state="normal")
        
        # Update summary text
        self.summary_text.insert(tk.END, summary)
        
        # Disable text widget
        self.summary_text.configure(state=tk.DISABLED)
    
    def execute_trade(self):
        """Execute the trade"""
        if not self.demo_manager.is_active():
            return
        
        symbol = self.token_symbol_var.get()
        if not symbol:
            return
        
        trade_type = self.trade_type_var.get()
        
        try:
            if trade_type == "BUY":
                # Get amount
                amount = self.amount_var.get()
                
                # Execute buy
                result = self.demo_manager.execute_buy(symbol, amount)
                
                if result["success"]:
                    messagebox.showinfo("Trade Executed", f"Successfully bought {result['quantity']:.8f} {symbol} for ${result['amount_usd']:.2f}")
                    
                    # Update UI
                    self.update_portfolio_summary()
                    self.update_holdings_table()
                    self.update_history_table()
                    self.update_trading_statistics()
                else:
                    messagebox.showerror("Trade Failed", result.get("error", "Unknown error"))
            else:  # SELL
                # Get quantity
                quantity = self.quantity_var.get()
                
                # Execute sell
                result = self.demo_manager.execute_sell(symbol, quantity=quantity)
                
                if result["success"]:
                    messagebox.showinfo("Trade Executed", f"Successfully sold {result['quantity']:.8f} {symbol} for ${result['amount_usd']:.2f}")
                    
                    # Update UI
                    self.update_portfolio_summary()
                    self.update_holdings_table()
                    self.update_history_table()
                    self.update_trading_statistics()
                    
                    # Update sell quantity
                    self.update_sell_quantity()
                    
                    # Update trade summary
                    self.update_trade_summary()
                else:
                    messagebox.showerror("Trade Failed", result.get("error", "Unknown error"))
        
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            messagebox.showerror("Error", f"Failed to execute trade: {str(e)}")
    
    def update_portfolio_summary(self):
        """Update portfolio summary"""
        if not self.demo_manager.is_active():
            return
        
        # Get portfolio summary
        summary = self.demo_manager.get_portfolio_summary()
        
        # Update labels
        self.initial_capital_label.configure(text=f"${summary['initial_capital']:.2f}")
        self.available_capital_label.configure(text=f"${summary['available_capital']:.2f}")
        self.holdings_value_label.configure(text=f"${summary['holdings_value']:.2f}")
        self.total_value_label.configure(text=f"${summary['total_value']:.2f}")
        
        # Set profit/loss color
        profit_loss = summary["profit_loss"]
        profit_loss_pct = summary["profit_loss_pct"]
        
        if profit_loss > 0:
            self.profit_loss_label.configure(
                text=f"+${profit_loss:.2f} (+{profit_loss_pct:.2f}%)",
                foreground="#2ecc71"
            )
        elif profit_loss < 0:
            self.profit_loss_label.configure(
                text=f"-${abs(profit_loss):.2f} ({profit_loss_pct:.2f}%)",
                foreground="#e74c3c"
            )
        else:
            self.profit_loss_label.configure(
                text=f"${profit_loss:.2f} ({profit_loss_pct:.2f}%)",
                foreground="#666666"
            )
        
        # Update duration
        duration = summary["duration"]
        days = duration.days
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        
        self.duration_label.configure(text=f"{days}d {hours:02d}h {minutes:02d}m")
        
        # Update progress bar
        target_value = self.target_value_var.get()
        progress_pct = min(100, (summary["total_value"] / target_value) * 100)
        
        self.progress_var.set(progress_pct)
        self.progress_label.configure(text=f"{progress_pct:.2f}%")
    
    def update_holdings_table(self):
        """Update holdings table"""
        if not self.demo_manager.is_active():
            return
        
        # Clear existing items
        for item in self.holdings_tree.get_children():
            self.holdings_tree.delete(item)
        
        # Get holdings
        holdings = self.demo_manager.get_holdings()
        
        if not holdings:
            # Insert empty row
            self.holdings_tree.insert("", "end", values=("No holdings", "", "", "", "", "", ""))
            return
        
        # Add holdings to tree
        for holding in holdings:
            symbol = holding.get("token_symbol", "")
            quantity = holding.get("quantity", 0)
            avg_price = holding.get("avg_price", 0)
            current_price = holding.get("current_price", 0)
            value = holding.get("current_value", 0)
            profit_loss = holding.get("profit_loss", 0)
            profit_loss_pct = holding.get("profit_loss_pct", 0)
            
            # Format values
            quantity_str = f"{quantity:.8f}"
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
                values=(symbol, quantity_str, avg_price_str, current_price_str, value_str, profit_loss_str, profit_loss_pct_str),
                tags=(tag,)
            )
        
        # Configure tags
        self.holdings_tree.tag_configure("positive", foreground="#2ecc71")
        self.holdings_tree.tag_configure("negative", foreground="#e74c3c")
    
    def update_history_table(self):
        """Update trade history table"""
        if not self.demo_manager.is_active():
            return
        
        # Clear existing items
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Get trade history
        history = self.demo_manager.get_trade_history()
        
        if not history:
            # Insert empty row
            self.history_tree.insert("", "end", values=("", "No trades", "", "", "", "", "", ""))
            return
        
        # Add trades to tree
        for trade in history:
            trade_id = trade.get("id", "")
            timestamp_str = trade.get("timestamp", "")
            trade_type = trade.get("type", "")
            symbol = trade.get("token_symbol", "")
            quantity = trade.get("quantity", 0)
            price = trade.get("price", 0)
            amount = trade.get("amount_usd", 0)
            status = trade.get("status", "")
            
            # Format timestamp
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
            
            # Format values
            quantity_str = f"{quantity:.8f}"
            price_str = f"{price:.8f}"
            amount_str = f"{amount:.2f}"
            
            # Insert into tree with color tag
            tag = "buy" if trade_type == "BUY" else "sell"
            
            item_id = self.history_tree.insert(
                "", 0,  # Insert at the beginning (newest first)
                values=(trade_id, timestamp_str, trade_type, symbol, quantity_str, price_str, amount_str, status),
                tags=(tag,)
            )
        
        # Configure tags
        self.history_tree.tag_configure("buy", foreground="#2980b9")
        self.history_tree.tag_configure("sell", foreground="#e67e22")
    
    def update_trading_statistics(self):
        """Update trading statistics"""
        if not self.demo_manager.is_active():
            return
        
        # Get trade history
        history = self.demo_manager.get_trade_history()
        
        # Calculate statistics
        total_trades = len(history)
        buy_trades = sum(1 for trade in history if trade.get("type") == "BUY")
        sell_trades = sum(1 for trade in history if trade.get("type") == "SELL")
        
        total_volume = sum(trade.get("amount_usd", 0) for trade in history)
        avg_trade_size = total_volume / total_trades if total_trades > 0 else 0
        
        # Calculate daily P/L
        summary = self.demo_manager.get_portfolio_summary()
        duration_days = max(1, summary["duration"].total_seconds() / (24 * 3600))
        daily_pl = summary["profit_loss"] / duration_days
        
        # Update labels
        self.total_trades_label.configure(text=str(total_trades))
        self.buy_trades_label.configure(text=str(buy_trades))
        self.sell_trades_label.configure(text=str(sell_trades))
        
        self.total_volume_label.configure(text=f"${total_volume:.2f}")
        self.avg_trade_label.configure(text=f"${avg_trade_size:.2f}")
        
        # Set daily P/L color
        if daily_pl > 0:
            self.daily_pl_label.configure(
                text=f"+${daily_pl:.2f}",
                foreground="#2ecc71"
            )
        elif daily_pl < 0:
            self.daily_pl_label.configure(
                text=f"-${abs(daily_pl):.2f}",
                foreground="#e74c3c"
            )
        else:
            self.daily_pl_label.configure(
                text=f"${daily_pl:.2f}",
                foreground="#666666"
            )
    
    def periodic_update(self):
        """Periodic update function"""
        if self.demo_manager.is_active():
            # Update token list (less frequently)
            if hasattr(self, "update_counter"):
                self.update_counter += 1
                if self.update_counter >= 10:  # Update every 10 seconds
                    self.load_tokens()
                    self.update_counter = 0
            else:
                self.update_counter = 0
            
            # Update portfolio and holdings
            self.update_portfolio_summary()
            self.update_holdings_table()
            
            # Update trade summary if form is filled
            if self.token_symbol_var.get():
                self.update_trade_summary()
        
        # Schedule next update
        self.update_id = self.after(1000, self.periodic_update)
    
    def on_closing(self):
        """Handle window closing"""
        # Cancel periodic update
        if hasattr(self, "update_id"):
            self.after_cancel(self.update_id)
        
        # Stop demo mode if active
        if self.demo_manager.is_active():
            self.demo_manager.stop_demo_mode()
