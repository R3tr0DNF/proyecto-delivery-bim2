import os
import random
import time
from decimal import Decimal
from datetime import datetime

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", os.getenv("POSTGRES_DB", "postgres")),
    "user": os.getenv("DB_USER", os.getenv("POSTGRES_USER", "postgres")),
    "password": os.getenv("DB_PASSWORD", os.getenv("POSTGRES_PASSWORD", "postgres")),
}

PRODUCTOS = [
    "Hamburguesa",
    "Pizza",
    "Sushi",
    "Tacos",
    "Ensalada",
    "Papas Fritas",
    "Pollo Broaster",
    "Hot Dog",
    "Arepa",
    "Burrito",
    "Ceviche",
    "Empanada"
]


ESTADOS = [
    "Recibido",
    "Preparando",
    "En camino",
    "Entregado"
]

def obtener_conexion():
    return psycopg2.connect(**DB_CONFIG)


def convertir_json(valor):
    if isinstance(valor, Decimal):
        return float(valor)

    if isinstance(valor, datetime):
        return valor.isoformat(sep=" ", timespec="seconds")

    return valor


def normalizar_fila(fila):
    return {clave: convertir_json(valor) for clave, valor in fila.items()}


def normalizar_filas(filas):
    return [normalizar_fila(fila) for fila in filas]


def filas_a_diccionarios(cursor):
    return [dict(fila) for fila in cursor.fetchall()]


def medir_tiempo(funcion):
    inicio = time.perf_counter()
    resultado = funcion()
    tiempo_ms = round((time.perf_counter() - inicio) * 1000, 3)
    return resultado, tiempo_ms


def obtener_tiempo_postgresql(sql, parametros=None):
    consulta_explain = "EXPLAIN (ANALYZE, FORMAT JSON) " + sql

    with obtener_conexion() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(consulta_explain, parametros or [])
            plan = cursor.fetchone()[0][0]
            return float(plan.get("Execution Time", 0))


def verificar_conexion():
    def consulta():
        with obtener_conexion() as conexion:
            with conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("SELECT current_database() AS base_datos, version() AS version_postgresql;")
                informacion = dict(cursor.fetchone())

                cursor.execute("SELECT * FROM citus_get_active_worker_nodes();")
                nodos_trabajadores = filas_a_diccionarios(cursor)

                return {
                    "estado": "Backend conectado correctamente a Citus",
                    "base_datos": informacion["base_datos"],
                    "version_postgresql": informacion["version_postgresql"],
                    "nodos_trabajadores": nodos_trabajadores,
                }

    return medir_tiempo(consulta)

