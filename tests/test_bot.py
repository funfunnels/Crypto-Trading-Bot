import asyncio
import logging
import os
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import bot components
from src.analysis.market_analyzer import MarketAnalyzer
from src.analysis.signal_generator import SignalAggregator
from src.strategy.trading_strategy import TradingStrategy
from src.risk.risk_manager import RiskManager

async def test_market_analyzer():
    """Test the market analyzer module"""
    logger.info("Testing Market Analyzer...")
    
    analyzer = MarketAnalyzer()
    
    # Test market analysis
    logger.info("Testing market analysis...")
    market_state = await analyzer.analyze_market()
    
    logger.info(f"SOL Price: ${market_state.sol_price}")
    logger.info(f"Market Sentiment: {market_state.market_sentiment}")
    logger.info(f"Found {len(market_state.trending_tokens)} trending tokens")
    
    # Test finding potential tokens
    logger.info("Testing potential token finder...")
    potential_tokens = await analyzer.find_potential_tokens(max_tokens=3)
    
    logger.info(f"Found {len(potential_tokens)} potential tokens")
    for i, token in enumerate(potential_tokens, 1):
        logger.info(f"{i}. {token.name} ({token.symbol})")
        logger.info(f"   Price: ${token.price_usd}")
        logger.info(f"   24h Change: {token.price_change_24h}%")
        logger.info(f"   Volume: ${token.volume_24h}")
        logger.info(f"   Liquidity: ${token.liquidity}")
    
    # Test token data enrichment
    if potential_tokens:
        logger.info("Testing token data enrichment...")
        enriched_token = await analyzer.enrich_token_data(potential_tokens[0])
        logger.info(f"Enriched {enriched_token.name} with {enriched_token.holders} holders")
    
    return True

async def test_signal_generator():
    """Test the signal generator module"""
    logger.info("Testing Signal Generator...")
    
    aggregator = SignalAggregator()
    
    # Add test wallets
    logger.info("Adding test wallets...")
    await aggregator.add_tracked_wallet("5ZWj7a1f8tWkjBESHKgrLmZhGh7yBR8Cmjw6aQGhRTMQ", "Whale 1")
    await aggregator.add_tracked_wallet("7NsngNMtXJNdHgeK4znQDZ5PJ19ykVvQvEF7BT5KFjMv", "Whale 2")
    
    # Test getting signals
    logger.info("Testing signal generation...")
    signals = await aggregator.get_trading_signals()
    
    logger.info(f"Generated {len(signals)} trading signals")
    for i, signal in enumerate(signals[:3], 1):  # Show top 3 signals
        logger.info(f"{i}. {signal.token.name} ({signal.token.symbol})")
        logger.info(f"   Signal Type: {signal.signal_type.value}")
        logger.info(f"   Confidence: {signal.confidence:.2f}")
        logger.info(f"   Entry Price: ${signal.entry_price}")
        logger.info(f"   Target Price: ${signal.target_price}")
        logger.info(f"   Stop Loss: ${signal.stop_loss}")
        logger.info(f"   Risk Level: {signal.risk_level.value}")
        logger.info(f"   Source: {signal.source}")
    
    return True

