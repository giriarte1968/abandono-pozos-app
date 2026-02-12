import streamlit as st
import streamlit_antd_components as sac
import time
# from .chat import render_chat

def render_sidebar():
    """
    Renderiza la barra lateral de navegación usando componentes modernos.
    """
    role = st.session_state.get('user_role')
    api = st.session_state.get('api_client')
    current_page = st.session_state.get('current_page', 'Dashboard')
    
    with st.sidebar:
        # Header con perfil
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

        # Definir items del menú según rol
        menu_items = [
            sac.MenuItem('Dashboard', icon='bar-chart-fill'),
        ]

        # Operaciones
        if role in ['Gerente', 'Administrativo', 'Ingeniero Campo']:
            op_children = [
                sac.MenuItem('Proyectos', icon='clipboard-data'),
                sac.MenuItem('Logística', icon='truck'),
                sac.MenuItem('Cementación', icon='moisture'),
                sac.MenuItem('Cierre Técnico', icon='flag-fill'),
            ]
            menu_items.append(sac.MenuItem('Operaciones', icon='tools', children=op_children))

        # Control & Calidad
        if role in ['Gerente', 'Supervisor']:
            qa_children = [
                sac.MenuItem('Cumplimiento', icon='file-earmark-check'),
                sac.MenuItem('Auditoría', icon='shield-lock-fill'),
                sac.MenuItem('Documentación', icon='folder-fill'),
            ]
            menu_items.append(sac.MenuItem('Control & Calidad', icon='check-circle-fill', children=qa_children))

        # Administración
        if role == 'Administrativo':
            menu_items.append(
                sac.MenuItem('Administración', icon='gear-fill', children=[
                    sac.MenuItem('Datos Maestros', icon='database-fill'),
                ])
            )

        # Renderizar Menú
        # Buscamos el index del item activo para mantener la selección visual
        # Esto previene que se resetee al Dashboard cuando navegamos programáticamente
        
        # Aplanar la lista de items para buscar el index
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
            # Si la página actual no está en el menú (ej: Detalle Proyecto), 
            # no forzamos un index específico para no romper la visual.
            # Podríamos dejarlo en 0 o buscar el padre. 
            # Para "Detalle Proyecto", lo lógico es mantener "Proyectos" abierto/activo si se pudiera,
            # pero sac.menu no soporta 'seleccion parcial'.
            # Usamos index 1 (Proyectos) como fallback visual si estamos en detalle
            if current_page == 'Detalle Proyecto':
                 default_index = 1 # Proyectos
            else:
                 default_index = 0

        # Renderizamos el menú.
        # IMPORTANTE: key='sidebar_menu' permite que el estado del componente persista
        # pero si cambiamos 'index' programáticamente (al volver de Detalle), el componente debería actualizarse.
        selected_item = sac.menu(
            items=menu_items,
            index=default_index,
            format_func='title',
            size='sm',
            indent=20,
            open_index=[1, 2],
            key='sidebar_menu' 
        )

    # Lógica de Navegación:
    # Solo navegamos si el usuario HIZO CLIC en el menú.
    # sac.menu retorna el item seleccionado.
    # Si el item seleccionado en el menú es distinto a la página actual...
    if selected_item != current_page:
        # 1. Caso especial: Estamos en 'Detalle Proyecto' y el menú dice 'Proyectos' (por default_index=1)
        #    Si el usuario NO hizo clic, selected_item será 'Proyectos' (por el index).
        #    Para distinguir clic real de render inicial, comparamos con el estado anterior del menú si existiera,
        #    o simplemente asumimos que si estamos en Detalle, ignoramos el primer render de 'Proyectos'.
        
        # Simplificación robusta:
        # Si estamos en Detalle Proyecto y el menú selecciona Proyectos, NO hacemos nada (asumimos que es visual).
        if current_page == 'Detalle Proyecto' and selected_item == 'Proyectos':
            pass
        elif selected_item not in ['Operaciones', 'Control & Calidad', 'Administración']:
            st.session_state['current_page'] = selected_item
            st.rerun()

        st.divider()
        
        # --- CONECTIVIDAD OFFLINE ---
        st.subheader("🌐 Conectividad")
        is_online = api.is_online()
        new_conn = sac.switch(label='Modo Online', value=is_online, align='center', size='sm')
        if new_conn != is_online:
            api.set_connectivity(new_conn)
            st.rerun()
            
        sync_count = api.get_sync_count()
        if sync_count > 0:
            sac.alert(label=f"{sync_count} pendientes", description="Datos por sincronizar", color='warning', icon='cloud-upload')
            if st.button("🔄 Sincronizar Ahora", use_container_width=True, type="primary"):
                with st.spinner("Sincronizando..."):
                    success, msg = api.synchronize()
                    if success: st.success(msg)
                    else: st.error(msg)
                    time.sleep(1)
                    st.rerun()
        else:
            sac.alert(label='Sincronizado', color='success', icon='check-circle', size='sm', variant='transparent')

        # Chat removido del sidebar, ahora es flotante global
        pass

        st.divider()
        
        # Logout
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state['user_role'] = None
            st.session_state['current_page'] = 'Login'
            st.rerun()

        st.caption("v2.1.0 • Dev • Mock Mode")
