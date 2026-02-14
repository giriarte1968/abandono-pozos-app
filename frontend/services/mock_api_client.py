import time
import random
import json
import os
import math
from datetime import datetime, timedelta
from .database_service import DatabaseService
from .audit_service import AuditService
from .ai_service import AIService

class MockApiClient:
    """
    Simula la interacción con el Backend (FastAPI) y el Orquestador (Temporal).
    Utiliza DatabaseService para MySQL y un archivo JSON local como Persistencia de Respaldo.
    Ahora integra AIService (Gemini Flash) para respuestas inteligentes.
    """

    def __init__(self, audit_service=None):
        self.db = DatabaseService()
        self.audit = audit_service or AuditService(self.db)
        self.ai = AIService() # Inicializar servicio de IA
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
            },
            {
                "id": "P-001",
                "nombre": "Pozo P-001 (YPF)",
                "yacimiento": "Manantiales Behr",
                "campana": "Campaña YPF 2025",
                "estado_proyecto": "EN_EJECUCION",
                "progreso": 25,
                "proximo_hito": "Preparación de Superficie",
                "responsable": "Pedro López",
                "lat": -45.9123, "lon": -67.1234,
                "workflow_status": "WAITING_DAILY_REPORT"
            },
            {
                "id": "P-002",
                "nombre": "Pozo P-002 (YPF)",
                "yacimiento": "Los Toldos",
                "campana": "Campaña YPF 2025",
                "estado_proyecto": "PLANIFICADO",
                "progreso": 5,
                "proximo_hito": "Permisos Municipales",
                "responsable": "Ana Martínez",
                "lat": -45.8234, "lon": -67.2345,
                "workflow_status": "WAITING_DTM_ASSIGNMENT"
            },
            {
                "id": "H-101",
                "nombre": "Pozo H-101 (YPF)",
                "yacimiento": "Bajada del Palo",
                "campana": "Campaña YPF 2025",
                "estado_proyecto": "PLANIFICADO",
                "progreso": 0,
                "proximo_hito": "Evaluación Técnica",
                "responsable": "Luis Fernández",
                "lat": -45.7345, "lon": -67.3456,
                "workflow_status": "WAITING_DTM_ASSIGNMENT"
            },
            {
                "id": "H-102",
                "nombre": "Pozo H-102 (Petrobras)",
                "yacimiento": "El Huemul",
                "campana": "Campaña Petrobras 2025",
                "estado_proyecto": "PLANIFICADO",
                "progreso": 15,
                "proximo_hito": "Movilización Equipos",
                "responsable": "Carlos Ruiz",
                "lat": -45.6456, "lon": -67.4567,
                "workflow_status": "WAITING_DTM_ASSIGNMENT"
            },
            {
                "id": "T-201",
                "nombre": "Pozo T-201 (Petrobras)",
                "yacimiento": "Tierra del Fuego",
                "campana": "Campaña Petrobras 2025",
                "estado_proyecto": "EN_EJECUCION",
                "progreso": 40,
                "proximo_hito": "Cementación Faja 1",
                "responsable": "Roberto Silva",
                "lat": -53.8123, "lon": -67.8912,
                "workflow_status": "WAITING_DAILY_REPORT"
            },
            {
                "id": "C-301",
                "nombre": "Pozo C-301 (Petrobras)",
                "yacimiento": "Cerro Dragón",
                "campana": "Campaña Petrobras 2025",
                "estado_proyecto": "COMPLETADO",
                "progreso": 100,
                "proximo_hito": "Archivo Final",
                "responsable": "María Torres",
                "lat": -45.5567, "lon": -67.5678,
                "workflow_status": "COMPLETED"
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
        # Robustez: Strip y comparacion case-insensitive si falla exacto
        if not project_id: return None
        
        target = str(project_id).strip()
        project = next((p for p in self._db_projects if p['id'] == target), None)
        
        # Fallback case-insensitive
        if not project:
            project = next((p for p in self._db_projects if p['id'].upper() == target.upper()), None)
            
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
        # time.sleep(1) # Simula latencia red
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
        # time.sleep(2)
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
        # time.sleep(1.5)
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
        # time.sleep(2)
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

    def send_chat_message(self, project_id, user_role, message, chat_history=None):
        """
        MOTOR DE IA OPERATIVA ANTIGRAVITY v4.0 (Hybrid RAG)
        Si hay API Key, usa Gemini 1.5 Flash con datos en vivo.
        Si no, usa el motor de reglas legacy v3.5.
        """
        print(f"\n[AI DEBUG] Mensaje Recibido: '{message}'")
        
        # 0. RESOLUCIÓN DE PROYECTO OBJETIVO
        msg_lower = message.lower()
        target_project = project_id
        
        # Intentar inferir proyecto del mensaje si no está seleccionado explícitamente
        for p in self._db_projects:
            if p['id'].lower() in msg_lower or p['nombre'].lower() in msg_lower:
                target_project = p['id']
                
        project = self.get_project_detail(target_project) if target_project else None
        
        # --- OPCIÓN A: INTELIGENCIA ARTIFICIAL REAL (Gemini) ---
        if self.ai.is_available():
            print(f"[AI DEBUG] Usando Motor Generativo (Gemini)")
            
            # Recopilar Contexto Completo
            context_data = project if project else None
            
            # Si quiere logística global, inyectamos eso también
            if "logistica" in msg_lower or "transporte" in msg_lower:
                if not context_data: 
                     context_data = {}
                context_data['global_logistics'] = self.get_all_logistics()

            # Inyección de Clima (WeatherService)
            if project:
                try:
                    from .weather_service import WeatherService
                    ws = WeatherService()
                    weather_data = ws.get_weather(project.get('lat', -46.0), project.get('lon', -67.0))
                    if weather_data:
                        context_data['weather_realtime'] = weather_data
                except Exception as e:
                    print(f"[AI DEBUG] Error fetching weather for context: {e}")
            
            # Inyección de Datos Financieros
            if any(word in msg_lower for word in ["finanzas", "financiero", "contrato", "backlog", "certificacion", "factura", "cobro", "costo", "presupuesto", "margen", "rentabilidad"]):
                try:
                    from .financial_service_mock import financial_service
                    if not context_data:
                        context_data = {}
                    
                    # Inyectar KPIs financieros
                    context_data['financial_kpis'] = financial_service.get_kpis_dashboard()
                    
                    # Inyectar contratos
                    context_data['contratos'] = financial_service.get_contratos()
                    
                    # Inyectar certificaciones recientes
                    context_data['certificaciones'] = financial_service.get_certificaciones()
                    
                    # Si hay un pozo específico, agregar sus costos
                    for p in financial_service.get_pozos():
                        if p['ID_WELL'].lower() in msg_lower:
                            context_data['pozo_financiero'] = p
                            context_data['costos_pozo'] = financial_service.get_costos_pozo(p['ID_WELL'])
                            cert_pozo = next((c for c in financial_service.get_certificaciones() if c['ID_WELL'] == p['ID_WELL']), None)
                            if cert_pozo:
                                context_data['certificacion_pozo'] = cert_pozo
                            break
                    
                    print(f"[AI DEBUG] Contexto financiero inyectado")
                except Exception as e:
                    print(f"[AI DEBUG] Error inyectando contexto financiero: {e}")

            # Llamada al LLM con Historial
            response_msg = self.ai.generate_response(message, context_data, user_role, chat_history=chat_history)
            
            # Post-Procesamiento (Simulado)
            # Aquí podríamos parsear JSON si la IA devolviera acciones estructuradas
            
        # --- OPCIÓN B: MOTOR DE REGLAS (Legacy Fallback) ---
        else:
            print(f"[AI DEBUG] Usando Motor de Reglas (Legacy)")
            
            response_msg = ""
            # ... (Lógica Legacy existente) ...
            
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

            # 2. CONOCIMIENTO INTEGRAL DEL PROCESO
            elif any(word in msg_lower for word in ["proceso", "ciclo", "etapa", "pasos", "documento inicial", "fases", "abandono"]):
                response_msg = (
                    "🤖 **Conocimiento Integral del Proceso de Abandono (Modo Offline):**\n\n"
                    "El proceso se divide en **6 ETAPAS** obligatorias:\n"
                    "1. Inicio Trámite\n2. Planificación (DTM)\n3. Ejecución\n4. Incidencia\n5. Cierre & Auditoría\n6. Finalizado\n"
                )

            # ... (Resto de reglas legacy) ...
            
            # 3. WHO IS WHO
            elif any(word in msg_lower for word in ["quien", "rol", "personal", "gente", "supervisor", "hse", "operario"]):
                if project:
                    response_msg = f"🤖 **Equipo Asignado al Pozo {target_project}:**\n\n"
                    for p in project['personnel_list']:
                        status = "✅" if p['medical_ok'] else "🚨"
                        response_msg += f"👤 **{p['name']}** - {p['role']} {status}\n"
                else:
                    response_msg = "🤖 Selecciona un pozo para ver el personal."

            # 4. LOGISTICA / TECNICO
            elif any(word in msg_lower for word in ["ubicacion", "gps", "logistica", "stock", "cementacion"]):
                if project:
                     response_msg = f"🤖 **Datos Técnicos de {target_project}:**\n"
                     response_msg += f"• Ubicación: {project['lat']}, {project['lon']}\n"
                     response_msg += f"• Estado: {project['status']}\n"
                     response_msg += "Para más detalles, activa el modo Online con Gemini API."
                else:
                    response_msg = "🤖 Selecciona un pozo para ver datos técnicos."
            
            # ANÁLISIS DE SITUACIÓN FINANCIERA INTEGRAL
            elif "analisis de situacion financiera" in msg_lower or "análisis financiero integral" in msg_lower:
                try:
                    from .financial_service_mock import financial_service
                    
                    kpis = financial_service.get_kpis_dashboard()
                    contratos = financial_service.get_contratos()
                    certificaciones = financial_service.get_certificaciones()
                    facturas = financial_service.get_facturas()
                    
                    response_msg = "🤖 **ANÁLISIS DE SITUACIÓN FINANCIERA - REPORTE EJECUTIVO**\n\n"
                    response_msg += "="*60 + "\n"
                    
                    # 1. SALUD FINANCIERA GENERAL
                    response_msg += "\n📊 **1. SALUD FINANCIERA GENERAL**\n\n"
                    response_msg += f"💰 Backlog Contractual: ${kpis['backlog_contractual']:,.2f}\n"
                    response_msg += f"📈 Avance Global: {kpis['avance_financiero_pct']:.1f}% (Financiero) / {kpis['avance_fisico_pct']:.1f}% (Físico)\n"
                    response_msg += f"💵 Saldo de Caja: ${kpis['saldo_caja']:,.2f}\n"
                    response_msg += f"⏱️ Días de Cobertura: {kpis['dias_cobertura']:.0f} días\n"
                    response_msg += f"🏦 Capital de Trabajo Requerido: ${kpis['capital_trabajo']:,.2f}\n\n"
                    
                    # Evaluación general
                    if kpis['alerta_cobertura']:
                        response_msg += "🔴 **ESTADO: CRÍTICO** - Liquidez comprometida\n"
                    elif kpis['backlog_contractual'] < 1000000:
                        response_msg += "🟡 **ESTADO: ATENCIÓN** - Backlog bajo\n"
                    else:
                        response_msg += "🟢 **ESTADO: SALUDABLE** - Indicadores dentro de parámetros\n"
                    
                    # 2. PORTFOLIO DE CONTRATOS
                    response_msg += "\n" + "="*60 + "\n"
                    response_msg += "\n📋 **2. PORTFOLIO DE CONTRATOS**\n\n"
                    for c in contratos:
                        avance = ((c['MONTO_TOTAL_CONTRACTUAL'] - c['BACKLOG_RESTANTE']) / c['MONTO_TOTAL_CONTRACTUAL'] * 100) if c['MONTO_TOTAL_CONTRACTUAL'] > 0 else 0
                        response_msg += f"• {c['NOMBRE_CONTRATO']}\n"
                        response_msg += f"  Backlog: ${c['BACKLOG_RESTANTE']:,.2f} | Avance: {avance:.1f}% | Cert: {c['total_certificaciones']}/{c['CANTIDAD_POZOS']}\n\n"
                    
                    # 3. GESTIÓN DE COBRANZAS
                    response_msg += "="*60 + "\n"
                    response_msg += "\n📄 **3. GESTIÓN DE COBRANZAS**\n\n"
                    total_certificado = sum(cert['MONTO_CERTIFICADO'] for cert in certificaciones)
                    facturas_cobradas = len([f for f in facturas if f['ESTADO'] == 'COBRADA'])
                    facturas_pendientes = len([f for f in facturas if f['ESTADO'] == 'EMITIDA'])
                    
                    response_msg += f"• Total Certificado: ${total_certificado:,.2f}\n"
                    response_msg += f"• Facturas Cobradas: {facturas_cobradas}\n"
                    response_msg += f"• Facturas Pendientes: {facturas_pendientes}\n\n"
                    
                    # 4. RECOMENDACIONES ESTRATÉGICAS PRIORIZADAS
                    response_msg += "="*60 + "\n"
                    response_msg += "\n💡 **4. RECOMENDACIONES ESTRATÉGICAS PRIORIZADAS**\n\n"
                    
                    recomendaciones = []
                    
                    # Prioridad 1: Liquidez
                    if kpis['alerta_cobertura']:
                        recomendaciones.append(("🔴 URGENTE", "LIQUIDEZ", "Días de cobertura críticos. Gestionar cobranzas inmediatamente y evaluar línea de crédito."))
                    
                    # Prioridad 2: Backlog
                    if kpis['backlog_contractual'] < 1000000:
                        recomendaciones.append(("🟡 ALTA", "BACKLOG", "Backlog menor a $1M. Priorizar búsqueda de nuevos contratos."))
                    
                    # Prioridad 3: Pozos completados sin certificar
                    pozos_completados = [p for p in financial_service.get_pozos() if p['ESTADO_PROYECTO'] == 'COMPLETADO']
                    pozos_no_certificados = [p for p in pozos_completados if not any(c['ID_WELL'] == p['ID_WELL'] for c in certificaciones)]
                    if pozos_no_certificados:
                        wells = ', '.join([p['ID_WELL'] for p in pozos_no_certificados])
                        recomendaciones.append(("🟡 ALTA", "CERTIFICACIÓN", f"Pozos {wells} completados sin certificar. Certificar para liberar flujo de caja."))
                    
                    # Prioridad 4: Facturas vencidas
                    import datetime as dt_module
                    hoy = dt_module.datetime.now()
                    facturas_vencidas = [f for f in facturas if f['ESTADO'] == 'EMITIDA' and f['FECHA_VENCIMIENTO'] < hoy]
                    if facturas_vencidas:
                        total_vencido = sum(f['MONTO'] for f in facturas_vencidas)
                        recomendaciones.append(("🟠 MEDIA", "COBRANZA", f"{len(facturas_vencidas)} facturas vencidas (${total_vencido:,.2f}). Contactar clientes."))
                    
                    # Mostrar recomendaciones
                    if recomendaciones:
                        for prioridad, area, accion in recomendaciones:
                            response_msg += f"{prioridad} [{area}]\n   → {accion}\n\n"
                    else:
                        response_msg += "✅ Sin alertas críticas. Situación financiera estable.\n\n"
                    
                    # 5. PRÓXIMOS PASOS SUGERIDOS
                    response_msg += "="*60 + "\n"
                    response_msg += "\n🎯 **5. PRÓXIMOS PASOS SUGERIDOS**\n\n"
                    response_msg += "1. Revisar dashboard financiero detallado\n"
                    response_msg += "2. Analizar rentabilidad por pozo certificado\n"
                    response_msg += "3. Evaluar pipeline de nuevos contratos\n"
                    response_msg += "4. Actualizar proyección de flujo de fondos\n\n"
                    response_msg += "📊 Para más detalle, consultar: Finanzas → Dashboard\n"
                    
                except Exception as e:
                    response_msg = f"🤖 Error en análisis financiero: {str(e)}"
            
            # 5. FINANZAS Y CONTROL CONTRACTUAL CON RECOMENDACIONES
            elif any(word in msg_lower for word in ["finanzas", "financiero", "contrato", "backlog", "certificacion", "factura", "cobro", "costo", "presupuesto", "margen", "rentabilidad"]):
                try:
                    # Importar servicio financiero
                    from .financial_service_mock import financial_service
                    
                    # Detectar si pregunta por un pozo específico
                    target_well = None
                    for p in financial_service.get_pozos():
                        if p['ID_WELL'].lower() in msg_lower:
                            target_well = p['ID_WELL']
                            break
                    
                    if "backlog" in msg_lower or "contrato" in msg_lower:
                        # Reporte de backlog con recomendaciones
                        contratos = financial_service.get_contratos()
                        total_backlog = sum(c['BACKLOG_RESTANTE'] for c in contratos)
                        response_msg = f"🤖 **Backlog Contractual Total: ${total_backlog:,.2f} USD**\n\n"
                        response_msg += "**Detalle por Contrato:**\n"
                        for c in contratos:
                            avance = ((c['MONTO_TOTAL_CONTRACTUAL'] - c['BACKLOG_RESTANTE']) / c['MONTO_TOTAL_CONTRACTUAL'] * 100) if c['MONTO_TOTAL_CONTRACTUAL'] > 0 else 0
                            response_msg += f"📋 {c['NOMBRE_CONTRATO']}\n"
                            response_msg += f"   • Backlog: ${c['BACKLOG_RESTANTE']:,.2f}\n"
                            response_msg += f"   • Avance: {avance:.1f}%\n"
                            response_msg += f"   • Pozos: {c['total_certificaciones']}/{c['CANTIDAD_POZOS']} certificados\n\n"
                        
                        # RECOMENDACIONES INTELIGENTES
                        response_msg += "\n💡 **Recomendaciones:**\n"
                        if total_backlog < 1000000:
                            response_msg += "⚠️ **CRÍTICO:** Backlog menor a $1M. Se recomienda priorizar la búsqueda de nuevos contratos para asegurar continuidad operativa.\n"
                        else:
                            response_msg += "✅ Backlog saludable. Capacidad operativa asegurada para los próximos 6-9 meses.\n"
                        
                        # Recomendar certificación de pozos completados
                        pozos_completados = [p for p in financial_service.get_pozos() if p['ESTADO_PROYECTO'] == 'COMPLETADO']
                        pozos_no_certificados = [p for p in pozos_completados if not any(c['ID_WELL'] == p['ID_WELL'] for c in financial_service.get_certificaciones())]
                        if pozos_no_certificados:
                            response_msg += f"🎯 **ACCIÓN SUGERIDA:** Hay {len(pozos_no_certificados)} pozo(s) completado(s) sin certificar: {', '.join([p['ID_WELL'] for p in pozos_no_certificados])}. Certificar para liberar flujo de caja.\n"
                    
                    elif "certificacion" in msg_lower or "factura" in msg_lower:
                        # Reporte de certificaciones con recomendaciones
                        certificaciones = financial_service.get_certificaciones()
                        facturas = financial_service.get_facturas()
                        total_cert = sum(c['MONTO_CERTIFICADO'] for c in certificaciones)
                        
                        response_msg = f"🤖 **Certificaciones - Total Certificado: ${total_cert:,.2f} USD**\n\n"
                        response_msg += "**Últimas Certificaciones:**\n"
                        for cert in certificaciones[-5:]:  # Últimas 5
                            factura = next((f for f in facturas if f['ID_CERTIFICACION'] == cert['ID_CERTIFICACION']), None)
                            response_msg += f"📄 Pozo {cert['ID_WELL']}: ${cert['MONTO_CERTIFICADO']:,.2f}"
                            if factura:
                                response_msg += f" - Factura {factura['NUMERO_FACTURA']} ({factura['ESTADO']})"
                            response_msg += "\n"
                        
                        # RECOMENDACIONES
                        facturas_pendientes = [f for f in facturas if f['ESTADO'] == 'EMITIDA']
                        if facturas_pendientes:
                            total_pendiente = sum(f['MONTO'] for f in facturas_pendientes)
                            response_msg += f"\n⚠️ **ATENCIÓN:** {len(facturas_pendientes)} factura(s) pendiente(s) de cobro por ${total_pendiente:,.2f}. Se recomienda gestionar cobranza.\n"
                        
                        # Verificar facturas vencidas
                        hoy = datetime.now()
                        facturas_vencidas = [f for f in facturas if f['ESTADO'] == 'EMITIDA' and f['FECHA_VENCIMIENTO'] < hoy]
                        if facturas_vencidas:
                            total_vencido = sum(f['MONTO'] for f in facturas_vencidas)
                            response_msg += f"🚨 **URGENTE:** {len(facturas_vencidas)} factura(s) VENCIDA(S) por ${total_vencido:,.2f}. Contactar clientes inmediatamente.\n"
                    
                    elif target_well and ("costo" in msg_lower or "margen" in msg_lower or "rentabilidad" in msg_lower):
                        # Análisis financiero por pozo con recomendaciones
                        cert = next((c for c in financial_service.get_certificaciones() if c['ID_WELL'] == target_well), None)
                        costos = financial_service.get_costos_pozo(target_well)
                        pozo_op = financial_service.get_pozo_by_id(target_well)
                        
                        response_msg = f"🤖 **Análisis Financiero - Pozo {target_well}**\n\n"
                        
                        if cert:
                            ingreso = cert['MONTO_CERTIFICADO']
                            response_msg += f"**Ingresos:**\n"
                            response_msg += f"• Monto Certificado: ${ingreso:,.2f}\n"
                            response_msg += f"• Estado: {cert['ESTADO']}\n\n"
                        else:
                            ingreso = 0
                            response_msg += f"**Ingresos:** Sin certificación registrada\n\n"
                        
                        if costos:
                            total_costos = sum(c['MONTO_USD'] for c in costos)
                            response_msg += f"**Costos (desde Operaciones):**\n"
                            for costo in costos:
                                response_msg += f"• {costo['CONCEPTO']}: ${costo['MONTO_USD']:,.2f}\n"
                            response_msg += f"**Total Costos: ${total_costos:,.2f}**\n\n"
                            
                            if ingreso > 0:
                                margen = ingreso - total_costos
                                margen_pct = (margen / ingreso * 100)
                                response_msg += f"**Margen: ${margen:,.2f} ({margen_pct:.1f}%)**\n"
                                
                                # RECOMENDACIONES DE RENTABILIDAD
                                if margen_pct < 20:
                                    response_msg += "⚠️ **ALERTA DE RENTABILIDAD:** Margen bajo (<20%). Se recomienda:\n"
                                    response_msg += "   - Revisar eficiencia operativa\n"
                                    response_msg += "   - Evaluar reducción de costos en próximos pozos similares\n"
                                    response_msg += "   - Negociar mejores tarifas con proveedores\n"
                                elif margen_pct > 40:
                                    response_msg += "✅ **Excelente margen de rentabilidad (>40%).** Mantener prácticas actuales como estándar.\n"
                                else:
                                    response_msg += "✓ **Margen aceptable (20-40%).** Dentro de rangos normales.\n"
                        else:
                            response_msg += "**Costos:** Sin costos registrados aún\n"
                            if pozo_op and pozo_op['ESTADO_PROYECTO'] == 'EN_EJECUCION':
                                response_msg += "💡 **Sugerencia:** El pozo está en ejecución pero sin costos registrados. Verificar registro de gastos en operaciones.\n"
                    
                    elif "kpi" in msg_lower or "dashboard" in msg_lower or "resumen" in msg_lower:
                        # KPIs generales con análisis y recomendaciones
                        kpis = financial_service.get_kpis_dashboard()
                        response_msg = "🤖 **KPIs Financieros - Dashboard**\n\n"
                        response_msg += f"💰 **Backlog Contractual:** ${kpis['backlog_contractual']:,.2f}\n"
                        response_msg += f"📈 **Avance Financiero:** {kpis['avance_financiero_pct']:.1f}%\n"
                        response_msg += f"📊 **Avance Físico:** {kpis['avance_fisico_pct']:.1f}%\n"
                        response_msg += f"💵 **Saldo de Caja:** ${kpis['saldo_caja']:,.2f}\n"
                        response_msg += f"⏱️ **Días de Cobertura:** {kpis['dias_cobertura']:.0f} días\n"
                        response_msg += f"🏦 **Capital de Trabajo Req.:** ${kpis['capital_trabajo']:,.2f}\n\n"
                        
                        # RECOMENDACIONES ESTRATÉGICAS
                        response_msg += "💡 **Análisis y Recomendaciones:**\n"
                        
                        if kpis['alerta_cobertura']:
                            response_msg += "🚨 **CRÍTICO - LIQUIDEZ:** Días de cobertura bajos (< 45). ACCIONES RECOMENDADAS:\n"
                            response_msg += "   1. Acelerar cobranzas de facturas pendientes\n"
                            response_msg += "   2. Evaluar línea de crédito bancaria\n"
                            response_msg += "   3. Postergar gastos no críticos\n"
                            response_msg += "   4. Negociar plazos de pago con proveedores\n"
                        else:
                            response_msg += "✅ **Liquidez estable.** Cobertura superior a 45 días.\n"
                        
                        if kpis['avance_fisico_pct'] < kpis['avance_financiero_pct']:
                            response_msg += "⚠️ **Desfasaje Avance:** El avance financiero supera al físico. Revisar si hay certificaciones adelantadas.\n"
                        
                        if kpis['saldo_caja'] < kpis['capital_trabajo']:
                            response_msg += "⚠️ **Capital de Trabajo:** El saldo de caja es inferior al capital de trabajo requerido. Planificar financiamiento.\n"
                    
                    else:
                        # Consulta general de finanzas
                        response_msg = (
                            "🤖 **Módulo Financiero - AbandonPro**\n\n"
                            "Puedo ayudarte con:\n"
                            "• 📊 **Dashboard** - KPIs y métricas financieras\n"
                            "• 📋 **Backlog** - Contratos pendientes por certificar\n"
                            "• 📄 **Certificaciones** - Facturas y cobros\n"
                            "• 💰 **Costos** - Análisis de rentabilidad por pozo\n\n"
                            "**Ejemplos de preguntas:**\n"
                            "• '¿Cuál es el backlog?'\n"
                            "• 'Análisis financiero del pozo X-123'\n"
                            "• '¿Qué certificaciones tenemos?'\n"
                            "• 'Dame los KPIs financieros'\n"
                        )
                        
                except Exception as e:
                    response_msg = f"🤖 Error al consultar datos financieros: {str(e)}"
            
            # 6. FALLBACK
            if not response_msg:
                 response_msg = (
                    "🤖 **Modo Offline (Reglas):**\n"
                    "No tengo conexión con el cerebro de IA (Gemini). Solo puedo responder comandos básicos sobre listados, personal y ubicación.\n"
                    "Por favor configura la API Key para razonamiento avanzado."
                )

        return {
            "sent": {"id": "c_user_" + str(int(time.time())), "ts": datetime.now().strftime("%Y-%m-%d %H:%M"), "user": "User", "rol": user_role, "origen": "HUMANO", "msg": message},
            "response": {
                "id": "c_ia_" + str(int(time.time())),
                "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "user": "ASISTENTE_IA",
                "rol": "IA",
                "origen": "IA",
                "msg": response_msg,
                "detected_context": target_project # Retornamos el contexto detectado para que el Frontend lo persista
            }
        }
