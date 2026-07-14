--Consultas de validacion y pruebas
 
--Validar que se cargaron los datos en las tablas

SELECT COUNT(*) AS total_clientes
FROM clientes;

SELECT COUNT(*) AS total_restaurantes
FROM restaurantes;

SELECT COUNT(*) AS total_repartidores
FROM repartidores;

SELECT COUNT(*) AS total_pedidos
FROM pedidos;

SELECT COUNT(*) AS total_detalle_pedidos
FROM detalle_pedidos;

--Validar de nodos worker activos
SELECT * FROM citus_get_active_worker_nodes();
 
--Validar tablas distribuidas

SELECT 
    logicalrelid AS tabla,
    partmethod AS metodo_particion,
    partkey AS clave_distribucion
FROM pg_dist_partition;


--Validar shards

SELECT 
    logicalrelid AS tabla,
    shardid,
    shardstorage,
    shardminvalue,
    shardmaxvalue
FROM pg_dist_shard
ORDER BY logicalrelid, shardid
LIMIT 50;

--Consulta por clave de distribucion, busca pedidos de un cliente especifico

EXPLAIN ANALYZE
SELECT 
    pedido_id,
    cliente_id,
    restaurante_id,
    repartidor_id,
    total,
    estado,
    fecha_pedido
FROM pedidos
WHERE cliente_id = 60365;

--Consulta por rango, recorre varios shards, busca pedidos realizados en un rango de fechas

EXPLAIN ANALYZE
SELECT 
    pedido_id,
    cliente_id,
    restaurante_id,
    total,
    estado,
    fecha_pedido
FROM pedidos
WHERE fecha_pedido >= '2026-01-01'
  AND total > 30
ORDER BY fecha_pedido DESC
LIMIT 100;

--Consulta agregada, calcula los 5 productos que mas dinero han generado

EXPLAIN ANALYZE
SELECT 
    producto_nombre,
    SUM(cantidad * precio_unitario) AS total_vendido,
    SUM(cantidad) AS unidades_vendidas
FROM detalle_pedidos
GROUP BY producto_nombre
ORDER BY total_vendido DESC
LIMIT 5;

--Consulta agregada por estado, resume cantidad y total de pedidos por estado

EXPLAIN ANALYZE
SELECT 
    estado,
    COUNT(*) AS cantidad_pedidos,
    SUM(total) AS total_vendido,
    ROUND(AVG(total), 2) AS promedio_pedido
FROM pedidos
GROUP BY estado
ORDER BY total_vendido DESC;

--Join que une pedidos con detalle_pedidos usando pedido_id y cliente_id, como ambas tablas estan distribuidas por cliente_id, el join se realiza localmente en cada shard

EXPLAIN ANALYZE
SELECT 
    p.pedido_id,
    p.cliente_id,
    p.fecha_pedido,
    p.estado,
    p.total,
    d.producto_nombre,
    d.cantidad,
    d.precio_unitario,
    d.cantidad * d.precio_unitario AS subtotal
FROM pedidos p
JOIN detalle_pedidos d
  ON p.pedido_id = d.pedido_id
 AND p.cliente_id = d.cliente_id
WHERE p.cliente_id = 60365;

--Join con las tablas de referencia, une pedidos con clientes, restaurantes y repartidores los dos ultimos son tablas de referencia

EXPLAIN ANALYZE
SELECT
    p.pedido_id,
    c.nombre AS cliente,
    r.nombre AS restaurante,
    rep.nombre AS repartidor,
    p.total,
    p.estado,
    p.fecha_pedido
FROM pedidos p
JOIN clientes c
  ON p.cliente_id = c.cliente_id
JOIN restaurantes r
  ON p.restaurante_id = r.restaurante_id
JOIN repartidores rep
  ON p.repartidor_id = rep.repartidor_id
WHERE p.cliente_id = 60365;


--Consulta global, recorre todos los shards

EXPLAIN ANALYZE
SELECT 
    r.restaurante_id,
    r.nombre AS restaurante,
    r.categoria,
    COUNT(p.pedido_id) AS total_pedidos,
    SUM(p.total) AS total_vendido
FROM pedidos p
JOIN restaurantes r
  ON p.restaurante_id = r.restaurante_id
GROUP BY r.restaurante_id, r.nombre, r.categoria
ORDER BY total_vendido DESC
LIMIT 10;

--Consulta de control de integridad, compara el total de pedidos con el total de detalle_pedidos para verificar que no haya discrepancias

SELECT 
    (SELECT ROUND(SUM(total), 2) FROM pedidos) AS total_tabla_pedidos,
    (SELECT ROUND(SUM(cantidad * precio_unitario), 2) FROM detalle_pedidos) AS total_tabla_detalles;