def obtener_destino_cliente(cliente_id):
    def consulta():
        with obtener_conexion() as conexion:
            with conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT get_shard_id_for_distribution_column('pedidos', %s) AS shard_id;
                    """,
                    (cliente_id,),
                )

                resultado_fragmento = cursor.fetchone()
                fragmento_id = resultado_fragmento["shard_id"] if resultado_fragmento else None

                if fragmento_id is None:
                    return {
                        "cliente_id": cliente_id,
                        "fragmento_id": None,
                        "nodo_trabajador": "No disponible",
                        "etiqueta": "No se pudo determinar el fragmento"
                    }

                cursor.execute(
                    """
                    SELECT
                        p.shardid AS fragmento_id,
                        n.nodename AS nodo_trabajador,
                        n.nodeport AS puerto
                    FROM pg_dist_placement p
                    JOIN pg_dist_node n ON p.groupid = n.groupid
                    WHERE p.shardid = %s
                    ORDER BY n.nodename
                    LIMIT 1;
                    """,
                    (fragmento_id,),
                )

                ubicacion = cursor.fetchone()

                if not ubicacion:
                    return {
                        "cliente_id": cliente_id,
                        "fragmento_id": fragmento_id,
                        "nodo_trabajador": "Sin ubicación",
                        "etiqueta": f"Fragmento {fragmento_id} sin nodo trabajador encontrado"
                    }

                return {
                    "cliente_id": cliente_id,
                    "fragmento_id": ubicacion["fragmento_id"],
                    "nodo_trabajador": ubicacion["nodo_trabajador"],
                    "puerto": ubicacion["puerto"],
                    "etiqueta": f"Enrutado a: Fragmento {ubicacion['fragmento_id']} en {ubicacion['nodo_trabajador']}",
                }

    return medir_tiempo(consulta)


def insertar_pedido(cliente_id, restaurante_id, repartidor_id, total, estado="Recibido"):
    def consulta():
        with obtener_conexion() as conexion:
            with conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:

                cursor.execute(
                    """
                    SELECT nombre
                    FROM clientes
                    WHERE cliente_id = %s;
                    """,
                    (cliente_id,),
                )
                cliente = cursor.fetchone()

                if not cliente:
                    raise Exception(f"No existe un cliente con ID {cliente_id}")

                cursor.execute(
                    """
                    SELECT nombre
                    FROM restaurantes
                    WHERE restaurante_id = %s;
                    """,
                    (restaurante_id,),
                )
                restaurante = cursor.fetchone()

                if not restaurante:
                    raise Exception(f"No existe un restaurante con ID {restaurante_id}")

                cursor.execute(
                    """
                    SELECT nombre
                    FROM repartidores
                    WHERE repartidor_id = %s;
                    """,
                    (repartidor_id,),
                )
                repartidor = cursor.fetchone()

                if not repartidor:
                    raise Exception(f"No existe un repartidor con ID {repartidor_id}")

                cursor.execute("SELECT COALESCE(MAX(pedido_id), 0) + 1 AS nuevo_id FROM pedidos;")
                pedido_id = cursor.fetchone()["nuevo_id"]

                cursor.execute(
                    """
                    INSERT INTO pedidos
                        (pedido_id, cliente_id, restaurante_id, repartidor_id, total, estado, fecha_pedido)
                    VALUES
                        (%s, %s, %s, %s, %s, %s, NOW())
                    RETURNING
                        pedido_id,
                        cliente_id,
                        restaurante_id,
                        repartidor_id,
                        total,
                        estado,
                        fecha_pedido;
                    """,
                    (
                        pedido_id,
                        cliente_id,
                        restaurante_id,
                        repartidor_id,
                        Decimal(str(total)),
                        estado,
                    ),
                )

                pedido = dict(cursor.fetchone())

            conexion.commit()

        destino, _ = obtener_destino_cliente(cliente_id)

        nombre_cliente = cliente["nombre"]
        nombre_restaurante = restaurante["nombre"]
        nombre_repartidor = repartidor["nombre"]

        return {
            "pedido": normalizar_fila(pedido),
            "cliente": {
                "cliente_id": cliente_id,
                "nombre": nombre_cliente
            },
            "restaurante": {
                "restaurante_id": restaurante_id,
                "nombre": nombre_restaurante
            },
            "repartidor": {
                "repartidor_id": repartidor_id,
                "nombre": nombre_repartidor
            },
            "destino": destino,
            "mensaje": f"Pedido creado para {nombre_cliente} en el restaurante {nombre_restaurante}, asignado al repartidor {nombre_repartidor}."
        }

    return medir_tiempo(consulta)

def eliminar_pedido(pedido_id, cliente_id):
    def consulta():
        with obtener_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM detalle_pedidos
                    WHERE pedido_id = %s
                      AND cliente_id = %s;
                    """,
                    (pedido_id, cliente_id),
                )

                detalles_eliminados = cursor.rowcount

                cursor.execute(
                    """
                    DELETE FROM pedidos
                    WHERE pedido_id = %s
                      AND cliente_id = %s;
                    """,
                    (pedido_id, cliente_id),
                )

                pedidos_eliminados = cursor.rowcount

            conexion.commit()

        destino, _ = obtener_destino_cliente(cliente_id)

        return {
            "pedido_id": pedido_id,
            "cliente_id": cliente_id,
            "pedidos_eliminados": pedidos_eliminados,
            "detalles_eliminados": detalles_eliminados,
            "destino": destino,
            "mensaje": "Eliminación ejecutada"
        }

    return medir_tiempo(consulta)

