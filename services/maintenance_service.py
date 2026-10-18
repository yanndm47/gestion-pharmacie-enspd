"""Maintenance quotidienne : lots périmés et ordonnances expirées (RG-13, RG-29)."""
from db.connection import transaction


def executer_maintenance() -> None:
    """Appelle la procédure sp_maintenance_quotidienne du script SQL 02."""
    with transaction() as cur:
        cur.execute("CALL sp_maintenance_quotidienne()")
