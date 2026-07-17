-- ================================================================
-- Generador de promociones aleatorias
--
-- Ejecutar en el nodo COORDINADOR (publicador), NO en el suscriptor.
-- Como la tabla "promociones" ya está cubierta por la publicación
-- pub_promociones, cada fila que se inserte aquí se replica sola
-- hacia el suscriptor en cuanto se hace COMMIT.
--
-- Requiere que la tabla "restaurantes" ya tenga datos cargados
-- (carga_datos.sql), porque cada promoción se asigna a un
-- restaurante existente.
-- ================================================================

DO $$
DECLARE
    cantidad INT := 30; -- <-- cambia aquí cuántas promociones quieres generar
    titulos TEXT[] := ARRAY[
        '2x1 en el menú',
        'Descuento por tiempo limitado',
        'Envío gratis en tu pedido',
        'Combo especial de temporada',
        'Happy Hour',
        'Promoción de bienvenida',
        'Descuento por la app',
        'Oferta relámpago',
        'Menú del día con descuento',
        'Cliente frecuente',
        'Descuento fin de semana',
        'Promoción de temporada'
    ];
BEGIN
    INSERT INTO promociones
        (restaurante_id, titulo, descripcion, descuento, fecha_inicio, fecha_fin, activa)
    SELECT
        (SELECT restaurante_id FROM restaurantes ORDER BY random() LIMIT 1),
        titulos[1 + floor(random() * array_length(titulos, 1))::int],
        'Promoción generada automáticamente para pruebas de replicación.',
        round((5 + random() * 45)::numeric, 2),
        CURRENT_DATE - (floor(random() * 15))::int,
        CURRENT_DATE + (floor(random() * 30) + 5)::int,
        (random() > 0.2)
    FROM generate_series(1, cantidad);
END $$;

-- Verificación rápida en el publicador
SELECT COUNT(*) AS total_promociones FROM promociones;
