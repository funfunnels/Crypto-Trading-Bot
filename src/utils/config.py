import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from src.utils.models import BotConfig, WalletInfo

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/trading_bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create necessary directories
def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        "logs",
        "config",
        "data/historical",
        "data/wallets",
        "data/tokens"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    logger.info("Directory structure verified")

# Default configuration
DEFAULT_CONFIG = BotConfig(
    initial_capital=200.0,
    max_risk_per_trade=0.15,  # 15% of capital per trade
    target_daily_profit=0.5,  # 50% daily profit target
    stop_loss_percentage=0.15,  # 15% stop loss
    take_profit_percentage=0.5,  # 50% take profit
    max_concurrent_trades=2,
    trading_hours=[{"start": "00:00", "end": "23:59"}],  # 24/7 trading
    risk_management_settings={
        "max_daily_loss": 0.2,  # 20% max daily loss
        "increase_position_threshold": 0.3,  # 30% profit to increase position
        "trailing_stop_activation": 0.2,  # Activate trailing stop at 20% profit
        "trailing_stop_distance": 0.1,  # 10% trailing stop distance
    },
    tracked_wallets=[
        WalletInfo(address="wallet_address_1"),
        WalletInfo(address="wallet_address_2"),
        WalletInfo(address="wallet_address_3"),
    ],
    api_keys={
        "solana_private_key": os.getenv("SOLANA_PRIVATE_KEY", ""),
    },
    notification_settings={
        "enable_notifications": True,
        "notify_on_signal": True,
        "notify_on_trade": True,
        "notify_on_error": True,
    }
)

# Application paths
class AppPaths:
    """Application paths"""
    ROOT_DIR = Path(__file__).parent.parent
    CONFIG_DIR = ROOT_DIR / "config"
    DATA_DIR = ROOT_DIR / "data"
    LOGS_DIR = ROOT_DIR / "logs"
    
    CONFIG_FILE = CONFIG_DIR / "config.json"
    WALLET_DATA = DATA_DIR / "wallets"
    TOKEN_DATA = DATA_DIR / "tokens"
    HISTORICAL_DATA = DATA_DIR / "historical"

# Initialize application
def initialize_app():
    """Initialize the application"""
    ensure_directories()
    logger.info("Application initialized")
    
    # Check for private key
    if not os.getenv("SOLANA_PRIVATE_KEY"):
        logger.warning("SOLANA_PRIVATE_KEY not found in environment variables")
        
    return DEFAULT_CONFIG

if __name__ == "__main__":
    initialize_app()
