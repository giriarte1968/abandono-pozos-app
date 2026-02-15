"""
Sidebar Component - Versión con Option Menu
Más estable que antd, mejor UX que botones nativos
"""

import streamlit as st
from streamlit_option_menu import option_menu
import time
from .chat import render_chat

def render_sidebar():
    """
    Renderiza la barra lateral con option_menu (estable y profesional).
    """
    role = st.session_state.get('user_role')
    api = st.session_state.get('api_client')
    current_page = st.session_state.get('current_page', 'Dashboard')
    
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
        
        # Preparar menús según rol
        menu_options = []
        menu_icons = []
        
        # Dashboard siempre
        menu_options.append("Dashboard")
        menu_icons.append("bar-chart")
        
        # Operaciones
        if role in ['Gerente', 'Administrativo', 'Ingeniero Campo']:
            menu_options.extend(["Proyectos", "Logística", "Cementación", "Cierre Técnico"])
            menu_icons.extend(["clipboard-data", "truck", "moisture", "flag"])
        
        # Finanzas
        if role in ['Administrativo', 'Gerente', 'Finanzas']:
            menu_options.extend(["Dashboard Financiero", "Contratos", "Certificaciones"])
            menu_icons.extend(["graph-up", "file-earmark-text", "clipboard-check"])
        
        # Control & Calidad
        if role in ['Gerente', 'Supervisor', 'Administrativo']:
            menu_options.extend(["Cumplimiento", "Auditoría", "Documentación"])
            menu_icons.extend(["file-earmark-check", "shield-lock", "folder"])
        
        # Administración
        if role in ['Administrativo', 'Gerente']:
            menu_options.extend(["Datos Maestros", "Datos Maestros Financieros"])
            menu_icons.extend(["database", "cash-coin"])
        
        # Encontrar índice de página actual
        try:
            default_index = menu_options.index(current_page)
        except ValueError:
            default_index = 0
        
        # Renderizar menú con option_menu
        selected = option_menu(
            menu_title=None,  # Sin título para look limpio
            options=menu_options,
            icons=menu_icons,
            menu_icon="cast",  # Icono opcional del menú
            default_index=default_index,
            orientation="vertical",
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#667eea", "font-size": "18px"}, 
                "nav-link": {
                    "font-size": "16px", 
                    "text-align": "left", 
                    "margin": "0px",
                    "--hover-color": "#f0f2f6",
                    "border-radius": "10px",
                    "padding": "12px 15px",
                },
                "nav-link-selected": {
                    "background-color": "#667eea", 
                    "color": "white",
                    "font-weight": "600",
                    "border-radius": "10px",
                    "box-shadow": "0 2px 8px rgba(102, 126, 234, 0.4)",
                },
            }
        )
        
        # Navegar si cambió
        if selected != current_page:
            st.session_state['current_page'] = selected
            st.rerun()

        st.divider()
        
        # --- CONECTIVIDAD ---
        st.markdown("###### 🌐 CONECTIVIDAD")
        if api:
            try:
                is_online = api.is_online()
                new_conn = st.toggle("Modo Online", value=is_online)
                if new_conn != is_online:
                    api.set_connectivity(new_conn)
                    st.rerun()
                
                sync_count = api.get_sync_count()
                if sync_count > 0:
                    st.warning(f"🔄 {sync_count} cambios pendientes")
                    if st.button("Sincronizar", use_container_width=True, type="primary"):
                        with st.spinner("Sincronizando..."):
                            success, msg = api.synchronize()
                            if success: st.success(msg)
                            else: st.error(msg)
                            time.sleep(1)
                            st.rerun()
                else:
                    st.success("✅ Sincronizado")
                    
            except Exception as e:
                st.error(f"Error: {e}")

        st.divider()
        
        # --- CHAT ---
        render_chat()

        st.divider()
        
        # Logout
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state['user_role'] = None
            st.session_state['current_page'] = 'Login'
            st.rerun()

        st.caption("v2.1.0 • Dev • Mock Mode")
