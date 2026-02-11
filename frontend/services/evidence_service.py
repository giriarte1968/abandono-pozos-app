import hashlib
import os
import json
import shutil
from datetime import datetime
from .database_service import DatabaseService
from .audit_service import AuditService

class EvidenceService:
    """
    Servicio para el manejo de evidencias digitales (Documentos, Fotos, Video).
    Gestiona el almacenamiento físico y el registro de integridad en DB y AuditLog.
    """
    
    def __init__(self, db_service=None, audit_service=None):
        self.db = db_service or DatabaseService()
        self.audit = audit_service or AuditService(self.db)
        self.storage_path = os.path.join(os.getcwd(), "storage", "evidence")
        
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)

    def _calculate_file_hash(self, file_content):
        """Calcula SHA256 de los bytes de un archivo."""
        sha256_hash = hashlib.sha256()
        # Si es un objeto de archivo de Streamlit, usamos read()
        if hasattr(file_content, 'getvalue'):
            sha256_hash.update(file_content.getvalue())
        else:
            sha256_hash.update(file_content)
        return sha256_hash.hexdigest()

    def upload_evidence(self, file_obj, project_id, workflow_step, user_id, user_role, metadata=None):
        """
        Procesa el upload de una evidencia, la guarda físicamente y registra el evento.
        """
        # 1. Validaciones básicas
        file_name = file_obj.name
        file_bytes = file_obj.getvalue()
        file_hash = self._calculate_file_hash(file_obj)
        file_size = len(file_bytes)
        
        # 2. Guardar en Sistema de Archivos
        file_ext = os.path.splitext(file_name)[1]
        stored_filename = f"{project_id}_{file_hash[:12]}{file_ext}"
        full_path = os.path.join(self.storage_path, stored_filename)
        
        with open(full_path, "wb") as f:
            f.write(file_bytes)

        # 3. Registrar en Tabla well_evidence (Si DB está disponible)
        if self.db.is_available():
            query = """
                INSERT INTO well_evidence 
                (id_pozo, etapa_workflow, nombre_archivo, path_archivo, 
                 mime_type, tamano_bytes, hash_sha256, id_usuario_carga, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                project_id, workflow_step, file_name, stored_filename,
                file_obj.type, file_size, file_hash, user_id, 
                json.dumps(metadata) if metadata else None
            )
            self.db.execute(query, params)

        # 4. Generar Evento de Auditoría (AuditService ya es resiliente)
        self.audit.log_event(
            user_id=user_id,
            user_role=user_role,
            event_type="EVIDENCE_UPLOAD",
            entity="POZO",
            entity_id=project_id,
            new_state={"file_name": file_name, "hash": file_hash, "step": workflow_step},
            metadata=metadata
        )

        return {
            "status": "success",
            "filename": stored_filename,
            "hash": file_hash
        }

    def get_evidence_for_well(self, project_id):
        """Recupera el listado de evidencias de un pozo."""
        if self.db.is_available():
            query = "SELECT * FROM well_evidence WHERE id_pozo = %s ORDER BY timestamp_carga DESC"
            return self.db.fetch_all(query, (project_id,))
        else:
            # En mock mode, extraemos la evidencia del log de auditoría
            # para no tener que mantener otro JSON separado de metadatos
            audit_events = self.audit.get_events_for_well(project_id)
            evidence = []
            for ev in audit_events:
                if ev['tipo_evento'] == "EVIDENCE_UPLOAD":
                    state = json.loads(ev['estado_nuevo']) if isinstance(ev['estado_nuevo'], str) else ev['estado_nuevo']
                    evidence.append({
                        "id_pozo": ev['entidad_id'],
                        "nombre_archivo": state['file_name'],
                        "hash_sha256": state['hash'],
                        "etapa_workflow": state['step'],
                        "timestamp_carga": ev['timestamp_utc']
                    })
            return evidence
