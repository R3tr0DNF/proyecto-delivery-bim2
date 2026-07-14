-- Cargar datos desde archivos CSV a PostgreSQL/Citus
-- Los CSV no tienen encabezado, por eso NO se usa CSV HEADER

-- Clientes
COPY clientes (cliente_id, nombre, email, telefono, zona_id, fecha_registro)
FROM '/datos-csv/clientes.csv'
DELIMITER ','
CSV;

-- Restaurantes
COPY restaurantes (restaurante_id, nombre, categoria, zona_id, activo)
FROM '/datos-csv/restaurantes.csv'
DELIMITER ','
CSV;

-- Repartidores
COPY repartidores (repartidor_id, nombre, vehiculo, activo)
FROM '/datos-csv/repartidores.csv'
DELIMITER ','
CSV;

-- Pedidos
COPY pedidos (pedido_id, cliente_id, restaurante_id, repartidor_id, total, estado, fecha_pedido)
FROM '/datos-csv/pedidos.csv'
DELIMITER ','
CSV;

-- Detalle_Pedidos
COPY detalle_pedidos (detalle_id, pedido_id, cliente_id, producto_nombre, cantidad, precio_unitario)
FROM '/datos-csv/detalle_pedidos.csv'
DELIMITER ','
CSV;
