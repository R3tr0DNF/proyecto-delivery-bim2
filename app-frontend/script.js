const URL_API = "http://localhost:5000";

function mostrarResultado(idElemento, datos) {
    const elemento = document.getElementById(idElemento);
    elemento.textContent = JSON.stringify(datos, null, 2);
}

function mostrarError(idElemento, error) {
    const elemento = document.getElementById(idElemento);
    elemento.textContent = "Error: " + error;
}

async function verificarConexion() {
    try {
        const respuesta = await fetch(`${URL_API}/salud`);
        const datos = await respuesta.json();
        mostrarResultado("resultadoConexion", datos);
    } catch (error) {
        mostrarError("resultadoConexion", error.message);
    }
}

async function insertarPedido() {
    const clienteId = document.getElementById("clienteInsertar").value;
    const restauranteId = document.getElementById("restauranteInsertar").value;
    const repartidorId = document.getElementById("repartidorInsertar").value;
    const total = document.getElementById("totalInsertar").value;
    const estado = document.getElementById("estadoInsertar").value;

    if (!clienteId || !restauranteId || !repartidorId || !total) {
        mostrarError("resultadoPedidos", "Completa todos los campos para insertar el pedido.");
        return;
    }

    const cuerpo = {
        cliente_id: Number(clienteId),
        restaurante_id: Number(restauranteId),
        repartidor_id: Number(repartidorId),
        total: Number(total),
        estado: estado
    };

    try {
        const respuesta = await fetch(`${URL_API}/api/pedidos`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(cuerpo)
        });

        const datos = await respuesta.json();
        mostrarResultado("resultadoPedidos", datos);
    } catch (error) {
        mostrarError("resultadoPedidos", error.message);
    }
}

async function eliminarPedido() {
    const pedidoId = document.getElementById("pedidoEliminar").value;
    const clienteId = document.getElementById("clienteEliminar").value;

    if (!pedidoId || !clienteId) {
        mostrarError("resultadoPedidos", "Ingresa pedido_id y cliente_id.");
        return;
    }

    try {
        const respuesta = await fetch(`${URL_API}/api/pedidos/${pedidoId}?cliente_id=${clienteId}`, {
            method: "DELETE"
        });

        const datos = await respuesta.json();
        mostrarResultado("resultadoPedidos", datos);
    } catch (error) {
        mostrarError("resultadoPedidos", error.message);
    }
}

async function simularPedidos() {
    const cantidad = document.getElementById("cantidadSimular").value || 1000;

    try {
        const respuesta = await fetch(`${URL_API}/api/simulacion/pedidos?cantidad=${cantidad}`, {
            method: "POST"
        });

        const datos = await respuesta.json();
        mostrarResultado("resultadoPedidos", datos);
    } catch (error) {
        mostrarError("resultadoPedidos", error.message);
    }
}

async function consultarDestinoCliente() {
    const clienteId = document.getElementById("clienteDestino").value;

    if (!clienteId) {
        mostrarError("resultadoDestino", "Ingresa un cliente_id.");
        return;
    }

    try {
        const respuesta = await fetch(`${URL_API}/api/metricas/destino/${clienteId}`);
        const datos = await respuesta.json();
        mostrarResultado("resultadoDestino", datos);
    } catch (error) {
        mostrarError("resultadoDestino", error.message);
    }
}

async function consultarProductosMasVendidos() {
    try {
        const respuesta = await fetch(`${URL_API}/api/consultas/productos-mas-vendidos`);
        const datos = await respuesta.json();
        mostrarResultado("resultadoConsultas", datos);
    } catch (error) {
        mostrarError("resultadoConsultas", error.message);
    }
}

async function consultarHistorial() {
    const fechaInicio = document.getElementById("fechaInicio").value;
    const fechaFin = document.getElementById("fechaFin").value;
    const montoMinimo = document.getElementById("montoMinimo").value;

    try {
        const respuesta = await fetch(
            `${URL_API}/api/consultas/historial?fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}&monto_minimo=${montoMinimo}`
        );

        const datos = await respuesta.json();
        mostrarResultado("resultadoConsultas", datos);
    } catch (error) {
        mostrarError("resultadoConsultas", error.message);
    }
}

async function consultarPedidosCliente() {
    const clienteId = document.getElementById("clienteConsultar").value;

    if (!clienteId) {
        mostrarError("resultadoConsultas", "Ingresa un cliente_id.");
        return;
    }

    try {
        const respuesta = await fetch(`${URL_API}/api/consultas/clientes/${clienteId}/pedidos`);
        const datos = await respuesta.json();
        mostrarResultado("resultadoConsultas", datos);
    } catch (error) {
        mostrarError("resultadoConsultas", error.message);
    }
}

async function consultarResumenEstados() {
    try {
        const respuesta = await fetch(`${URL_API}/api/consultas/resumen-estados`);
        const datos = await respuesta.json();
        mostrarResultado("resultadoConsultas", datos);
    } catch (error) {
        mostrarError("resultadoConsultas", error.message);
    }
}