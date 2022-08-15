import sys
from redis import Redis

r = Redis("localhost", 6379, retry_on_timeout=True)

def publish(message):
    ret = r.xadd("packages", message)
    print(ret)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Invalid argument.\nusage: python publisher.py <seller_id> <package_id>")
        exit(0)
    publish({
        "seller_id": sys.argv[1],
        "package_id": sys.argv[2]
    })