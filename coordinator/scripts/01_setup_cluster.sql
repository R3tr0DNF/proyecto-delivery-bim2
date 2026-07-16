-- ============================================
-- Para registrar los dos nodos en el cluster
-- ============================================

SELECT citus_add_node('192.168.0.11', 35568);

SELECT citus_add_node('192.168.0.12', 35568);