def simular_pedidos(cantidad=1000):
    cantidad = max(1, min(int(cantidad), 5000))

    def consulta():
        with obtener_conexion() as conexion:
            with conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT cliente_id FROM clientes ORDER BY random() LIMIT %s;",
                    (cantidad,),
                )
                clientes = [fila["cliente_id"] for fila in cursor.fetchall()]

                cursor.execute("SELECT restaurante_id FROM restaurantes WHERE activo = TRUE;")
                restaurantes = [fila["restaurante_id"] for fila in cursor.fetchall()]

                cursor.execute("SELECT repartidor_id FROM repartidores WHERE activo = TRUE;")
                repartidores = [fila["repartidor_id"] for fila in cursor.fetchall()]

                if not clientes or not restaurantes or not repartidores:
                    raise Exception("No hay datos suficientes en clientes, restaurantes o repartidores")

                cursor.execute("SELECT COALESCE(MAX(pedido_id), 0) + 1 AS siguiente_pedido FROM pedidos;")
                siguiente_pedido = cursor.fetchone()["siguiente_pedido"]

                cursor.execute("SELECT COALESCE(MAX(detalle_id), 0) + 1 AS siguiente_detalle FROM detalle_pedidos;")
                siguiente_detalle = cursor.fetchone()["siguiente_detalle"]

                pedidos = []
                detalles = []

                for i in range(cantidad):
                    pedido_id = siguiente_pedido + i
                    cliente_id = clientes[i % len(clientes)]
                    restaurante_id = random.choice(restaurantes)
                    repartidor_id = random.choice(repartidores)
                    total = Decimal(str(round(random.uniform(5, 80), 2)))
                    estado = random.choice(ESTADOS)

                    pedidos.append(
                        (
                            pedido_id,
                            cliente_id,
                            restaurante_id,
                            repartidor_id,
                            total,
                            estado,
                        )
                    )

                    cantidad_producto = random.randint(1, 4)
                    precio_unitario = Decimal(str(round(float(total) / cantidad_producto, 2)))

                    detalles.append(
                        (
                            siguiente_detalle + i,
                            pedido_id,
                            cliente_id,
                            random.choice(PRODUCTOS),
                            cantidad_producto,
                            precio_unitario,
                        )
                    )

                psycopg2.extras.execute_values(
                    cursor,
                    """
                    INSERT INTO pedidos
                        (pedido_id, cliente_id, restaurante_id, repartidor_id, total, estado, fecha_pedido)
                    VALUES %s;
                    """,
                    pedidos,
                    template="(%s, %s, %s, %s, %s, %s, NOW())",
                    page_size=1000,
                )

                psycopg2.extras.execute_values(
                    cursor,
                    """
                    INSERT INTO detalle_pedidos
                        (detalle_id, pedido_id, cliente_id, producto_nombre, cantidad, precio_unitario)
                    VALUES %s;
                    """,
                    detalles,
                    page_size=1000,
                )

            conexion.commit()

        destino_ejemplo, _ = obtener_destino_cliente(pedidos[0][1])

        return {
            "pedidos_insertados": cantidad,
            "detalles_insertados": cantidad,
            "destino_ejemplo": destino_ejemplo,
            "mensaje": f"Se simularon {cantidad} pedidos correctamente"
        }

    return medir_tiempo(consulta)


def consultar_productos_mas_vendidos():
    sql = """
        SELECT
            producto_nombre,
            SUM(cantidad) AS unidades_vendidas,
            SUM(cantidad * precio_unitario) AS total_vendido
        FROM detalle_pedidos
        GROUP BY producto_nombre
        ORDER BY unidades_vendidas DESC
        LIMIT 5
    """

    def consulta():
        tiempo_postgresql = obtener_tiempo_postgresql(sql)

        with obtener_conexion() as conexion:
            with conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(sql)
                filas = normalizar_filas(filas_a_diccionarios(cursor))

        return {
            "resultados": filas,
            "tiempo_postgresql_ms": tiempo_postgresql,
            "tipo_consulta": "Consulta agregada global sobre varios fragmentos"
        }

    return medir_tiempo(consulta)


def consultar_historial(fecha_inicio, fecha_fin, monto_minimo):
    sql = """
        SELECT
            pedido_id,
            cliente_id,
            restaurante_id,
            repartidor_id,
            total,
            estado,
            fecha_pedido
        FROM pedidos
        WHERE fecha_pedido >= %s
          AND fecha_pedido < %s
          AND total >= %s
        ORDER BY fecha_pedido DESC
        LIMIT 100
    """

    parametros = (fecha_inicio, fecha_fin, Decimal(str(monto_minimo)))

    def consulta():
        tiempo_postgresql = obtener_tiempo_postgresql(sql, parametros)

        with obtener_conexion() as conexion:
            with conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(sql, parametros)
                filas = normalizar_filas(filas_a_diccionarios(cursor))

        return {
            "resultados": filas,
            "tiempo_postgresql_ms": tiempo_postgresql,
            "tipo_consulta": "Consulta por rango de fechas y monto"
        }

    return medir_tiempo(consulta)


def consultar_pedidos_cliente(cliente_id):
    sql = """
        SELECT
            p.pedido_id,
            p.cliente_id,
            p.fecha_pedido,
            p.estado,
            p.total,
            r.nombre AS restaurante,
            rep.nombre AS repartidor
        FROM pedidos p
        JOIN restaurantes r ON p.restaurante_id = r.restaurante_id
        JOIN repartidores rep ON p.repartidor_id = rep.repartidor_id
        WHERE p.cliente_id = %s
        ORDER BY p.fecha_pedido DESC
        LIMIT 100
    """

    parametros = (cliente_id,)

    def consulta():
        tiempo_postgresql = obtener_tiempo_postgresql(sql, parametros)

        with obtener_conexion() as conexion:
            with conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(sql, parametros)
                filas = normalizar_filas(filas_a_diccionarios(cursor))

        destino, _ = obtener_destino_cliente(cliente_id)

        return {
            "resultados": filas,
            "tiempo_postgresql_ms": tiempo_postgresql,
            "destino": destino,
            "tipo_consulta": "Consulta localizada por cliente_id"
        }

    return medir_tiempo(consulta)


