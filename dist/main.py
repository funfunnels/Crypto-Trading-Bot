#!/usr/bin/env python3
import os
import sys
import tkinter as tk
from src.ui.main_app import TradingBotApp

def main():
    """Main function to start the application"""
    root = tk.Tk()
    app = TradingBotApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
