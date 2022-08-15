```
create STREAM package_beep_stream (
   seller_id   INTEGER, 
   package_id  VARCHAR,
   date_time   VARCHAR
) with ( 
   kafka_topic='PACKAGE_BEEP_STREAM',
   timestamp='date_time',
   timestamp_format='yyyy-MM-dd''T''HH:mm:ss', 
   value_format='json', 
   partitions=1
);
```

Reparticionar os dados por seller:


```
create STREAM package_by_seller_rekeyed
with ( kafka_topic='package_by_seller_rekeyed' ) AS
    SELECT * 
    FROM   package_beep_stream
    PARTITION BY seller_id;
```

```
CREATE TABLE packages_seller with (kafka_topic='PACKAGES_BY_SELLER') AS 
  SELECT seller_id, 
         AS_VALUE(seller_id) as id, 
         TOPKDISTINCT(package_id, 100) as packages, 
         TIMESTAMPTOSTRING(WINDOWEND, 'yyyy-MM-dd HH:mm:ss Z') AS AGG_DATE
  FROM   package_by_seller_rekeyed 
  WINDOW TUMBLING (SIZE 3 MINUTES)
  GROUP BY seller_id;
```

```
  select * from packages_seller where rowtime >= 1659634560000;

  guardar a data de windowend do último envio.
```