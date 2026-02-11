import streamlit as st
from components.sidebar import render_sidebar
from views import login, dashboard, project_list, execution_detail
from services.mock_api_client import MockApiClient

# Configuración de página - Debe ser lo primero
st.set_page_config(
    page_title="Sistema P&A - SureOil",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_session_state():
    """Inicializa variables de sesión si no existen."""
    if 'user_role' not in st.session_state:
        st.session_state['user_role'] = None
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = 'Login'
    if 'selected_project_id' not in st.session_state:
        st.session_state['selected_project_id'] = None
    if 'api_client' not in st.session_state:
        st.session_state['api_client'] = MockApiClient()

def main_router():
    """
    Router Principal de la Aplicación.
    Controla qué vista se renderiza basado en el estado de la sesión.
    NO contiene lógica de negocio, solo switch de navegación.
    """
    role = st.session_state.get('user_role')
    page = st.session_state.get('current_page')

    # 1. Si no hay usuario logueado, forzar Login
    if not role:
        login.render_view()
        return

    # 2. Renderizar Sidebar Común (Navegación)
    render_sidebar()

    # 3. Router de Vistas
    if page == 'Dashboard':
        dashboard.render_view()
    
    elif page == 'Proyectos':
        project_list.render_view()
    
    elif page == 'Detalle Proyecto':
        # Validar que tengamos un ID seleccionado
        project_id = st.session_state.get('selected_project_id')
        if project_id:
            execution_detail.render_view(project_id)
        else:
            st.error("Error de Navegación: No se seleccionó ningún proyecto.")
            if st.button("Volver al Listado"):
                st.session_state['current_page'] = 'Proyectos'
                st.rerun()
                
    elif page == 'Logística':
        from views import logistics
        logistics.render_view()
        
    elif page == 'Documentación':
        st.title("🚧 Gestión Documental (Próximamente)")
    
    elif page == 'Datos Maestros':
        from views import admin_master_data
        admin_master_data.render_view()
        
    elif page == 'Auditoría':
        from views import global_audit
        global_audit.render_view()
        
    else:
        st.warning(f"Página no encontrada: {page}")

if __name__ == "__main__":
    init_session_state()
    main_router()
