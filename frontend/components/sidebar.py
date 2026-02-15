"""
Sidebar Component - Versión 100% Nativa Streamlit
Elimina completamente la dependencia de streamlit_antd_components
"""

import streamlit as st

def render_sidebar():
    """
    Renderiza la barra lateral de navegación usando solo componentes nativos de Streamlit.
    Versión estable para producción en DigitalOcean.
    """
    role = st.session_state.get('user_role')
    api = st.session_state.get('api_client')
    current_page = st.session_state.get('current_page', 'Dashboard')
    
    with st.sidebar:
        # 1. Header con perfil
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px; padding-bottom: 20px;">
            <div style="background: #007bff; color: white; border-radius: 50%; width: 40px; height: 40px; display: flex; justify-content: center; align-items: center; font-weight: bold;">
                {role[0] if role else 'U'}
            </div>
            <div>
                <div style="font-weight: 600; font-size: 0.9rem;">{role}</div>
                <div style="font-size: 0.75rem; color: #888;">Online</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        
        # 2. SECCIÓN CONECTIVIDAD
        if api:
            st.markdown("###### 🌐 CONECTIVIDAD")
            try:
                is_online = api.is_online()
                
                # Toggle nativo de Streamlit
                new_conn = st.toggle("Modo Online", value=is_online)
                if new_conn != is_online:
                    api.set_connectivity(new_conn)
                    st.rerun()
                
                sync_count = api.get_sync_count()
                if sync_count > 0:
                    st.warning(f"🔄 {sync_count} cambios pendientes de sincronización")
                    if st.button("Sincronizar Ahora", use_container_width=True, type="primary"):
                        with st.spinner("Sincronizando..."):
                            success, msg = api.synchronize()
                            if success: st.success(msg)
                            else: st.error(msg)
                            st.rerun()
                            
            except Exception as e:
                st.error(f"Error de conectividad: {e}")

            st.divider()

        # 3. Menú de Navegación - 100% Nativo
        st.markdown("###### 📍 NAVEGACIÓN")
        
        # Dashboard siempre visible
        if st.button("📊 Dashboard", use_container_width=True, 
                    type="primary" if current_page == 'Dashboard' else "secondary"):
            st.session_state['current_page'] = 'Dashboard'
            st.rerun()
        
        st.divider()
        
        # Operaciones
        if role in ['Gerente', 'Administrativo', 'Ingeniero Campo']:
            st.markdown("**⚙️ Operaciones**")
            if st.button("📋 Proyectos", use_container_width=True,
                        type="primary" if current_page == 'Proyectos' else "secondary"):
                st.session_state['current_page'] = 'Proyectos'
                st.rerun()
            if st.button("🚚 Logística", use_container_width=True,
                        type="primary" if current_page == 'Logística' else "secondary"):
                st.session_state['current_page'] = 'Logística'
                st.rerun()
            if st.button("🏗️ Cementación", use_container_width=True,
                        type="primary" if current_page == 'Cementación' else "secondary"):
                st.session_state['current_page'] = 'Cementación'
                st.rerun()
            if st.button("🏁 Cierre Técnico", use_container_width=True,
                        type="primary" if current_page == 'Cierre Técnico' else "secondary"):
                st.session_state['current_page'] = 'Cierre Técnico'
                st.rerun()
            st.divider()
        
        # Finanzas
        if role in ['Administrativo', 'Gerente', 'Finanzas']:
            st.markdown("**💰 Finanzas**")
            if st.button("📈 Dashboard Financiero", use_container_width=True,
                        type="primary" if current_page == 'Dashboard Financiero' else "secondary"):
                st.session_state['current_page'] = 'Dashboard Financiero'
                st.rerun()
            if st.button("📑 Contratos", use_container_width=True,
                        type="primary" if current_page == 'Contratos' else "secondary"):
                st.session_state['current_page'] = 'Contratos'
                st.rerun()
            if st.button("📋 Certificaciones", use_container_width=True,
                        type="primary" if current_page == 'Certificaciones' else "secondary"):
                st.session_state['current_page'] = 'Certificaciones'
                st.rerun()
            st.divider()
        
        # Control & Calidad
        if role in ['Gerente', 'Supervisor', 'Administrativo']:
            st.markdown("**✅ Control & Calidad**")
            if st.button("📋 Cumplimiento", use_container_width=True,
                        type="primary" if current_page == 'Cumplimiento' else "secondary"):
                st.session_state['current_page'] = 'Cumplimiento'
                st.rerun()
            if st.button("🔒 Auditoría", use_container_width=True,
                        type="primary" if current_page == 'Auditoría' else "secondary"):
                st.session_state['current_page'] = 'Auditoría'
                st.rerun()
            st.divider()
        
        # Administración
        if role in ['Administrativo', 'Gerente']:
            st.markdown("**⚙️ Administración**")
            if st.button("🗄️ Datos Maestros", use_container_width=True,
                        type="primary" if current_page == 'Datos Maestros' else "secondary"):
                st.session_state['current_page'] = 'Datos Maestros'
                st.rerun()
            if st.button("💵 Datos Maestros Financieros", use_container_width=True,
                        type="primary" if current_page == 'Datos Maestros Financieros' else "secondary"):
                st.session_state['current_page'] = 'Datos Maestros Financieros'
                st.rerun()
            st.divider()
        
        # 4. Logout & Footer
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state['user_role'] = None
            st.session_state['current_page'] = 'Login'
            st.rerun()

        st.caption("v2.1.0 • Dev • Mock Mode")
