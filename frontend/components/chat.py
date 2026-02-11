import streamlit as st

def render_chat():
    """
    Renderiza el Asistente Virtual Operativo Antigravity v3.5.
    Disponible globalmente en el Sidebar.
    """
    api = st.session_state.get('api_client')
    project_id = st.session_state.get('selected_project_id')
    user_role = st.session_state.get('user_role', 'Supervisor')

    st.divider()
    st.markdown("### 🤖 Asistente Virtual")
    st.caption(f"Contexto: {project_id if project_id else 'Global'}")
    
    # Botón de Recomendación Rápida
    if st.button("📊 Generar Análisis de Situación", type="primary", use_container_width=True):
        result = api.send_chat_message(project_id, user_role, "Analiza la situación actual y dame recomendaciones")
        history_key = f"chat_history_{project_id if project_id else 'global'}"
        if history_key not in st.session_state:
            st.session_state[history_key] = api.get_chat_history(project_id) if project_id else []
        
        st.session_state[history_key].append(result['sent'])
        st.session_state[history_key].append(result['response'])
        st.rerun()

    # Historial de Chat
    history_key = f"chat_history_{project_id if project_id else 'global'}"
    if history_key not in st.session_state:
        st.session_state[history_key] = api.get_chat_history(project_id) if project_id else []
    
    chat_container = st.container(height=350)
    
    # Renderizar historial
    for msg in st.session_state[history_key]:
        is_ia = msg['origen'] == 'IA'
        with chat_container:
            if is_ia:
                st.chat_message("assistant", avatar="🤖").write(msg['msg'])
            else:
                st.chat_message("user").write(f"**{msg['rol']}**: {msg['msg']}")
    
    # Input de chat
    if prompt := st.chat_input("Pregunta al asistente..."):
        result = api.send_chat_message(project_id, user_role, prompt)
        st.session_state[history_key].append(result['sent'])
        if result['response']:
            st.session_state[history_key].append(result['response'])
        st.rerun()