def consultar_resumen_estados():
    sql = """
        SELECT
            estado,
            COUNT(*) AS cantidad_pedidos,
            SUM(total) AS total_vendido,
            ROUND(AVG(total), 2) AS promedio_pedido
        FROM pedidos
        GROUP BY estado
        ORDER BY cantidad_pedidos DESC
    """

    def consulta():
        tiempo_postgresql = obtener_tiempo_postgresql(sql)

        with obtener_conexion() as conexion:
            with conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(sql)
                filas = normalizar_filas(filas_a_diccionarios(cursor))

        return {
            "resultados": filas,
            "tiempo_postgresql_ms": tiempo_postgresql,
            "tipo_consulta": "Consulta agregada sobre varios fragmentos"
        }

    return medir_tiempo(consulta)

def consultar_disponibilidad_operativa():
    sql_restaurantes = """
        SELECT
            COUNT(*) AS total_restaurantes,
            COUNT(*) FILTER (WHERE activo = TRUE) AS restaurantes_atendiendo
        FROM restaurantes;
    """

    sql_repartidores = """
        SELECT
            COUNT(*) AS total_repartidores,
            COUNT(*) FILTER (WHERE activo = TRUE) AS repartidores_disponibles
        FROM repartidores;
    """

    sql_muestra_restaurantes = """
        SELECT
            restaurante_id,
            nombre,
            categoria,
            zona_id,
            activo
        FROM restaurantes
        WHERE activo = TRUE
        ORDER BY restaurante_id
        LIMIT 5;
    """

    sql_muestra_repartidores = """
        SELECT
            repartidor_id,
            nombre,
            vehiculo,
            activo
        FROM repartidores
        WHERE activo = TRUE
        ORDER BY repartidor_id
        LIMIT 5;
    """

    sql_ubicacion_copias = """
        SELECT
            s.logicalrelid AS tabla,
            p.shardid AS fragmento_id,
            n.nodename AS nodo_trabajador,
            n.nodeport AS puerto
        FROM pg_dist_shard s
        JOIN pg_dist_placement p ON s.shardid = p.shardid
        JOIN pg_dist_node n ON p.groupid = n.groupid
        WHERE s.logicalrelid IN ('restaurantes', 'repartidores')
        ORDER BY s.logicalrelid, n.nodename;
    """

    def consulta():
        tiempo_restaurantes = obtener_tiempo_postgresql(sql_restaurantes)
        tiempo_repartidores = obtener_tiempo_postgresql(sql_repartidores)

        with obtener_conexion() as conexion:
            with conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:

                cursor.execute(sql_restaurantes)
                resumen_restaurantes = normalizar_fila(dict(cursor.fetchone()))

                cursor.execute(sql_repartidores)
                resumen_repartidores = normalizar_fila(dict(cursor.fetchone()))

                cursor.execute(sql_muestra_restaurantes)
                muestra_restaurantes = normalizar_filas(filas_a_diccionarios(cursor))

                cursor.execute(sql_muestra_repartidores)
                muestra_repartidores = normalizar_filas(filas_a_diccionarios(cursor))

                cursor.execute(sql_ubicacion_copias)
                ubicacion_copias = normalizar_filas(filas_a_diccionarios(cursor))

                cursor.execute("SELECT * FROM citus_get_active_worker_nodes();")
                nodos_activos = normalizar_filas(filas_a_diccionarios(cursor))

        return {
            "resumen_restaurantes": resumen_restaurantes,
            "resumen_repartidores": resumen_repartidores,
            "muestra_restaurantes": muestra_restaurantes,
            "muestra_repartidores": muestra_repartidores,
            "ubicacion_copias": ubicacion_copias,
            "nodos_activos": nodos_activos,
            "tiempo_postgresql_ms": round(tiempo_restaurantes + tiempo_repartidores, 3),
            "tipo_consulta": "Lectura de disponibilidad operativa desde tablas de referencia",
            "mensaje": "Restaurantes atendiendo y repartidores disponibles consultados correctamente."
        }

    return medir_tiempo(consulta)