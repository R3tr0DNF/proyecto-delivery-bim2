-- ============================================
-- Informacion del cluster creado
-- ============================================

-- Versión de Citus
SELECT citus_version();

-- Nodos registrados
SELECT
    nodeid,
    nodename,
    nodeport,
    noderole,
    isactive
FROM pg_dist_node
ORDER BY nodeid;

-- Tablas distribuidas
SELECT
    logicalrelid::regclass AS tabla,
    partmethod,
    partkey
FROM pg_dist_partition;