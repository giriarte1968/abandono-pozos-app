import os
import requests
from datetime import datetime

# Importación lazy de servicios para evitar imports circulares
def _get_financial_service():
    try:
        from services.financial_service_mock import financial_service
        return financial_service
    except Exception:
        return None

def _get_api_client():
    try:
        from services.mock_api_client import MockApiClient
        return MockApiClient()
    except Exception:
        return None

def _get_recurso_estado_service():
    try:
        from services.recurso_estado_service import recurso_estado_service
        return recurso_estado_service
    except Exception:
        return None

def _get_compliance_service():
    try:
        from services.compliance_service import ComplianceService
        return ComplianceService()
    except Exception:
        return None

def _get_audit_service():
    try:
        from services.audit_service import AuditService
        return AuditService()
    except Exception:
        return None

def _get_capacidad_service():
    try:
        from services.capacidad_contrato_service import CapacidadContratoService
        return CapacidadContratoService()
    except Exception:
        return None

def _get_cementation_service():
    try:
        from services.cementation_service import CementationService
        return CementationService()
    except Exception:
        return None

def _get_closure_service():
    try:
        from services.closure_service import ClosureService
        return ClosureService()
    except Exception:
        return None

def _get_weather_service():
    try:
        from services.weather_service import WeatherService
        return WeatherService()
    except Exception:
        return None

try:
    import google.genai as genai
    USE_NEW_PACKAGE = True
    print("[AI SERVICE] Usando google.genai (nuevo paquete)")
except ImportError:
    try:
        import google.generativeai as genai
        USE_NEW_PACKAGE = False
        print("[AI SERVICE] Usando google.generativeai (paquete legacy)")
    except ImportError:
        genai = None
        USE_NEW_PACKAGE = None
        print("[AI SERVICE] Sin paquete de Google AI")

SYSTEM_PROMPT = """Eres **AbandonPro AI**, un Ingeniero en Petróleo Senior con 20+ años de experiencia especializada en abandono de pozos (P&A - Plug and Abandonment) en Argentina.

## Tu Perfil Profesional

### Especialización Técnica:
- **Regulaciones**: Secretaría de Energía, normativas provinciales (Neuquén, Chubut, Santa Cruz, Mendoza), IRAM, API Spec 10A
- **Procedimientos**: Cementación forzada, tapones mecánicos, corte y recuperación de casing, sellado de cellar, recuperación de locación
- **Integridad**: Evaluación de corrosión, presión de formación, migración de fluidos, integridad de barreras
- **HSE**: Permisos de trabajo, análisis de riesgo, auditorías ambientales, plan de contingencias

### Competencia Financiera:
- **CAPEX/OPEX**: Presupuestos de abandono, provisiones contables, análisis de costos por pozo
- **Contratos**: Evaluación de ofertas, términos de pago, penalidades, garantías
- **Auditoría**: Cierre de proyectos, certificaciones para facturación, trazabilidad documental
- **KPIs**: Backlog, coverage ratio, días de caja, pronóstico financiero

## Directivas de Respuesta

1. **Precisión Técnica**: Usa terminología correcta (slaughter, squeeze, sump, cellar, conductor, surface casing, production casing)
2. **Contexto Regulatorio**: Cita normativas cuando aplique (ej: "Según Res. SE N°...")
3. **Impacto Financiero**: Considera costos, plazos y riesgos en cada recomendación
4. **Concisión**: Respuestas directas, máximo 3 párrafos salvo que se requiera más detalle
5. **Formato**: Usa Markdown, bullet points, y tablas cuando sea útil

## 🚨 REGLA CRÍTICA ANTI-ALUCINACIÓN 🚨

El sistema te provee un bloque de DATOS REALES DEL SISTEMA en cada consulta.
**NUNCA inventes, supongas ni completes datos que no estén en ese bloque.**
- Si te preguntan sobre un contrato → solo usa los contratos listados en DATOS REALES.
- Si te preguntan sobre un pozo → solo usa los pozos listados en DATOS REALES.
- Si te preguntan sobre montos, IDs, casings, garantías, o cualquier dato específico que NO está en DATOS REALES → responde: "No tengo ese dato en el sistema actual."
- **Nunca inventes IDs de pozos, montos, términos contractuales ni referencias normativas específicas.**"""


