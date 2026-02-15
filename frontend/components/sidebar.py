"""
Sidebar Component - Versión con Expanders (Acordeones)
Menú organizado por categorías, sin iconos, botones compactos
"""

import streamlit as st
import time
from .chat import render_chat

def render_sidebar():
    """
    Renderiza la barra lateral con menú organizado en expanders.
    Botones compactos sin iconos.
    """
    role = st.session_state.get('user_role')
    api = st.session_state.get('api_client')
    current_page = st.session_state.get('current_page', 'Dashboard')
    
    # CSS para hacer botones más compactos
    st.markdown("""
    <style>
    .stButton button {
        padding: 4px 8px !important;
        margin: 2px 0 !important;
        min-height: 32px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        # Header con perfil
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px; padding-bottom: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 50%; width: 45px; height: 45px; display: flex; justify-content: center; align-items: center; font-weight: bold; font-size: 1.2rem;">
                {role[0] if role else 'U'}
            </div>
            <div>
                <div style="font-weight: 600; font-size: 0.95rem;">{role}</div>
                <div style="font-size: 0.75rem; color: #888;">Online</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        
        # DASHBOARD - Siempre visible
        if st.button("Dashboard", use_container_width=True,
                    type="primary" if current_page == 'Dashboard' else "secondary"):
            st.session_state['current_page'] = 'Dashboard'
            st.rerun()
        
        st.divider()
        
        # OPERACIONES
        if role in ['Gerente', 'Administrativo', 'Ingeniero Campo']:
            with st.expander("Operaciones", expanded=False):
                if st.button("Proyectos", use_container_width=True,
                            type="primary" if current_page == 'Proyectos' else "secondary"):
                    st.session_state['current_page'] = 'Proyectos'
                    st.rerun()
                if st.button("Logística", use_container_width=True,
                            type="primary" if current_page == 'Logística' else "secondary"):
                    st.session_state['current_page'] = 'Logística'
                    st.rerun()
                if st.button("Cementación", use_container_width=True,
                            type="primary" if current_page == 'Cementación' else "secondary"):
                    st.session_state['current_page'] = 'Cementación'
                    st.rerun()
                if st.button("Cierre Técnico", use_container_width=True,
                            type="primary" if current_page == 'Cierre Técnico' else "secondary"):
                    st.session_state['current_page'] = 'Cierre Técnico'
                    st.rerun()
        
        # FINANZAS
        if role in ['Administrativo', 'Gerente', 'Finanzas']:
            with st.expander("Finanzas", expanded=False):
                if st.button("Dashboard Financiero", use_container_width=True,
                            type="primary" if current_page == 'Dashboard Financiero' else "secondary"):
                    st.session_state['current_page'] = 'Dashboard Financiero'
                    st.rerun()
                if st.button("Contratos", use_container_width=True,
                            type="primary" if current_page == 'Contratos' else "secondary"):
                    st.session_state['current_page'] = 'Contratos'
                    st.rerun()
                if st.button("Certificaciones", use_container_width=True,
                            type="primary" if current_page == 'Certificaciones' else "secondary"):
                    st.session_state['current_page'] = 'Certificaciones'
                    st.rerun()
        
        # CONTROL & CALIDAD
        if role in ['Gerente', 'Supervisor', 'Administrativo']:
            with st.expander("Control & Calidad", expanded=False):
                if st.button("Cumplimiento", use_container_width=True,
                            type="primary" if current_page == 'Cumplimiento' else "secondary"):
                    st.session_state['current_page'] = 'Cumplimiento'
                    st.rerun()
                if st.button("Auditoría", use_container_width=True,
                            type="primary" if current_page == 'Auditoría' else "secondary"):
                    st.session_state['current_page'] = 'Auditoría'
                    st.rerun()
                if st.button("Documentación", use_container_width=True,
                            type="primary" if current_page == 'Documentación' else "secondary"):
                    st.session_state['current_page'] = 'Documentación'
                    st.rerun()
        
        # ADMINISTRACIÓN
        if role in ['Administrativo', 'Gerente']:
            with st.expander("Administración", expanded=False):
                if st.button("Datos Maestros", use_container_width=True,
                            type="primary" if current_page == 'Datos Maestros' else "secondary"):
                    st.session_state['current_page'] = 'Datos Maestros'
                    st.rerun()
                if st.button("Datos Maestros Financieros", use_container_width=True,
                            type="primary" if current_page == 'Datos Maestros Financieros' else "secondary"):
                    st.session_state['current_page'] = 'Datos Maestros Financieros'
                    st.rerun()
        
        st.divider()
        
        # CONECTIVIDAD
        st.markdown("###### Conectividad")
        if api:
            try:
                is_online = api.is_online()
                new_conn = st.toggle("Modo Online", value=is_online)
                if new_conn != is_online:
                    api.set_connectivity(new_conn)
                    st.rerun()
                
                sync_count = api.get_sync_count()
                if sync_count > 0:
                    st.warning(f"{sync_count} cambios pendientes")
                    if st.button("Sincronizar", use_container_width=True, type="primary"):
                        with st.spinner("Sincronizando..."):
                            success, msg = api.synchronize()
                            if success: st.success(msg)
                            else: st.error(msg)
                            time.sleep(1)
                            st.rerun()
                else:
                    st.success("Sincronizado")
                    
            except Exception as e:
                st.error(f"Error: {e}")

        st.divider()
        
        # CHAT
        render_chat()

        st.divider()
        
        # LOGOUT
        if st.button("Cerrar Sesión", use_container_width=True):
            st.session_state['user_role'] = None
            st.session_state['current_page'] = 'Login'
            st.rerun()

        st.caption("v2.1.0 • Dev • Mock Mode")
