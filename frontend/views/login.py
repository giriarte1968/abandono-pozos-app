import streamlit as st
import base64
import os
from services.auth_service import AuthService

def get_base64_cached(file_path):
    """Cachea el base64 en session_state para evitar recodificar en cada render."""
    cache_key = f"bg_base64_{file_path}"
    if cache_key not in st.session_state:
        try:
            with open(file_path, 'rb') as f:
                st.session_state[cache_key] = base64.b64encode(f.read()).decode()
        except FileNotFoundError:
            st.session_state[cache_key] = None
    return st.session_state[cache_key]

def set_png_as_page_bg(png_file):
    """Establece una imagen local como fondo de pantalla completo."""
    bin_str = get_base64_cached(png_file)
    if bin_str:
        page_bg_img = f'''
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        /* Hacer transparente el contenedor principal para ver el fondo */
        [data-testid="stAppViewContainer"] > .main {{
            background-color: transparent;
        }}
        /* Contenedor de Login: Glassmorphism más sólido (0.55) */
        [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {{
            background-color: rgba(0, 0, 0, 0.55) !important;
            padding: 30px 40px !important;
            border-radius: 20px !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            max-width: 340px !important;
            margin: auto !important;
            backdrop-filter: blur(15px) !important;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5) !important;
        }}
        
        /* HACER CAMPOS DE INPUT UN POCO MÁS SÓLIDOS (0.15) */
        div[data-baseweb="input"], div[data-baseweb="select"], .stSelectbox div, .stTextInput div {{
            background-color: rgba(255, 255, 255, 0.15) !important;
            border-color: rgba(255, 255, 255, 0.3) !important;
            color: white !important;
        }}
        
        /* Asegurar que el texto sea blanco en los inputs */
        input {{
            color: white !important;
        }}
        
        /* Botón primario estilizado */
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

        /* Ocultar elementos molestos de Streamlit */
        header {{visibility: hidden;}}
        #MainMenu {{visibility: hidden; font-size: 0;}}
        footer {{visibility: hidden;}}

        /* Textos Centrados */
        h1, h2, h3, p, label {{
            color: white !important;
            text-align: center !important;
            font-family: 'Helvetica', sans-serif !important;
        }}
        </style>
        '''
        st.markdown(page_bg_img, unsafe_allow_html=True)
    else:
        st.warning(f"No se encontró la imagen de fondo en: {png_file}")

def render_view():
    """
    Vista de Login (Landing Page) con Imagen de Fondo Full Screen.
    """
    # 1. Configurar Fondo (preferir WebP por menor tamaño)
    bg_file = "frontend/assets/landing_bg.webp"
    if not os.path.exists(bg_file):
        bg_file = "frontend/assets/landing_bg.jpg"
    
    set_png_as_page_bg(bg_file)

    # 2. Espaciador Vertical
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    
    # Columnas para centrar el bloque
    col1, col2, col3 = st.columns([1.2, 1, 1.2])
    
    with col2:
        st.markdown("<div style='text-align: center;'><span style='font-size: 28px; font-weight: bold;'>AbandonPro</span> <span style='font-size: 14px; font-weight: 200; letter-spacing: 2px;'>V1.0</span></div>", unsafe_allow_html=True)
        st.write("")
        
        user = st.text_input("USER", label_visibility="collapsed", placeholder="USUARIO")
        password = st.text_input("PASS", type="password", label_visibility="collapsed", placeholder="CONTRASEÑA (OPCIONAL)")
        
        st.write("")
        if st.button("INGRESAR", use_container_width=True):
            if not user:
                st.error("Por favor, ingrese un usuario.")
            else:
                auth_service = AuthService()
                # El password ya no se valida en el servicio
                user_data = auth_service.authenticate(user, "")
                
                if user_data:
                    st.session_state['username'] = user_data['username']
                    st.session_state['user_role'] = user_data['role']
                    st.session_state['user_fullname'] = user_data['nombre_completo']
                    st.session_state['current_page'] = 'Dashboard'
                    st.success(f"Bienvenido {user_data['nombre_completo']}")
                    st.rerun()
                else:
                    st.error("Usuario no encontrado en la base de datos.")

        st.markdown("<div style='text-align: center; color: rgba(255,255,255,0.3); font-size: 0.7rem; margin-top: 25px;'>© 2026 AbandonPro V1.0</div>", unsafe_allow_html=True)
