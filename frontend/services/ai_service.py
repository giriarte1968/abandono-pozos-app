import os
import requests
from datetime import datetime

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

## Información del Contexto Operativo
El sistema te proporciona datos en tiempo real de pozos, equipos, personal, logística y finanzas. Úsalos para respuestas contextuales precisas."""

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
        if not ctx:
            return "CONTEXTO: Pregunta general sin proyecto activo."
        
        return f"""CONTEXTO OPERATIVO ACTUAL:
- Pozo: {ctx.get('name', 'N/A')} (ID: {ctx.get('id', 'N/A')})
- Yacimiento: {ctx.get('yacimiento', 'N/A')}
- Estado: {ctx.get('status', 'N/A')}
- Progreso: {ctx.get('progreso', 0)}%
- Personal: {len(ctx.get('personnel_list', []))} personas
- Equipos: {len(ctx.get('equipment_list', []))} en locación"""

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