async def test_trading_strategy():
    """Test the trading strategy module"""
    logger.info("Testing Trading Strategy...")
    
    strategy = TradingStrategy(initial_capital=200.0, target_value=10000.0, days_remaining=10)
    
    # Add test wallets
    logger.info("Adding test wallets...")
    await strategy.add_tracked_wallet("5ZWj7a1f8tWkjBESHKgrLmZhGh7yBR8Cmjw6aQGhRTMQ", "Whale 1")
    await strategy.add_tracked_wallet("7NsngNMtXJNdHgeK4znQDZ5PJ19ykVvQvEF7BT5KFjMv", "Whale 2")
    
    # Set private key (dummy for testing)
    strategy.set_private_key("dummy_private_key")
    
    # Test getting trading signals
    logger.info("Testing trading signal retrieval...")
    signals = await strategy.get_trading_signals()
    logger.info(f"Retrieved {len(signals)} trading signals")
    
    # Test portfolio update
    logger.info("Testing portfolio update...")
    portfolio = await strategy.update_portfolio()
    logger.info(f"Portfolio value: ${portfolio.total_value_usd:.2f}")
    logger.info(f"Available capital: ${portfolio.available_capital:.2f}")
    
    # Test getting recommended actions
    logger.info("Testing recommended actions...")
    recommendations = await strategy.get_recommended_actions()
    
    logger.info(f"Buy signals: {len(recommendations['buy_signals'])}")
    logger.info(f"Sell recommendations: {len(recommendations['sell_recommendations'])}")
    
    # Test executing a buy signal if available
    if recommendations['buy_signals']:
        signal = recommendations['buy_signals'][0]
        logger.info(f"Testing buy execution for {signal.token.symbol}...")
        trade = await strategy.execute_buy_signal(signal)
        
        if trade:
            logger.info(f"Successfully executed buy trade for {trade.token.symbol}")
            logger.info(f"Quantity: {trade.quantity}")
            logger.info(f"Amount: ${trade.amount_usd}")
            logger.info(f"Transaction hash: {trade.transaction_hash}")
        else:
            logger.warning("Buy execution failed")
    
    # Update portfolio again to see changes
    portfolio = await strategy.update_portfolio()
    logger.info(f"Updated portfolio value: ${portfolio.total_value_usd:.2f}")
    logger.info(f"Updated available capital: ${portfolio.available_capital:.2f}")
    logger.info(f"Holdings: {len(portfolio.holdings)}")
    
    return True

async def test_risk_manager():
    """Test the risk manager module"""
    logger.info("Testing Risk Manager...")
    
    strategy = TradingStrategy(initial_capital=200.0, target_value=10000.0, days_remaining=10)
    risk_manager = RiskManager(strategy)
    
    # Test updating risk metrics
    logger.info("Testing risk metrics update...")
    metrics = await risk_manager.update_risk_metrics()
    
    logger.info(f"Daily drawdown: {metrics['daily_drawdown']:.2f}%")
    logger.info(f"Max drawdown: {metrics['max_drawdown']:.2f}%")
    logger.info(f"Portfolio risk: {metrics['portfolio_risk_percentage']:.2f}%")
    logger.info(f"Required daily growth: {metrics['required_daily_growth']:.2f}%")
    logger.info(f"Risk budget: {metrics['risk_budget']:.2f}%")
    
    # Test checking risk limits
    logger.info("Testing risk limit check...")
    limits_ok, reason = await risk_manager.check_risk_limits()
    
    if limits_ok:
        logger.info("Risk limits check passed")
    else:
        logger.warning(f"Risk limits check failed: {reason}")
    
    # Test position size adjustment
    logger.info("Testing position size adjustment...")
    base_size = 30.0
    from src.utils.models import RiskLevel
    adjusted_size = await risk_manager.adjust_position_size(base_size, RiskLevel.MEDIUM)
    
    logger.info(f"Base position size: ${base_size:.2f}")
    logger.info(f"Adjusted position size: ${adjusted_size:.2f}")
    
    # Test risk report generation
    logger.info("Testing risk report generation...")
    report = await risk_manager.get_risk_report()
    
    logger.info(f"Risk-adjusted return: {report['performance_metrics']['risk_adjusted_return']:.2f}")
    logger.info(f"Win rate: {report['performance_metrics']['win_rate']:.2f}%")
    logger.info(f"Kelly percentage: {report['performance_metrics']['kelly_percentage']:.2f}%")
    logger.info(f"Days to target: {report['performance_metrics']['days_to_target']:.1f}")
    
    return True

