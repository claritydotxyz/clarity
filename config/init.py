"""Configuration management for Clarity."""
from clarity.config.development import DevelopmentSettings
from clarity.config.production import ProductionSettings
from clarity.config.testing import TestingSettings
import os

def get_settings():
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestingSettings()
    return DevelopmentSettings()

settings = get_settings()
