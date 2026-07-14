--Distribucion de tablas con citus

CREATE EXTENSION IF NOT EXISTS citus;

--REGISTRAR NODOS WORKER EN EL NODO COORDINADOR

SELECT citus_add_node('citus-worker-1', 5432);
SELECT citus_add_node('citus-worker-2', 5432);

--Verificar los workers

SELECT * FROM citus_get_active_worker_nodes();

--Tablas de referencia (Estas se usaran para replicarse en los workers)

SELECT create_reference_table('restaurantes');
SELECT create_reference_table('repartidores');

--Distribuir las tablas de clientes y pedidos por cliente_id

SELECT create_distributed_table('clientes', 'cliente_id');
SELECT create_distributed_table('pedidos', 'cliente_id');

SELECT create_distributed_table('detalle_pedidos', 'cliente_id', colocate_with => 'pedidos');

--Verificar la distribución de las tablas

SELECT 
    logicalrelid AS tabla,
    partmethod AS metodo_particion,
    partkey AS clave_distribucion
FROM pg_dist_partition;