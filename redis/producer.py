import os
import logging

# from datetime import datetime
from redis_dm import RedisDelayedMessage

# Main/Test Code

def producer():
    """ Entry point function """
    # Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', default=logging.INFO)  # Log Level
    logging.basicConfig(level = LOG_LEVEL)
    dm = RedisDelayedMessage({
        "host": os.getenv('REDIS_HOST', default='localhost'),
        "port": os.getenv('REDIS_PORT', default=6379)
    })

    # Publication of the delayed messages
    dm.publish('SELLER', 'AAA', 10) # Fired after 10 seconds
    dm.publish('OPERATOR', 'BBB', 20) # Fired after 20 seconds

if __name__ == "__main__":
    """ Main function """
    producer()