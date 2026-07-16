-- Tablas de referencia

SELECT create_reference_table('restaurantes');

SELECT create_reference_table('repartidores');

-- Tablas distribuidas

SELECT create_distributed_table('clientes','cliente_id');

SELECT create_distributed_table('pedidos','cliente_id');

SELECT create_distributed_table(
    'detalle_pedidos',
    'cliente_id',
    colocate_with=>'pedidos'
);

-- Verificación

SELECT
    logicalrelid,
    partmethod,
    partkey
FROM pg_dist_partition;