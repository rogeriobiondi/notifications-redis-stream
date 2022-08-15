import re
import redis
import logging

from typing import Callable
from datetime import datetime, timedelta

class RedisDelayedMessage:
    """ 
        This class uses the Redis keyspace notifications to implement 
        a Delayed Message mechanism.   
    """

    routes = []

    def __init__(self, config: dict):
        """
            Class constructor.
            
            config: redis configuration. Example
            config = {
                "host": "localhost",
                "port": 6379
            }
        """
        # Connection
        self.config = config
        self.conn = redis.Redis(config["host"], config["port"], 
                                retry_on_timeout=True)
        self.stream = self.conn.pubsub()
        self.conn.config_set('notify-keyspace-events', 'KEx')

    def publish(self, channel: str, correlation_key: str, timeout: int):
        """ 
            Schedules a delayed message
            publish(type: str, correlation_key: str, timeout: int)

            channel         : channel of message. e. g. 'SELLER' or 'OPERATOR'.
            correlation_key : identification key to correlate the delayed message 
                              with your demand.
            timeout         : timeout of delayed message, in seconds
        """
        self.conn.set(f"{channel.upper()}:{correlation_key}", value = 1, 
                      ex = timeout)
        eta = datetime.now() + timedelta(seconds = timeout)
        logging.info(f"Message published. Corr key: {correlation_key}. ETA: {eta}")

    def add_route(self, channel:str, handler: Callable):
        """ Adds a route"""
        self.routes.append({
            "channel": channel,
            "handler": handler
        })

    def route(self, msg: dict):
        """ Route messages to the correct message handler """
        # Checks if the message is valid, otherwise ignore it.
        try:
            key = msg["data"].decode("utf-8")
        except Exception as ex:
            # TODO: implement proper error handling
            pass
        # Routes the message to the correct message handler
        for route in self.routes:
            pattern = re.compile(route['channel'].upper() + ':[a-zA-Z0-9]*')
            if pattern.match(key):
                # Splits the key and passes to the handling function
                dec_key = key.split(':')
                route['handler'](dec_key[0], dec_key[1])
    
    def consume(self):
        """ Start consuming messages from the notify-keyspace-events stream """
        self.stream.psubscribe(**{"__keyevent@0__:expired": self.route})
        self.stream.run_in_thread(sleep_time=0.01)
        logging.info("Monitoring messages from the Redis Stream")