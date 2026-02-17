import os
import requests
from datetime import datetime

# Intentar usar el nuevo paquete google.genai, sino caer a google.generativeai
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
        print("[AI SERVICE] ⚠️ Sin paquete de Google AI")

class AIService:
    """
    Servicio de Inteligencia Artificial Generativa (RAG + Reasoning).
    Utiliza cascada: Gemini → Mistral (OpenRouter) → Offline
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.model = None
        self._initialized = False
        
        if self.api_key:
            print(f"[AI SERVICE] API Key Gemini encontrada")
        if self.openrouter_key:
            print(f"[AI SERVICE] API Key OpenRouter encontrada")
        if not self.api_key and not self.openrouter_key:
            print("[AI SERVICE] ⚠️ Sin API Keys - modo offline")
    
    def _lazy_init(self):
        """Inicialización perezosa de Gemini - solo cuando se necesita"""
        if self._initialized or not self.api_key or not genai:
            return
        
        try:
            if USE_NEW_PACKAGE:
                genai.configure(api_key=self.api_key)
            
            # Lista de modelos preferidos - usar gemini-2.0-flash que es el más reciente
            preferred_models = [
                "gemini-2.0-flash",
                "gemini-2.0-flash-lite",
                "gemini-1.5-flash",
                "gemini-1.5-flash-8b",
                "gemini-1.0-pro"
            ]
            
            # Intentar usar el primer modelo disponible
            for model_name in preferred_models:
                try:
                    self.model = genai.GenerativeModel(model_name)
                    print(f"[AI SERVICE] Gemini inicializado: {model_name}")
                    self._initialized = True
                    return
                except Exception as e:
                    print(f"[AI SERVICE] Modelo {model_name} no disponible: {e}")
                    continue
            
            print("[AI SERVICE] ❌ No se pudo inicializar ningún modelo Gemini")
                
        except Exception as e:
            print(f"[AI SERVICE] Error inicializando Gemini: {e}")
        
        self._initialized = True

    def call_openrouter(self, prompt, context="", history=""):
        """Usa OpenRouter con Mistral como fallback"""
        if not self.openrouter_key:
            return None
        
        try:
            full_prompt = f"""
Eres 'AbandonPro AI', un asistente experto en ingeniería de abandono de pozos (P&A).
Tu objetivo es ayudar al usuario a tomar decisiones operativas basadas en datos en tiempo real.

{context}

{history}

---PREGUNTA---
{prompt}

Responde de manera concisa, útil y profesional. Usa formato Markdown.
"""
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openrouter_key}",
                    "HTTP-Referer": "https://abandono-pozos-app.ondigitalocean.app",
                    "X-Title": "AbandonPro"
                },
                json={
                    "model": "mistralai/mistral-7b-instruct",
                    "messages": [
                        {"role": "user", "content": full_prompt}
                    ],
                    "max_tokens": 500
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                print(f"[AI SERVICE] OpenRouter error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"[AI SERVICE] OpenRouter exception: {e}")
            return None

    def is_available(self):
        self._lazy_init()
        return self.model is not None or self.openrouter_key is not None

    def generate_response(self, user_query, project_context=None, user_role="Usuario", chat_history=None):
        """
        Genera respuesta con cascada: Gemini → Mistral → Offline
        """
        # Preparar contexto
        context = self._build_context(project_context)
        history = self._build_history(chat_history)
        
        # 1️⃣ Intentar Gemini
        self._lazy_init()
        if self.model:
            try:
                full_prompt = f"""
{context}
{history}
---
PREGUNTA DEL USUARIO ({user_role}):
"{user_query}"
---
Responde de manera concisa, útil y profesional. Usa formato Markdown.
"""
                response = self.model.generate_content(full_prompt)
                return response.text
            except Exception as e:
                error_msg = str(e).lower()
                print(f"[AI SERVICE] Gemini error: {e}")
                
                # 2️⃣ Si es error de quota (429), usar OpenRouter
                if "429" in error_msg or "quota" in error_msg or "exceeded" in error_msg:
                    print("[AI SERVICE] 💰 Cuota Gemini agotada → Usando OpenRouter (Mistral)")
                    fallback_response = self.call_openrouter(user_query, context, history)
                    if fallback_response:
                        return fallback_response + "\n\n*(Respondido via Mistral - Fallback)*"
        
        # 3️⃣ Si Gemini no está disponible o falló, intentar OpenRouter directamente
        if self.openrouter_key:
            print("[AI SERVICE] 🔄 Usando OpenRouter (Mistral)")
            fallback_response = self.call_openrouter(user_query, context, history)
            if fallback_response:
                return fallback_response + "\n\n*(Respondido via Mistral)*"
        
        # 4️⃣ Si todo falla, usar modo offline
        print("[AI SERVICE] ⚠️ Sin acceso a LLM → Modo Offline")
        return self._offline_response(user_query, project_context, user_role)
    
    def _build_context(self, context):
        """Construye el contexto del proyecto"""
        if not context:
            return "SIN CONTEXTO DE PROYECTO (Pregunta General)"
        
        return f"""
