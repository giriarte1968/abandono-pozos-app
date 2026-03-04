import streamlit as st
import base64
import os
from services.auth_service import AuthService

@st.cache_data(ttl=3600)
def get_base64_cached(file_path):
    """Cachea el base64 globalmente (una vez por hora, no por sesión)."""
    try:
        with open(file_path, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return None

def set_white_bg():
    """Establece un fondo blanco limpio y ajusta colores de texto para legibilidad."""
    page_bg_style = '''
    <style>
    .stApp {
        background-color: #FFFFFF !important;
    }
    
    /* Contenedor de Login: Fondo claro con sombra suave */
    [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
        background-color: #f8f9fa !important;
        padding: 40px !important;
        border-radius: 12px !important;
        border: 1px solid #dee2e6 !important;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05) !important;
    }
    
    /* Campos de Input */
    div[data-baseweb="input"], div[data-baseweb="select"], .stSelectbox div, .stTextInput div {
        background-color: #FFFFFF !important;
        border-color: #ced4da !important;
        color: #212529 !important;
    }
    
    input {
        color: #212529 !important;
    }
    
    /* Botón */
    .stButton button {
        background-color: #007bff !important;
        border: none !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: 0.3s !important;
        padding: 0.5rem 1rem !important;
    }
    .stButton button:hover {
        background-color: #0056b3 !important;
        transform: translateY(-1px);
    }

    /* Ocultar elementos de Streamlit */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden; font-size: 0;}
    footer {visibility: hidden;}

    /* Textos Oscuros para fondo blanco */
    h1, h2, h3, p, label, span {
        color: #212529 !important;
        text-align: center !important;
        font-family: 'Inter', sans-serif !important;
    }
    </style>
    '''
    st.markdown(page_bg_style, unsafe_allow_html=True)

def render_view():
    """
    Vista de Login (Landing Page) con layout dividido: Imagen Izquierda, Login Derecha.
    """
    set_white_bg()

    # Espaciado superior para centrar verticalmente
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    # Layout de 2 columnas (50% / 50%)
    col_img, col_form = st.columns([1, 1], gap="large")
    
    with col_img:
        # Mostrar logo/imagen en la columna izquierda
        image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "braco_chalten.jpg")
        img_base64 = get_base64_cached(image_path)
        
        if img_base64:
            st.image(f"data:image/jpeg;base64,{img_base64}", width="stretch")
        else:
            st.warning("Imagen no encontrada")

    with col_form:
        # Contenedor para el formulario a la derecha
        with st.container():
            # Título de texto
            st.markdown("<div style='text-align: center; margin-bottom: 30px;'><span style='font-size: 32px; font-weight: bold; color: #004085;'>AbandonPro</span> <br><span style='font-size: 14px; font-weight: 500; color: #6c757d;'>V1.0</span></div>", unsafe_allow_html=True)
            
            user = st.text_input("USER", label_visibility="collapsed", placeholder="USUARIO")
            
            st.write("")
            if st.button("INGRESAR", use_container_width=True):
                if not user:
                    st.error("Por favor, ingrese un usuario.")
                else:
                    auth_service = AuthService()
                    user_data = auth_service.authenticate(user, "")
                    
                    if user_data:
                        st.session_state['username'] = user_data['username']
                        st.session_state['user_role'] = user_data['role']
                        st.session_state['user_fullname'] = user_data['nombre_completo']
                        st.session_state['current_page'] = 'Dashboard'
                        st.success(f"Bienvenido {user_data['nombre_completo']}")
                        st.rerun()
                    else:
                        st.error("Usuario no encontrado. Prueba: admin, sebastian.cannes, juan.supervisor")

            st.markdown("<div style='text-align: center; color: #6c757d; font-size: 0.85rem; margin-top: 25px;'>Usuarios: admin, sebastian.cannes, demo.user</div>", unsafe_allow_html=True)
            st.markdown("<div style='text-align: center; color: #adb5bd; font-size: 0.75rem; margin-top: 15px;'>© 2026 AbandonPro V1.0</div>", unsafe_allow_html=True)
