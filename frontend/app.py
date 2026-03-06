import streamlit as st
import os
from dotenv import load_dotenv

# Configuración de página - Debe ser lo primero (Streamlit rule)
st.set_page_config(
    page_title="Sistema P&A - SureOil",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

import sys

# Cargar variables de entorno desde la raíz del proyecto
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)
load_dotenv(os.path.join(project_root, ".env"))

# Importaciones globales LIGERAS (para evitar KeyError: 'components' en hot-reload)
from components.sidebar import render_sidebar
from components.chat import render_chat
from styles.custom_css import load_custom_css

# Debug: Verificar si se cargó la API Key
if os.getenv("GEMINI_API_KEY"):
    pass # print("✅ GEMINI_API_KEY cargada correctamente")
else:
    print("⚠️ GEMINI_API_KEY NO encontrada en variables de entorno")

def init_session_state():
    """Inicializa variables de sesión si no existen."""
    if 'user_role' not in st.session_state:
        st.session_state['user_role'] = None
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = 'Login'
    if 'selected_project_id' not in st.session_state:
        st.session_state['selected_project_id'] = None
    if 'api_client' not in st.session_state:
        from services.mock_api_client import MockApiClient
        st.session_state['api_client'] = MockApiClient()

def main_router():
    """
    Router Principal de la Aplicación.
    Controla qué vista se renderiza basado en el estado de la sesión.
    """
    role = st.session_state.get('user_role')
    page = st.session_state.get('current_page')

    # 1. Si no hay usuario logueado, forzar Login
    if not role:
        from views import login
        login.render_view()
        return

    # Inyectar CSS global
    load_custom_css()

    # 2. Renderizar Sidebar Común (Navegación)
    render_sidebar()

    # 3. Router de Vistas
    if page == 'Dashboard':
        from views import dashboard
        dashboard.render_view()
    
    elif page == 'Proyectos':
        from views import project_list
        project_list.render_view()

    elif page == 'Estado Recursos':
        from views import dashboard_recursos_view
        dashboard_recursos_view.render_view()
    
    elif page == 'Detalle Proyecto':
        # Validar que tengamos un ID seleccionado
        project_id = st.session_state.get('selected_project_id')
        if project_id:
            from views import execution_detail
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
        
    elif page == 'Capacidad Contrato':
        from views import capacidad_contrato_view
        capacidad_contrato_view.render_view()
    
    elif page == 'Eficiencia Operativa':
        from views import dashboard_eficiencia_view
        dashboard_eficiencia_view.render_dashboard_eficiencia()
    
    elif page == 'Análisis Operacional':
        from views import analisis_operacional_view
        analisis_operacional_view.render_analisis_operacional()
    
    else:
        st.warning(f"Página no encontrada: {page}")

    # 4. Renderizar Chat Flotante Global
    with st.sidebar:
        render_chat()

if __name__ == "__main__":
    init_session_state()
    main_router()