ESTADO OPERATIVO DEL POZO/PROYECTO ACTUAL:
- Nombre: {context.get('name', 'N/A')} (ID: {context.get('id', 'N/A')})
- Yacimiento: {context.get('yacimiento', 'N/A')}
- Estado: {context.get('status', 'N/A')}
- Progreso: {context.get('progreso', 0)}%
- Workflow Stage: {context.get('workflow_status', 'N/A')}

PERSONAL: {self._format_list(context.get('personnel_list', []), ['name', 'role'])}
LOGÍSTICA: {self._format_list(context.get('transport_list', []), ['type', 'driver', 'status'])}
EQUIPOS: {self._format_list(context.get('equipment_list', []), ['name', 'type', 'status'])}
"""
    
    def _build_history(self, chat_history):
        """Construye el historial de chat"""
        if not chat_history:
            return ""
        
        history = "\nHISTORIAL RECIENTE:\n"
        for msg in chat_history[-3:]:
            role = "USUARIO" if msg.get('rol') == 'user' else "ASISTENTE"
            content = msg.get('msg', '')
            history += f"- {role}: {content}\n"
        return history
    
    def _format_list(self, items, fields):
        """Formatea una lista de diccionarios"""
        if not items:
            return "No disponible"
        return ", ".join([str(i.get(f, 'N/A')) for i in items[:3] for f in fields])

    def _offline_response(self, query, context, role):
        """Respuestas predefinidas cuando no hay acceso a LLM"""
        query_lower = query.lower()
        
        responses = {
            "estado": """📊 Estado Operativo Actual:

• Pozos en Ejecución: 5
• Pozos Planificados: 4
• Pozos Bloqueados: 1
• Pozos Completados: 1

Backlog Total: $1,470,000
Avance Financiero: 30.5%""",
            
            "backlog": """💰 Resumen Financiero:

• SureOil: $740,000 (4 pozos)
• YPF: $585,000 (3 pozos)
• Petrobras: $525,000 (3 pozos)

Total: $1,850,000""",
            
            "pozo": """🛢️ Información de Pozos:

• X-123: EN_EJECUCION (45%) - Los Perales
• A-321: PLANIFICADO (10%) - Las Heras
• Z-789: BLOQUEADO (60%) - El Tordillo
• M-555: EN_ESPERA (95%) - Cañadón Seco
• C-301: COMPLETADO (100%) - Cerro Dragón

Para más detalles, consulta el Dashboard.""",
            
            "certificacion": """📋 Certificaciones:

• Total Certificadas: 3
• Pendientes: 2
• Facturadas: $247,500
• Por Facturar: $855,000""",
            
            "alerta": """⚠️ Alertas Activas:

• Cobertura de caja: 42 días (UMBRAL: 45 días)
• Pozo Z-789 bloqueado por incidencia HSE
• 3 permisos por vencer en 15 días""",
            
            "logistica": """🚚 Estado de Logística:

• Equipos en campo: 8
• Disponibles: 5
• En mantenimiento: 3
• Camiones en ruta: 4
• Próximos arrivals: 2 (30 min)""",
            
            "cementacion": """🔧 Cementaciones Recientes:

• Pozo X-123: Faja 2 completada
• Pozo T-201: Programada para mañana
• Pozo C-301: Validada OK""",
        }
        
        for key, response in responses.items():
            if key in query_lower:
                return response
        
        return f"""🤖 Modo Offline - Respuesta Automática

No puedo acceder a los servicios de IA en este momento.

Información General:
• 10 pozos activos
• 5 en ejecución, 4 planificados, 1 completado
• Backlog: $1,850,000
• Contratos: 3 activos

Sugerencias:
• Consulta el Dashboard para detalles en tiempo real
• Revisa el módulo de Finanzas para контрактación
• Verifica Pozos para estado de cada proyecto

Para acceder a análisis IA avanzado, intenta más tarde o contacta al administrador."""
