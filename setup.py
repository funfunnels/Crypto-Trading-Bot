#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="solana_meme_coin_bot",
    version="1.0.0",
    description="Trading bot for Solana meme coins",
    author="Trading Bot Developer",
    packages=find_packages(),
    install_requires=[
        "solana>=0.30.2",
        "python-binance>=1.0.16",
        "web3>=6.5.0",
        "pandas>=2.0.3",
        "numpy>=1.24.3",
        "matplotlib>=3.7.2",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "aiohttp>=3.8.5",
        "asyncio>=3.4.3",
        "pytz>=2023.3",
        "tk>=0.1.0",
        "pillow>=10.0.0",
    ],
    entry_points={
        'console_scripts': [
            'solana_meme_coin_bot=main:main',
        ],
    },
)
