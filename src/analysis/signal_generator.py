import logging
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random

from src.utils.models import TokenInfo, TradingSignal, TradingSignalType, RiskLevel, WalletInfo
from src.analysis.market_analyzer import MarketAnalyzer

logger = logging.getLogger(__name__)

class WalletTracker:
    """Tracks successful wallets for trading signals"""
    
    def __init__(self, wallets: List[WalletInfo] = None):
        self.wallets = wallets or []
        self.solscan_base_url = "https://api.solscan.io/account/transaction"
        
    async def add_wallet(self, wallet_address: str, name: Optional[str] = None) -> WalletInfo:
        """
        Add a wallet to track
        
        Args:
            wallet_address: The wallet address to track
            name: Optional name for the wallet
            
        Returns:
            WalletInfo object for the added wallet
        """
        wallet = WalletInfo(
            address=wallet_address,
            name=name or f"Wallet-{len(self.wallets) + 1}",
            tags=["copy_trade"],
            performance_7d=None,
            total_trades=None,
            successful_trades=None,
            metadata={}
        )
        
        self.wallets.append(wallet)
        logger.info(f"Added wallet {wallet.name} ({wallet.address}) to tracking")
        
        return wallet
    
    async def get_wallet_transactions(self, wallet_address: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent transactions for a wallet
        
        Args:
            wallet_address: The wallet address to get transactions for
            limit: Maximum number of transactions to return
            
        Returns:
            List of transaction data
        """
        # Note: In a real implementation, this would make API calls to Solscan or similar
        # For this prototype, we'll simulate transaction data
        
        logger.info(f"Fetching transactions for wallet {wallet_address}")
        
        # Simulate API call delay
        await asyncio.sleep(0.5)
        
        # Generate random transactions
        transactions = []
        current_time = datetime.now()
        
        for i in range(limit):
            # Random time in the past 7 days
            tx_time = current_time - timedelta(
                days=random.randint(0, 6),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            # Random transaction type (buy or sell)
            tx_type = random.choice(["buy", "sell"])
            
            # Random token from a list of meme coins
            meme_coins = [
                {"symbol": "BONK", "name": "Bonk", "address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"},
                {"symbol": "WIF", "name": "Dogwifhat", "address": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65QAQb"},
                {"symbol": "POPCAT", "name": "Popcat", "address": "A98UDy7z8MfmWnTQt6cKjje7UfqV3pTLf4yEbuwL2HrH"},
                {"symbol": "BERN", "name": "Bernie", "address": "BERNKKUZJvVYyJRBpS4HLx8QJYcJ75cTxveQNQfR9Yy2"},
                {"symbol": "SLERF", "name": "Slerf", "address": "4LLdQMcQKy3Q8j5fYJaMDYX4GpgBsvYXBgLapYeXZGQ1"}
            ]
            token = random.choice(meme_coins)
            
            # Random amount between 0.1 and 10 SOL
            amount_sol = round(random.uniform(0.1, 10), 2)
            
            # Random price change after transaction (for "success" calculation)
            price_change = round(random.uniform(-30, 60), 2)
            
            transaction = {
                "signature": f"tx_{wallet_address[:8]}_{i}",
                "timestamp": tx_time.isoformat(),
                "type": tx_type,
                "token": token,
                "amount_sol": amount_sol,
                "price_change_after_24h": price_change,
                "success": price_change > 0 if tx_type == "buy" else price_change < 0
            }
            
            transactions.append(transaction)
        
        # Sort by timestamp (newest first)
        transactions.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return transactions
    
    async def analyze_wallet_performance(self, wallet: WalletInfo) -> WalletInfo:
        """
        Analyze a wallet's performance based on transaction history
        
        Args:
            wallet: WalletInfo object to analyze
            
        Returns:
            Updated WalletInfo object with performance metrics
        """
        transactions = await self.get_wallet_transactions(wallet.address, limit=50)
        
        if not transactions:
            logger.warning(f"No transactions found for wallet {wallet.address}")
            return wallet
        
        # Calculate performance metrics
        total_trades = len(transactions)
        successful_trades = sum(1 for tx in transactions if tx.get("success", False))
        success_rate = successful_trades / total_trades if total_trades > 0 else 0
        
        # Calculate 7-day performance
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_transactions = [
            tx for tx in transactions 
            if datetime.fromisoformat(tx["timestamp"]) > seven_days_ago
        ]
        
        recent_success = sum(1 for tx in recent_transactions if tx.get("success", False))
        recent_total = len(recent_transactions)
        performance_7d = recent_success / recent_total if recent_total > 0 else 0
        
        # Update wallet info
        wallet.performance_7d = performance_7d
        wallet.total_trades = total_trades
        wallet.successful_trades = successful_trades
        
        if wallet.metadata is None:
            wallet.metadata = {}
            
        wallet.metadata.update({
            "success_rate": success_rate,
            "recent_transactions": len(recent_transactions),
            "last_analyzed": datetime.now().isoformat()
        })
        
        logger.info(f"Analyzed wallet {wallet.address}: {successful_trades}/{total_trades} successful trades ({success_rate:.2%})")
        
        return wallet
    
    async def get_trading_signals_from_wallets(self) -> List[TradingSignal]:
        """
        Get trading signals based on wallet activity
        
        Returns:
            List of TradingSignal objects
        """
        signals = []
        
        for wallet in self.wallets:
            # Update wallet performance
            updated_wallet = await self.analyze_wallet_performance(wallet)
            
            # Skip wallets with poor performance
            if updated_wallet.performance_7d and updated_wallet.performance_7d < 0.5:
                logger.info(f"Skipping wallet {wallet.address} due to poor performance: {updated_wallet.performance_7d:.2%}")
                continue
            
            # Get recent transactions
            transactions = await self.get_wallet_transactions(wallet.address, limit=10)
            
            # Look for buy transactions in the last 24 hours
            current_time = datetime.now()
            recent_buys = [
                tx for tx in transactions
                if tx["type"] == "buy" and 
                (current_time - datetime.fromisoformat(tx["timestamp"])).total_seconds() < 86400  # 24 hours
            ]
            
            for tx in recent_buys:
                token_data = tx["token"]
                
                # Create a TokenInfo object
                token = TokenInfo(
                    symbol=token_data["symbol"],
                    name=token_data["name"],
                    address=token_data["address"],
                    price_usd=0,  # We'll need to fetch the current price
                    metadata={"source_transaction": tx["signature"]}
                )
                
                # Create a trading signal
                signal = TradingSignal(
                    token=token,
                    signal_type=TradingSignalType.BUY,
                    confidence=min(0.5 + (updated_wallet.performance_7d or 0.5), 0.95),  # Scale confidence based on wallet performance
                    entry_price=0,  # We'll need to fetch the current price
                    target_price=0,  # Will be calculated based on entry price
                    stop_loss=0,    # Will be calculated based on entry price
                    risk_level=RiskLevel.HIGH,
                    timestamp=datetime.now(),
                    reasoning=f"Copied from successful wallet {wallet.name} with {updated_wallet.performance_7d:.2%} 7-day performance",
                    source="wallet_tracking",
                    metadata={
                        "wallet_address": wallet.address,
                        "wallet_name": wallet.name,
                        "transaction_signature": tx["signature"],
                        "transaction_timestamp": tx["timestamp"]
                    }
                )
                
                signals.append(signal)
        
        logger.info(f"Generated {len(signals)} trading signals from wallet tracking")
        return signals


class TrendAnalyzer:
    """Analyzes market trends to generate trading signals"""
    
    def __init__(self):
        self.market_analyzer = MarketAnalyzer()
    
    async def get_trading_signals_from_trends(self) -> List[TradingSignal]:
        """
        Get trading signals based on market trends
        
        Returns:
            List of TradingSignal objects
        """
        signals = []
        
        # Get potential tokens from market analyzer
        potential_tokens = await self.market_analyzer.find_potential_tokens(max_tokens=5)
        
        for token in potential_tokens:
            # Enrich token data
            enriched_token = await self.market_analyzer.enrich_token_data(token)
            
            # Calculate confidence based on various factors
            confidence = 0.5  # Base confidence
            
            # Adjust based on price change
            if enriched_token.price_change_24h:
                if enriched_token.price_change_24h > 20:
                    confidence += 0.1
                elif enriched_token.price_change_24h > 10:
                    confidence += 0.05
                elif enriched_token.price_change_24h < -10:
                    confidence -= 0.1
            
            # Adjust based on volume
            if enriched_token.volume_24h:
                if enriched_token.volume_24h > 500000:
                    confidence += 0.1
                elif enriched_token.volume_24h > 100000:
                    confidence += 0.05
            
            # Adjust based on liquidity
            if enriched_token.liquidity:
                if enriched_token.liquidity > 500000:
                    confidence += 0.1
                elif enriched_token.liquidity > 100000:
                    confidence += 0.05
                elif enriched_token.liquidity < 50000:
                    confidence -= 0.1
            
            # Cap confidence between 0.3 and 0.9
            confidence = max(0.3, min(confidence, 0.9))
            
            # Determine risk level based on various factors
            risk_level = RiskLevel.HIGH  # Default for meme coins
            
            if enriched_token.liquidity and enriched_token.liquidity < 50000:
                risk_level = RiskLevel.VERY_HIGH
            elif enriched_token.created_at and (datetime.now() - enriched_token.created_at).days < 3:
                risk_level = RiskLevel.VERY_HIGH
            elif enriched_token.liquidity and enriched_token.liquidity > 500000:
                risk_level = RiskLevel.MEDIUM
            
            # Calculate target price and stop loss
            entry_price = enriched_token.price_usd
            target_price = entry_price * 1.5  # 50% profit target
            stop_loss = entry_price * 0.85    # 15% stop loss
            
            # Create trading signal
            signal = TradingSignal(
                token=enriched_token,
                signal_type=TradingSignalType.BUY,
                confidence=confidence,
                entry_price=entry_price,
                target_price=target_price,
                stop_loss=stop_loss,
                risk_level=risk_level,
                timestamp=datetime.now(),
                reasoning=f"Trending token with {enriched_token.price_change_24h:.2f}% 24h change, ${enriched_token.volume_24h:.2f} volume, and ${enriched_token.liquidity:.2f} liquidity",
                source="trend_analysis",
                metadata={
                    "price_change_24h": enriched_token.price_change_24h,
                    "volume_24h": enriched_token.volume_24h,
                    "liquidity": enriched_token.liquidity,
                    "holders": enriched_token.holders
                }
            )
            
            signals.append(signal)
        
        logger.info(f"Generated {len(signals)} trading signals from trend analysis")
        return signals


class SignalAggregator:
    """Aggregates trading signals from multiple sources"""
    
    def __init__(self):
        self.wallet_tracker = WalletTracker()
        self.trend_analyzer = TrendAnalyzer()
        
    async def add_tracked_wallet(self, wallet_address: str, name: Optional[str] = None) -> None:
        """
        Add a wallet to track
        
        Args:
            wallet_address: The wallet address to track
            name: Optional name for the wallet
        """
        await self.wallet_tracker.add_wallet(wallet_address, name)
    
    async def get_trading_signals(self) -> List[TradingSignal]:
        """
        Get aggregated trading signals from all sources
        
        Returns:
            List of TradingSignal objects
        """
        # Get signals from different sources
        wallet_signals = await self.wallet_tracker.get_trading_signals_from_wallets()
        trend_signals = await self.trend_analyzer.get_trading_signals_from_trends()
        
        # Combine signals
        all_signals = wallet_signals + trend_signals
        
        # Sort by confidence (highest first)
        all_signals.sort(key=lambda x: x.confidence, reverse=True)
        
        logger.info(f"Aggregated {len(all_signals)} trading signals from all sources")
        
        return all_signals


# Example usage
async def main():
    # Create signal aggregator
    aggregator = SignalAggregator()
    
    # Add some wallets to track
    await aggregator.add_tracked_wallet("5ZWj7a1f8tWkjBESHKgrLmZhGh7yBR8Cmjw6aQGhRTMQ", "Whale 1")
    await aggregator.add_tracked_wallet("7NsngNMtXJNdHgeK4znQDZ5PJ19ykVvQvEF7BT5KFjMv", "Whale 2")
    
    # Get trading signals
    signals = await aggregator.get_trading_signals()
    
    # Print signals
    print(f"Found {len(signals)} trading signals:")
    
    for i, signal in enumerate(signals, 1):
        print(f"\n{i}. {signal.token.name} ({signal.token.symbol})")
        print(f"   Signal Type: {signal.signal_type.value}")
        print(f"   Confidence: {signal.confidence:.2%}")
        print(f"   Entry Price: ${signal.entry_price}")
        print(f"   Target Price: ${signal.target_price}")
        print(f"   Stop Loss: ${signal.stop_loss}")
        print(f"   Risk Level: {signal.risk_level.value}")
        print(f"   Source: {signal.source}")
        print(f"   Reasoning: {signal.reasoning}")

if __name__ == "__main__":
    asyncio.run(main())
