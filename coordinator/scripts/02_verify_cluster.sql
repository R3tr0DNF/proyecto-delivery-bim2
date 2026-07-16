-- ============================================
-- Verificar todos los nodos activos dentro del cluster
-- ============================================

SELECT
    nodeid,
    nodename,
    nodeport,
    groupid,
    noderole,
    isactive
FROM pg_dist_node
ORDER BY nodeid;