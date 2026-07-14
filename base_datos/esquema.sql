-- CREACION DE LAS TABLAS DE LA BASE DE DATOS EN BASE AL ESQUEMA RELACIONAL

DROP TABLE IF EXISTS detalle_pedidos CASCADE;
DROP TABLE IF EXISTS pedidos CASCADE;
DROP TABLE IF EXISTS clientes CASCADE;
DROP TABLE IF EXISTS restaurantes CASCADE;
DROP TABLE IF EXISTS repartidores CASCADE;

--Tabla Clientes

CREATE TABLE clientes (
    cliente_id INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    zona_id INT NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (cliente_id)
);

--Tabla Restaurantes

CREATE TABLE restaurantes (
    restaurante_id INT NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    categoria VARCHAR(50),
    zona_id INT NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (restaurante_id)
);

--Tabla Repartidores

CREATE TABLE repartidores (
    repartidor_id INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    vehiculo VARCHAR(30),
    activo BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (repartidor_id)
);

--Tabla Pedidos

CREATE TABLE pedidos (
    pedido_id INT NOT NULL,
    cliente_id INT NOT NULL,
    restaurante_id INT NOT NULL,
    repartidor_id INT NOT NULL,
    total NUMERIC(10, 2) NOT NULL,
    estado VARCHAR(20) DEFAULT 'Recibido',
    fecha_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (pedido_id, cliente_id)
);

--Tabla Detalle_Pedidos

CREATE TABLE detalle_pedidos (
    detalle_id INT NOT NULL,
    pedido_id INT NOT NULL,
    cliente_id INT NOT NULL,
    producto_nombre VARCHAR(100) NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario NUMERIC(10, 2) NOT NULL,
    PRIMARY KEY (detalle_id, cliente_id)
);
