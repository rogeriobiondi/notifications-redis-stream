# notifications-redis-stream


## Objetivo

Enviar notificações para o seller conforme os pacotes forem bipados. A ideia é que a notificação seja enviada após algum tempo depois que o seller bipou o último pacote. Se até esse tempo ser novamente atingido, ocorrer um novo bipe para este seller, o prazo de 1h volta a contar. Exemplos:

Exemplo 1:

```
Hora: 12:00 PM
Seller id: 10
bipou pacote AAAAAA
bipou pacote BBBBBB
bipou pacote CCCCCC

Hora: 13:00 PM
Notificação enviada com os pacotes foram bipados
```

Exemplo 2:

```
Hora: 12:00 PM
Seller id: 10
bipou pacote AAAAAA
bipou pacote BBBBBB
bipou pacote CCCCCC

Hora: 12:30 PM
bipou pacote DDDDDD
bipou pacote EEEEEE

Hora: 13:30 PM
Notificação enviada com os pacotes foram bipados
```

## Solução por SQL (base relacional)


```
create table CounterShippingPackage (seller_id int, package_id varchar(30), date_time datetime);
insert into CounterShippingPackage  values 
(10, 'AAAAAA', '2022-06-28 19:35:00'),
(10, 'BBBBBB', '2022-06-28 19:36:00'),
(10, 'CCCCCC', '2022-06-28 19:36:30'),
(20, 'XXXXXX', '2022-06-28 19:35:10'),
(20, 'YYYYYY', '2022-06-28 19:35:20');

SELECT seller_id, date_time
FROM CounterShippingPackage
``` 

Os seguintes dados são gerados:

| seller_id | package_id | date_time           |
|-----------|------------|---------------------|
| 10        | AAAAAA     | 2022-06-28 19:35:00 |
| 10        | BBBBBB     | 2022-06-28 19:36:00 |
| 10        | CCCCCC     | 2022-06-28 19:36:30 |
| 20        | XXXXXX     | 2022-06-28 19:35:10 |
| 20        | YYYYYY     | 2022-06-28 19:35:20 |
| 30        | ZZZZZZ     | 2022-06-28 19:35:06 |
| 30        | TTTTTT     | 2022-06-28 19:35:08 |


Queremos agrupar os dados pelo `seller_id` e trazer a data do último pacote bipado e colocar uma hora de corte para os sellers até as `19:35:25`: 


```
SELECT t2.seller_id, t2.date_time
FROM (
  SELECT seller_id, MAX(date_time) date_time
  FROM CounterShippingPackage
  GROUP BY seller_id
 ) t1
 INNER JOIN CounterShippingPackage t2 on t2.seller_id = t1.seller_id
 and        t2.date_time = t1.date_time
 WHERE    t2.date_time < datetime('2022-06-28 19:35:25')
 ORDER BY t2.seller_id;
```

Resulta no seguinte:

| seller_id | date_time           |
|-----------|---------------------|
| 20        | 2022-06-28 19:35:20 |
| 30        | 2022-06-28 19:35:08 |

E finalmente buscar para cada seller os pacotes até essa data de corte:

```
for each seller take p_seller:
    select seller_id, package_id, date_time from CounterShippingPackage
    where seller_id = p_seller
    order by date_time < datetime('2022-06-28 19:35:25')
```

Resulta nos pacotes de cada seller:

seller 20

| seller_id | package_id | date_time           |
|-----------|------------|---------------------|
| 20        | XXXXXX     | 2022-06-28 19:35:10 |
| 20        | YYYYYY     | 2022-06-28 19:35:20 |


seller 30

| seller_id | package_id | date_time           |
|-----------|------------|---------------------|
| 30        | ZZZZZZ     | 2022-06-28 19:35:06 |
| 30        | TTTTTT     | 2022-06-28 19:35:08 |


### Demonstração

http://www.sqlfiddle.com/#!5/7b358/1



### Vantagens e Desvantagens

#### Pontos positivos:

- Facilidade e rapidez de implementar
- Queries podem ser traduzidas com facilidade para o modelo do Django Admin
- Não requer infra especial


#### Pontos negativos:

- CounterShippingPackage tende a crescer muito, dificultando a busca
- Tempo de execução e ocupação do banco operacional (Loggi Web)
- A lista dos pacotes poderia ser buscada numa única query, mas o problema do desempenho tende a crescer cada vez mais.


## Solução por Redis (NoSQL chave-valor)

Nesta solução usamos o Redis Stream

Publisher:

Cada pacote bipado é enviado para o redis stream usando a api redis-py:

```
xadd packages * seller_id 10 package_id AAAAAA
xadd packages * seller_id 10 package_id BBBBBB
xadd packages * seller_id 10 package_id CCCCCC
```

Consumer:

Inicia o processo de consumo com o comando

```
xread COUNT 1 BLOCK 5000 STREAMS packages 0

1) 1) "packages"
   2) 1) 1) "1656454392117-0"
         2) 1) "seller_id"
            2) "10"
            3) "package_id"
            4) "AAAAAA"

```

Para cada leitura que realizar, usar o id do objeto anterior recebido:

```
xread COUNT 1 BLOCK 5000 STREAMS packages 1656454392117-0
1) 1) "packages"
   2) 1) 1) "1656454396695-0"
         2) 1) "seller_id"
            2) "10"
            3) "package_id"
            4) "BBBBBB"

``` 

E assim por diante.

Para cada elemento recebido no stream, criar uma lista com a chave `SELLER:<seller_id>`

```
lpush SELLER:10 AAAAAA
lpush SELLER:10 BBBBBB
```

### Verificando a idade das chaves de seller

```
keys "SELLER:*"
```

Para cada chave que receber (iterate), obter o tempo de vida dela:

```
OBJECT IDLETIME SELLER:10
(integer) 22
``` 

Se o objeto tiver o número de segundos maior do que o configurado para envio da notificação, por exemplo 3600 = 1h, envia a notificação com os dados da chave e apaga a chave do cache.


### Manutenção do cache

Realizar uma limpeza no cache para manter apenas os últimos 10.000 eventos no stream `packages`:

``` 
XTRIM packages MAXLEN ~ 10000
``` 

### Vantagens e desvantagens

#### Pontos positivos

- Rápido e fácil de implementar
- Trabalha fora da base do Loggi Web
- Solução auto mantida (limpeza das chaves e trimming do stream)

#### Pontos negativos

- Escala conforme o número de sellers, mas só os sellers que estiverem dropando pacotes é que ocuparão a memória do cache
- Os dados vivem no cache por um período muito curto de tempo
- Loggi compliant???

### Demonstração


Instalar ambiente:

```
# Instalar python 3.10.4, caso não esteja instalado ainda
pyenv install 3.10.4

# configurar pyenv
cd redis-notifications
pyenv virtualenv 3.10.4 redis-notifications
pyenv local redis-notifications
python -m pip install --upgrade pip
``` 

Instalar dependências

```
make install
``` 

Subir infra

```
make start
```


Executar o consumer

```
make consumer

```

Executar o publisher

```
python publisher.py 10 AAAAAA
python publisher.py 10 BBBBBB
python publisher.py 10 CCCCCC
python publisher.py 20 XXXXXX
python publisher.py 20 YYYYYY
...
```
