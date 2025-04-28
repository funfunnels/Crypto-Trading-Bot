import logging
import aiohttp
import asyncio
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from src.utils.models import TokenInfo, MarketState

logger = logging.getLogger(__name__)

class DexScreenerAPI:
    """API client for DexScreener to fetch trending meme coins on Solana"""
    
    BASE_URL = "https://api.dexscreener.com/latest"
    
    async def get_trending_tokens(self, limit: int = 20) -> List[TokenInfo]:
        """
        Get trending tokens on Solana from DexScreener
        
        Args:
            limit: Maximum number of tokens to return
            
        Returns:
            List of TokenInfo objects for trending tokens
        """
        try:
            url = f"{self.BASE_URL}/dex/search?q=meme&chain=solana"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch trending tokens: {response.status}")
                        return []
                    
                    data = await response.json()
                    
                    if not data.get("pairs"):
                        logger.warning("No pairs found in DexScreener response")
                        return []
                    
                    # Filter and sort by volume
                    pairs = data["pairs"]
                    pairs.sort(key=lambda x: float(x.get("volume", {}).get("h24", 0)), reverse=True)
                    
                    # Convert to TokenInfo objects
                    tokens = []
                    for pair in pairs[:limit]:
                        try:
                            token = TokenInfo(
                                symbol=pair.get("baseToken", {}).get("symbol", "UNKNOWN"),
                                name=pair.get("baseToken", {}).get("name", "Unknown"),
                                address=pair.get("baseToken", {}).get("address", ""),
                                price_usd=float(pair.get("priceUsd", 0)),
                                market_cap=float(pair.get("fdv", 0)) if pair.get("fdv") else None,
                                volume_24h=float(pair.get("volume", {}).get("h24", 0)),
                                price_change_24h=float(pair.get("priceChange", {}).get("h24", 0)),
                                liquidity=float(pair.get("liquidity", {}).get("usd", 0)),
                                created_at=datetime.fromtimestamp(int(pair.get("pairCreatedAt", 0)) / 1000) if pair.get("pairCreatedAt") else None,
                                metadata={
                                    "dex": pair.get("dexId"),
                                    "pair_address": pair.get("pairAddress"),
                                    "fdv": float(pair.get("fdv", 0)) if pair.get("fdv") else None,
                                    "price_change_1h": float(pair.get("priceChange", {}).get("h1", 0)),
                                    "price_change_7d": float(pair.get("priceChange", {}).get("h7d", 0)),
                                    "txns_24h": pair.get("txns", {}).get("h24"),
                                }
                            )
                            tokens.append(token)
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Error parsing token data: {e}")
                            continue
                    
                    logger.info(f"Found {len(tokens)} trending tokens on Solana")
                    return tokens
                    
        except Exception as e:
            logger.error(f"Error fetching trending tokens: {e}")
            return []

    async def get_token_info(self, token_address: str) -> Optional[TokenInfo]:
        """
        Get detailed information about a specific token
        
        Args:
            token_address: The token address to look up
            
        Returns:
            TokenInfo object or None if not found
        """
        try:
            url = f"{self.BASE_URL}/dex/tokens/{token_address}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch token info: {response.status}")
                        return None
                    
                    data = await response.json()
                    
                    if not data.get("pairs") or len(data["pairs"]) == 0:
                        logger.warning(f"No pairs found for token {token_address}")
                        return None
                    
                    # Use the first pair with the highest liquidity
                    pairs = data["pairs"]
                    pairs.sort(key=lambda x: float(x.get("liquidity", {}).get("usd", 0)), reverse=True)
                    pair = pairs[0]
                    
                    token = TokenInfo(
                        symbol=pair.get("baseToken", {}).get("symbol", "UNKNOWN"),
                        name=pair.get("baseToken", {}).get("name", "Unknown"),
                        address=token_address,
                        price_usd=float(pair.get("priceUsd", 0)),
                        market_cap=float(pair.get("fdv", 0)) if pair.get("fdv") else None,
                        volume_24h=float(pair.get("volume", {}).get("h24", 0)),
                        price_change_24h=float(pair.get("priceChange", {}).get("h24", 0)),
                        liquidity=float(pair.get("liquidity", {}).get("usd", 0)),
                        created_at=datetime.fromtimestamp(int(pair.get("pairCreatedAt", 0)) / 1000) if pair.get("pairCreatedAt") else None,
                        metadata={
                            "dex": pair.get("dexId"),
                            "pair_address": pair.get("pairAddress"),
                            "fdv": float(pair.get("fdv", 0)) if pair.get("fdv") else None,
                            "price_change_1h": float(pair.get("priceChange", {}).get("h1", 0)),
                            "price_change_7d": float(pair.get("priceChange", {}).get("h7d", 0)),
                            "txns_24h": pair.get("txns", {}).get("h24"),
                        }
                    )
                    
                    return token
                    
        except Exception as e:
            logger.error(f"Error fetching token info: {e}")
            return None


