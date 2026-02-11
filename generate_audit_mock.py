import hashlib
import json
import os
from datetime import datetime, timedelta

def calculate_hash(event_data, prev_hash):
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

def generate_mock_audit():
    events = []
    prev_hash = "0" * 64
    base_time = datetime.utcnow() - timedelta(days=10)

    raw_events = [
        # Session 1: Planning A-321
        {"user": "m.gonzalez", "role": "HSE", "type": "DATA_CHANGE", "ent": "POZO", "ent_id": "A-321", "ant": None, "new": {"estado": "PLANIFICADO"}, "meta": {"event": "Campaña Norte Initial Load"}},
        
        # Session 2: Activity on X-123
        {"user": "j.perez", "role": "Supervisor", "type": "EVIDENCE_UPLOAD", "ent": "POZO", "ent_id": "X-123", "ant": None, "new": {"file": "X-123_pre_work_site.jpg", "hash": "sha256:d5f..."}, "meta": {"desc": "Validación estado inicial locación"}},
        {"user": "j.perez", "role": "Supervisor", "type": "DATA_CHANGE", "ent": "POZO", "ent_id": "X-123", "ant": {"progreso": 40}, "new": {"progreso": 45}, "meta": {"action": "Inyectando Tapón de Cemento #1"}},
        {"user": "j.perez", "role": "Supervisor", "type": "SIGNAL_SENT", "ent": "POZO", "ent_id": "X-123", "ant": None, "new": {"signal": "PARTE_DIARIO", "channel": "INTERNET"}, "meta": {"report": "Cementing ops 22and Feb"}},

        # Session 3: Z-789 Incident Log
        {"user": "m.gonzalez", "role": "HSE", "type": "DATA_CHANGE", "ent": "POZO", "ent_id": "Z-789", "ant": {"workflow": "NORMAL"}, "new": {"workflow": "BLOCKED_BY_INCIDENT"}, "meta": {"incident_id": "INC-882", "desc": "Minor fluid seepage near cellar"}},
        {"user": "m.gonzalez", "role": "HSE", "type": "EVIDENCE_UPLOAD", "ent": "POZO", "ent_id": "Z-789", "ant": None, "new": {"file": "Z-789_leakage_cellar.jpg", "hash": "sha256:a12b..."}, "meta": {"desc": "Photo of leakage for insurance"}},
        {"user": "s.cannes", "role": "Gerente", "type": "OPERATIONAL_OVERRIDE", "ent": "POZO", "ent_id": "Z-789", "ant": {"gate": "HSE", "status": "LOCKED"}, "new": {"gate": "HSE", "status": "OVERRIDDEN"}, "meta": {"justification": "Remediación superficial certificada. Se autoriza continuar con taponamiento."}},

        # Session 4: M-555 Final Steps
        {"user": "j.perez", "role": "Supervisor", "type": "EVIDENCE_UPLOAD", "ent": "POZO", "ent_id": "M-555", "ant": None, "new": {"file": "M-555_capped_wellhead.jpg", "hash": "sha256:4432..."}, "meta": {"desc": "Wellhead cut and capped - Final"}},
        {"user": "s.cannes", "role": "Gerente", "type": "DATA_CHANGE", "ent": "POZO", "ent_id": "M-555", "ant": {"estado": "EN_EJECUCION"}, "new": {"estado": "EN_ESPERA_APROBACION"}, "meta": {"event": "Final field audit completed"}},
        
        # Logins
        {"user": "giriarte", "role": "Gerente", "type": "LOGIN_SUCCESS", "ent": "SISTEMA", "ent_id": "GLOBAL", "ant": None, "new": {"session": "active"}, "meta": {"device": "Windows Ops Room"}},
        {"user": "j.perez", "role": "Supervisor", "type": "LOGIN_SUCCESS", "ent": "SISTEMA", "ent_id": "GLOBAL", "ant": None, "new": {"session": "active"}, "meta": {"device": "Android Field Tablet"}}
    ]

    for i, raw in enumerate(raw_events):
        ts = (base_time + timedelta(hours=i*12)).isoformat()
        ev_info = {
            "id_usuario": raw["user"],
            "rol_usuario": raw["role"],
            "tipo_evento": raw["type"],
            "entidad": raw["ent"],
            "entidad_id": raw["ent_id"],
            "estado_anterior": json.dumps(raw["ant"]) if raw["ant"] else None,
            "estado_nuevo": json.dumps(raw["new"]) if raw["new"] else None,
            "metadata": json.dumps(raw["meta"]) if raw["meta"] else None
        }
        
        h = calculate_hash(ev_info, prev_hash)
        
        full_event = {
            "id": i + 1,
            "timestamp_utc": ts,
            "id_usuario": raw["user"],
            "rol_usuario": raw["role"],
            "tipo_evento": raw["type"],
            "entidad": raw["ent"],
            "entidad_id": raw["ent_id"],
            "estado_anterior": ev_info["estado_anterior"],
            "estado_nuevo": ev_info["estado_nuevo"],
            "metadata": ev_info["metadata"],
            "ip_origen": "192.168.1." + str(100+i),
            "hash_previo": prev_hash,
            "hash_evento": h
        }
        events.append(full_event)
        prev_hash = h

    os.makedirs("frontend/services", exist_ok=True)
    with open("frontend/services/audit_events.json", "w", encoding='utf-8') as f:
        json.dump(events, f, indent=4)

    # Create dummy evidence files
    storage_path = "storage/evidence"
    os.makedirs(storage_path, exist_ok=True)
    evidence_files = [
        "X-123_pre_work_site.jpg",
        "Z-789_leakage_cellar.jpg",
        "M-555_capped_wellhead.jpg"
    ]
    for f_name in evidence_files:
        with open(os.path.join(storage_path, f_name), "w") as f:
            f.write(f"Mock photo data for {f_name}")

if __name__ == "__main__":
    generate_mock_audit()
    print("Audit events and dummy evidence files generated.")
