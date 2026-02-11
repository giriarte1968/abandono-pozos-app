import hashlib
import json
import unittest
from services.audit_service import AuditService
from services.database_service import DatabaseService

class TestAuditIntegrity(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseService()
        self.audit = AuditService(self.db)
        # Limpiar tabla de test si fuera necesario (O usar una BD de test)
        # Para este mock usamos la misma pero con un ID unico de test
        self.test_entity_id = "TEST-WELL-999"

    def test_chain_integrity(self):
        """Verifica que el encadenamiento de hashes sea válido."""
        # 1. Registrar eventos
        self.audit.log_event("user1", "Admin", "TEST_START", "POZO", self.test_entity_id)
        self.audit.log_event("user1", "Admin", "TEST_STEP", "POZO", self.test_entity_id, new_state={"step": 1})
        
        # 2. Verificar integridad
        is_ok, errors = self.audit.verify_integrity()
        self.assertTrue(is_ok, f"La integridad debería ser válida. Errores: {errors}")

    def test_tamper_detection(self):
        """Verifica que se detecten alteraciones manuales en la DB."""
        # 1. Registrar evento
        h = self.audit.log_event("user2", "Supervisor", "SENSITIVE_OP", "POZO", self.test_entity_id)
        
        # 2. Simular alteración manual maliciosa en la DB
        last_id = self.db.fetch_one("SELECT id FROM audit_events ORDER BY id DESC LIMIT 1")['id']
        self.db.execute("UPDATE audit_events SET estado_nuevo = %s WHERE id = %s", 
                        (json.dumps({"modified": "true"}), last_id))
        
        # 3. Verificar integridad (Debe fallar)
        is_ok, errors = self.audit.verify_integrity()
        self.assertFalse(is_ok, "La integridad debería fallar tras una modificación manual.")
        self.assertIn(f"Inconsistencia en ID {last_id}", errors[0])

if __name__ == "__main__":
    unittest.main()