class AIService:
    """
    Servicio de IA con cascada: Mistral (OpenRouter) → Gemini → Offline
    Mistral es el modelo principal por velocidad y disponibilidad.
    """

    def __init__(self):
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model = None
        self._gemini_initialized = False
        
        if self.openrouter_key:
            print("[AI SERVICE] OpenRouter API Key disponible")
        if self.gemini_api_key:
            print("[AI SERVICE] Gemini API Key disponible (fallback)")
        if not self.openrouter_key and not self.gemini_api_key:
            print("[AI SERVICE] Sin API Keys - modo offline")

    def _init_gemini(self):
        """Inicialización perezosa de Gemini (solo como fallback)"""
        if self._gemini_initialized or not self.gemini_api_key or not genai:
            return
        
        try:
            if USE_NEW_PACKAGE:
                genai.configure(api_key=self.gemini_api_key)
            
            models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.0-pro"]
            for model_name in models:
                try:
                    self.gemini_model = genai.GenerativeModel(model_name)
                    print(f"[AI SERVICE] Gemini fallback listo: {model_name}")
                    break
                except:
                    continue
        except Exception as e:
            print(f"[AI SERVICE] Error init Gemini: {e}")
        
        self._gemini_initialized = True

    def call_mistral(self, prompt, context="", history=""):
        """Llamada a Mistral via OpenRouter (modelo principal)"""
        if not self.openrouter_key:
            return None
        
        full_prompt = f"{SYSTEM_PROMPT}\n\n{context}\n{history}\n\n---PREGUNTA---\n{prompt}\n\nResponde de manera concisa y profesional."
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openrouter_key}",
                    "HTTP-Referer": "https://abandono-pozos-app.ondigitalocean.app",
                    "X-Title": "AbandonPro"
                },
                json={
                    "model": "deepseek/deepseek-chat",
                    "messages": [{"role": "user", "content": full_prompt}],
                    "max_tokens": 600
                },
                timeout=25
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                print(f"[AI SERVICE] Mistral error: {response.status_code}")
                return None
        except Exception as e:
            print(f"[AI SERVICE] Mistral exception: {e}")
            return None

    def call_gemini(self, prompt, context="", history=""):
        """Llamada a Gemini (fallback)"""
        self._init_gemini()
        if not self.gemini_model:
            return None
        
        try:
            full_prompt = f"{SYSTEM_PROMPT}\n\n{context}\n{history}\n\n---PREGUNTA---\n{prompt}"
            response = self.gemini_model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            print(f"[AI SERVICE] Gemini exception: {e}")
            return None

    def is_available(self):
        return bool(self.openrouter_key or self.gemini_api_key)

    def generate_response(self, user_query, project_context=None, user_role="Usuario", chat_history=None):
        """
        Cascada: Mistral → Gemini → Offline
        """
        context = self._build_context(project_context)
        history = self._build_history(chat_history)
        
        # 1. Mistral (principal)
        response = self.call_mistral(user_query, context, history)
        if response:
            return response
        
        # 2. Gemini (fallback)
        print("[AI SERVICE] Mistral no disponible → Intentando Gemini")
        response = self.call_gemini(user_query, context, history)
        if response:
            return response + "\n\n*(via Gemini fallback)*"
        
        # 3. Offline
        print("[AI SERVICE] Sin LLM disponible → Modo Offline")
        return self._offline_response(user_query, project_context, user_role)

    def _build_context(self, ctx):
        """
        Construye el contexto de datos REALES para el LLM.
        Inyecta contratos, pozos, personal y equipos actuales del sistema
        para evitar alucinaciones con datos inventados.
        """
        lines = ["=== DATOS REALES DEL SISTEMA (USA SOLO ESTOS, NO INVENTES) ==="]

        # --- CONTRATOS ---
        try:
            fin = _get_financial_service()
            if fin:
                contratos = fin.get_contratos()
                lines.append("\n## CONTRATOS ACTIVOS:")
                for c in contratos:
                    pozos_str = ", ".join(c.get('pozos_asignados', []))
                    lines.append(
                        f"  - [{c['ID_CONTRATO']}] {c['NOMBRE_CONTRATO']} | Cliente: {c['CLIENTE']} "
                        f"| Pozos: {c['CANTIDAD_POZOS']} ({pozos_str}) "
                        f"| Valor unitario: USD {c['VALOR_UNITARIO_BASE_USD']:,.0f} "
                        f"| Monto total: USD {c['MONTO_TOTAL_CONTRACTUAL']:,.0f} "
                        f"| Backlog: USD {c['BACKLOG_RESTANTE']:,.0f} "
                        f"| Pago: {c['PLAZO_PAGO_DIAS']} días | Estado: {c['ESTADO']}"
                    )
                certificaciones = fin.get_certificaciones()
                lines.append("\n## CERTIFICACIONES:")
                for cert in certificaciones:
                    lines.append(
                        f"  - Cert #{cert['ID_CERTIFICACION']}: Pozo {cert['ID_WELL']} ({cert['WELL_NAME']}) "
                        f"| Monto: USD {cert['MONTO_CERTIFICADO']:,.0f} "
                        f"| Estado: {cert['ESTADO']}"
                    )
        except Exception as e:
            lines.append(f"  (Error al cargar datos financieros: {e})")

        # --- POZOS OPERATIVOS ---
        try:
            api = _get_api_client()
            if api:
                pozos = api.get_all_wells()
                lines.append("\n## POZOS OPERATIVOS:")
                for p in pozos:
                    lines.append(
                        f"  - {p['id']} | {p['nombre']} | Yacimiento: {p['yacimiento']} "
                        f"| Estado: {p['estado_proyecto']} | Progreso: {p['progreso']}% "
                        f"| Próximo hito: {p.get('proximo_hito', 'N/A')} "
                        f"| Cliente: {p.get('cliente', 'N/A')}"
                    )
                # Personal y Equipos
                personal = api.get_master_personnel()
                lines.append("\n## PERSONAL EN CATÁLOGO:")
                for per in personal:
                    nombre = per.get('nombre_completo') or per.get('name', 'N/A')
                    rol = per.get('rol_principal') or per.get('role', 'N/A')
                    lines.append(f"  - {nombre} | Rol: {rol}")

                equipos = api.get_master_equipment()
                lines.append("\n## EQUIPOS EN CATÁLOGO:")
                for eq in equipos:
                    nombre = eq.get('nombre_equipo') or eq.get('name', 'N/A')
                    tipo = eq.get('tipo_equipo') or eq.get('type', 'N/A')
                    estado = eq.get('status', 'N/A')
                    lines.append(f"  - {nombre} | Tipo: {tipo} | Estado: {estado}")

                # --- ESTADO DIARIO DE RECURSOS ---
                res_service = _get_recurso_estado_service()
                if res_service:
                    from datetime import date
                    hoy = date.today()
                    estados_hoy = res_service.get_estados(fecha=hoy)
                    if estados_hoy:
                        lines.append(f"\n## ESTADO DIARIO Y ASIGNACIONES RECURSOS ({hoy.isoformat()}):")
                        for est in estados_hoy:
                            asignacion = f" -> Asignado a Pozo: {est['id_pozo']}" if est.get('id_pozo') else " (Sin asignación específica)"
                            lines.append(
                                f"  - {est['id_recurso']} ({est['tipo_recurso']}) "
                                f"| Estado Hoy: {est['estado_operativo']}{asignacion}"
                            )

                # --- CUMPLIMIENTO REGULATORIO ---
                comp_service = _get_compliance_service()
                if comp_service:
                    summaries = comp_service.get_all_compliance_summaries()
                    if summaries:
                        lines.append("\n## CUMPLIMIENTO REGULATORIO Y BLOQUEOS:")
                        for s in summaries:
                            status_icon = "🔴" if not s['puede_avanzar'] else ("🟡" if s['advertencia'] > 0 else "🟢")
                            lines.append(
                                f"  - Pozo {s['pozo_id']} {status_icon} | Resumen: {s['resumen']} "
                                f"| Reglas: {s['cumple']} OK, {s['no_cumple']} Fail, {s['overrides']} Overrides"
                            )

                # --- AUDITORÍA RECIENTE (TIMELINE) ---
                audit_svc = _get_audit_service()
                if audit_svc:
                    events = audit_svc.get_all_events()[:5] # Últimos 5
                    if events:
                        lines.append("\n## ÚLTIMA ACTIVIDAD DEL SISTEMA (Auditoría):")
                        for ev in events:
                            ts = ev.get('timestamp_utc')
                            if hasattr(ts, 'strftime'): ts = ts.strftime("%H:%M:%S")
                            else: ts = str(ts)[-8:]
                            lines.append(f"  - [{ts}] {ev['id_usuario']} ({ev['rol_usuario']}): {ev['tipo_evento']} en {ev['entidad']} {ev['entidad_id']}")

                # --- CAPACIDAD CONTRACTUAL ---
                cap_svc = _get_capacidad_service()
                if cap_svc:
                    active_contracts = cap_svc.get_active_contracts()
                    if active_contracts:
                        lines.append("\n## CAPACIDAD OPERATIVA POR CONTRATO:")
                        for c in active_contracts:
                            report = cap_svc.get_availability_report(c['ID_CONTRATO'])
                            if not report.empty:
                                gaps = report[report['Estado'].str.contains("⚠️")]
                                if not gaps.empty:
                                    gap_summary = ", ".join([f"{r['Recurso']}: {r['Estado']}" for _, r in gaps.iterrows()])
                                    lines.append(f"  - {c['NOMBRE_CONTRATO']}: {gap_summary}")
                                else:
                                    lines.append(f"  - {c['NOMBRE_CONTRATO']}: ✅ Capacidad Completa")

                # --- ESTADOS DE INGENIERÍA (Cementación y Cierre) ---
                cem_svc = _get_cementation_service()
                clo_svc = _get_closure_service()
                if cem_svc:
                    pozo_ids = cem_svc.get_all_pozo_ids()
                    if pozo_ids:
                        lines.append("\n## ESTADO TÉCNICO POZOS (Cementación/Cierre):")
                        for pid in pozo_ids:
                            cem_st = cem_svc.get_estado_cementacion_pozo(pid)
                            clo_st = clo_svc.get_estado_cierre_pozo(pid) if clo_svc else {"resumen": "N/A"}
                            lines.append(f"  - Pozo {pid}: {cem_st['resumen']} | {clo_st['resumen']}")

                # --- LOGÍSTICA Y MOVILIZACIONES ---
                logistics = api.get_all_logistics()
                if logistics:
                    lines.append("\n## LOGÍSTICA Y MOVILIZACIONES (HOY):")
                    for t in logistics:
                        lines.append(
                            f"  - {t['type']} ({t['driver']}) | Proyecto: {t['project_id']} "
                            f"| Estado: {t['status']} | Plan: {t['time_plan']} "
                            f"| GPS: {t['dist_to_well']:.1f}km (ETA: {t['eta_minutes']}min)"
                        )

                # --- SUMINISTROS e INSUMOS ---
                supplies = api.get_all_supplies_status()
                if supplies:
                    lines.append("\n## BALANCE DE INSUMOS (Stock Crítico):")
                    for s in supplies:
                        if s['current'] <= s['min']:
                            lines.append(f"  - 🚨 {s['item']} en {s['project_id']}: {s['current']} {s['unit']} (Mín: {s['min']})")

                # --- MENSAJERÍA DE EMERGENCIA ---
                emergency = api.get_emergency_inbox()
                if emergency:
                    lines.append("\n## ALERTAS DE EMERGENCIA (SMS/SAT):")
                    for m in emergency:
                        lines.append(f"  - [{m['ts']}] Pozo {m['project_id']}: {m['decoded_data'].get('desc')}")
        except Exception as e:
            lines.append(f"  (Error al cargar datos operativos extendidos: {e})")

        # --- CONTEXTO DE POZO ACTIVO (si hay uno seleccionado) ---
        if ctx:
            lines.append("\n## POZO ACTIVO EN PANTALLA:")
            lines.append(
                f"  Nombre: {ctx.get('name', 'N/A')} (ID: {ctx.get('id', 'N/A')}) "
                f"| Yacimiento: {ctx.get('yacimiento', 'N/A')} "
                f"| Estado: {ctx.get('status', 'N/A')} | Progreso: {ctx.get('progreso', 0)}%"
            )
            # Agregar clima si es pozo activo
            coords = ctx.get('coordinates', {}) or ctx.get('coords', {})
            if coords and 'lat' in coords and 'lon' in coords:
                w_svc = _get_weather_service()
                if w_svc:
                    weather = w_svc.get_weather(coords['lat'], coords['lon'])
                    if weather:
                        lines.append(f"  - Clima: {weather['temp_actual']}, Viento: {weather['viento_actual']} ({'ALERTA' if weather['alerta_viento'] else 'Seguro para operar'})")

        lines.append("\n=== FIN DE DATOS REALES. NUNCA inventes datos que no estén aquí. ===")
        return "\n".join(lines)

    def _build_history(self, chat_history):
        if not chat_history:
            return ""
        h = "\nHISTORIAL:\n"
        for msg in chat_history[-3:]:
            role = "Usuario" if msg.get('rol') == 'user' else "Asistente"
            h += f"- {role}: {msg.get('msg', '')[:100]}\n"
        return h

    def _offline_response(self, query, context, role):
        q = query.lower()
        
        responses = {
            "estado": "📊 5 pozos en ejecución, 4 planificados, 1 bloqueado, 1 completado. Backlog: $1.47M. Avance: 30.5%",
            "backlog": "💰 SureOil $740K, YPF $585K, Petrobras $525K. Total: $1.85M",
            "pozo": "🛢️ X-123 (45%), A-321 (10%), Z-789 bloqueado, M-555 (95%), C-301 completado",
            "cementacion": "🔧 X-123 Faja 2 OK, T-201 programada mañana, C-301 validada",
            "alerta": "⚠️ Cobertura 42 días (umbral 45), Z-789 bloqueado HSE, 3 permisos por vencer",
            "costo": "💵 Costo promedio abandono: $50-80K/pozo superficial, $150-250K/pozo profundo",
        }
        
        for key, resp in responses.items():
            if key in q:
                return resp
        
        return """🤖 **Modo Offline**

Sin acceso a IA. Datos generales:
• 10 pozos activos | Backlog: $1.85M
• Consulta Dashboard para tiempo real
• Reintenta más tarde para análisis IA"""
