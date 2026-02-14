import streamlit as st
from dotenv import load_dotenv

# Cargar variables de entorno antes de cualquier otra cosa
load_dotenv()
from components.sidebar import render_sidebar
from views import login, dashboard, project_list, execution_detail
from services.mock_api_client import MockApiClient
from styles.custom_css import load_custom_css

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

    # Inyectar CSS global
    load_custom_css()

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
        from views import documentation_view
        documentation_view.render_view()
    
    elif page == 'Datos Maestros':
        from views import admin_master_data
        admin_master_data.render_view()
        
    elif page == 'Auditoría':
        from views import global_audit
        global_audit.render_view()

    elif page == 'Cumplimiento':
        from views import compliance_view
        compliance_view.render_view()

    elif page == 'Cementación':
        from views import cementation_view
        cementation_view.render_view()

    elif page == 'Cierre Técnico':
        from views import closure_view
        closure_view.render_view()

    elif page == 'Dashboard Financiero':
        from views import financial_dashboard
        financial_dashboard.render_financial_dashboard()

    elif page == 'Contratos':
        from views import financial_contracts
        financial_contracts.render_contracts_view()

    elif page == 'Certificaciones':
        from views import financial_certifications
        financial_certifications.render_certifications_view()

    elif page == 'Datos Maestros Financieros':
        from views import admin_financial_master_data
        admin_financial_master_data.render_view()
        
    else:
        st.warning(f"Página no encontrada: {page}")

    # 4. Renderizar Chat Flotante Global
    # Lo renderizamos dentro del Sidebar para evitar que ocupe espacio en el layout principal
    # al cargar, evitando el "salto" visual. CSS fixed lo posicionará en la pantalla.
    with st.sidebar:
        from components.chat import render_chat
        render_chat()

if __name__ == "__main__":
    init_session_state()
    main_router()
