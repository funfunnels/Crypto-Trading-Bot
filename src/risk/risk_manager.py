import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import math

from src.utils.models import Portfolio, TokenInfo, TradeExecution, RiskLevel
from src.strategy.trading_strategy import TradingStrategy

logger = logging.getLogger(__name__)

class RiskManager:
    """Manages risk for the trading bot"""
    
    def __init__(self, 
                 strategy: TradingStrategy,
                 max_daily_loss: float = 0.2,  # 20% max daily loss
                 max_drawdown: float = 0.3,    # 30% max drawdown
                 max_risk_per_trade: float = 0.15,  # 15% max risk per trade
                 max_portfolio_risk: float = 0.5):  # 50% max portfolio risk
        self.strategy = strategy
        self.max_daily_loss = max_daily_loss
        self.max_drawdown = max_drawdown
        self.max_risk_per_trade = max_risk_per_trade
        self.max_portfolio_risk = max_portfolio_risk
        self.daily_high_value = 0
        self.all_time_high = 0
        self.last_day_reset = datetime.now().date()
        self.daily_trades = []
        self.risk_metrics = {}
    
    async def update_risk_metrics(self) -> Dict[str, Any]:
        """
        Update risk metrics based on current portfolio
        
        Returns:
            Dictionary of risk metrics
        """
        # Get current portfolio
        portfolio = await self.strategy.update_portfolio()
        current_value = portfolio.total_value_usd
        
        # Check if we need to reset daily metrics
        current_date = datetime.now().date()
        if current_date > self.last_day_reset:
            self.daily_high_value = current_value
            self.last_day_reset = current_date
            self.daily_trades = []
            logger.info(f"Reset daily risk metrics for {current_date}")
        
        # Update high values
        if current_value > self.daily_high_value:
            self.daily_high_value = current_value
        
        if current_value > self.all_time_high:
            self.all_time_high = current_value
        
        # Calculate drawdowns
        daily_drawdown = 0
        if self.daily_high_value > 0:
            daily_drawdown = (self.daily_high_value - current_value) / self.daily_high_value
        
        max_drawdown = 0
        if self.all_time_high > 0:
            max_drawdown = (self.all_time_high - current_value) / self.all_time_high
        
        # Calculate daily P&L
        daily_pl = 0
        daily_pl_percentage = 0
        
        if len(self.daily_trades) > 0:
            daily_pl = sum(trade.amount_usd if trade.trade_type.value == "SELL" else -trade.amount_usd 
                          for trade in self.daily_trades)
            daily_pl_percentage = daily_pl / (current_value - daily_pl) if (current_value - daily_pl) > 0 else 0
        
        # Calculate portfolio risk exposure
        total_risk_exposure = 0
        for holding in portfolio.holdings:
            # Calculate potential loss if stop loss is hit (15% per position)
            potential_loss = holding["current_value"] * 0.15
            total_risk_exposure += potential_loss
        
        portfolio_risk_percentage = total_risk_exposure / current_value if current_value > 0 else 0
        
        # Calculate required daily growth
        days_remaining = self.strategy.days_remaining
        target_value = self.strategy.target_value
        
        if days_remaining > 0 and current_value > 0:
            required_daily_growth = ((target_value / current_value) ** (1 / days_remaining)) - 1
        else:
            required_daily_growth = 0
        
        # Calculate risk budget based on required growth
        # Higher required growth = higher risk budget
        base_risk_budget = self.max_risk_per_trade
        growth_factor = min(required_daily_growth * 10, 2)  # Cap at 2x
        adjusted_risk_budget = base_risk_budget * max(1, growth_factor)
        
        # Cap at max_risk_per_trade
        risk_budget = min(adjusted_risk_budget, self.max_risk_per_trade * 2)
        
        # Store and return metrics
        self.risk_metrics = {
            "current_value": current_value,
            "daily_high_value": self.daily_high_value,
            "all_time_high": self.all_time_high,
            "daily_drawdown": daily_drawdown * 100,  # Convert to percentage
            "max_drawdown": max_drawdown * 100,  # Convert to percentage
            "daily_pl": daily_pl,
            "daily_pl_percentage": daily_pl_percentage * 100,  # Convert to percentage
            "portfolio_risk_exposure": total_risk_exposure,
            "portfolio_risk_percentage": portfolio_risk_percentage * 100,  # Convert to percentage
            "required_daily_growth": required_daily_growth * 100,  # Convert to percentage
            "risk_budget": risk_budget * 100,  # Convert to percentage
            "max_daily_loss": self.max_daily_loss * 100,  # Convert to percentage
            "max_drawdown_limit": self.max_drawdown * 100,  # Convert to percentage
            "max_risk_per_trade": self.max_risk_per_trade * 100,  # Convert to percentage
            "max_portfolio_risk": self.max_portfolio_risk * 100,  # Convert to percentage
            "last_updated": datetime.now().isoformat()
        }
        
        return self.risk_metrics
    
    def record_trade(self, trade: TradeExecution) -> None:
        """
        Record a trade for risk tracking
        
        Args:
            trade: TradeExecution object to record
        """
        self.daily_trades.append(trade)
        logger.info(f"Recorded {trade.trade_type.value} trade for risk tracking: ${trade.amount_usd:.2f}")
    
    async def check_risk_limits(self) -> Tuple[bool, Optional[str]]:
        """
        Check if any risk limits are exceeded
        
        Returns:
            Tuple of (limits_ok, reason) where limits_ok is True if all limits are ok,
            and reason is a string explaining why limits are exceeded (if applicable)
        """
        # Update risk metrics
        metrics = await self.update_risk_metrics()
        
        # Check daily loss limit
        if metrics["daily_pl_percentage"] <= -self.max_daily_loss * 100:
            return False, f"Daily loss limit exceeded: {metrics['daily_pl_percentage']:.2f}% (limit: {-self.max_daily_loss * 100:.2f}%)"
        
        # Check max drawdown
        if metrics["max_drawdown"] >= self.max_drawdown * 100:
            return False, f"Maximum drawdown exceeded: {metrics['max_drawdown']:.2f}% (limit: {self.max_drawdown * 100:.2f}%)"
        
        # Check portfolio risk exposure
        if metrics["portfolio_risk_percentage"] >= self.max_portfolio_risk * 100:
            return False, f"Portfolio risk exposure too high: {metrics['portfolio_risk_percentage']:.2f}% (limit: {self.max_portfolio_risk * 100:.2f}%)"
        
        return True, None
    
    async def adjust_position_size(self, base_size: float, risk_level: RiskLevel) -> float:
        """
        Adjust position size based on risk metrics
        
        Args:
            base_size: Base position size calculated by strategy
            risk_level: Risk level of the trade
            
        Returns:
            Adjusted position size
        """
        # Update risk metrics
        metrics = await self.update_risk_metrics()
        
        # Start with base size
        adjusted_size = base_size
        
        # Adjust based on portfolio risk exposure
        portfolio_risk_factor = 1.0
        if metrics["portfolio_risk_percentage"] > 30:
            # Reduce position size as portfolio risk increases
            portfolio_risk_factor = 1.0 - ((metrics["portfolio_risk_percentage"] - 30) / 70)
            portfolio_risk_factor = max(0.5, portfolio_risk_factor)  # Don't go below 50%
        
        # Adjust based on daily P&L
        daily_pl_factor = 1.0
        if metrics["daily_pl_percentage"] < 0:
            # Reduce position size if we're down for the day
            daily_pl_factor = 1.0 - min(0.5, abs(metrics["daily_pl_percentage"]) / 100)
        elif metrics["daily_pl_percentage"] > 20:
            # Increase position size if we're up significantly for the day
            daily_pl_factor = 1.0 + min(0.5, (metrics["daily_pl_percentage"] - 20) / 100)
        
        # Adjust based on drawdown
        drawdown_factor = 1.0
        if metrics["max_drawdown"] > 10:
            # Reduce position size as drawdown increases
            drawdown_factor = 1.0 - ((metrics["max_drawdown"] - 10) / 90)
            drawdown_factor = max(0.5, drawdown_factor)  # Don't go below 50%
        
        # Adjust based on risk level
        risk_level_factor = 1.0
        if risk_level == RiskLevel.LOW:
            risk_level_factor = 1.2
        elif risk_level == RiskLevel.MEDIUM:
            risk_level_factor = 1.0
        elif risk_level == RiskLevel.HIGH:
            risk_level_factor = 0.8
        else:  # VERY_HIGH
            risk_level_factor = 0.6
        
        # Adjust based on progress toward target
        progress_factor = 1.0
        portfolio = await self.strategy.update_portfolio()
        progress = portfolio.total_value_usd / self.strategy.target_value
        
        if progress < 0.3:
            # Early stages, be more aggressive
            progress_factor = 1.2
        elif progress > 0.7:
            # Later stages, be more conservative to protect gains
            progress_factor = 0.8
        
        # Apply all factors
        adjusted_size = adjusted_size * portfolio_risk_factor * daily_pl_factor * drawdown_factor * risk_level_factor * progress_factor
        
        # Ensure we don't exceed available capital
        adjusted_size = min(adjusted_size, portfolio.available_capital * 0.95)
        
        logger.info(f"Adjusted position size from ${base_size:.2f} to ${adjusted_size:.2f}")
        logger.info(f"Adjustment factors: portfolio_risk={portfolio_risk_factor:.2f}, daily_pl={daily_pl_factor:.2f}, " +
                   f"drawdown={drawdown_factor:.2f}, risk_level={risk_level_factor:.2f}, progress={progress_factor:.2f}")
        
        return adjusted_size
    
    async def calculate_optimal_stop_loss(self, token_info: TokenInfo, entry_price: float) -> float:
        """
        Calculate optimal stop loss price based on token volatility and risk metrics
        
        Args:
            token_info: TokenInfo object
            entry_price: Entry price for the trade
            
        Returns:
            Recommended stop loss price
        """
        # Get volatility estimate from token price history
        # In a real implementation, we would analyze price history
        # For this prototype, we'll use a simple approach based on metadata
        
        volatility = 0.15  # Default 15% volatility
        
        if token_info.metadata:
            # If we have price change data, use it to estimate volatility
            price_change_24h = abs(token_info.price_change_24h or 0)
            price_change_1h = abs(token_info.metadata.get("price_change_1h", 0))
            
            if price_change_1h > 0:
                hourly_volatility = price_change_1h / 100
                volatility = min(hourly_volatility * 4, 0.3)  # Cap at 30%
            elif price_change_24h > 0:
                daily_volatility = price_change_24h / 100
                volatility = min(daily_volatility / 6, 0.3)  # Cap at 30%
        
        # Adjust based on risk metrics
        metrics = await self.update_risk_metrics()
        
        # Base stop loss percentage
        base_stop_percentage = volatility * 1.5  # 1.5x volatility
        
        # Adjust based on portfolio risk
        if metrics["portfolio_risk_percentage"] > 30:
            # Tighter stop loss if portfolio risk is high
            base_stop_percentage = base_stop_percentage * 0.8
        
        # Adjust based on progress toward target
        portfolio = await self.strategy.update_portfolio()
        progress = portfolio.total_value_usd / self.strategy.target_value
        
        if progress > 0.7:
            # Tighter stop loss if we're close to target
            base_stop_percentage = base_stop_percentage * 0.8
        
        # Cap stop loss percentage
        stop_percentage = min(base_stop_percentage, 0.2)  # Max 20% stop loss
        
        # Calculate stop loss price
        stop_loss_price = entry_price * (1 - stop_percentage)
        
        logger.info(f"Calculated stop loss for {token_info.symbol}: ${stop_loss_price:.8f} " +
                   f"({stop_percentage:.2%} below entry price of ${entry_price:.8f})")
        
        return stop_loss_price
    
    async def calculate_take_profit_levels(self, token_info: TokenInfo, entry_price: float) -> List[Dict[str, float]]:
        """
        Calculate multiple take profit levels
        
        Args:
            token_info: TokenInfo object
            entry_price: Entry price for the trade
            
        Returns:
            List of dictionaries with price and percentage of position to sell
        """
        # Get volatility estimate
        volatility = 0.15  # Default 15% volatility
        
        if token_info.metadata:
            # If we have price change data, use it to estimate volatility
            price_change_24h = abs(token_info.price_change_24h or 0)
            price_change_1h = abs(token_info.metadata.get("price_change_1h", 0))
            
            if price_change_1h > 0:
                hourly_volatility = price_change_1h / 100
                volatility = min(hourly_volatility * 4, 0.3)  # Cap at 30%
            elif price_change_24h > 0:
                daily_volatility = price_change_24h / 100
                volatility = min(daily_volatility / 6, 0.3)  # Cap at 30%
        
        # Calculate required daily growth
        metrics = await self.update_risk_metrics()
        required_daily_growth = metrics["required_daily_growth"] / 100  # Convert from percentage
        
        # Base take profit levels
        base_levels = [
            {"percentage": 0.2, "portion": 0.3},   # 20% profit, sell 30% of position
            {"percentage": 0.5, "portion": 0.3},   # 50% profit, sell 30% of position
            {"percentage": 1.0, "portion": 0.2},   # 100% profit, sell 20% of position
            {"percentage": 2.0, "portion": 0.2}    # 200% profit, sell 20% of position
        ]
        
        # Adjust based on required growth
        adjusted_levels = []
        
        for level in base_levels:
            adjusted_percentage = level["percentage"]
            
            # If we need higher growth, increase take profit targets
            if required_daily_growth > 0.5:  # Need more than 50% daily growth
                growth_factor = required_daily_growth / 0.5
                adjusted_percentage = level["percentage"] * min(growth_factor, 2)  # Cap at 2x
            
            # If token is volatile, adjust targets
            if volatility > 0.2:
                volatility_factor = volatility / 0.2
                adjusted_percentage = adjusted_percentage * min(volatility_factor, 1.5)  # Cap at 1.5x
            
            # Calculate price
            take_profit_price = entry_price * (1 + adjusted_percentage)
            
            adjusted_levels.append({
                "price": take_profit_price,
                "percentage": adjusted_percentage * 100,  # Convert to percentage
                "portion": level["portion"]
            })
        
        logger.info(f"Calculated take profit levels for {token_info.symbol}:")
        for level in adjusted_levels:
            logger.info(f"- ${level['price']:.8f} ({level['percentage']:.2f}% gain): Sell {level['portion'] * 100:.0f}% of position")
        
        return adjusted_levels
    
    async def should_increase_position(self, token_address: str) -> Tuple[bool, float]:
        """
        Determine if we should increase position size for a token
        
        Args:
            token_address: Address of the token
            
        Returns:
            Tuple of (should_increase, additional_amount)
        """
        # Get current portfolio
        portfolio = await self.strategy.update_portfolio()
        
        # Find the holding
        holding = next((h for h in portfolio.holdings if h["token_address"] == token_address), None)
        
        if not holding:
            return False, 0
        
        # Check if we have significant profit
        if holding["profit_loss_percentage"] < 30:
            return False, 0
        
        # Check risk metrics
        metrics = await self.update_risk_metrics()
        
        # Don't increase position if portfolio risk is too high
        if metrics["portfolio_risk_percentage"] > 30:
            return False, 0
        
        # Don't increase position if we're in drawdown
        if metrics["daily_drawdown"] > 10:
            return False, 0
        
        # Calculate additional amount (50% of current position)
        additional_amount = holding["current_value"] * 0.5
        
        # Cap at available capital
        additional_amount = min(additional_amount, portfolio.available_capital * 0.5)
        
        # Minimum amount check
        if additional_amount < 20:
            return False, 0
        
        logger.info(f"Recommending position increase for {holding['token_symbol']}: +${additional_amount:.2f}")
        
        return True, additional_amount
    
    async def get_risk_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive risk report
        
        Returns:
            Dictionary with risk report data
        """
        # Update risk metrics
        metrics = await self.update_risk_metrics()
        
        # Get portfolio
        portfolio = await self.strategy.update_portfolio()
        
        # Calculate risk-adjusted return
        rar = 0
        if metrics["max_drawdown"] > 0:
            rar = (portfolio.profit_loss_percentage / 100) / (metrics["max_drawdown"] / 100)
        
        # Calculate Sharpe ratio (simplified)
        # Assuming risk-free rate of 0% and using drawdown as volatility
        sharpe = 0
        if metrics["max_drawdown"] > 0:
            sharpe = (portfolio.profit_loss_percentage / 100) / (metrics["max_drawdown"] / 100)
        
        # Calculate Kelly criterion for optimal position sizing
        win_rate = 0.5  # Default assumption
        if len(self.daily_trades) > 0:
            wins = sum(1 for trade in self.daily_trades if 
                      (trade.trade_type.value == "SELL" and trade.amount_usd > 0))
            win_rate = wins / len(self.daily_trades) if len(self.daily_trades) > 0 else 0.5
        
        # Simplified Kelly formula: K% = W - (1-W)/(R/1) where W is win rate and R is win/loss ratio
        avg_win = 0.5  # Default assumption: 50% gain on winners
        avg_loss = 0.15  # Default assumption: 15% loss on losers
        win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 1
        
        kelly_percentage = win_rate - ((1 - win_rate) / win_loss_ratio)
        kelly_percentage = max(0, min(kelly_percentage, 0.5))  # Cap between 0% and 50%
        
        # Calculate time to target
        days_to_target = 0
        if portfolio.total_value_usd > 0 and portfolio.total_value_usd < self.strategy.target_value:
            daily_growth_rate = metrics["required_daily_growth"] / 100  # Convert from percentage
            if daily_growth_rate > 0:
                days_to_target = math.log(self.strategy.target_value / portfolio.total_value_usd) / math.log(1 + daily_growth_rate)
        
        # Generate risk report
        report = {
            "portfolio_summary": {
                "total_value": portfolio.total_value_usd,
                "initial_capital": portfolio.initial_capital,
                "profit_loss": portfolio.profit_loss,
                "profit_loss_percentage": portfolio.profit_loss_percentage,
                "available_capital": portfolio.available_capital
            },
            "risk_metrics": metrics,
            "performance_metrics": {
                "risk_adjusted_return": rar,
                "sharpe_ratio": sharpe,
                "win_rate": win_rate * 100,  # Convert to percentage
                "kelly_percentage": kelly_percentage * 100,  # Convert to percentage
                "days_to_target": days_to_target
            },
            "risk_status": {
                "daily_loss_limit_status": "OK" if metrics["daily_pl_percentage"] > -self.max_daily_loss * 100 else "EXCEEDED",
                "drawdown_limit_status": "OK" if metrics["max_drawdown"] < self.max_drawdown * 100 else "EXCEEDED",
                "portfolio_risk_status": "OK" if metrics["portfolio_risk_percentage"] < self.max_portfolio_risk * 100 else "EXCEEDED"
            },
            "recommendations": {
                "position_size_adjustment": "NORMAL",
                "risk_budget": metrics["risk_budget"],
                "suggested_max_position": portfolio.available_capital * (kelly_percentage if kelly_percentage > 0 else 0.15)
            }
        }
        
        # Add position size adjustment recommendation
        if metrics["portfolio_risk_percentage"] > 40:
            report["recommendations"]["position_size_adjustment"] = "REDUCE"
        elif metrics["daily_pl_percentage"] < -10:
            report["recommendations"]["position_size_adjustment"] = "REDUCE"
        elif metrics["max_drawdown"] > 20:
            report["recommendations"]["position_size_adjustment"] = "REDUCE"
        elif portfolio.profit_loss_percentage > 100:
            report["recommendations"]["position_size_adjustment"] = "REDUCE"  # Protect profits
        elif metrics["required_daily_growth"] > 100:
            report["recommendations"]["position_size_adjustment"] = "INCREASE"  # Need aggressive growth
        
        return report


# Example usage
async def main():
    # Create trading strategy
    strategy = TradingStrategy(initial_capital=200.0, target_value=10000.0, days_remaining=10)
    
    # Create risk manager
    risk_manager = RiskManager(strategy)
    
    # Get risk report
    report = await risk_manager.get_risk_report()
    
    # Print risk report
    print("Risk Report:")
    print(f"Portfolio Value: ${report['portfolio_summary']['total_value']:.2f}")
    print(f"Profit/Loss: ${report['portfolio_summary']['profit_loss']:.2f} ({report['portfolio_summary']['profit_loss_percentage']:.2f}%)")
    
    print("\nRisk Metrics:")
    print(f"Daily Drawdown: {report['risk_metrics']['daily_drawdown']:.2f}%")
    print(f"Max Drawdown: {report['risk_metrics']['max_drawdown']:.2f}%")
    print(f"Portfolio Risk: {report['risk_metrics']['portfolio_risk_percentage']:.2f}%")
    print(f"Required Daily Growth: {report['risk_metrics']['required_daily_growth']:.2f}%")
    
    print("\nPerformance Metrics:")
    print(f"Risk-Adjusted Return: {report['performance_metrics']['risk_adjusted_return']:.2f}")
    print(f"Win Rate: {report['performance_metrics']['win_rate']:.2f}%")
    print(f"Kelly Percentage: {report['performance_metrics']['kelly_percentage']:.2f}%")
    print(f"Estimated Days to Target: {report['performance_metrics']['days_to_target']:.1f}")
    
    print("\nRisk Status:")
    print(f"Daily Loss Limit: {report['risk_status']['daily_loss_limit_status']}")
    print(f"Drawdown Limit: {report['risk_status']['drawdown_limit_status']}")
    print(f"Portfolio Risk: {report['risk_status']['portfolio_risk_status']}")
    
    print("\nRecommendations:")
    print(f"Position Size Adjustment: {report['recommendations']['position_size_adjustment']}")
    print(f"Risk Budget: {report['recommendations']['risk_budget']:.2f}%")
    print(f"Suggested Max Position: ${report['recommendations']['suggested_max_position']:.2f}")

if __name__ == "__main__":
    asyncio.run(main())
