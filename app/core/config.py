"""
Application configuration settings.
"""

import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Application settings
class Config:
    """Application configuration."""

    # API Configuration
    ANIMALS_API_BASE_URL = os.getenv("ANIMALS_API_BASE_URL", "http://localhost:3123")

    # Application metadata
    APP_TITLE = "Animal API"
    APP_DESCRIPTION = "API to fetch animals from the animals service"
    APP_VERSION = "1.0.0"

    # Processing settings
    MAX_CONCURRENT_REQUESTS = 100
    BATCH_SIZE = 100
    MAX_ANIMALS_PER_BATCH = 100

    # Retry settings
    MAX_RETRIES = 5
    INITIAL_RETRY_DELAY = 2
    MAX_RETRY_DELAY = 16

    # HTTP settings
    REQUEST_TIMEOUT = 20
    CONNECT_TIMEOUT = 5
    BATCH_POST_TIMEOUT = 60


config = Config()
