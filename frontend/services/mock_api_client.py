import time
import random
import json
import os
import math
from datetime import datetime, timedelta
from .database_service import DatabaseService
from .audit_service import AuditService

class MockApiClient:
    """
    Simula la interacción con el Backend (FastAPI) y el Orquestador (Temporal).
    Utiliza DatabaseService para MySQL y un archivo JSON local como Persistencia de Respaldo.
    """

    def __init__(self, audit_service=None):
        self.db = DatabaseService()
        self.audit = audit_service or AuditService(self.db)
        self.storage_path = "frontend/services/persistence_db.json"
        
        # Cargar datos iniciales desde JSON si existe
        self._db_data = self._load_persistence()
        
        # Mapeo de listas internas con datos por defecto si están vacíos
        self._db_projects = self._db_data.get('projects') or self._generate_mock_projects()
        self._db_master_people = self._db_data.get('people') or self._generate_mock_people()
        self._db_master_equipment = self._db_data.get('equipment') or self._generate_mock_equipment()
        self._db_master_supplies = self._db_data.get('supplies') or self._generate_mock_supplies()

        # --- LOGICA OFFLINE ---
        self._is_online = True
        self._outbox = self._db_data.get('sync_outbox') or []
        self._offline_cache = self._db_data.get('offline_cache') or {}
        self._emergency_inbox = self._db_data.get('emergency_inbox') or []

    def _get_distance(self, lat1, lon1, lat2, lon2):
        """Calcula distancia en km entre dos puntos (haversine aproximado para mock)."""
        return math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2) * 111

    def _load_persistence(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_persistence(self):
        data = {
            "projects": self._db_projects,
            "people": self._db_master_people,
            "equipment": self._db_master_equipment,
            "supplies": self._db_master_supplies,
            "sync_outbox": self._outbox,
            "offline_cache": self._offline_cache,
            "emergency_inbox": self._emergency_inbox
        }
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def _generate_mock_projects(self):
        return [
            {
                "id": "X-123",
                "nombre": "Pozo X-123",
                "yacimiento": "Los Perales",
                "campana": "Campaña Norte 2024",
                "estado_proyecto": "EN_EJECUCION",
                "progreso": 45,
                "proximo_hito": "Cementación Faja 2",
                "responsable": "Juan Pérez",
                "lat": -46.4328, "lon": -67.5267,  # Los Perales, Chubut
                "workflow_status": "WAITING_DAILY_REPORT"
            },
            {
                "id": "A-321",
                "nombre": "Pozo A-321",
                "yacimiento": "Las Heras",
                "campana": "Campaña Norte 2024",
                "estado_proyecto": "PLANIFICADO",
                "progreso": 10,
                "proximo_hito": "Asignación de Equipos",
                "responsable": "Maria Gonzalez",
                "lat": -46.5428, "lon": -68.9344,  # Las Heras, Santa Cruz
                "workflow_status": "WAITING_DTM_ASSIGNMENT"
            },
            {
                "id": "Z-789",
                "nombre": "Pozo Z-789",
                "yacimiento": "El Tordillo",
                "campana": "Campaña Sur 2024",
                "estado_proyecto": "BLOQUEADO",
                "progreso": 60,
                "proximo_hito": "Resolución Incidencia HSE",
                "responsable": "Carlos Ruiz",
                "lat": -45.8569, "lon": -67.4853,  # El Tordillo, Chubut
                "workflow_status": "BLOCKED_BY_INCIDENT"
            },
            {
                "id": "M-555",
                "nombre": "Pozo M-555",
                "yacimiento": "Cañadón Seco",
                "campana": "Campaña Sur 2024",
                "estado_proyecto": "EN_ESPERA_APROBACION",
                "progreso": 95,
                "proximo_hito": "Firma Auditoría Final",
                "responsable": "Juan Pérez",
                "lat": -46.5337, "lon": -67.6172,  # Cañadón Seco, Santa Cruz
                "workflow_status": "WAITING_FINAL_APPROVAL"
            }
        ]

    def _generate_mock_people(self):
        return [
            {"name": "Juan Pérez", "role": "Supervisor", "category": "DIRECTO", "medical_ok": True, "induction_ok": True},
            {"name": "Maria Gonzalez", "role": "HSE", "category": "DIRECTO", "medical_ok": True, "induction_ok": True},
            {"name": "Sebastian Cannes", "role": "Gerente", "category": "DIRECTO", "medical_ok": True, "induction_ok": True},
            {"name": "Roberto Ruiz", "role": "Operario", "category": "INDIRECTO", "medical_ok": True, "induction_ok": False}
        ]

    def _generate_mock_equipment(self):
        return [
            {"name": "Pulling Unit #01", "type": "PULLING", "category": "DIRECTO", "status": "OPERATIVO"},
            {"name": "Cisterna 25m3 #1", "type": "CISTERNA", "category": "INDIRECTO", "status": "OPERATIVO"},
            {"name": "Camion de Apoyo", "type": "APERTURA", "category": "INDIRECTO", "status": "DISPONIBLE"}
        ]

    def _generate_mock_supplies(self):
        return [
            {"item": "Cemento (Bolsas)", "unit": "u", "min": 50},
            {"item": "Agua Industrial", "unit": "m3", "min": 10},
            {"item": "Gasoil", "unit": "lts", "min": 500}
        ]

    def get_all_logistics(self):
        """Consolida información logística de todos los proyectos activos."""
        logistics_data = []
        for p in self._db_projects:
            detail = self.get_project_detail(p['id'])
            if detail:
                for t in detail.get('transport_list', []):
                    t_copy = t.copy()
                    t_copy['project_id'] = p['id']
                    t_copy['project_name'] = p['nombre']
                    logistics_data.append(t_copy)
        return logistics_data

    def get_all_supplies_status(self):
        """Consolida el estado de stock crítico de todos los proyectos."""
        stock_status = []
        for p in self._db_projects:
            detail = self.get_project_detail(p['id'])
            if detail:
                for s in detail.get('stock_list', []):
                    s_copy = s.copy()
                    s_copy['project_id'] = p['id']
                    s_copy['project_name'] = p['nombre']
                    stock_status.append(s_copy)
        return stock_status

    # --- QUERIES (Lectura) ---

    def get_dashboard_stats(self):
        """Simula KPIs agregados para el Dashboard Gerencial."""
        df = self._db_projects
        return {
            "total_activos": len(df),
            "en_planificacion": len([p for p in df if p['estado_proyecto'] == 'PLANIFICADO']),
            "en_ejecucion": len([p for p in df if p['estado_proyecto'] == 'EN_EJECUCION']),
            "bloqueados": len([p for p in df if p['estado_proyecto'] == 'BLOQUEADO']),
            "alertas_activas": 2 # Hardcoded simulation
        }

    def get_projects(self, filter_status=None):
        """Retorna lista de proyectos (MODO MOCK EXCLUSIVO)."""
        # --- BD Comentada para Local ---
        # try:
        #     db_pozos = self.db.fetch_all("SELECT * FROM tbl_pozos")
        #     ...
        # except Exception as e:
        #     print(f"[ERROR] DB: {e}")
        
        processed = self._db_projects
        if filter_status and filter_status != 'Todos':
            return [p for p in processed if p['estado_proyecto'] == filter_status]
        return processed

    def get_master_personnel(self):
        """Retorna personal (MODO MOCK EXCLUSIVO)."""
        # try:
        #     return self.db.fetch_all("SELECT * FROM tbl_personal_catalogo")
        # except:
        return self._db_master_people

    def get_master_equipment(self):
        """Retorna equipos (MODO MOCK EXCLUSIVO)."""
        # try:
        #     return self.db.fetch_all("SELECT * FROM tbl_equipos_catalogo")
        # except:
        return self._db_master_equipment

    def get_master_supplies(self):
        """Retorna insumos (MODO MOCK EXCLUSIVO)."""
        # try:
        #     return self.db.fetch_all("SELECT * FROM tbl_stock_inventario WHERE id_expediente='CATALOGO'")
        # except:
        return self._db_master_supplies

    def get_project_detail(self, project_id):
        """Retorna detalle completo de un proyecto con lógica basada en el Estado."""
        # Simula busqueda en persistencia local
        project = next((p for p in self._db_projects if p['id'] == project_id), None)
        if not project:
            return None
        
        status = project.get('estado_proyecto', 'PLANIFICADO')
        project_copy = project.copy()
        project_copy['well'] = project['id']
        project_copy['name'] = project['nombre']
        project_copy['status'] = status

        well_lat = project.get('lat', -45.8)
        well_lon = project.get('lon', -67.4)

        # --- LÓGICA BASADA EN ESTADO ---
        if status == "PLANIFICADO":
            project_copy['dtm_confirmado'] = False
            project_copy['personal_confirmado_hoy'] = False
            project_copy['allowed_operations'] = ["ESPERA"]
            transports = [
                {"id": "T01", "type": "Minibus", "driver": "Logistica Sur", "status": "CARGANDO_RECURSOS", "time_plan": "07:30", "gps_active": True, "cur_lat": well_lat - 0.2, "cur_lon": well_lon - 0.2, "dist_to_well": 25.0, "eta_minutes": 45},
                {"id": "T02", "type": "Camion Cisterna", "driver": "Aguas Patagonicas", "status": "PROGRAMADO", "time_plan": "08:00", "gps_active": False},
            ]
            equipment = [
                {"name": "Pulling Unit #01", "category": "DIRECTO", "type": "PULLING", "status": "OPERATIVO", "assigned": True, "is_on_location": False},
            ]
            telemetry = None
        elif status == "BLOQUEADO":
            project_copy['dtm_confirmado'] = True
            project_copy['personal_confirmado_hoy'] = True
            project_copy['allowed_operations'] = ["ESPERA"]
            transports = [
                {"id": "T01", "type": "Minibus", "driver": "Logistica Sur", "status": "ARRIBO", "time_plan": "07:30", "time_arrival": "07:15", "gps_active": False},
                {"id": "T03", "type": "Cisterna Combustible", "driver": "YPF Directo", "status": "DEMORADO_CHECKPOINT", "time_plan": "09:00", "gps_active": True, "cur_lat": well_lat + 0.05, "cur_lon": well_lon + 0.02, "dist_to_well": 5.4, "eta_minutes": 15},
            ]
            equipment = [
                {"name": "Pulling Unit #01", "category": "DIRECTO", "type": "PULLING", "status": "FALLA CRITICA", "assigned": True, "is_on_location": True},
            ]
            telemetry = self._generate_rig_telemetry(critical_fail=True)
        else: # EN_EJECUCION
            project_copy['dtm_confirmado'] = True
            project_copy['personal_confirmado_hoy'] = True
            project_copy['allowed_operations'] = ["ESPERA", "CEMENTACION", "DTM"]
            transports = [
                {"id": "T01", "type": "Minibus", "driver": "Logistica Sur", "status": "ARRIBO", "time_plan": "07:30", "time_arrival": "07:10", "gps_active": False},
                {
                    "id": "T02", "type": "Camion Cisterna (25m3)", 
                    "driver": "Aguas Patagonicas", 
                    "status": "EN RUTA", 
                    "time_plan": "08:00",
                    "gps_active": True,
                    "cur_lat": well_lat + 0.1, 
                    "cur_lon": well_lon + 0.05,
                    "dist_to_well": 12.5,
                    "eta_minutes": 25 
                },
            ]
            equipment = [
                {"name": "Pulling Unit #01", "category": "DIRECTO", "type": "PULLING", "status": "OPERATIVO", "assigned": True, "is_on_location": True},
                {"name": "Cementador #1", "category": "DIRECTO", "type": "CEMENTADOR", "status": "OPERATIVO", "assigned": True, "is_on_location": True},
            ]
            telemetry = self._generate_rig_telemetry()

        project_copy['transport_list'] = transports
        project_copy['equipment_list'] = equipment
        project_copy['rig_telemetry'] = telemetry
        
        # Datos comunes (Personal y Stock)
        project_copy['personnel_list'] = [
            {"id": "PD01", "name": "Juan Perez", "role": "Supervisor", "category": "DIRECTO", "critical": True, "present": True,
             "medical_ok": True, "medical_source": "AUTOMATIC", "medical_validated_by": "Corp", "medical_validated_at": "2026-01-15 08:00",
             "induction_ok": True, "induction_source": "AUTOMATIC", "induction_validated_by": "HSE", "induction_validated_at": "2026-01-10 10:00"},
            {"id": "PD02", "name": "Carlos Gomez", "role": "Op. Pulling", "category": "DIRECTO", "critical": True, "present": True,
             "medical_ok": True, "medical_source": "AUTOMATIC", "medical_validated_by": "Corp", "medical_validated_at": "2026-01-20 09:00",
             "induction_ok": status != "BLOQUEADO", "induction_source": "AUTOMATIC", "induction_validated_by": "HSE", "induction_validated_at": "2025-12-01 14:00"},
        ]
        
        project_copy['stock_list'] = [
            {"item": "Cemento (Bolsas)", "current": 150 if status != "PLANIFICADO" else 0, "consumed": 0, "min": 50, "unit": "u"},
            {"item": "Agua Industrial", "current": 25.0 if status != "PLANIFICADO" else 5.0, "consumed": 0, "min": 10.0, "unit": "m3"},
        ]

        # Quotas
        project_copy['quotas'] = {
            "DIRECTO": {"PULLING": {"target": 1, "current": 1 if status != "PLANIFICADO" else 0}},
            "PERSONNEL": {"DIRECTO": {"target": 10, "current": 10 if status != "PLANIFICADO" else 0}}
        }

        return project_copy

    def analyze_project_status(self, project_id):
        """Analiza toda la info disponible y saca una conclusión o recomendación."""
        project = self.get_project_detail(project_id)
        if not project:
            return "No encuentro datos suficientes para analizar este pozo."

        status = project['status']
        recommendations = []
        alerts = []

        # 1. Análisis de Gates / HSE
        if not project.get('dtm_confirmado'):
            alerts.append("🔴 **BLOQUEO LEGAL**: El Gate DTM está cerrado.")
            recommendations.append("Solicitar la confirmación del DTM al centro de planificación para habilitar la locación.")
        
        for p in project.get('personnel_list', []):
            if not p['medical_ok'] or not p['induction_ok']:
                alerts.append(f"🔴 **RIESGO HSE**: {p['name']} ({p['role']}) no está apto.")
                recommendations.append(f"Reemplazar a {p['name']} o actualizar su documentación HSE antes de iniciar tareas críticas.")

        # 2. Análisis de Telemetría (EDR)
        telemetry = project.get('rig_telemetry')
        if telemetry:
            if telemetry['rig_state'] == 'ALARM_STOP':
                alerts.append("🚨 **PARADA DE EMERGENCIA**: El equipo de Pulling está en ALARM_STOP.")
                recommendations.append("Inspeccionar falla crítica en Pulling Unit #01 y verificar bitácora de mantenimiento.")
            
            if telemetry['annular_pressure'] > 120:
                alerts.append(f"⚠️ **ALTA PRESIÓN ANULAR**: {telemetry['annular_pressure']} psi detectados.")
                recommendations.append("Realizar prueba de integridad de la faja o ventear según protocolo de control de pozo.")

        # 3. Análisis de Logística / Stock
        for t in project.get('transport_list', []):
            if t['status'] == 'DEMORADO_CHECKPOINT':
                alerts.append(f"🛑 **DEMORA LOGÍSTICA**: {t['type']} demorado en checkpoint.")
                recommendations.append(f"Contactar a {t['driver']} para agilizar el ingreso de recursos críticos.")

        # 4. Análisis de Stock
        for s in project.get('stock_list', []):
            if s['current'] < s['min']:
                alerts.append(f"📦 **STOCK BAJO**: {s['item']} ({s['current']} {s['unit']})")
                recommendations.append(f"Generar pedido de abastecimiento urgente para {s['item']}.")

        # Generar Respuesta
        if not alerts:
            summary = "✅ **Estado Operativo Óptimo.** Todos los parámetros están dentro de la norma."
            rec_text = "Continuar con el cronograma y emitir el reporte diario al finalizar el turno."
        else:
            summary = "⚠️ **Análisis de Situación:**\n" + "\n".join(alerts)
            rec_text = "**Acciones Recomendadas:**\n" + "\n".join([f"{i+1}. {r}" for i, r in enumerate(list(set(recommendations)))])

        return f"{summary}\n\n{rec_text}"

    def _generate_rig_telemetry(self, critical_fail=False):
        """Simula datos de EDR (Electronic Data Recorder) de alta fidelidad."""
        has_val = not critical_fail
        return {
            "hook_load": random.uniform(20.0, 25.0) if has_val else 0.0,
            "hook_load_unit": "tn",
            "wob": random.uniform(2.0, 5.0) if has_val else 0.0,
            "wob_unit": "tn",
            "bit_depth": random.uniform(1200.0, 1500.0),
            "bit_depth_unit": "m",
            "pump_pressure": random.uniform(800.0, 1200.0) if has_val else 0.0,
            "pump_pressure_unit": "psi",
            "annular_pressure": random.uniform(50.0, 150.0) if has_val else 0.0,
            "annular_pressure_unit": "psi",
            "pit_volume": random.uniform(40.0, 45.0) if has_val else 0.0,
            "pit_volume_unit": "m3",
            "trip_tank": random.uniform(2.5, 3.0) if has_val else 0.0,
            "trip_tank_unit": "m3",
            "torque": random.uniform(500.0, 800.0) if has_val else 0.0,
            "torque_unit": "ft-lb",
            "spm": random.randint(40, 60) if has_val else 0,
            "gas_total": random.uniform(0.1, 0.5) if has_val else 0.0,
            "gas_unit": "%",
            "rig_state": "TRIPPING" if has_val else "ALARM_STOP",
            "last_update": datetime.now().strftime("%H:%M:%S")
        }

    def upsert_well(self, data, user_id="system", user_role="admin"):
        """CRUD: Registro de Pozo (MODO MOCK EXCLUSIVO)."""
        print(f"[MOCK] Guardando pozo {data['id']}")
        
        # Obtener estado anterior para el log
        existing = next((p for p in self._db_projects if p['id'] == data['id']), None)
        prev_state = existing.copy() if existing else None
        
        # Persistir en JSON local
        if existing: existing.update(data)
        else: self._db_projects.append(data)
        self._save_persistence()

        # Auditoría
        self.audit.log_event(
            user_id=user_id,
            user_role=user_role,
            event_type="DATA_CHANGE",
            entity="POZO",
            entity_id=data['id'],
            prev_state=prev_state,
            new_state=data,
            metadata={"action": "upsert_well"}
        )
        return True

    def upsert_person(self, data):
        """CRUD: Alta de Personal (MODO MOCK EXCLUSIVO)."""
        print(f"[MOCK] Guardando persona {data['name']}")
        # --- BD Comentada ---
        
        # Backup local
        self._db_master_people.insert(0, data)
        self._save_persistence()
        return True

    def upsert_equipment(self, data):
        """CRUD: Alta de Equipo (MODO MOCK EXCLUSIVO)."""
        print(f"[MOCK] Guardando equipo {data['name']}")
        # --- BD Comentada ---
        
        self._db_master_equipment.insert(0, data)
        self._save_persistence()
        return True

    def upsert_supply(self, data):
        """CRUD: Alta de Insumo (MODO MOCK EXCLUSIVO)."""
        print(f"[MOCK] Guardando insumo {data['item']}")
        # --- BD Comentada ---
            
        self._db_master_supplies.insert(0, data)
        self._save_persistence()
        return True

    def upsert_campaign(self, data):
        """CRUD: Alta/Edición de Campaña en MySQL."""
        print(f"[DB] Admin CRUD: Guardando campaña {data['name']}")
        # ... (Temporal signal/DB logic bypass for MVP)
        self._save_persistence()
        return True

    def send_signal_justificacion(self, project_id, file_name):
        """Signal: Admin carga justificación técnica."""
        print(f"[MOCK] Enviando Signal 'Justificacion' para {project_id} con archivo {file_name}")
        # En prod: grpc_client.signal_workflow(...)
        return True

    def send_signal_dtm(self, project_id, resources_list):
        """Signal: Admin asigna recursos (DTM)."""
        print(f"[MOCK] Enviando Signal 'AsignarRecursos' para {project_id}. Equipos: {resources_list}")
        time.sleep(1) # Simula latencia red
        return True

    def send_signal_check_personal(self, project_id, personal_data):
        """Signal: Check-in de personal diario."""
        print(f"[MOCK] Enviando Signal 'CheckPersonal' para {project_id}. Data: {personal_data}")
        return True

    def send_signal_check_transporte(self, project_id, transporte_data):
        """Signal: Confirmación de transporte."""
        print(f"[MOCK] Enviando Signal 'CheckTransporte' para {project_id}. Data: {transporte_data}")
        return True

    def send_signal_check_permisos(self, project_id, permisos_data):
        """Signal: Validación de permisos diarios."""
        print(f"[MOCK] Enviando Signal 'CheckPermisos' para {project_id}. Data: {permisos_data}")
        return True

    # --- MOTOR DE EMERGENCIA (SMS / SATELITAL) ---

    def encode_for_emergency_channel(self, project_id, report_data):
        """Genera un string comprimido para canales de bajo ancho de banda (SMS/Sat)."""
        op_code = report_data.get('op', 'UNK')[:3].upper()
        # Mock encoding: ABND:[ID]:[OP]:[DESC_LEN]:[CHECKSUM]
        desc_summary = report_data.get('desc', '')[:10]
        checksum = sum(ord(c) for c in desc_summary) % 100
        encoded = f"ABND:{project_id}:{op_code}:{len(desc_summary)}:{checksum}"
        return encoded.upper()

    def simulate_emergency_tx(self, channel, encoded_msg):
        """Simula la transmisión por un canal no-IP."""
        print(f"[MOCK] Transmitiendo vía {channel}: {encoded_msg}")
        # Simular delay de satélite o red de texto
        time.sleep(2)
        return True

    def send_signal_parte_diario(self, project_id, report_data, channel="INTERNET", user_id="unknown", user_role="unknown"):
        """Signal: Ing Campo envía parte diario con selección de canal."""
        
        # Registrar evento de auditoría
        self.audit.log_event(
            user_id=user_id,
            user_role=user_role,
            event_type="SIGNAL_SENT",
            entity="POZO",
            entity_id=project_id,
            new_state=report_data,
            metadata={"channel": channel, "signal": "ParteDiario"}
        )

        if channel == "INTERNET" and not self._is_online:
            item = {
                "id": f"sync_{int(time.time())}",
                "project_id": project_id,
                "type": "PARTE_DIARIO",
                "data": report_data,
                "ts": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            self._outbox.append(item)
            self._save_persistence()
            return {"status": "QUEUED", "msg": "Guardado en Outbox (Sin conexión)."}

        if channel in ["SMS", "SATELITAL"]:
            encoded = self.encode_for_emergency_channel(project_id, report_data)
            self.simulate_emergency_tx(channel, encoded)
            
            # Guardar en "Inundación Central" (Simulación Receptor)
            self._emergency_inbox.insert(0, {
                "id": f"rec_{int(time.time())}",
                "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "channel": channel,
                "project_id": project_id,
                "raw_code": encoded,
                "decoded_data": report_data,
                "status": "DECODED"
            })
            self._save_persistence()
            
            return {"status": "EMERGENCY_SENT", "msg": f"Enviado vía {channel}: {encoded}"}

        # Flujo Normal Online
        print(f"[MOCK] Enviando Signal 'ParteDiario' via {channel} para {project_id}.")
        time.sleep(1.5)
        return {"status": "SENT", "msg": "Parte enviado exitosamente por Internet"}

    # --- LOGICA DE SINCRONIZACION & CONECTIVIDAD ---

    def set_connectivity(self, online: bool):
        self._is_online = online
        return f"Modo {'Online' if online else 'Offline'} activado."

    def is_online(self):
        return self._is_online

    def get_sync_count(self):
        return len(self._outbox)

    def synchronize(self):
        """Procesa la cola de sincronización."""
        if not self._is_online:
            return False, "No hay conexión para sincronizar."
        
        count = len(self._outbox)
        if count == 0:
            return True, "No hay datos pendientes."

        # Simular procesamiento
        time.sleep(2)
        self._outbox = []
        self._save_persistence()
        return True, f"Sincronizados {count} eventos exitosamente."

    def get_emergency_inbox(self):
        """Retorna los mensajes recibidos por canales de emergencia."""
        return self._emergency_inbox

    def manual_override_gate(self, project_id, gate_id, reason, user_id="unknown", user_role="unknown"):
        """Permite forzar un Gate operativo en modo offline."""
        
        # 0. Registrar Override en Tabla Dedicada
        query = """
            INSERT INTO operational_overrides (id_pozo, gate_id, id_usuario_autoriza, motivo_obligatorio)
            VALUES (%s, %s, %s, %s)
        """
        self.db.execute(query, (project_id, gate_id, user_id, reason))

        # 1. Registrar Evento de Auditoría
        self.audit.log_event(
            user_id=user_id,
            user_role=user_role,
            event_type="OPERATIONAL_OVERRIDE",
            entity="POZO",
            entity_id=project_id,
            new_state={"gate": gate_id, "reason": reason},
            metadata={"action": "manual_override"}
        )

        item = {
            "id": f"sync_ov_{int(time.time())}",
            "project_id": project_id,
            "type": "GATE_OVERRIDE",
            "data": {"gate": gate_id, "reason": reason},
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self._outbox.append(item)
        
        # Guardar en cache local para que la UI refleje el cambio de inmediato
        if project_id not in self._offline_cache:
            self._offline_cache[project_id] = {}
        self._offline_cache[project_id][gate_id] = True
        
        self._save_persistence()
        return True

    # --- CHAT OPERATIVO & IA ASSISTANT ---

    def get_chat_history(self, project_id):
        """Simula recuperación de historial de chat de la DB."""
        # Historial base simulado
        return [
            {"id": "c1", "ts": "2026-02-01 09:00", "user": "Supervisor", "rol": "Supervisor", "origen": "HUMANO", 
             "msg": "¿Por qué está bloqueado el permiso de Izaje Pesado?"},
            {"id": "c2", "ts": "2026-02-01 09:01", "user": "ASISTENTE_IA", "rol": "IA", "origen": "IA", 
             "msg": "🤖 Hola. El permiso de Izaje Pesado venció el 2026-01-30. Requiere renovación en el módulo de Permisos para habilitar la operación."},
            {"id": "c3", "ts": "2026-02-01 10:30", "user": "HSE Officer", "rol": "HSE", "origen": "HUMANO", 
             "msg": "He revisado la certificación de Roberto Ruiz, pero sigue apareciendo como médica vencida."},
        ]

    def send_chat_message(self, project_id, user_role, message):
        """
        MOTOR DE IA OPERATIVA ANTIGRAVITY v3.5 (Expert Process Engine)
        Conocimiento: Ciclo de Vida P&A, Reglas HSE, Listados Reales y Data-Driven Search.
        """
        print(f"[MOCK] AI Brain v3.5: Scanning for '{message}' (Context: {project_id or 'Global'})")
        
        msg_lower = message.lower()
        response_msg = ""
        
        # 1. BÚSQUEDA GLOBAL / LISTADOS DE POZOS
        if any(word in msg_lower for word in ["listado", "pozos", "todos los pozos", "general", "yacimientos"]):
            response_msg = "🤖 **Reporte Geral de Pozos Activos (Visión Global):**\n\n"
            for p in self._db_projects:
                response_msg += (
                    f"📍 **{p['nombre']}** ({p['id']})\n"
                    f"   - Yacimiento: {p['yacimiento']}\n"
                    f"   - Estado: `{p['estado_proyecto']}` | Avance: {p['progreso']}%\n"
                )
            response_msg += "\n¿Deseas el detalle técnico de algún pozo en particular? O puedes pedirme un 'Análisis de Situación'."

        # 2. CONOCIMIENTO INTEGRAL DEL PROCESO (Documento Inicial P&A)
        elif any(word in msg_lower for word in ["proceso", "ciclo", "etapa", "pasos", "documento inicial", "fases", "abandono"]):
            response_msg = (
                "🤖 **Conocimiento Integral del Proceso de Abandono:**\n\n"
                "El proceso se divide en **6 ETAPAS** obligatorias que garantizan la seguridad y trazabilidad:\n\n"
                "• **1. Inicio Trámite**: Carga de la Justificación Técnica.\n"
                "• **2. Planificación**: Asignación de recursos (Personal, Equipos, Logística) tras el DTM.\n"
                "• **3. Ejecución**: Fase operativa donde se rinde el *Parte Diario*. El sistema bloquea si hay fallas HSE.\n"
                "• **4. Incidencia (Bloqueo)**: Estado disparado ante riesgos críticos (HSE/Técnico).\n"
                "• **5. Cierre & Auditoría**: Validación de evidencias físicas y documentales.\n"
                "• **6. Finalizado**: Cierre legal del expediente.\n\n"
                "**Reglas de Oro**: \n"
                "- Validaciones Médicas e Inducción son AUTOMÁTICAS y provienen de sistemas maestros.\n"
                "- El stock bajo mínimo permite operar bajo 'Riesgo Asumido' (Estado Parcial)."
            )

        # 3. IDENTIFICACIÓN DE POZO / PERSONAL / CARGOS (Who is Who)
        target_project = project_id
        for p in self._db_projects:
            if p['id'].lower() in msg_lower or p['nombre'].lower() in msg_lower:
                target_project = p['id']

        project = self.get_project_detail(target_project) if target_project else None

        if any(word in msg_lower for word in ["quien", "rol", "personal", "gente", "supervisor", "hse", "operario", "médico", "inducción"]):
            if not project:
                response_msg = "🤖 Por favor selecciona un pozo para ver quién es quién. A nivel general, el equipo estándar por pozo incluye 1 Supervisor, 1 HSE y 2 Ayudantes."
            else:
                response_msg = f"🤖 **Equipo Asignado al Pozo {target_project}:**\n\n"
                for p in project['personnel_list']:
                    # Filtro por cargo si se solicita
                    if any(role.lower() in msg_lower for role in ["supervisor", "hse", "ayudante", "operario"]) and not any(role.lower() in msg_lower for role in p['role'].lower().split()):
                        continue
                        
                    status = "✅ APTO" if p['medical_ok'] and p['induction_ok'] else "🚨 NO APTO"
                    crit = " (CRÍTICO)" if p['critical'] else ""
                    response_msg += f"👤 **{p['name']}** - {p['role']}{crit}\n   - Estado: {status}\n"
                    if not p['medical_ok']: 
                        response_msg += f"   - 🩺 Falla: {p['medical_source']} (Vencimiento: 2025-11-15)\n"
                    if not p['induction_ok']:
                        response_msg += "   - 🦺 Falla: Inducción HSE vencida.\n"
                    response_msg += "\n"

        # 4. DETALLES TÉCNICOS / LOGÍSTICA / STOCK
        elif any(word in msg_lower for word in ["ubicacion", "gps", "coordenadas", "longitud", "latitud", "yacimiento"]):
            if project:
                response_msg = (
                    f"🤖 **Identificación Técnica {project['id']}:**\n"
                    f"• Coordenadas: Lat {project['lat']}, Lon {project['lon']}\n"
                    f"• Yacimiento: {project['yacimiento']}\n"
                    f"• Responsable: {project['responsable']}"
                )
            else:
                response_msg = "🤖 Por favor selecciona un pozo para ver sus coordenadas exactas."

        elif any(word in msg_lower for word in ["logistica", "transporte", "stock", "insumos", "camion", "minibus"]):
            if project:
                if "stock" in msg_lower or "insumos" in msg_lower:
                    response_msg = f"🤖 **Balance de Insumos ({target_project}):**\n"
                    for s in project['stock_list']:
                        response_msg += f"- {s['item']}: {s['current']} {s['unit']} (Mínimo: {s['min']})\n"
                else:
                    response_msg = f"🤖 **Plan de Logística ({target_project}):**\n"
                    for t in project['transport_list']:
                        response_msg += f"- {t['type']} ({t['driver']}): {t['status']} (Arribo: {t['time_plan']})\n"
            else:
                response_msg = "🤖 Debes estar en el detalle de un pozo para ver su logística o stock."

        elif any(word in msg_lower for word in ["analiza", "recomienda", "hacer", "estado", "situacion", "conclusión", "qué hago"]):
            if project:
                response_msg = f"🤖 **Análisis de AbandonPro para {target_project}:**\n\n"
                response_msg += self.analyze_project_status(target_project)
            else:
                response_msg = "🤖 Por favor selecciona un pozo para que pueda analizar su estado operativo actual."

        # 5. FALLBACK
        if not response_msg:
             response_msg = (
                "🤖 **Soy tu Asistente Operativo.**\n"
                "Puedo ayudarte con:\n"
                "- 📜 **Listados**: 'Dame la lista de todos los pozos'.\n"
                "- 👤 **Personal**: '¿Quién es el supervisor?' o '¿Qué gente tengo?'.\n"
                "- 📍 **Fases**: 'Explícame el proceso de abandono' o 'Cuáles son las etapas'.\n"
                "- ⚙️ **Operativo**: 'Estado de stock', 'Ubicación GPS' o 'Logística'."
            )

        return {
            "sent": {"id": "c_user_" + str(int(time.time())), "ts": datetime.now().strftime("%Y-%m-%d %H:%M"), "user": "User", "rol": user_role, "origen": "HUMANO", "msg": message},
            "response": {
                "id": "c_ia_" + str(int(time.time())),
                "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "user": "ASISTENTE_IA",
                "rol": "IA",
                "origen": "IA",
                "msg": response_msg
            }
        }
