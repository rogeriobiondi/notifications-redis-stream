import json, time
from redis import Redis

# Segundos para enviar notificação para o seller
# No nosso exemplo, 60 segundos
SELLER_NOTIFICATION_TIMEOUT = 60

r = Redis("localhost", 6379, retry_on_timeout=True)

def consumer():
    last_msg = 0
    block_timeout = 5000
    # Limpa os eventos antigos do stream
    r.xtrim("packages", 10000)
    while True:
        # Lê e adiciona o package ao seller
        ret = r.xread({ "packages": last_msg }, count = 1, block = block_timeout)
        if ret: 
            stream_key, values = ret[0]
            last_id, data = values[0]
            print(last_id, data)
            add_package_seller(data)
            last_msg = last_id
        # Verifica quais sellers passaram de 2 minutos sem um novo pacote adicionado
        for key in r.scan_iter("SELLER:*"):
            idle_time = r.object("IDLETIME", key)
            # Atingiu o limite para notificar.
            if idle_time > SELLER_NOTIFICATION_TIMEOUT:
                push_seller_notification(key, data)
                # Remove a chave SELLER:id
                r.delete(key)
            else:
                print(f"{key}:idle_time", idle_time)
        time.sleep(5)
        

def push_seller_notification(key, data):
    # TODO formatar msg e publicar no AWS-SNS
    print("Enviando notificações com o pacote do seller: ", key)
    pacotes_seller = r.lrange(key, 0, 1000)
    print(pacotes_seller)
        
def add_package_seller(data):
    # Adiciona o pacote apenas se ele ainda não existir
    pacotes_seller = r.lrange(f"SELLER:{int(data[b'seller_id'])}", 0, 1000)
    if not (data[b'package_id'] in pacotes_seller):
        r.lpush(f"SELLER:{int(data[b'seller_id'])}", data[b'package_id'])

if __name__ == "__main__":
    consumer()
