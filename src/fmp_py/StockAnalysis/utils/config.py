"""
Configuration Management for FMP Stock Analysis

This module handles configuration settings for the FMP API client
and analysis tools.
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
import json


@dataclass
class Config:
    """Configuration class for FMP Stock Analysis"""
    
    # API Configuration
    api_key: str = ""
    api_timeout: int = 30
    api_retries: int = 3
    
    # Data Configuration
    default_period: str = "annual"
    default_limit: int = 5
    cache_enabled: bool = True
    cache_duration: int = 300  # 5 minutes
    
    # Analysis Configuration
    risk_free_rate: float = 0.02  # 2% default risk-free rate
    market_return: float = 0.10   # 10% default market return
    
    # Display Configuration
    decimal_places: int = 2
    currency_symbol: str = "$"
    percentage_format: str = ".2%"
    
    @classmethod
    def from_env(cls) -> 'Config':
        """
        Create configuration from environment variables
        
        Returns:
            Config: Configuration instance with values from environment
        """
        config = cls()
        
        # API settings
        config.api_key = os.getenv('FMP_API_KEY', '')
        config.api_timeout = int(os.getenv('FMP_API_TIMEOUT', '30'))
        config.api_retries = int(os.getenv('FMP_API_RETRIES', '3'))
        
        # Data settings
        config.default_period = os.getenv('FMP_DEFAULT_PERIOD', 'annual')
        config.default_limit = int(os.getenv('FMP_DEFAULT_LIMIT', '5'))
        config.cache_enabled = os.getenv('FMP_CACHE_ENABLED', 'true').lower() == 'true'
        config.cache_duration = int(os.getenv('FMP_CACHE_DURATION', '300'))
        
        # Analysis settings
        config.risk_free_rate = float(os.getenv('FMP_RISK_FREE_RATE', '0.02'))
        config.market_return = float(os.getenv('FMP_MARKET_RETURN', '0.10'))
        
        return config
    
    @classmethod
    def from_file(cls, filepath: str) -> 'Config':
        """
        Load configuration from JSON file
        
        Args:
            filepath (str): Path to configuration file
            
        Returns:
            Config: Configuration instance
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        config = cls()
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        return config
    
    def to_file(self, filepath: str) -> None:
        """
        Save configuration to JSON file
        
        Args:
            filepath (str): Path to save configuration
        """
        data = {
            'api_key': self.api_key,
            'api_timeout': self.api_timeout,
            'api_retries': self.api_retries,
            'default_period': self.default_period,
            'default_limit': self.default_limit,
            'cache_enabled': self.cache_enabled,
            'cache_duration': self.cache_duration,
            'risk_free_rate': self.risk_free_rate,
            'market_return': self.market_return,
            'decimal_places': self.decimal_places,
            'currency_symbol': self.currency_symbol,
            'percentage_format': self.percentage_format
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def validate(self) -> bool:
        """
        Validate configuration settings
        
        Returns:
            bool: True if configuration is valid
        """
        if not self.api_key:
            return False
        
        if self.api_timeout <= 0:
            return False
        
        if self.default_period not in ['annual', 'quarter']:
            return False
        
        return True
    
    def get_env_template(self) -> str:
        """
        Get environment variable template
        
        Returns:
            str: Template for .env file
        """
        return f"""# FMP API Configuration
FMP_API_KEY={self.api_key}
FMP_API_TIMEOUT={self.api_timeout}
FMP_API_RETRIES={self.api_retries}

# Data Configuration
FMP_DEFAULT_PERIOD={self.default_period}
FMP_DEFAULT_LIMIT={self.default_limit}
FMP_CACHE_ENABLED={str(self.cache_enabled).lower()}
FMP_CACHE_DURATION={self.cache_duration}

# Analysis Configuration
FMP_RISK_FREE_RATE={self.risk_free_rate}
FMP_MARKET_RETURN={self.market_return}
"""


# Global configuration instance
_global_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get global configuration instance
    
    Returns:
        Config: Global configuration
    """
    global _global_config
    if _global_config is None:
        _global_config = Config.from_env()
    return _global_config


def set_config(config: Config) -> None:
    """
    Set global configuration instance
    
    Args:
        config (Config): Configuration to set as global
    """
    global _global_config
    _global_config = config


def reset_config() -> None:
    """Reset global configuration to None"""
    global _global_config
    _global_config = None