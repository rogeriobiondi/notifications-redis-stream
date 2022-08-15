# from ksql import KSQLAPI
# from collections.abc import Iterable
# client = KSQLAPI('http://localhost:8088')
# query = client.query('select seller_id, packages from packages_by_seller')
# for item in query:
#     print(item)

from kafka import KafkaConsumer, TopicPartition
consumer = KafkaConsumer(bootstrap_servers='localhost:29092')
consumer.subscribe('package_topic')
for msg in consumer:
    print (msg)