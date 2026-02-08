import streamlit as st

def render_sidebar():
    """
    Renderiza la barra lateral de navegación.
    Adapta las opciones según el Rol del usuario.
    """
    role = st.session_state.get('user_role')
    
    with st.sidebar:
        st.header("🛢️ Gestión P&A")
        st.caption(f"Conectado como: **{role}**")
        st.divider()

        # Opciones Generales (Todos)
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state['current_page'] = 'Dashboard'
            st.rerun()

        # Opciones por Rol
        if role in ['Gerente', 'Administrativo', 'Ingeniero Campo']:
            if st.button("📋 Proyectos", use_container_width=True):
                st.session_state['current_page'] = 'Proyectos'
                st.rerun()

        if role == 'Administrativo':
            if st.button("🚚 Logística (DTM)", use_container_width=True):
                st.session_state['current_page'] = 'Logística'
                st.rerun()
            if st.button("📂 Documentación", use_container_width=True):
                st.session_state['current_page'] = 'Documentación'
                st.rerun()
            if st.button("⚙️ Datos Maestros", use_container_width=True):
                st.session_state['current_page'] = 'Datos Maestros'
                st.rerun()

        st.divider()
        
        # Logout simulado
        if st.button("🚪 Cerrar Sesión"):
            st.session_state['user_role'] = None
            st.session_state['current_page'] = 'Login'
            st.rerun()

        st.info("Build v0.1.0\nEnvironment: Dev (Mock)")
