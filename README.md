# Proyecto Delivery - Bases de Datos Distribuidas

Proyecto final de la asignatura **Bases de Datos Distribuidas**.

Este proyecto extiende el sistema de delivery desarrollado durante el primer bimestre, implementando una arquitectura de base de datos distribuida mediante **PostgreSQL** y **Citus**, utilizando múltiples computadoras físicas como nodos conectados a través de una red local.

## Tecnologías utilizadas

- PostgreSQL
- Citus
- Docker
- Python
- HTML, CSS y JavaScript

## Estructura del proyecto

```text
.
├── app-backend/
├── app-frontend/
├── base_datos/
├── coordinator/
├── worker/
├── datos-csv/
└── README.md
```

## Arquitectura

El sistema estará conformado por:

- 1 nodo Coordinator
- 2 nodos Worker
- Comunicación mediante red local
- Contenedores Docker ejecutándose en computadoras diferentes

## Funcionalidades

- Fragmentación horizontal de datos.
- Procesamiento de consultas distribuidas.
- Replicación de datos.
- Demostración de transacciones distribuidas.
- Administración de datos mediante PostgreSQL y Citus.

