import logging
from .database_service import DatabaseService

logger = logging.getLogger(__name__)

class AuthService:
    """Servicio de Autenticación integrado con MySQL."""
    
    def __init__(self, audit_service=None):
        self.db = DatabaseService()
        from .audit_service import AuditService
        self.audit = audit_service or AuditService(self.db)

    def authenticate(self, username, password):
        """
        Verifica credenciales. USANDO MOCK EXCLUSIVO (BD comentada para local).
        """
        # MOCK DATA para desarrollo local sin base de datos
        mock_users = {
            "sebastian.cannes": {"username": "sebastian.cannes", "nombre_completo": "Sebastian Cannes", "role": "Gerente"},
            "admin": {"username": "admin", "nombre_completo": "Administrador", "role": "Administrativo"},
            "juan.supervisor": {"username": "juan.supervisor", "nombre_completo": "Juan Supervisor", "role": "Supervisor"},
            "demo.user": {"username": "demo.user", "nombre_completo": "Usuario Demo", "role": "Usuario"}
        }

        user_data = None
        if username in mock_users:
            user_data = mock_users[username]
        
        # Registrar en Auditoría
        if user_data:
            self.audit.log_event(
                user_id=username,
                user_role=user_data['role'],
                event_type="LOGIN_SUCCESS",
                entity="USUARIO",
                entity_id=username,
                metadata={"nombre": user_data['nombre_completo']}
            )
            return user_data
        else:
            self.audit.log_event(
                user_id=username or "unknown",
                user_role="GUEST",
                event_type="LOGIN_FAILURE",
                entity="USUARIO",
                entity_id=username or "none",
                metadata={"reason": "Invalid credentials"}
            )
            return None
