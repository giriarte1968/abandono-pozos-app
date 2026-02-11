import hashlib
import json
import os
from datetime import datetime
from .database_service import DatabaseService

class AuditService:
    """
    Servicio de Auditoría Regulatoria Avanzada.
    Implementa un log inmutable con integridad verificable mediante encadenamiento de Hash (Blockchain Light).
    """
    
    def __init__(self, db_service=None):
        self.db = db_service or DatabaseService()
        self.mock_db_path = "frontend/services/audit_events.json"
        
    def _load_mock_events(self):
        if os.path.exists(self.mock_db_path):
            with open(self.mock_db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _save_mock_events(self, events):
        with open(self.mock_db_path, 'w', encoding='utf-8') as f:
            json.dump(events, f, indent=4, default=str)

    def _calculate_hash(self, event_data, prev_hash):
        """Calcula el hash SHA256 del evento incluyendo el hash del evento anterior."""
        # Serializamos los datos de forma consistente para el hash
        payload = {
            "usuario": event_data.get("id_usuario"),
            "rol": event_data.get("rol_usuario"),
            "tipo": event_data.get("tipo_evento"),
            "entidad": event_data.get("entidad"),
            "entidad_id": event_data.get("entidad_id"),
            "anterior": event_data.get("estado_anterior"),
            "nuevo": event_data.get("estado_nuevo"),
            "metadata": event_data.get("metadata"),
            "prev_hash": prev_hash
        }
        encoded_data = json.dumps(payload, sort_keys=True, default=str).encode('utf-8')
        return hashlib.sha256(encoded_data).hexdigest()

    def log_event(self, user_id, user_role, event_type, entity, entity_id, 
                  prev_state=None, new_state=None, metadata=None, ip=None):
        """
        Registra un evento auditable encadenado.
        """
        db_available = self.db.is_available()
        prev_hash = "0" * 64
        
        if db_available:
            last_event = self.db.fetch_one("SELECT hash_evento FROM audit_events ORDER BY id DESC LIMIT 1")
            if last_event:
                prev_hash = last_event['hash_evento']
        else:
            events = self._load_mock_events()
            if events:
                prev_hash = events[-1]['hash_evento']

        # 2. Preparar datos y calcular hash
        event_info = {
            "id_usuario": user_id,
            "rol_usuario": user_role,
            "tipo_evento": event_type,
            "entidad": entity,
            "entidad_id": entity_id,
            "estado_anterior": prev_state,
            "estado_nuevo": new_state,
            "metadata": metadata
        }
        
        event_hash = self._calculate_hash(event_info, prev_hash)

        # 3. Persistir
        if db_available:
            query = """
                INSERT INTO audit_events 
                (id_usuario, rol_usuario, tipo_evento, entidad, entidad_id, 
                 estado_anterior, estado_nuevo, metadata, ip_origen, hash_previo, hash_evento)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                user_id, user_role, event_type, entity, entity_id,
                json.dumps(prev_state) if prev_state else None,
                json.dumps(new_state) if new_state else None,
                json.dumps(metadata) if metadata else None,
                ip, prev_hash, event_hash
            )
            self.db.execute(query, params)
        else:
            # Mock persistence
            new_event = {
                "id": len(events) + 1,
                "timestamp_utc": datetime.utcnow().isoformat(),
                "id_usuario": user_id,
                "rol_usuario": user_role,
                "tipo_evento": event_type,
                "entidad": entity,
                "entidad_id": entity_id,
                "estado_anterior": json.dumps(prev_state) if prev_state else None,
                "estado_nuevo": json.dumps(new_state) if new_state else None,
                "metadata": json.dumps(metadata) if metadata else None,
                "ip_origen": ip,
                "hash_previo": prev_hash,
                "hash_evento": event_hash
            }
            events.append(new_event)
            self._save_mock_events(events)
            
        return event_hash

    def verify_integrity(self):
        """
        Corrobora la integridad de toda la cadena de auditoría.
        Retorna (bool, list_of_errors)
        """
        if self.db.is_available():
            events = self.db.fetch_all("SELECT * FROM audit_events ORDER BY id ASC")
        else:
            events = self._load_mock_events()

        errors = []
        expected_prev_hash = "0" * 64

        for event in events:
            # Re-serializar para verificar
            verif_info = {
                "id_usuario": event['id_usuario'],
                "rol_usuario": event['rol_usuario'],
                "tipo_evento": event['tipo_evento'],
                "entidad": event['entidad'],
                "entidad_id": event['entidad_id'],
                "estado_anterior": json.loads(event['estado_anterior']) if event['estado_anterior'] else None,
                "estado_nuevo": json.loads(event['estado_nuevo']) if event['estado_nuevo'] else None,
                "metadata": json.loads(event['metadata']) if event['metadata'] else None
            }
            
            # Verificar hash previo
            if event['hash_previo'] != expected_prev_hash:
                errors.append(f"Ruptura de cadena en ID {event['id']}: Hash previo no coincide.")
            
            # Verificar hash actual
            calculated_hash = self._calculate_hash(verif_info, event['hash_previo'])
            if event['hash_evento'] != calculated_hash:
                errors.append(f"Inconsistencia en ID {event['id']}: Hash de datos alterado.")
            
            expected_prev_hash = event['hash_evento']

        return (len(errors) == 0, errors)

    def get_events_for_well(self, project_id):
        """Recupera todos los eventos de auditoría para un pozo específico."""
        if self.db.is_available():
            query = "SELECT * FROM audit_events WHERE entidad = 'POZO' AND entidad_id = %s ORDER BY timestamp_utc DESC"
            return self.db.fetch_all(query, (project_id,))
        else:
            events = self._load_mock_events()
            well_events = [e for e in events if e['entidad'] == 'POZO' and e['entidad_id'] == project_id]
            # Convert string timestamps to datetime objects for UI consistency
            for e in well_events:
                if isinstance(e['timestamp_utc'], str):
                    try:
                        e['timestamp_utc'] = datetime.fromisoformat(e['timestamp_utc'])
                    except:
                        pass
            return sorted(well_events, key=lambda x: x['timestamp_utc'], reverse=True)
