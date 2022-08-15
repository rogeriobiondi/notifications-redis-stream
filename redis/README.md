# Using Redis for Delayed Messages


## Problem

Implementation of the delayed message mechanism. The producer creates a message to be consumed in the future.



## Concept Tests


Redis Stream may be used for delayed messages leveraging the event notifications. This is the steps to use redis for delayed messages:

- Redis notify-keyspace-events configuration;
- Set the keys with a TTL/expiration of 15 minutes;
- Consume the events from the  notify-keyspace-events stream;

Further information about Redis Keyspace Notifications can be found here:

https://redis.io/docs/manual/keyspace-notifications/ 



### Configuration

Since Redis runs as a single thread process, a good practice would be using a small (1 core, 256 mb), but dedicated instance for lauching the notification database, instead of using the Loggi Web Redis (where the feature switches status are stored) or a separated database, which is a deprecated practice due to performance issues.  

By default keyspace event notifications are disabled because while not very sensible the feature also uses some CPU power. Notifications are enabled using the notify-keyspace-events of redis.conf or via the CONFIG SET in redis-cli:


```
CONFIG SET notify-keyspace-events KEx
```

### Setting the keys

We’ll set the keys using a prefix SELLER: to identify them as seller notifications. We may distinct any other kind of notification by this prefix. The operation will be SET and the size of the key will be 1-byte, a fixed value of 1. We’ll use the EXPIRE option set to 900 (15 minutes x 60 seconds). For testing purposes you could use 10 seconds, for example:

```
redis-cli
127.0.0.1:6379> CONFIG SET notify-keyspace-events KEx
OK
127.0.0.1:6379> SET SELLER:1 1 EX 900
OK
```

### Consuming events from notify-keyspace-events stream

Next we’ll launch a new terminal instance with a separetad redis-cli comand to subscribe the stream of events:

```
redis-cli psubscribe '*:expired'
```


After 15 minutes (or the expiring time), the message will be expired in cache and the notification will be launched by the redis event stream:

```
Reading messages... (press Ctrl-C to quit)
1) "psubscribe"
2) "*:expired"
3) (integer) 1
1) "pmessage"
2) "*:expired"
3) "__keyevent@0__:expired"
4) "SELLER:1"
```


### PoC (Proof of Concept)

The same behaviour can be achieved through python code redis_dm.py , worker.py and publisher.py. (runnable but for illustrative purposes only):

The class `redis_dm.py` publishes and consumes the messages. The RedisDelayedMessage class is the core of the demonstration.

The `worker.py` module is responsible for consuming the delayed messages and dispatching the SMS messages.

And finally this is the `producer.py` code which creates the delayed message.



### Testing


#### Installing the libraries:

```
pip install redis==4.3.4
```

#### Running the worker.

```
python worker.py 
INFO:root:Monitoring messages from the Redis Stream
```


#### Producing the delayed messages:

```
python producer.py 
INFO:root:Message published. Corr key: AAA. ETA: 2022-08-11 12:32:30.573941
INFO:root:Message published. Corr key: BBB. ETA: 2022-08-11 12:32:40.574082
``` 

After 10 and 20 seconds, the messages for the SELLER and PUDO OPERATOR will be launched.

```
python worker.py 
INFO:root:Monitoring messages from the Redis Stream
INFO:root:2022-08-11 12:32:30.621446 Received. channel: SELLER, c_key: AAA
INFO:root:2022-08-11 12:32:40.653803 Received. channel: OPERATOR, c_key: BBB
```

# Conclusion

Redis has good resources for implementing the delayed messages and proves to be functional. But there are other problems to be addressed. For example: one of the components is off-line (worker/consumer), the keys will be expired and events lost. A further research on the redis pub sub system will be also required to understand the consumer groups and if is possible consuming these past (lost) events.