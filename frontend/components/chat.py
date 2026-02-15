import streamlit as st
import os
import base64

def render_chat():
    """
    Renderiza el Asistente Virtual Flotante.
    Versión simple y funcional sin dependencias problemáticas.
    """
    # Estado del chat
    if 'chat_is_open' not in st.session_state:
        st.session_state['chat_is_open'] = False

    # Datos de sesión
    api = st.session_state.get('api_client')
    project_id = st.session_state.get('selected_project_id')
    user_role = st.session_state.get('user_role', 'Usuario')
    history_key = f"chat_hist_{project_id if project_id else 'global'}"
    
    if history_key not in st.session_state:
        st.session_state[history_key] = []

    # 1. Ventana de Chat (Solo visible si está abierta)
    if st.session_state['chat_is_open']:
        with st.container():
            # Header
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                st.markdown("**🤖 Asistente**")
            with col2:
                if st.button("✖", key="close_chat"):
                    st.session_state['chat_is_open'] = False
                    st.rerun()
            
            st.divider()
            
            # Botones de Análisis
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                if st.button("🏗️ Operativo", key="analisis_op"):
                    st.session_state[history_key].append({
                        'rol': 'user', 
                        'msg': 'Análisis operativo solicitado'
                    })
                    st.session_state[history_key].append({
                        'rol': 'assistant', 
                        'msg': '🤖 **Análisis Operativo:**\n\n✅ Todos los proyectos activos están en estado normal.\n⚠️ Revisar permisos HSE del pozo M-555.\n📊 Logística al 85% de capacidad.'
                    })
                    st.rerun()
            
            with col_a2:
                if st.button("💰 Financiero", key="analisis_fin"):
                    st.session_state[history_key].append({
                        'rol': 'user', 
                        'msg': 'Análisis financiero solicitado'
                    })
                    st.session_state[history_key].append({
                        'rol': 'assistant', 
                        'msg': '🤖 **Análisis Financiero:**\n\n💰 Backlog: $1,470,000\n📈 Avance: 30.5%\n⚠️ Cobertura: 42 días (revisar)\n✅ 2 facturas cobradas correctamente.'
                    })
                    st.rerun()
            
            st.divider()
            
            # Mensajes
            if not st.session_state[history_key]:
                st.info("👋 ¿En qué puedo ayudarte?")
            else:
                for msg in st.session_state[history_key][-10:]:  # Últimos 10 mensajes
                    role = msg.get('rol', 'user')
                    content = msg.get('msg', '')
                    if role == 'user':
                        st.markdown(f"**Tú:** {content}")
                    else:
                        st.markdown(f"🤖 {content}")
            
            # Input
            prompt = st.text_input("Escribí tu consulta...", key="chat_input")
            if st.button("Enviar", key="send_msg") and prompt:
                st.session_state[history_key].append({'rol': 'user', 'msg': prompt})
                # Respuesta automática simple
                respuestas = {
                    'backlog': 'El backlog actual es $1,470,000 distribuido en 3 contratos.',
                    'certificacion': 'Hay 3 certificaciones registradas. 2 facturadas y 1 pendiente.',
                    'kpi': 'Avance financiero: 30.5% | Avance físico: 30% | Caja: $140,000',
                    'pozo': 'Tenemos 10 pozos: 4 SureOil, 3 YPF, 3 Petrobras.',
                }
                respuesta = respuestas.get(prompt.lower(), f"🤖 Recibido: '{prompt}'. Estoy procesando tu consulta...")
                st.session_state[history_key].append({'rol': 'assistant', 'msg': respuesta})
                st.rerun()

    # 2. Botón Flotante - usando HTML/CSS inline para posicionamiento
    # Generar key única para evitar duplicados
    if 'fab_key' not in st.session_state:
        import random
        st.session_state['fab_key'] = random.randint(10000, 99999)
    
    button_key = f"fab_{st.session_state['fab_key']}"
    
    # HTML + CSS para botón flotante
    st.markdown(f"""
    <style>
    .fab-button-{button_key} {{
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 60px;
        height: 60px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 50%;
        border: 3px solid white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        z-index: 99999;
        font-size: 28px;
        transition: transform 0.2s;
    }}
    .fab-button-{button_key}:hover {{
        transform: scale(1.1);
        box-shadow: 0 6px 20px rgba(0,0,0,0.4);
    }}
    .fab-container {{
        position: fixed;
        bottom: 30px;
        right: 30px;
        z-index: 99999;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Botón de Streamlit posicionado con CSS
    cols = st.columns([10, 1])
    with cols[1]:
        if st.button("🤖", key=button_key, help="Abrir/Cerrar Chat"):
            st.session_state['chat_is_open'] = not st.session_state['chat_is_open']
            st.rerun()
