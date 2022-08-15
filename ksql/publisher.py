import sys
import json
from datetime import datetime

# from datetime import datetime
# from ksql import KSQLAPI

# logging.basicConfig(level=logging.DEBUG)
# client = KSQLAPI('http://localhost:8088')


seller_id = sys.argv[1]
package_id = sys.argv[2]

# def json_serial(obj):
#     """JSON serializer for objects not serializable by default json code"""
#     if isinstance(obj, (datetime, date)):
#         return obj.isoformat()
#     raise TypeError ("Type %s not serializable" % type(obj))


# query = client.query('select * from package_stream', use_http2=False)
# for item in query: print(item)



event = {
        "SELLER_ID": 10,
        "PACKAGE_ID": package_id,
        "DATE_TIME": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
}

txe = json.dumps(event)

print ("Evento gerado:")
print (txe)

# client.inserts_stream("package_stream", rows)

from kafka import KafkaProducer
producer = KafkaProducer(bootstrap_servers='localhost:29092')
#  producer.send('package_topic', b'{ "SELLER_ID": 10, "PACKAGE_ID": "111111", "DATE_TIME": "2022-07-01T15:30:00" }')
# future = producer.send('package_topic', b'{ "SELLER_ID": 10, "PACKAGE_ID": "111111", "DATE_TIME": "2022-07-01T15:30:00" }')
future = producer.send('package_topic', txe.encode('utf-8'))
result = future.get(timeout=60)
print(result)
producer.flush()