async def test_ui_data_flow():
    """Test the data flow for the UI"""
    logger.info("Testing UI data flow...")
    
    # Create strategy and risk manager
    strategy = TradingStrategy(initial_capital=200.0, target_value=10000.0, days_remaining=10)
    risk_manager = RiskManager(strategy)
    
    # Add test wallets
    await strategy.add_tracked_wallet("5ZWj7a1f8tWkjBESHKgrLmZhGh7yBR8Cmjw6aQGhRTMQ", "Whale 1")
    await strategy.add_tracked_wallet("7NsngNMtXJNdHgeK4znQDZ5PJ19ykVvQvEF7BT5KFjMv", "Whale 2")
    
    # Set private key (dummy for testing)
    strategy.set_private_key("dummy_private_key")
    
    # Test data for dashboard
    logger.info("Testing dashboard data...")
    portfolio = await strategy.update_portfolio()
    
    logger.info(f"Portfolio value: ${portfolio.total_value_usd:.2f}")
    logger.info(f"Profit/Loss: ${portfolio.profit_loss:.2f} ({portfolio.profit_loss_percentage:.2f}%)")
    logger.info(f"Available capital: ${portfolio.available_capital:.2f}")
    
    # Test data for signals tab
    logger.info("Testing signals data...")
    recommendations = await strategy.get_recommended_actions()
    
    logger.info(f"Buy signals: {len(recommendations['buy_signals'])}")
    logger.info(f"Sell recommendations: {len(recommendations['sell_recommendations'])}")
    
    # Test data for risk tab
    logger.info("Testing risk data...")
    report = await risk_manager.get_risk_report()
    
    logger.info(f"Daily drawdown: {report['risk_metrics']['daily_drawdown']:.2f}%")
    logger.info(f"Max drawdown: {report['risk_metrics']['max_drawdown']:.2f}%")
    logger.info(f"Portfolio risk: {report['risk_metrics']['portfolio_risk_percentage']:.2f}%")
    
    # Execute a test trade to populate portfolio
    if recommendations['buy_signals']:
        signal = recommendations['buy_signals'][0]
        logger.info(f"Executing test trade for {signal.token.symbol}...")
        trade = await strategy.execute_buy_signal(signal)
        
        if trade:
            logger.info(f"Successfully executed test trade")
            
            # Update portfolio
            portfolio = await strategy.update_portfolio()
            logger.info(f"Updated portfolio value: ${portfolio.total_value_usd:.2f}")
            logger.info(f"Holdings: {len(portfolio.holdings)}")
            
            # Check if we have holdings to test sell functionality
            if portfolio.holdings:
                holding = portfolio.holdings[0]
                logger.info(f"Testing sell functionality for {holding['token_symbol']}...")
                
                # Simulate a sell condition
                sell_recommendations = await strategy.check_sell_conditions()
                
                if sell_recommendations:
                    holding, reason = sell_recommendations[0]
                    logger.info(f"Sell recommendation found: {reason}")
                    
                    # Execute sell
                    trade = await strategy.execute_sell(holding, reason)
                    
                    if trade:
                        logger.info(f"Successfully executed sell trade")
                        
                        # Update portfolio again
                        portfolio = await strategy.update_portfolio()
                        logger.info(f"Final portfolio value: ${portfolio.total_value_usd:.2f}")
                        logger.info(f"Final holdings: {len(portfolio.holdings)}")
                    else:
                        logger.warning("Sell execution failed")
                else:
                    logger.info("No sell recommendations found")
        else:
            logger.warning("Test trade execution failed")
    
    return True

async def run_all_tests():
    """Run all tests"""
    logger.info("Starting comprehensive test suite...")
    
    tests = [
        ("Market Analyzer", test_market_analyzer),
        ("Signal Generator", test_signal_generator),
        ("Trading Strategy", test_trading_strategy),
        ("Risk Manager", test_risk_manager),
        ("UI Data Flow", test_ui_data_flow)
    ]
    
    results = {}
    
    for name, test_func in tests:
        logger.info(f"\n{'=' * 50}")
        logger.info(f"Running test: {name}")
        logger.info(f"{'=' * 50}")
        
        try:
            start_time = datetime.now()
            success = await test_func()
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            results[name] = {
                "success": success,
                "duration": duration,
                "error": None
            }
            
            logger.info(f"Test {name} {'passed' if success else 'failed'} in {duration:.2f} seconds")
        except Exception as e:
            logger.error(f"Test {name} failed with error: {e}", exc_info=True)
            results[name] = {
                "success": False,
                "duration": 0,
                "error": str(e)
            }
    
    # Print summary
    logger.info("\n\n")
    logger.info(f"{'=' * 50}")
    logger.info("Test Summary")
    logger.info(f"{'=' * 50}")
    
    all_passed = True
    for name, result in results.items():
        status = "PASSED" if result["success"] else "FAILED"
        if not result["success"]:
            all_passed = False
        logger.info(f"{name}: {status} ({result['duration']:.2f}s)")
        if result["error"]:
            logger.info(f"  Error: {result['error']}")
    
    logger.info(f"{'=' * 50}")
    logger.info(f"Overall: {'PASSED' if all_passed else 'FAILED'}")
    logger.info(f"{'=' * 50}")
    
    return all_passed

if __name__ == "__main__":
    asyncio.run(run_all_tests())
