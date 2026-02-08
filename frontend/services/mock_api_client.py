import time
import random
import json
import os
from datetime import datetime, timedelta
from .database_service import DatabaseService

class MockApiClient:
    """
    Simula la interacción con el Backend (FastAPI) y el Orquestador (Temporal).
    Utiliza DatabaseService para MySQL y un archivo JSON local como Persistencia de Respaldo.
    """

    def __init__(self):
        self.db = DatabaseService()
        self.storage_path = "frontend/services/persistence_db.json"
        
        # Cargar datos iniciales desde JSON si existe
        self._db_data = self._load_persistence()
        
        # Mapeo de listas internas para compatibilidad con código existente
        self._db_projects = self._db_data.get('projects', self._generate_mock_data())
        self._db_master_people = self._db_data.get('people', [])
        self._db_master_equipment = self._db_data.get('equipment', [])
        self._db_master_supplies = self._db_data.get('supplies', [])

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
            "supplies": self._db_master_supplies
        }
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def _generate_mock_data(self):
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
        """Retorna lista de proyectos desde MySQL + Mock de apoyo."""
        try:
            db_pozos = self.db.fetch_all("SELECT * FROM tbl_pozos")
            # Mapeamos campos de la DB al formato esperado por la UI
            processed = []
            for p in db_pozos:
                processed.append({
                    "id": p['id_pozo'],
                    "nombre": p['nombre_pozo'],
                    "yacimiento": p['id_yacimiento'],
                    "estado_proyecto": "EN_CURSO" if p['estado_pozo'] == 'ACTIVO' else "PLANIFICADO",
                    "progreso": 0,
                    "responsable": p.get('responsable_asig', 'No asignado')
                })
            # Mezclamos con los mocks (para no perder los demos Z-789 etc.)
            for m in self._db_projects:
                if not any(p['id'] == m['id'] for p in processed):
                    processed.append(m)
            
            if filter_status and filter_status != 'Todos':
                return [p for p in processed if p['estado_proyecto'] == filter_status]
            return processed
        except Exception as e:
            print(f"[ERROR] DB: {e}")
            return self._db_projects

    def get_master_personnel(self):
        # Prioridad 1: MySQL (si está disponible)
        try:
            return self.db.fetch_all("SELECT * FROM tbl_personal_catalogo")
        except:
            # Prioridad 2: Local Persistence JSON
            return self._db_master_people

    def get_master_equipment(self):
        try:
            return self.db.fetch_all("SELECT * FROM tbl_equipos_catalogo")
        except:
            return self._db_master_equipment

    def get_master_supplies(self):
        try:
            return self.db.fetch_all("SELECT * FROM tbl_stock_inventario WHERE id_expediente='CATALOGO'")
        except:
            return self._db_master_supplies

    def get_project_detail(self, project_id):
        """Retorna detalle completo de un proyecto."""
        # Simula busqueda en DB
        project = next((p for p in self._db_projects if p['id'] == project_id), None)
        if not project:
            return None
        
        # UI Compatibility Mappings
        project['well'] = project['id']
        project['name'] = project['nombre']
        project['status'] = project['workflow_status']

        # --- Extended Operational Data ---
        # Each validation can have: source (AUTOMATIC|EXTERNAL|MANUAL), validated_by, validated_at, justification
        # CRITICAL: For Personnel HSE validations, only AUTOMATIC sources are valid
        # --- Quotas & Constraints (New Logic) ---
        # --- Hybrid Model States (External Truth + Internal Gate) ---
        project['dtm_confirmado'] = True if project['id'] != "A-321" else False # A-321 is waiting for DTM
        project['personal_confirmado_hoy'] = True
        
        # Event History (External Truth Log)
        project['external_truth_log'] = [
            {"ts": "2026-02-01 07:00", "source": "DTM_GATEWAY", "event": "DTM_CONFIRMADO", "payload": "Apertura de locación validada", "status": "GATE_OPEN"},
            {"ts": "2026-02-03 07:15", "source": "CONTROL_ACCESO", "event": "PERSONAL_PRESENTE", "payload": "Conteo 70/70 verificado", "status": "INFO"},
            {"ts": "2026-02-03 08:30", "source": "WEATHER_NET", "event": "METEOROLOGIA_ACTUALIZADA", "payload": "Viento 25km/h - Despejado", "status": "INFO"},
        ]

        # --- Quotas & Constraints ---
        project['quotas'] = {
            "DIRECTO": {
                "PULLING": {"target": 3, "current": 3},
                "PILETA": {"target": 3, "current": 3},
                "CEMENTADOR": {"target": 2, "current": 2},
                "WIRELINE": {"target": 1, "current": 1}
            },
            "PERSONNEL": {
                "DIRECTO": {"target": 45, "current": 45},
                "INDIRECTO": {"target": 25, "current": 25}
            }
        }

        # Simulating personnel list...
        project['personnel_list'] = [
            {"id": "PD01", "name": "Juan Perez", "role": "Supervisor", "category": "DIRECTO", "critical": True, "present": True,
             "medical_ok": True, "medical_source": "AUTOMATIC", "medical_validated_by": "Sistema Médico Corporativo", "medical_validated_at": "2026-01-15 08:00",
             "induction_ok": True, "induction_source": "AUTOMATIC", "induction_validated_by": "Sistema HSE", "induction_validated_at": "2026-01-10 10:00"},
            {"id": "PD02", "name": "Carlos Gomez", "role": "Op. Pulling", "category": "DIRECTO", "critical": True, "present": True,
             "medical_ok": True, "medical_source": "AUTOMATIC", "medical_validated_by": "Sistema Médico Corporativo", "medical_validated_at": "2026-01-20 09:00",
             "induction_ok": False, "induction_source": "AUTOMATIC", "induction_validated_by": "Sistema HSE", "induction_validated_at": "2025-12-01 14:00"},
            {"id": "PI01", "name": "Roberto Ruiz", "role": "Chofer Cisterna", "category": "INDIRECTO", "critical": False, "present": True,
             "medical_ok": True, "medical_source": "AUTOMATIC", "medical_validated_by": "Sistema Médico Corporativo", "medical_validated_at": "2025-11-30 16:00",
             "induction_ok": True, "induction_source": "AUTOMATIC", "induction_validated_by": "Sistema HSE", "induction_validated_at": "2026-01-12 13:00"},
        ]
        
        project['personnel_summary'] = {"direct": 45, "indirect": 25, "total": 70}

        project['transport_list'] = [
             {"id": "T01", "type": "Minibus", "driver": "Logistica Sur", "status": "PROGRAMADO", "time_plan": "07:30", "time_arrival": None},
             {"id": "T02", "type": "Camion Cisterna (25m3)", "driver": "Aguas Patagonicas", "status": "ARRIBO", "time_plan": "08:00", "time_arrival": "08:15"},
        ]

        project['stock_list'] = [
            {"item": "Cemento (Bolsas)", "current": 150, "consumed": 0, "min": 50, "unit": "u"},
            {"item": "Agua Industrial", "current": 25.0, "consumed": 0, "min": 10.0, "unit": "m3"},
        ]

        project['equipment_list'] = [
            {"name": "Pulling Unit #01", "category": "DIRECTO", "type": "PULLING", "status": "OPERATIVO", "assigned": True, "is_on_location": True,
             "validation_source": "AUTOMATIC", "validated_by": "Sistema Mantenimiento", "validated_at": "2026-02-01 06:00"},
            {"name": "Cementador #1", "category": "DIRECTO", "type": "CEMENTADOR", "status": "OPERATIVO", "assigned": True, "is_on_location": True},
            {"name": "Cisterna 25m3 #1", "category": "INDIRECTO", "type": "CISTERNA", "status": "OPERATIVO", "assigned": True, "is_on_location": True},
            {"name": "Set Apertura Locación", "category": "INDIRECTO", "type": "APERTURA", "status": "OPERATIVO", "assigned": True, "is_on_location": True},
        ]
        
        # --- Rule Engine (Hybrid Logic) ---
        project['allowed_operations'] = ["ESPERA"]
        
        # GATE 1: DTM Confirmado
        if project.get('dtm_confirmado'):
            # Dependencies
            cisternas_ok = any(e['type'] == 'CISTERNA' and e['status'] == 'OPERATIVO' and e.get('is_on_location') for e in project['equipment_list'])
            apertura_ok = any(e['type'] == 'APERTURA' and e['status'] == 'OPERATIVO' for e in project['equipment_list'])
            
            if cisternas_ok:
                project['allowed_operations'].append("CEMENTACION")
            if apertura_ok:
                project['allowed_operations'].append("DTM")
        else:
            project['blocking_message'] = "⚠ OPERACIONES BLOQUEADAS: Esperando evento DTM_CONFIRMADO (External Truth)"

        project['permits_list'] = [
             {"type": "Trabajo en Caliente", "expires": "2026-02-01", "status": "VIGENTE"},
             {"type": "Izaje Pesado", "expires": "2026-01-30", "status": "VENCIDO"},
        ]
        
        project['history'] = [
            {"fecha": "2024-05-01", "evento": "Inicio Trámite", "usuario": "Sistema"},
            {"fecha": "2024-05-10", "evento": "Inicio Logística", "usuario": "Admin"},
        ]
        return project

    def upsert_well(self, data):
        """CRUD: Alta/Edición de Pozo en MySQL."""
        print(f"[DB] Admin CRUD: Guardando pozo {data['id']}")
        query = """
        INSERT INTO tbl_pozos (id_pozo, nombre_pozo, id_yacimiento, lat, lon, estado_pozo, responsable_asig, creado_por)
        VALUES (%(id)s, %(nombre)s, %(yacimiento)s, %(lat)s, %(lon)s, 'ACTIVO', %(responsable)s, 'ADMIN')
        ON DUPLICATE KEY UPDATE 
            nombre_pozo=%(nombre)s, id_yacimiento=%(yacimiento)s, lat=%(lat)s, lon=%(lon)s, responsable_asig=%(responsable)s
        """
        try:
            self.db.execute(query, data)
        except Exception as e:
            print(f"[ERROR DB] {e}")
        
        # SIEMPRE persistir en JSON local para que sobreviva el F5
        existing = next((p for p in self._db_projects if p['id'] == data['id']), None)
        if existing: existing.update(data)
        else: self._db_projects.append(data)
        self._save_persistence()
        return True

    def upsert_person(self, data):
        """CRUD: Alta/Edición de Personal en MySQL."""
        print(f"[DB] Admin CRUD: Guardando persona {data['name']}")
        query = """
        INSERT INTO tbl_personal_catalogo (id_persona, dni, nombre_completo, rol_principal, activo, creado_por)
        VALUES (%(dni)s, %(dni)s, %(name)s, %(role)s, 1, 'ADMIN')
        ON DUPLICATE KEY UPDATE nombre_completo=%(name)s, rol_principal=%(role)s
        """
        try:
            self.db.execute(query, data)
        except Exception as e:
            print(f"[ERROR DB] {e}")
        
        # Backup local
        self._db_master_people.insert(0, data)
        self._save_persistence()
        return True

    def upsert_equipment(self, data):
        """CRUD: Alta/Edición de Equipo en MySQL."""
        print(f"[DB] Admin CRUD: Guardando equipo {data['name']}")
        query = """
        INSERT INTO tbl_equipos_catalogo (id_equipo, nombre_equipo, tipo_equipo, es_critico, activo, creado_por)
        VALUES (%(name)s, %(name)s, %(type)s, %(assigned)s, 1, 'ADMIN')
        ON DUPLICATE KEY UPDATE tipo_equipo=%(type)s
        """
        try:
            self.db.execute(query, data)
        except Exception as e:
            print(f"[ERROR DB] {e}")
        
        self._db_master_equipment.insert(0, data)
        self._save_persistence()
        return True

    def upsert_supply(self, data):
        """CRUD: Alta/Edición de Insumo en MySQL."""
        print(f"[DB] Admin CRUD: Guardando insumo {data['item']}")
        query = """
        INSERT INTO tbl_stock_inventario (id_stock, id_expediente, item, unidad, stock_inicial, stock_minimo, fecha_operativa, registrado_por)
        VALUES (%(item)s, 'CATALOGO', %(item)s, %(unit)s, 1000, %(min)s, CURDATE(), 'ADMIN')
        ON DUPLICATE KEY UPDATE stock_minimo=%(min)s, unidad=%(unit)s
        """
        try:
            self.db.execute(query, data)
        except Exception as e:
            print(f"[ERROR DB] {e}")
            
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

    def send_signal_parte_diario(self, project_id, report_data):
        """Signal: Ing Campo envía parte diario."""
        print(f"[MOCK] Enviando Signal 'ParteDiario' para {project_id}. Data: {report_data}")
        time.sleep(1.5)
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
            response_msg += "\n¿Deseas el detalle técnico de algún pozo en particular?"

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