class BirdeyeAPI:
    """API client for Birdeye to get additional token information"""
    
    BASE_URL = "https://public-api.birdeye.so/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "BIRDEYE_API_KEY"  # Replace with actual API key if available
        
    async def get_token_metadata(self, token_address: str) -> Dict[str, Any]:
        """
        Get token metadata from Birdeye
        
        Args:
            token_address: The token address to look up
            
        Returns:
            Dictionary with token metadata
        """
        try:
            url = f"{self.BASE_URL}/token/meta?address={token_address}"
            headers = {"X-API-KEY": self.api_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch token metadata: {response.status}")
                        return {}
                    
                    data = await response.json()
                    return data.get("data", {})
                    
        except Exception as e:
            logger.error(f"Error fetching token metadata: {e}")
            return {}
    
    async def get_token_holders(self, token_address: str) -> int:
        """
        Get number of token holders from Birdeye
        
        Args:
            token_address: The token address to look up
            
        Returns:
            Number of token holders or 0 if not available
        """
        try:
            url = f"{self.BASE_URL}/token/holders?address={token_address}"
            headers = {"X-API-KEY": self.api_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch token holders: {response.status}")
                        return 0
                    
                    data = await response.json()
                    return data.get("data", {}).get("total", 0)
                    
        except Exception as e:
            logger.error(f"Error fetching token holders: {e}")
            return 0


class MarketAnalyzer:
    """Analyzes the Solana meme coin market to find potential opportunities"""
    
    def __init__(self):
        self.dexscreener = DexScreenerAPI()
        self.birdeye = BirdeyeAPI()
        self.last_update = None
        self.market_state = None
        
    async def get_sol_price(self) -> float:
        """Get current SOL price in USD"""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch SOL price: {response.status}")
                        return 0
                    
                    data = await response.json()
                    return float(data.get("solana", {}).get("usd", 0))
                    
        except Exception as e:
            logger.error(f"Error fetching SOL price: {e}")
            return 0
    
    async def analyze_market(self) -> MarketState:
        """
        Analyze the current market state
        
        Returns:
            MarketState object with current market information
        """
        # Check if we need to update (cache for 5 minutes)
        current_time = datetime.now()
        if self.last_update and (current_time - self.last_update) < timedelta(minutes=5) and self.market_state:
            return self.market_state
        
        # Get trending tokens
        trending_tokens = await self.dexscreener.get_trending_tokens(limit=20)
        
        # Get SOL price
        sol_price = await self.get_sol_price()
        
        # Determine market sentiment based on trending tokens
        bullish_count = 0
        bearish_count = 0
        
        for token in trending_tokens:
            if token.price_change_24h and token.price_change_24h > 0:
                bullish_count += 1
            elif token.price_change_24h and token.price_change_24h < 0:
                bearish_count += 1
        
        if bullish_count > bearish_count * 1.5:
            sentiment = "bullish"
        elif bearish_count > bullish_count * 1.5:
            sentiment = "bearish"
        else:
            sentiment = "neutral"
        
        # Create market state
        self.market_state = MarketState(
            trending_tokens=trending_tokens,
            sol_price=sol_price,
            market_sentiment=sentiment,
            updated_at=current_time,
            metadata={
                "bullish_tokens": bullish_count,
                "bearish_tokens": bearish_count,
                "neutral_tokens": len(trending_tokens) - bullish_count - bearish_count,
                "total_tokens_analyzed": len(trending_tokens)
            }
        )
        
        self.last_update = current_time
        logger.info(f"Market analysis completed. Sentiment: {sentiment}, SOL price: ${sol_price}")
        
        return self.market_state
    
    async def find_potential_tokens(self, max_tokens: int = 5) -> List[TokenInfo]:
        """
        Find potential tokens for trading based on various criteria
        
        Args:
            max_tokens: Maximum number of tokens to return
            
        Returns:
            List of TokenInfo objects for potential trading opportunities
        """
        market_state = await self.analyze_market()
        
        if not market_state or not market_state.trending_tokens:
            logger.warning("No market data available for finding potential tokens")
            return []
        
        # Filter tokens based on criteria
        potential_tokens = []
        
        for token in market_state.trending_tokens:
            # Skip tokens with very low liquidity
            if token.liquidity and token.liquidity < 10000:
                continue
            
            # Skip tokens with very low volume
            if token.volume_24h and token.volume_24h < 5000:
                continue
            
            # Prioritize tokens with positive price action
            score = 0
            
            if token.price_change_24h and token.price_change_24h > 0:
                score += token.price_change_24h / 10  # Add points for positive 24h change
            
            if token.metadata and token.metadata.get("price_change_1h", 0) > 0:
                score += token.metadata.get("price_change_1h", 0) / 5  # Add points for positive 1h change
            
            # Add points for higher liquidity (normalized)
            if token.liquidity:
                score += min(token.liquidity / 1000000, 5)  # Cap at 5 points
            
            # Add points for higher volume (normalized)
            if token.volume_24h:
                score += min(token.volume_24h / 500000, 5)  # Cap at 5 points
            
            # Add points for newer tokens (within last 7 days)
            if token.created_at and (datetime.now() - token.created_at).days <= 7:
                days_old = (datetime.now() - token.created_at).days
                score += max(0, (7 - days_old)) / 2  # Newer tokens get more points
            
            # Add token with its score
            potential_tokens.append((token, score))
        
        # Sort by score and take top tokens
        potential_tokens.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"Found {len(potential_tokens)} potential tokens for trading")
        
        # Return just the tokens (without scores)
        return [token for token, _ in potential_tokens[:max_tokens]]
    
    async def enrich_token_data(self, token: TokenInfo) -> TokenInfo:
        """
        Enrich token data with additional information from Birdeye
        
        Args:
            token: TokenInfo object to enrich
            
        Returns:
            Enriched TokenInfo object
        """
        try:
            # Get token holders
            holders = await self.birdeye.get_token_holders(token.address)
            token.holders = holders
            
            # Get additional metadata
            metadata = await self.birdeye.get_token_metadata(token.address)
            
            if token.metadata is None:
                token.metadata = {}
                
            token.metadata.update({
                "holders": holders,
                "birdeye_metadata": metadata
            })
            
            return token
            
        except Exception as e:
            logger.error(f"Error enriching token data: {e}")
            return token


# Example usage
async def main():
    analyzer = MarketAnalyzer()
    market_state = await analyzer.analyze_market()
    
    print(f"SOL Price: ${market_state.sol_price}")
    print(f"Market Sentiment: {market_state.market_sentiment}")
    print(f"Updated At: {market_state.updated_at}")
    
    print("\nTop 5 Trending Tokens:")
    for i, token in enumerate(market_state.trending_tokens[:5], 1):
        print(f"{i}. {token.name} ({token.symbol})")
        print(f"   Price: ${token.price_usd}")
        print(f"   24h Change: {token.price_change_24h}%")
        print(f"   Volume: ${token.volume_24h}")
        print(f"   Liquidity: ${token.liquidity}")
        print()
    
    print("\nPotential Trading Opportunities:")
    potential_tokens = await analyzer.find_potential_tokens(max_tokens=3)
    
    for i, token in enumerate(potential_tokens, 1):
        enriched_token = await analyzer.enrich_token_data(token)
        print(f"{i}. {enriched_token.name} ({enriched_token.symbol})")
        print(f"   Price: ${enriched_token.price_usd}")
        print(f"   24h Change: {enriched_token.price_change_24h}%")
        print(f"   Volume: ${enriched_token.volume_24h}")
        print(f"   Liquidity: ${enriched_token.liquidity}")
        print(f"   Holders: {enriched_token.holders}")
        print()

if __name__ == "__main__":
    asyncio.run(main())
