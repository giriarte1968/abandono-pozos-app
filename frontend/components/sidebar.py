import streamlit as st
import streamlit_antd_components as sac
import time

def render_sidebar():
    """
    Renderiza la barra lateral de navegación usando componentes modernos.
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
        
        # 2. SECCIÓN CONECTIVIDAD (Justo debajo del perfil)
        st.markdown("###### 🌐 CONECTIVIDAD")
        is_online = api.is_online()
        new_conn = sac.switch(label='Modo Online', value=is_online, align='center', size='sm')
        if new_conn != is_online:
            api.set_connectivity(new_conn)
            st.rerun()
            
        sync_count = api.get_sync_count()
        if sync_count > 0:
            sac.alert(label=f"{sync_count} pendientes", description="Sincronizar datos", color='warning', icon='cloud-upload')
            if st.button("🔄 Sincronizar Ahora", use_container_width=True, type="primary"):
                with st.spinner("Sincronizando..."):
                    success, msg = api.synchronize()
                    if success: st.success(msg)
                    else: st.error(msg)
                    st.rerun()

        st.divider()

        # 3. Menú de Navegación
        menu_items = [
            sac.MenuItem('Dashboard', icon='bar-chart-fill'),
        ]

        if role in ['Gerente', 'Administrativo', 'Ingeniero Campo']:
            op_children = [
                sac.MenuItem('Proyectos', icon='clipboard-data'),
                sac.MenuItem('Logística', icon='truck'),
                sac.MenuItem('Cementación', icon='moisture'),
                sac.MenuItem('Cierre Técnico', icon='flag-fill'),
            ]
            menu_items.append(sac.MenuItem('Operaciones', icon='tools', children=op_children))

        if role in ['Gerente', 'Supervisor', 'Administrativo']:
            qa_children = [
                sac.MenuItem('Cumplimiento', icon='file-earmark-check'),
                sac.MenuItem('Auditoría', icon='shield-lock-fill'),
                sac.MenuItem('Documentación', icon='folder-fill'),
            ]
            menu_items.append(sac.MenuItem('Control & Calidad', icon='check-circle-fill', children=qa_children))

        if role in ['Administrativo', 'Gerente']:
            admin_children = [
                sac.MenuItem('Datos Maestros', icon='database-fill'),
                sac.MenuItem('Datos Maestros Financieros', icon='cash-coin'),
            ]
            menu_items.append(sac.MenuItem('Administración', icon='gear-fill', children=admin_children))

        if role in ['Administrativo', 'Gerente', 'Finanzas']:
            fin_children = [
                sac.MenuItem('Dashboard Financiero', icon='graph-up'),
                sac.MenuItem('Contratos', icon='file-earmark-text'),
                sac.MenuItem('Certificaciones', icon='clipboard-check'),
            ]
            menu_items.append(sac.MenuItem('Finanzas', icon='cash-stack', children=fin_children))

        # Aplanar para index
        flat_items = []
        def flatten(items):
            for item in items:
                flat_items.append(item.label)
                if hasattr(item, 'children') and item.children:
                    flatten(item.children)
        flatten(menu_items)
        
        try:
            default_index = flat_items.index(current_page)
        except ValueError:
            default_index = 1 if current_page == 'Detalle Proyecto' else 0

        selected_item = sac.menu(
            items=menu_items,
            index=default_index,
            format_func='title',
            size='sm',
            indent=20,
            open_index=[1, 2],
            key='sidebar_menu' 
        )

        st.divider()
        
        # 4. Logout & Footer
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state['user_role'] = None
            st.session_state['current_page'] = 'Login'
            st.rerun()

        st.caption("v2.1.0 • Dev • Mock Mode")

    # Lógica de Navegación (FUERA del sidebar context)
    if selected_item != current_page:
        if current_page == 'Detalle Proyecto' and selected_item == 'Proyectos':
            pass
        elif selected_item not in ['Operaciones', 'Control & Calidad', 'Administración']:
            st.session_state['current_page'] = selected_item
            st.rerun()
