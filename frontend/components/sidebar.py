import streamlit as st
import time

from .chat import render_chat

def render_sidebar():
    """
    Renderiza la barra lateral de navegación.
    Adapta las opciones según el Rol del usuario.
    """
    role = st.session_state.get('user_role')
    api = st.session_state.get('api_client')
    
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
            if st.button("🛡️ Auditoría", use_container_width=True):
                st.session_state['current_page'] = 'Auditoría'
                st.rerun()
            if st.button("📜 Cumplimiento", use_container_width=True):
                st.session_state['current_page'] = 'Cumplimiento'
                st.rerun()
            if st.button("🧪 Cementación", use_container_width=True):
                st.session_state['current_page'] = 'Cementación'
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
        
        # --- CONECTIVIDAD OFFLINE ---
        st.subheader("🌐 Conectividad")
        is_online = api.is_online()
        new_conn = st.toggle("Modo Online", value=is_online, help="Simula pérdida de señal en el campo")
        if new_conn != is_online:
            api.set_connectivity(new_conn)
            st.rerun()
            
        sync_count = api.get_sync_count()
        if sync_count > 0:
            st.warning(f"📦 {sync_count} oper. pendientes")
            if st.button("🔄 Sincronizar Ahora", use_container_width=True, type="primary"):
                with st.spinner("Sincronizando con central..."):
                    success, msg = api.synchronize()
                    if success: st.success(msg)
                    else: st.error(msg)
                    time.sleep(1)
                    st.rerun()
        else:
            st.success("✅ Datos sincronizados")

        # --- ASISTENTE VIRTUAL GLOBAL ---
        render_chat()

        st.divider()
        
        # Logout simulado
        if st.button("🚪 Cerrar Sesión"):
            st.session_state['user_role'] = None
            st.session_state['current_page'] = 'Login'
            st.rerun()

        st.info("Build v0.1.0\nEnvironment: Dev (Mock)")
