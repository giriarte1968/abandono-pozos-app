import streamlit as st
import os
import base64
from streamlit_float import *

def render_chat():
    """
    Renderiza el Asistente Virtual Flotante (Versión Estable).
    """
    # Inicializar float si no está hecho
    float_init()

    # Estado del chat
    if 'chat_is_open' not in st.session_state:
        st.session_state['chat_is_open'] = False

    # Estado de Posición (Cycle: BR -> BL -> TL -> TR)
    if 'chat_position' not in st.session_state:
        st.session_state['chat_position'] = 'BR' # Bottom-Right default

    # Datos de sesión
    api = st.session_state.get('api_client')
    project_id = st.session_state.get('selected_project_id')
    user_role = st.session_state.get('user_role', 'Usuario')
    history_key = f"chat_hist_{project_id if project_id else 'global'}"
    
    if history_key not in st.session_state:
        st.session_state[history_key] = []

    # 1. Ventana de Chat (Solo visible si está abierta)
    if st.session_state['chat_is_open']:
        chat_container = st.container()
        
        with chat_container:
            # Header Simplificado (Como la versión que funcionaba correctamente)
            h_col1, h_col2, h_col3 = st.columns([0.7, 0.15, 0.15])
            with h_col1:
                st.markdown("##### 🤖 Asistente")
            
            with h_col2:
                # Botón de Ciclo de Posición
                if st.button("⛶", key="cycle_pos", help="Mover ventana"):
                    curr = st.session_state['chat_position']
                    cycle = {'BR': 'BL', 'BL': 'TL', 'TL': 'TR', 'TR': 'BR'}
                    st.session_state['chat_position'] = cycle.get(curr, 'BR')
                    st.rerun()

            with h_col3:
                # Botón de Cerrar
                if st.button("✖", key="close_chat_x"):
                    st.session_state['chat_is_open'] = False
                    st.rerun()
            
            # --- VENTANA PRINCIPAL ---
            # DEFINICIÓN DEL CONTEXTO
            active_context_id = project_id 
            if not active_context_id:
                active_context_id = st.session_state.get('chat_focus_context')

            ctx_display = active_context_id if active_context_id else 'Global'
            if active_context_id and active_context_id != project_id:
                ctx_display += " (Chat context)"
            
            st.caption(f"📍 Contexto: **{ctx_display}**")
            
            # Botones de Acción Rápida: Análisis Doble (Operativo + Financiero)
            st.markdown("**📊 Análisis de Situación:**")
            col_analisis1, col_analisis2 = st.columns(2)
            
            with col_analisis1:
                if st.button("🏗️ Operativo", type="secondary", key="btn_analisis_operativo"):
                    st.toast("🤖 Analizando situación operativa...", icon="⏳")
                    prompt_text = "Análisis de situación operativa: Revisa el estado de los proyectos, personal, equipos, logística y alertas técnicas. Dame un resumen ejecutivo con recomendaciones priorizadas."
                    st.session_state[history_key].append({'rol': 'user', 'msg': '📋 Solicito análisis operativo'})
                    
                    try:
                        if not api: raise ValueError("API Client no inicializado")
                        with st.spinner("Analizando operaciones..."):
                            resp = api.send_chat_message(active_context_id, user_role, prompt_text, chat_history=st.session_state[history_key])
                            if isinstance(resp, dict) and 'response' in resp:
                                rta = resp['response']
                                msg_content = rta['msg'] if isinstance(rta, dict) and 'msg' in rta else rta
                            else:
                                msg_content = str(resp)
                            st.session_state[history_key].append({'rol': 'assistant', 'msg': msg_content})
                    except Exception as e:
                        st.session_state[history_key].append({'rol': 'assistant', 'msg': f"Error: {e}"})
                    st.rerun()
            
            with col_analisis2:
                if st.button("💰 Financiero", type="secondary", key="btn_analisis_financiero"):
                    st.toast("🤖 Analizando situación financiera...", icon="⏳")
                    prompt_text = "Análisis de situación financiera: Revisa backlog, certificaciones, flujo de caja, rentabilidad por pozo y alertas económicas. Dame un resumen ejecutivo con recomendaciones financieras priorizadas."
                    st.session_state[history_key].append({'rol': 'user', 'msg': '💰 Solicito análisis financiero'})
                    
                    try:
                        if not api: raise ValueError("API Client no inicializado")
                        with st.spinner("Analizando finanzas..."):
                            resp = api.send_chat_message(active_context_id, user_role, prompt_text, chat_history=st.session_state[history_key])
                            if isinstance(resp, dict) and 'response' in resp:
                                rta = resp['response']
                                msg_content = rta['msg'] if isinstance(rta, dict) and 'msg' in rta else rta
                            else:
                                msg_content = str(resp)
                            st.session_state[history_key].append({'rol': 'assistant', 'msg': msg_content})
                    except Exception as e:
                        st.session_state[history_key].append({'rol': 'assistant', 'msg': f"Error: {e}"})
                    st.rerun()

            st.divider()
            
            # Area de Mensajes
            messages = st.container(height=350)
            with messages:
                if not st.session_state[history_key]:
                    st.info("👋 ¿En qué puedo ayudarte hoy?")
                
                for msg in st.session_state[history_key]:
                    role = msg.get('rol') or msg.get('role')
                    content = msg.get('msg')
                    if role == 'user':
                        st.chat_message("user").write(content)
                    else:
                        if isinstance(content, dict): st.chat_message("assistant", avatar="🤖").json(content)
                        else: st.chat_message("assistant", avatar="🤖").markdown(content)
            
            # Chat Input (Inyectado en el historial)
            if prompt := st.chat_input("Escribí tu consulta...", key="float_chat_input"):
                st.session_state[history_key].append({'rol': 'user', 'msg': prompt})
                try:
                    resp = api.send_chat_message(active_context_id, user_role, prompt, chat_history=st.session_state[history_key])
                    rta_msg = ""
                    if isinstance(resp, dict) and 'response' in resp:
                        rta_msg = resp['response']['msg']
                    else:
                        rta_msg = str(resp)
                    st.session_state[history_key].append({'rol': 'assistant', 'msg': rta_msg})
                except Exception as e:
                    st.session_state[history_key].append({'rol': 'assistant', 'msg': "Error conectando con IA."})
                st.rerun()

        # Posicionamiento CSS
        pos_code = st.session_state.get('chat_position', 'BR')
        css_pos = "bottom: 110px; right: 30px;"
        if pos_code == 'BL': css_pos = "bottom: 110px; left: 30px;"
        elif pos_code == 'TL': css_pos = "top: 100px; left: 30px;"
        elif pos_code == 'TR': css_pos = "top: 100px; right: 30px;"

        chat_window_css = f"""
            position: fixed;
            {css_pos}
            width: 400px;
            max-width: 90vw;
            background-color: #1e1e1e;
            border: 2px solid #555;
            border-radius: 12px;
            padding: 15px;
            z-index: 9999;
            box-shadow: 0 10px 40px rgba(0,0,0,0.8);
        """
        chat_container.float(chat_window_css)

    # 2. Botón Flotante (FAB) - Versión robusta con fallback a emoji
    img_b64 = ""
    icon_loaded = False
    
    try:
        # Intentar múltiples rutas posibles (local y Docker)
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "chatbot_icon.png"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "chatbot_icon.png"),
            "/app/frontend/assets/chatbot_icon.png",  # Ruta Docker
            "frontend/assets/chatbot_icon.png",  # Ruta relativa
        ]
        
        for icon_path in possible_paths:
            if os.path.exists(icon_path):
                with open(icon_path, "rb") as f:
                    img_b64 = base64.b64encode(f.read()).decode()
                    icon_loaded = True
                    break
    except Exception as e:
        print(f"[CHAT] No se pudo cargar icono: {e}")
        img_b64 = ""

    fab_container = st.container()
    with fab_container:
        # Usar key única basada en timestamp para evitar duplicados
        import time
        unique_key = f"fab_main_btn_{int(time.time() * 1000) % 10000}"
        if st.button("🤖", key=unique_key, help="Abrir/Cerrar Asistente"):
            st.session_state['chat_is_open'] = not st.session_state['chat_is_open']
            st.rerun()

    # CSS para posicionar el botón flotante
    if icon_loaded and img_b64:
        # Usar imagen como icono
        icon_url = f"data:image/png;base64,{img_b64}"
        fab_css = """
            position: fixed; bottom: 30px; right: 30px;
            width: 70px; height: 70px; z-index: 100001; opacity: 0;
        """
        st.markdown(f"""
            <style>
            .chat-fab-overlay {{
                position: fixed; bottom: 30px; right: 30px;
                width: 70px; height: 70px; z-index: 100000;
                background-image: url('{icon_url}');
                background-size: contain; background-repeat: no-repeat; background-position: center;
                border-radius: 50%; box-shadow: 0 8px 24px rgba(0,0,0,0.4);
                cursor: pointer; transition: transform 0.2s; border: 3px solid white;
            }}
            .chat-fab-overlay:hover {{ transform: scale(1.1); box-shadow: 0 12px 30px rgba(0,0,0,0.5); }}
            </style>
            <div class="chat-fab-overlay" onclick="document.querySelector('button[kind=secondary]').click();"></div>
        """, unsafe_allow_html=True)
    else:
        # Fallback: usar emoji 🤖 como icono visible
        fab_css = """
            position: fixed; bottom: 30px; right: 30px;
            width: 70px; height: 70px; z-index: 100001;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%; border: 3px solid white;
            box-shadow: 0 8px 24px rgba(0,0,0,0.4);
            display: flex; align-items: center; justify-content: center;
            font-size: 35px; cursor: pointer; transition: transform 0.2s;
        """
    
    fab_container.float(fab_css)
