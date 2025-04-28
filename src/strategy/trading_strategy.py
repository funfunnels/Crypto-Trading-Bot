import logging
import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import random

from src.utils.models import TokenInfo, TradingSignal, TradingSignalType, TradeExecution, Portfolio, RiskLevel
from src.analysis.signal_generator import SignalAggregator

logger = logging.getLogger(__name__)

class JupiterTrader:
    """Handles trading on Jupiter Exchange"""
    
    def __init__(self, private_key: Optional[str] = None):
        self.private_key = private_key
        self.jupiter_api_url = "https://quote-api.jup.ag/v6"
        
    async def get_token_price(self, token_address: str) -> float:
        """
        Get current price of a token in USD
        
        Args:
            token_address: The token address to get price for
            
        Returns:
            Current price in USD
        """
        # In a real implementation, this would make API calls to Jupiter
        # For this prototype, we'll simulate price data
        
        logger.info(f"Fetching price for token {token_address}")
        
        # Simulate API call delay
        await asyncio.sleep(0.2)
        
        # Generate a random price between 0.000001 and 0.1
        price = random.uniform(0.000001, 0.1)
        
        return price
    
    async def get_swap_quote(self, input_token: str, output_token: str, amount: float) -> Dict[str, Any]:
        """
        Get a swap quote from Jupiter
        
        Args:
            input_token: The input token address
            output_token: The output token address
            amount: The amount of input token to swap
            
        Returns:
            Swap quote data
        """
        # In a real implementation, this would make API calls to Jupiter
        # For this prototype, we'll simulate quote data
        
        logger.info(f"Getting swap quote for {amount} of {input_token} to {output_token}")
        
        # Simulate API call delay
        await asyncio.sleep(0.5)
        
        # SOL address
        sol_address = "So11111111111111111111111111111111111111112"
        
        # Generate a random output amount (simulate slippage and fees)
        output_amount = amount * random.uniform(0.97, 0.99)
        
        quote = {
            "inputMint": input_token if input_token != "SOL" else sol_address,
            "outputMint": output_token,
            "amount": str(int(amount * 1e9)),  # Convert to lamports
            "otherAmountThreshold": "0",
            "swapMode": "ExactIn",
            "slippageBps": 50,
            "route": [
                {
                    "marketInfos": [
                        {
                            "id": "random_market_id",
                            "label": "Raydium",
                            "inputMint": input_token if input_token != "SOL" else sol_address,
                            "outputMint": output_token,
                            "inAmount": str(int(amount * 1e9)),
                            "outAmount": str(int(output_amount * 1e9)),
                            "lpFee": {
                                "amount": "10000000",
                                "percent": 0.3
                            }
                        }
                    ],
                    "amount": str(int(amount * 1e9)),
                    "outAmount": str(int(output_amount * 1e9)),
                    "fee": {
                        "amount": "10000000",
                        "mint": input_token if input_token != "SOL" else sol_address,
                        "percent": 0.3
                    }
                }
            ],
            "outAmount": str(int(output_amount * 1e9)),
            "priceImpactPct": random.uniform(0.1, 2.0)
        }
        
        return quote
    
    async def execute_swap(self, quote: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a swap on Jupiter
        
        Args:
            quote: The swap quote to execute
            
        Returns:
            Transaction data
        """
        # In a real implementation, this would make API calls to Jupiter
        # For this prototype, we'll simulate transaction data
        
        logger.info(f"Executing swap with quote")
        
        # Simulate API call delay
        await asyncio.sleep(1.0)
        
        # Generate a random transaction hash
        tx_hash = ''.join(random.choices('0123456789abcdef', k=64))
        
        transaction = {
            "txid": tx_hash,
            "status": "confirmed",
            "inputAmount": quote["amount"],
            "outputAmount": quote["outAmount"],
            "timestamp": datetime.now().isoformat(),
            "fee": "0.000005",
            "blockhash": ''.join(random.choices('0123456789abcdef', k=64))
        }
        
        logger.info(f"Swap executed with transaction hash {tx_hash}")
        
        return transaction
    
    async def buy_token(self, token_address: str, amount_sol: float) -> Optional[TradeExecution]:
        """
        Buy a token with SOL
        
        Args:
            token_address: The token address to buy
            amount_sol: The amount of SOL to spend
            
        Returns:
            TradeExecution object if successful, None otherwise
        """
        try:
            # SOL address
            sol_address = "SOL"  # In a real implementation, use the actual SOL address
            
            # Get token price
            token_price = await self.get_token_price(token_address)
            
            # Get swap quote
            quote = await self.get_swap_quote(sol_address, token_address, amount_sol)
            
            # In a real implementation, we would check if the private key is set
            # and sign the transaction
            if not self.private_key:
                logger.warning("Private key not set, cannot execute trade")
                return None
            
            # Execute swap
            transaction = await self.execute_swap(quote)
            
            # Calculate token quantity
            quantity = float(quote["outAmount"]) / 1e9  # Convert from lamports
            
            # Create trade execution record
            trade = TradeExecution(
                token=TokenInfo(
                    symbol="UNKNOWN",  # We would fetch this in a real implementation
                    name="Unknown",
                    address=token_address,
                    price_usd=token_price
                ),
                trade_type=TradingSignalType.BUY,
                amount_usd=amount_sol * await self.get_token_price(sol_address),  # Convert SOL to USD
                quantity=quantity,
                price=token_price,
                timestamp=datetime.now(),
                transaction_hash=transaction["txid"],
                fee=float(transaction["fee"]),
                status="completed"
            )
            
            logger.info(f"Bought {quantity} of {token_address} for {amount_sol} SOL")
            
            return trade
            
        except Exception as e:
            logger.error(f"Error buying token: {e}")
            return None
    
    async def sell_token(self, token_address: str, quantity: float) -> Optional[TradeExecution]:
        """
        Sell a token for SOL
        
        Args:
            token_address: The token address to sell
            quantity: The quantity of token to sell
            
        Returns:
            TradeExecution object if successful, None otherwise
        """
        try:
            # SOL address
            sol_address = "SOL"  # In a real implementation, use the actual SOL address
            
            # Get token price
            token_price = await self.get_token_price(token_address)
            
            # Get swap quote
            quote = await self.get_swap_quote(token_address, sol_address, quantity)
            
            # In a real implementation, we would check if the private key is set
            # and sign the transaction
            if not self.private_key:
                logger.warning("Private key not set, cannot execute trade")
                return None
            
            # Execute swap
            transaction = await self.execute_swap(quote)
            
            # Calculate SOL amount received
            sol_amount = float(quote["outAmount"]) / 1e9  # Convert from lamports
            
            # Create trade execution record
            trade = TradeExecution(
                token=TokenInfo(
                    symbol="UNKNOWN",  # We would fetch this in a real implementation
                    name="Unknown",
                    address=token_address,
                    price_usd=token_price
                ),
                trade_type=TradingSignalType.SELL,
                amount_usd=sol_amount * await self.get_token_price(sol_address),  # Convert SOL to USD
                quantity=quantity,
                price=token_price,
                timestamp=datetime.now(),
                transaction_hash=transaction["txid"],
                fee=float(transaction["fee"]),
                status="completed"
            )
            
            logger.info(f"Sold {quantity} of {token_address} for {sol_amount} SOL")
            
            return trade
            
        except Exception as e:
            logger.error(f"Error selling token: {e}")
            return None


class PortfolioManager:
    """Manages the trading portfolio"""
    
    def __init__(self, initial_capital: float = 200.0):
        self.initial_capital = initial_capital
        self.available_capital = initial_capital
        self.holdings = []  # List of current token holdings
        self.trade_history = []  # List of trade executions
        self.last_updated = datetime.now()
    
    async def update_holdings_value(self, trader: JupiterTrader) -> None:
        """
        Update the current value of all holdings
        
        Args:
            trader: JupiterTrader instance to get token prices
        """
        for holding in self.holdings:
            token_price = await trader.get_token_price(holding["token_address"])
            holding["current_price"] = token_price
            holding["current_value"] = holding["quantity"] * token_price
            holding["profit_loss"] = holding["current_value"] - holding["cost_basis"]
            holding["profit_loss_percentage"] = (holding["profit_loss"] / holding["cost_basis"]) * 100 if holding["cost_basis"] > 0 else 0
        
        self.last_updated = datetime.now()
    
    def add_trade(self, trade: TradeExecution) -> None:
        """
        Add a trade to the portfolio
        
        Args:
            trade: TradeExecution object to add
        """
        self.trade_history.append(trade)
        
        if trade.trade_type == TradingSignalType.BUY:
            # Check if we already hold this token
            existing_holding = next((h for h in self.holdings if h["token_address"] == trade.token.address), None)
            
            if existing_holding:
                # Update existing holding
                total_quantity = existing_holding["quantity"] + trade.quantity
                total_cost = existing_holding["cost_basis"] + trade.amount_usd
                
                existing_holding["quantity"] = total_quantity
                existing_holding["cost_basis"] = total_cost
                existing_holding["average_price"] = total_cost / total_quantity
                existing_holding["current_price"] = trade.price
                existing_holding["current_value"] = total_quantity * trade.price
                existing_holding["last_updated"] = datetime.now()
            else:
                # Add new holding
                self.holdings.append({
                    "token_address": trade.token.address,
                    "token_symbol": trade.token.symbol,
                    "token_name": trade.token.name,
                    "quantity": trade.quantity,
                    "average_price": trade.price,
                    "cost_basis": trade.amount_usd,
                    "current_price": trade.price,
                    "current_value": trade.quantity * trade.price,
                    "profit_loss": 0,
                    "profit_loss_percentage": 0,
                    "purchase_date": trade.timestamp,
                    "last_updated": datetime.now()
                })
            
            # Update available capital
            self.available_capital -= trade.amount_usd
            
        elif trade.trade_type == TradingSignalType.SELL:
            # Find the holding
            existing_holding = next((h for h in self.holdings if h["token_address"] == trade.token.address), None)
            
            if existing_holding:
                # Update existing holding
                remaining_quantity = existing_holding["quantity"] - trade.quantity
                
                if remaining_quantity <= 0:
                    # Remove holding if fully sold
                    self.holdings = [h for h in self.holdings if h["token_address"] != trade.token.address]
                else:
                    # Update holding with remaining quantity
                    proportion_sold = trade.quantity / existing_holding["quantity"]
                    cost_basis_sold = existing_holding["cost_basis"] * proportion_sold
                    
                    existing_holding["quantity"] = remaining_quantity
                    existing_holding["cost_basis"] -= cost_basis_sold
                    existing_holding["current_value"] = remaining_quantity * trade.price
                    existing_holding["last_updated"] = datetime.now()
                
                # Update available capital
                self.available_capital += trade.amount_usd
    
    def get_portfolio(self) -> Portfolio:
        """
        Get the current portfolio state
        
        Returns:
            Portfolio object with current state
        """
        # Calculate total value
        holdings_value = sum(holding["current_value"] for holding in self.holdings)
        total_value = self.available_capital + holdings_value
        
        # Calculate profit/loss
        profit_loss = total_value - self.initial_capital
        profit_loss_percentage = (profit_loss / self.initial_capital) * 100 if self.initial_capital > 0 else 0
        
        return Portfolio(
            total_value_usd=total_value,
            initial_capital=self.initial_capital,
            available_capital=self.available_capital,
            profit_loss=profit_loss,
            profit_loss_percentage=profit_loss_percentage,
            holdings=self.holdings,
            trade_history=self.trade_history,
            updated_at=self.last_updated
        )


class TradingStrategy:
    """Implements the trading strategy"""
    
    def __init__(self, 
                 initial_capital: float = 200.0, 
                 target_value: float = 10000.0,
                 days_remaining: int = 10,
                 max_risk_per_trade: float = 0.15):
        self.signal_aggregator = SignalAggregator()
        self.trader = JupiterTrader()
        self.portfolio_manager = PortfolioManager(initial_capital)
        self.target_value = target_value
        self.days_remaining = days_remaining
        self.max_risk_per_trade = max_risk_per_trade
        self.last_signal_check = None
        
    async def add_tracked_wallet(self, wallet_address: str, name: Optional[str] = None) -> None:
        """
        Add a wallet to track for trading signals
        
        Args:
            wallet_address: The wallet address to track
            name: Optional name for the wallet
        """
        await self.signal_aggregator.add_tracked_wallet(wallet_address, name)
    
    def set_private_key(self, private_key: str) -> None:
        """
        Set the private key for trading
        
        Args:
            private_key: The private key to use for trading
        """
        self.trader.private_key = private_key
    
    async def get_trading_signals(self) -> List[TradingSignal]:
        """
        Get current trading signals
        
        Returns:
            List of TradingSignal objects
        """
        # Check if we need to refresh signals (cache for 30 minutes)
        current_time = datetime.now()
        if self.last_signal_check and (current_time - self.last_signal_check) < timedelta(minutes=30):
            logger.info("Using cached trading signals")
            return self.cached_signals
        
        # Get fresh signals
        signals = await self.signal_aggregator.get_trading_signals()
        
        # Update signal cache
        self.cached_signals = signals
        self.last_signal_check = current_time
        
        return signals
    
    async def update_portfolio(self) -> Portfolio:
        """
        Update the portfolio with current values
        
        Returns:
            Updated Portfolio object
        """
        await self.portfolio_manager.update_holdings_value(self.trader)
        return self.portfolio_manager.get_portfolio()
    
    def calculate_position_size(self, signal: TradingSignal) -> float:
        """
        Calculate the position size for a trade based on the signal
        
        Args:
            signal: TradingSignal object
            
        Returns:
            Amount in USD to trade
        """
        portfolio = self.portfolio_manager.get_portfolio()
        available_capital = portfolio.available_capital
        
        # Base position size on risk level and confidence
        base_percentage = self.max_risk_per_trade
        
        # Adjust based on risk level
        if signal.risk_level == RiskLevel.LOW:
            risk_multiplier = 1.2
        elif signal.risk_level == RiskLevel.MEDIUM:
            risk_multiplier = 1.0
        elif signal.risk_level == RiskLevel.HIGH:
            risk_multiplier = 0.8
        else:  # VERY_HIGH
            risk_multiplier = 0.5
        
        # Adjust based on confidence
        confidence_multiplier = signal.confidence
        
        # Adjust based on days remaining (more aggressive as deadline approaches)
        days_multiplier = 1.0 + max(0, (10 - self.days_remaining) / 10)
        
        # Adjust based on progress toward target
        progress = portfolio.total_value_usd / self.target_value
        progress_multiplier = 1.0
        
        if progress < 0.3:
            # Early stages, be more aggressive
            progress_multiplier = 1.2
        elif progress > 0.7:
            # Later stages, be more conservative to protect gains
            progress_multiplier = 0.8
        
        # Calculate final percentage
        percentage = base_percentage * risk_multiplier * confidence_multiplier * days_multiplier * progress_multiplier
        
        # Cap at 50% of available capital
        percentage = min(percentage, 0.5)
        
        # Calculate amount
        amount = available_capital * percentage
        
        logger.info(f"Calculated position size: ${amount:.2f} ({percentage:.2%} of ${available_capital:.2f})")
        
        return amount
    
    async def execute_buy_signal(self, signal: TradingSignal) -> Optional[TradeExecution]:
        """
        Execute a buy signal
        
        Args:
            signal: TradingSignal object to execute
            
        Returns:
            TradeExecution object if successful, None otherwise
        """
        # Calculate position size
        position_size_usd = self.calculate_position_size(signal)
        
        # Get SOL price
        sol_price = await self.trader.get_token_price("SOL")
        
        # Convert USD to SOL
        position_size_sol = position_size_usd / sol_price
        
        # Execute buy
        trade = await self.trader.buy_token(signal.token.address, position_size_sol)
        
        if trade:
            # Update portfolio
            self.portfolio_manager.add_trade(trade)
            logger.info(f"Executed buy signal for {signal.token.symbol} with ${position_size_usd:.2f}")
        
        return trade
    
    async def check_sell_conditions(self) -> List[Tuple[Dict[str, Any], str]]:
        """
        Check if any holdings meet sell conditions
        
        Returns:
            List of (holding, reason) tuples for holdings that should be sold
        """
        portfolio = await self.update_portfolio()
        to_sell = []
        
        for holding in portfolio.holdings:
            # Skip if no profit/loss data
            if "profit_loss_percentage" not in holding:
                continue
            
            reason = None
            
            # Check take profit condition (50% or more profit)
            if holding["profit_loss_percentage"] >= 50:
                reason = f"Take profit triggered at {holding['profit_loss_percentage']:.2f}% gain"
            
            # Check stop loss condition (15% or more loss)
            elif holding["profit_loss_percentage"] <= -15:
                reason = f"Stop loss triggered at {holding['profit_loss_percentage']:.2f}% loss"
            
            # Check time-based condition (held for more than 2 days with less than 20% profit)
            elif (datetime.now() - holding["purchase_date"]).days >= 2 and holding["profit_loss_percentage"] < 20:
                reason = f"Time-based exit after 2+ days with only {holding['profit_loss_percentage']:.2f}% gain"
            
            if reason:
                to_sell.append((holding, reason))
        
        return to_sell
    
    async def execute_sell(self, holding: Dict[str, Any], reason: str) -> Optional[TradeExecution]:
        """
        Sell a holding
        
        Args:
            holding: Holding dictionary to sell
            reason: Reason for selling
            
        Returns:
            TradeExecution object if successful, None otherwise
        """
        # Execute sell
        trade = await self.trader.sell_token(holding["token_address"], holding["quantity"])
        
        if trade:
            # Add reason to trade metadata
            if trade.metadata is None:
                trade.metadata = {}
            trade.metadata["sell_reason"] = reason
            
            # Update portfolio
            self.portfolio_manager.add_trade(trade)
            logger.info(f"Sold {holding['token_symbol']} for ${trade.amount_usd:.2f}. Reason: {reason}")
        
        return trade
    
    async def get_recommended_actions(self) -> Dict[str, Any]:
        """
        Get recommended trading actions
        
        Returns:
            Dictionary with recommended actions
        """
        # Update portfolio
        portfolio = await self.update_portfolio()
        
        # Check sell conditions
        sell_recommendations = await self.check_sell_conditions()
        
        # Get buy signals
        buy_signals = await self.get_trading_signals()
        
        # Filter buy signals based on available capital and existing holdings
        filtered_buy_signals = []
        
        for signal in buy_signals:
            # Skip if signal is not a buy
            if signal.signal_type != TradingSignalType.BUY:
                continue
            
            # Skip if we already hold this token
            if any(h["token_address"] == signal.token.address for h in portfolio.holdings):
                continue
            
            # Skip if confidence is too low
            if signal.confidence < 0.4:
                continue
            
            # Calculate position size
            position_size = self.calculate_position_size(signal)
            
            # Skip if position size is too small
            if position_size < 10:
                continue
            
            # Add position size to signal metadata
            if signal.metadata is None:
                signal.metadata = {}
            signal.metadata["recommended_position_size"] = position_size
            
            filtered_buy_signals.append(signal)
        
        # Calculate progress metrics
        daily_target = self.target_value / 10  # $1,000 per day
        days_elapsed = 10 - self.days_remaining
        expected_value = self.initial_capital + (daily_target * days_elapsed)
        value_difference = portfolio.total_value_usd - expected_value
        on_track = value_difference >= 0
        
        # Calculate required daily growth for remaining days
        if self.days_remaining > 0:
            required_daily_growth = ((self.target_value / portfolio.total_value_usd) ** (1 / self.days_remaining)) - 1
        else:
            required_daily_growth = 0
        
        return {
            "portfolio": portfolio,
            "sell_recommendations": sell_recommendations,
            "buy_signals": filtered_buy_signals,
            "progress": {
                "days_remaining": self.days_remaining,
                "current_value": portfolio.total_value_usd,
                "target_value": self.target_value,
                "progress_percentage": (portfolio.total_value_usd / self.target_value) * 100,
                "expected_value": expected_value,
                "value_difference": value_difference,
                "on_track": on_track,
                "required_daily_growth": required_daily_growth * 100  # Convert to percentage
            }
        }


# Example usage
async def main():
    # Create trading strategy
    strategy = TradingStrategy(initial_capital=200.0, target_value=10000.0, days_remaining=10)
    
    # Add some wallets to track
    await strategy.add_tracked_wallet("5ZWj7a1f8tWkjBESHKgrLmZhGh7yBR8Cmjw6aQGhRTMQ", "Whale 1")
    await strategy.add_tracked_wallet("7NsngNMtXJNdHgeK4znQDZ5PJ19ykVvQvEF7BT5KFjMv", "Whale 2")
    
    # Set private key (would be loaded from config in real implementation)
    strategy.set_private_key("dummy_private_key")
    
    # Get recommended actions
    recommendations = await strategy.get_recommended_actions()
    
    # Print portfolio summary
    portfolio = recommendations["portfolio"]
    print(f"Portfolio Summary:")
    print(f"Total Value: ${portfolio.total_value_usd:.2f}")
    print(f"Initial Capital: ${portfolio.initial_capital:.2f}")
    print(f"Available Capital: ${portfolio.available_capital:.2f}")
    print(f"Profit/Loss: ${portfolio.profit_loss:.2f} ({portfolio.profit_loss_percentage:.2f}%)")
    
    # Print progress
    progress = recommendations["progress"]
    print(f"\nProgress:")
    print(f"Days Remaining: {progress['days_remaining']}")
    print(f"Progress: ${progress['current_value']:.2f} / ${progress['target_value']:.2f} ({progress['progress_percentage']:.2f}%)")
    print(f"On Track: {progress['on_track']}")
    print(f"Required Daily Growth: {progress['required_daily_growth']:.2f}%")
    
    # Print sell recommendations
    sell_recommendations = recommendations["sell_recommendations"]
    print(f"\nSell Recommendations ({len(sell_recommendations)}):")
    
    for holding, reason in sell_recommendations:
        print(f"- {holding['token_symbol']}: {holding['quantity']} tokens, ${holding['current_value']:.2f}")
        print(f"  Reason: {reason}")
    
    # Print buy signals
    buy_signals = recommendations["buy_signals"]
    print(f"\nBuy Signals ({len(buy_signals)}):")
    
    for signal in buy_signals:
        position_size = signal.metadata.get("recommended_position_size", 0)
        print(f"- {signal.token.name} ({signal.token.symbol})")
        print(f"  Confidence: {signal.confidence:.2f}")
        print(f"  Risk Level: {signal.risk_level.value}")
        print(f"  Recommended Position: ${position_size:.2f}")
        print(f"  Reasoning: {signal.reasoning}")

if __name__ == "__main__":
    asyncio.run(main())
