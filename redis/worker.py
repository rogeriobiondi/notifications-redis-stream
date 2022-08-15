import os
import logging

from datetime import datetime
from redis_dm import RedisDelayedMessage

# Main/Test Code

def handler_seller(channel: str, correlation_key: str):
    """ Message handler for processing seller messages... """
    logging.info(f"{datetime.now()} Received. channel: {channel}, c_key: {correlation_key}")

def handler_operator(channel, correlation_key: str):
    """ Message handler for processing pudo operator messages... """
    logging.info(f"{datetime.now()} Received. channel: {channel}, c_key: {correlation_key}")

def consumer():
    """ Entry point function """
    # Configuration
    LOG_LEVEL     = os.getenv('LOG_LEVEL', default=logging.INFO)  # Log Level
    logging.basicConfig(level=LOG_LEVEL)
    dm = RedisDelayedMessage({
        "host": os.getenv('REDIS_HOST', default='localhost'),
        "port":  os.getenv('REDIS_PORT', default=6379)
    })
    # Message handler for SELLER
    dm.add_route('SELLER', handler_seller)
    # Message handler for PUDO OPERATORS
    dm.add_route('OPERATOR', handler_operator)
    # Start consuming messages
    dm.consume()

if __name__ == "__main__":
    """ Main function """
    consumer()