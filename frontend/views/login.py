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

def set_background(png_file):
    """Establece una imagen local como fondo y ajusta estilos para legibilidad."""
    bin_str = get_base64_cached(png_file)
    if not bin_str:
        return
        
    page_bg_style = f'''
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
        zoom: 90%;
    }}
    
    /* Hacer transparente el contenedor principal para ver el fondo */
    [data-testid="stAppViewContainer"] > .main {{
        background-color: transparent;
    }}

    /* Contenedor de Login: Glassmorphism */
    [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {{
        background-color: rgba(0, 0, 0, 0.45) !important;
        padding: 30px 40px !important;
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        max-width: 340px !important;
        margin: auto !important;
        backdrop-filter: blur(15px) !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5) !important;
    }}
    
    /* Campos de Input */
    div[data-baseweb="input"], div[data-baseweb="select"], .stSelectbox div, .stTextInput div {{
        background-color: rgba(255, 255, 255, 0.15) !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
        color: white !important;
    }}
    
    input {{
        color: white !important;
    }}
    
    /* Botón */
    .stButton button {{
        background-color: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.4) !important;
        color: white !important;
        border-radius: 10px !important;
        transition: 0.3s !important;
    }}
    .stButton button:hover {{
        background-color: rgba(255, 255, 255, 0.2) !important;
        border-color: white !important;
    }}

    /* Ocultar elementos de Streamlit */
    header {{visibility: hidden;}}
    #MainMenu {{visibility: hidden; font-size: 0;}}
    footer {{visibility: hidden;}}

    /* Textos Blancos para fondo de imagen */
    h1, h2, h3, p, label, span {{
        color: white !important;
        text-align: center !important;
        font-family: 'Inter', sans-serif !important;
    }}
    </style>
    '''
    st.markdown(page_bg_style, unsafe_allow_html=True)

def render_view():
    """
    Vista de Login (Landing Page) con Fondo de Imagen.
    """
    set_background("frontend/assets/landing_bg.jpg")

    # 2. Espaciador Vertical
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    
    # Columnas para centrar el bloque
    col1, col2, col3 = st.columns([1.2, 1, 1.2])
    
    with col2:
        # Logo con Braco (base64 para performance)
        logo_path = "frontend/assets/braco_logo.jpeg"
        logo_b64 = get_base64_cached(logo_path)
        if logo_b64:
            st.markdown(f"""
                <div style='text-align: center; margin-bottom: 25px;'>
                    <img src='data:image/jpeg;base64,{logo_b64}' style='width: 260px;'>
                    <br><span style='font-size: 13px; font-weight: 500; letter-spacing: 1px; color: rgba(255,255,255,0.7) !important;'>V 1.0</span>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("<div style='text-align: center;'><span style='font-size: 28px; font-weight: bold;'>AbandonPro</span> <br><span style='font-size: 13px; font-weight: 500;'>V1.0</span></div>", unsafe_allow_html=True)
        
        st.write("")
        
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

        st.markdown("<div style='text-align: center; color: #6c757d; font-size: 0.75rem; margin-top: 15px;'>Usuarios: admin, sebastian.cannes, juan.supervisor, demo.user</div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center; color: #adb5bd; font-size: 0.7rem; margin-top: 25px;'>© 2026 AbandonPro V1.0</div>", unsafe_allow_html=True)
