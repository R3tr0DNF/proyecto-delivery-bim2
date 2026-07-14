import os

from flask import Flask, jsonify, request
from flask_cors import CORS

from consultas import (
    verificar_conexion,
    obtener_destino_cliente,
    insertar_pedido,
    eliminar_pedido,
    simular_pedidos,
    consultar_productos_mas_vendidos,
    consultar_historial,
    consultar_pedidos_cliente,
    consultar_resumen_estados,
    consultar_disponibilidad_operativa,
)


aplicacion = Flask(__name__)
CORS(aplicacion)


def respuesta_correcta(datos, tiempo_ms=None, estado_http=200):
    respuesta = {
        "correcto": True,
        "datos": datos,
    }

    if tiempo_ms is not None:
        respuesta["tiempo_respuesta_servidor_ms"] = tiempo_ms

    return jsonify(respuesta), estado_http


def respuesta_error(error, estado_http=500):
    return jsonify({
        "correcto": False,
        "error": str(error)
    }), estado_http


@aplicacion.route("/", methods=["GET"])
def inicio():
    return jsonify({
        "mensaje": "API del sistema Delivery con PostgreSQL y Citus",
        "rutas": {
            "verificar_conexion": "GET /salud",

            "gestion_pedidos": {
                "insertar_pedido": "POST /api/pedidos",
                "eliminar_pedido": "DELETE /api/pedidos/<pedido_id>?cliente_id=<cliente_id>",
                "simular_pedidos": "POST /api/simulacion/pedidos?cantidad=1000",
                "destino_cliente": "GET /api/metricas/destino/<cliente_id>"
            },

            "consultas_analiticas": {
                "productos_mas_vendidos": "GET /api/consultas/productos-mas-vendidos",
                "historial": "GET /api/consultas/historial?fecha_inicio=2026-01-01&fecha_fin=2026-12-31&monto_minimo=30",
                "pedidos_cliente": "GET /api/consultas/clientes/<cliente_id>/pedidos",
                "resumen_estados": "GET /api/consultas/resumen-estados"
            }
        }
    })


@aplicacion.route("/salud", methods=["GET"])
def salud():
    try:
        datos, tiempo_ms = verificar_conexion()
        return respuesta_correcta(datos, tiempo_ms)

    except Exception as error:
        return respuesta_error(error)


@aplicacion.route("/api/metricas/destino/<int:cliente_id>", methods=["GET"])
def api_destino_cliente(cliente_id):
    try:
        datos, tiempo_ms = obtener_destino_cliente(cliente_id)
        return respuesta_correcta(datos, tiempo_ms)

    except Exception as error:
        return respuesta_error(error)


@aplicacion.route("/api/pedidos", methods=["POST"])
def api_insertar_pedido():
    try:
        cuerpo = request.get_json(silent=True) or {}

        campos_requeridos = [
            "cliente_id",
            "restaurante_id",
            "repartidor_id",
            "total"
        ]

        campos_faltantes = [
            campo for campo in campos_requeridos
            if campo not in cuerpo
        ]

        if campos_faltantes:
            return respuesta_error(
                f"Faltan campos obligatorios: {', '.join(campos_faltantes)}",
                400
            )

        datos, tiempo_ms = insertar_pedido(
            cliente_id=int(cuerpo["cliente_id"]),
            restaurante_id=int(cuerpo["restaurante_id"]),
            repartidor_id=int(cuerpo["repartidor_id"]),
            total=cuerpo["total"],
            estado=cuerpo.get("estado", "Recibido"),
        )

        return respuesta_correcta(datos, tiempo_ms, 201)

    except ValueError:
        return respuesta_error(
            "Los campos cliente_id, restaurante_id y repartidor_id deben ser números enteros.",
            400
        )

    except Exception as error:
        return respuesta_error(error)


@aplicacion.route("/api/pedidos/<int:pedido_id>", methods=["DELETE"])
def api_eliminar_pedido(pedido_id):
    try:
        cliente_id = request.args.get("cliente_id", type=int)

        if cliente_id is None:
            return respuesta_error(
                "Debes enviar cliente_id. Ejemplo: /api/pedidos/400001?cliente_id=10",
                400
            )

        datos, tiempo_ms = eliminar_pedido(
            pedido_id=pedido_id,
            cliente_id=cliente_id,
        )

        return respuesta_correcta(datos, tiempo_ms)

    except Exception as error:
        return respuesta_error(error)


@aplicacion.route("/api/simulacion/pedidos", methods=["POST"])
def api_simular_pedidos():
    try:
        cantidad = request.args.get("cantidad", default=1000, type=int)

        if cantidad is None:
            cantidad = 1000

        datos, tiempo_ms = simular_pedidos(cantidad)

        return respuesta_correcta(datos, tiempo_ms, 201)

    except Exception as error:
        return respuesta_error(error)


@aplicacion.route("/api/consultas/productos-mas-vendidos", methods=["GET"])
def api_productos_mas_vendidos():
    try:
        datos, tiempo_ms = consultar_productos_mas_vendidos()
        return respuesta_correcta(datos, tiempo_ms)

    except Exception as error:
        return respuesta_error(error)


@aplicacion.route("/api/consultas/historial", methods=["GET"])
def api_historial():
    try:
        fecha_inicio = request.args.get("fecha_inicio", "2026-01-01")
        fecha_fin = request.args.get("fecha_fin", "2026-12-31")
        monto_minimo = request.args.get("monto_minimo", "0")

        datos, tiempo_ms = consultar_historial(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            monto_minimo=monto_minimo,
        )

        return respuesta_correcta(datos, tiempo_ms)

    except Exception as error:
        return respuesta_error(error)


@aplicacion.route("/api/consultas/clientes/<int:cliente_id>/pedidos", methods=["GET"])
def api_pedidos_cliente(cliente_id):
    try:
        datos, tiempo_ms = consultar_pedidos_cliente(cliente_id)
        return respuesta_correcta(datos, tiempo_ms)

    except Exception as error:
        return respuesta_error(error)


@aplicacion.route("/api/consultas/resumen-estados", methods=["GET"])
def api_resumen_estados():
    try:
        datos, tiempo_ms = consultar_resumen_estados()
        return respuesta_correcta(datos, tiempo_ms)

    except Exception as error:
        return respuesta_error(error)
    

@aplicacion.route("/api/consultas/disponibilidad-operativa", methods=["GET"])
def api_disponibilidad_operativa():
    try:
        datos, tiempo_ms = consultar_disponibilidad_operativa()
        return respuesta_correcta(datos, tiempo_ms)

    except Exception as error:
        return respuesta_error(error)


if __name__ == "__main__":
    puerto = int(os.getenv("FLASK_PORT", "5000"))
    aplicacion.run(host="0.0.0.0", port=puerto, debug=True)