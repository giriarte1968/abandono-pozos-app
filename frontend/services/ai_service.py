import os
import google.generativeai as genai
from datetime import datetime

class AIService:
    """
    Servicio de Inteligencia Artificial Generativa (RAG + Reasoning).
    Utiliza Google Gemini 1.5 Flash para razonar sobre datos operativos en vivo.
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = None
        self._initialized = False
        
        if self.api_key:
            print(f"[AI SERVICE] API Key encontrada (modo lazy activado)")
        else:
            print("[AI SERVICE] ⚠️ No API Key - modo offline")
    
    def _lazy_init(self):
        """Inicialización perezosa - solo cuando se necesita"""
        if self._initialized or not self.api_key:
            return
        
        try:
            genai.configure(api_key=self.api_key)
            
            # Lista de modelos preferidos
            preferred_models = [
                "models/gemini-1.5-flash",
                "models/gemini-1.5-flash-latest", 
                "models/gemini-2.0-flash",
                "models/gemini-pro"
            ]
            
            # Intentar usar el primer modelo disponible sin listar todos
            for model_name in preferred_models:
                try:
                    self.model = genai.GenerativeModel(model_name)
                    print(f"[AI SERVICE] Usando: {model_name}")
                    break
                except:
                    continue
            
            if not self.model:
                print("[AI SERVICE] ❌ No se pudo inicializar ningún modelo")
                
        except Exception as e:
            print(f"[AI SERVICE] Error: {e}")
        
        self._initialized = True

    def is_available(self):
        self._lazy_init()
        return self.model is not None

    def generate_response(self, user_query, project_context=None, user_role="Usuario", chat_history=None):
        """
        Genera una respuesta natural basada en la consulta del usuario y el contexto operativo.
        """
        self._lazy_init()
        if not self.model:
            return "Error: Servicio de IA no disponible (Falta API Key)."

        # 1. Construcción del Prompt del Sistema (Context Injection)
        system_prompt = self._build_system_prompt(project_context, user_role)
        
        # 2. Construcción de Historial (Short-Term Memory)
        history_str = ""
        if chat_history:
            # Tomamos los últimos 3 mensajes para contexto inmediato
            history_str = "\nHISTORIAL RECIENTE:\n"
            for msg in chat_history[-3:]:
                role = "USUARIO" if msg.get('rol') == 'user' else "ASISTENTE"
                content = msg.get('msg', '')
                history_str += f"- {role}: {content}\n"

        # 3. Construcción del Prompt Completo
        full_prompt = f"""
        {system_prompt}
        
        {history_str}
        
        ---
        PREGUNTA DEL USUARIO ({user_role}):
        "{user_query}"
        ---
        
        Responde de manera concisa, útil y profesional. Usa formato Markdown.
        """

        try:
            # 3. Inferencia
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            print(f"[AI SERVICE] Error generando respuesta: {e}")
            return f"⚠️ **Error de IA**: {str(e)}"

    def _build_system_prompt(self, context, role):
        """
        Crea el prompt del sistema inyectando los datos crudos del proyecto.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        context_str = "SIN CONTEXTO DE PROYECTO (Pregunta General)"
        if context:
            # Formateamos el JSON de contexto a texto legible para el LLM
            context_str = f"""
            ESTADO OPERATIVO DEL POZO/PROYECTO ACTUAL:
            - Nombre: {context.get('name')} (ID: {context.get('id')})
            - Yacimiento: {context.get('yacimiento')}
            - Estado: {context.get('status')}
            - Progreso: {context.get('progreso')}%
            - Workflow Stage: {context.get('workflow_status')}
            
            PERSONAL:
            {self._format_list(context.get('personnel_list'), ['name', 'role', 'medical_ok', 'induction_ok'])}
            
            LOGÍSTICA Y TRANSPORTE:
            {self._format_list(context.get('transport_list'), ['type', 'driver', 'status', 'eta_minutes'])}
            
            EQUIPOS:
            {self._format_list(context.get('equipment_list'), ['name', 'type', 'status'])}
            
            STOCK / INSUMOS:
            {self._format_list(context.get('stock_list'), ['item', 'current', 'min', 'unit'])}
            
             TELEMETRÍA (EDR):
            {context.get('rig_telemetry', 'No disponible')}
            
            DATOS FINANCIEROS Y CONTRACTUALES:
            {self._format_financial_context(context)}
            """

        prompt = f"""
        Eres 'AbandonPro AI', un asistente experto en ingeniería de abandono de pozos (P&A).
        Tu objetivo es ayudar al usuario ({role}) a tomar decisiones operativas basadas en datos en tiempo real.
        
        FECHA/HORA ACTUAL: {timestamp}
        
        CONTEXTO DE DATOS EN VIVO (Fuente de Verdad):
        {context_str}
        
        REGLAS:
        1. Basa tus respuestas ESTRICTAMENTE en los datos provistos arriba. No inventes información.
        2. Si un dato es crítico (ej. Alerta HSE, Stock bajo), resáltalo con emojis (🚨, ⚠️).
        3. Sé proactivo: Si ves un problema en los datos (ej. personal no apto), sugiérelo aunque no lo pregunten explícitamente.
        4. Si te preguntan algo fuera del contexto provisto, usa tu conocimiento general de ingeniería de petróleos pero aclara que es información general.
        5. Habla en español profesional, directo y conciso.
        """
        return prompt

    def _format_financial_context(self, context):
        """Formatea los datos financieros para el contexto del LLM"""
        if not context or 'financial_kpis' not in context:
            return "No hay datos financieros disponibles"
        
        try:
            kpis = context.get('financial_kpis', {})
            contratos = context.get('contratos', [])
            certificaciones = context.get('certificaciones', [])
            
            result = f"""
            💰 **KPIs FINANCIEROS:**
            - Backlog Contractual: ${kpis.get('backlog_contractual', 0):,.2f} USD
            - Avance Financiero: {kpis.get('avance_financiero_pct', 0):.1f}%
            - Avance Físico: {kpis.get('avance_fisico_pct', 0):.1f}%
            - Saldo de Caja: ${kpis.get('saldo_caja', 0):,.2f} USD
            - Días de Cobertura: {kpis.get('dias_cobertura', 0):.0f}
            - Capital de Trabajo Requerido: ${kpis.get('capital_trabajo', 0):,.2f} USD
            
            📋 **CONTRATOS ACTIVOS ({len(contratos)}):**
            """
            
            for c in contratos:
                avance = ((c['MONTO_TOTAL_CONTRACTUAL'] - c['BACKLOG_RESTANTE']) / c['MONTO_TOTAL_CONTRACTUAL'] * 100) if c['MONTO_TOTAL_CONTRACTUAL'] > 0 else 0
                result += f"""
            - {c['NOMBRE_CONTRATO']}
              Cliente: {c['CLIENTE']}
              Monto Total: ${c['MONTO_TOTAL_CONTRACTUAL']:,.2f} USD
              Backlog Restante: ${c['BACKLOG_RESTANTE']:,.2f} USD
              Avance: {avance:.1f}%
              Pozos: {c['total_certificaciones']}/{c['CANTIDAD_POZOS']} certificados
              Plazo de Pago: {c['PLAZO_PAGO_DIAS']} días
                """
            
            result += f"""
            📄 **CERTIFICACIONES RECIENTES ({len(certificaciones)}):**
            """
            
            for cert in certificaciones[-5:]:  # Últimas 5
                result += f"""
            - Pozo {cert['ID_WELL']}: ${cert['MONTO_CERTIFICADO']:,.2f} USD ({cert['ESTADO']})
                """
            
            # Si hay información de pozo específico
            if 'pozo_financiero' in context:
                pozo = context['pozo_financiero']
                result += f"""
            🛢️ **DATOS FINANCIEROS DEL POZO {pozo['ID_WELL']}:**
            - Nombre: {pozo['WELL_NAME']}
            - Estado Operativo: {pozo['ESTADO_PROYECTO']}
            - Progreso: {pozo.get('PROGRESO', 0)}%
                """
                
                if 'certificacion_pozo' in context:
                    cert = context['certificacion_pozo']
                    result += f"""
            - Monto Certificado: ${cert['MONTO_CERTIFICADO']:,.2f} USD
            - % de Avance Certificado: {cert['PORCENTAJE_AVANCE']}%
                    """
                
                if 'costos_pozo' in context and context['costos_pozo']:
                    costos = context['costos_pozo']
                    total_costos = sum(c['MONTO_USD'] for c in costos)
                    result += f"""
            - Costos Registrados: ${total_costos:,.2f} USD
                    """
                    for costo in costos:
                        result += f"              • {costo['CONCEPTO']}: ${costo['MONTO_USD']:,.2f}\n"
                    
                    if 'certificacion_pozo' in context:
                        ingreso = context['certificacion_pozo']['MONTO_CERTIFICADO']
                        margen = ingreso - total_costos
                        margen_pct = (margen / ingreso * 100) if ingreso > 0 else 0
                        result += f"            - Margen: ${margen:,.2f} ({margen_pct:.1f}%)\n"
            
            return result
            
        except Exception as e:
            return f"Error al formatear contexto financiero: {str(e)}"

    def _format_list(self, data_list, fields):
        if not data_list: return "Ninguno/No disponible"
        result = ""
        for item in data_list:
            parts = [f"{k}: {item.get(k, 'N/A')}" for k in fields]
            result += "- " + ", ".join(parts) + "\n"
        return result
