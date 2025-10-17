import os
from dotenv import load_dotenv

load_dotenv()

# Default settings - API keys will be input by user
DEFAULT_QUERIES = [
    "NVIDIA stock price",
    "AMD earnings",
    "Intel processors",
    "TSMC semiconductor",
    "Qualcomm chips"
]

COMPETITORS = {
    "NVIDIA": ["NVIDIA", "NVDA"],
    "AMD": ["AMD", "Advanced Micro Devices"],
    "Intel": ["Intel", "INTC"],
    "TSMC": ["TSMC", "Taiwan Semiconductor"],
    "Qualcomm": ["Qualcomm", "QCOM"],
    "Apple": ["Apple", "AAPL"],
    "Google": ["Google", "Alphabet", "GOOGL"],
    "Microsoft": ["Microsoft", "MSFT"]
}

SENTIMENT_CONFIG = {
    'positive_threshold': 0.1,
    'negative_threshold': -0.1
}

# UI Configuration
UI_CONFIG = {
    'theme': {
        'primary_color': '#1f77b4',
        'secondary_color': '#ff7f0e',
        'success_color': '#2ecc71',
        'warning_color': '#f39c12',
        'error_color': '#e74c3c',
        'background_color': '#ffffff',
        'text_color': '#2c3e50'
    }
}