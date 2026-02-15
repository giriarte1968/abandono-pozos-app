import streamlit as st
import base64
import os
from services.auth_service import AuthService

def get_base64_of_bin_file(bin_file):
    """Lee un archivo binario y devuelve la cadena base64 para incrustar en CSS."""
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

def set_png_as_page_bg(png_file):
    """Establece una imagen local como fondo de pantalla completo."""
    bin_str = get_base64_of_bin_file(png_file)
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
        /* Contenedor de Login: Glassmorphism MEJORADO - más brillo */
        [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {{
            background: linear-gradient(135deg, rgba(0, 0, 0, 0.7) 0%, rgba(20, 20, 40, 0.8) 100%) !important;
            padding: 35px 45px !important;
            border-radius: 20px !important;
            border: 2px solid rgba(255, 255, 255, 0.4) !important;
            max-width: 340px !important;
            margin: auto !important;
            backdrop-filter: blur(20px) saturate(180%) !important;
            box-shadow: 
                0 8px 32px 0 rgba(0, 0, 0, 0.6),
                0 0 0 1px rgba(255, 255, 255, 0.1) inset,
                0 0 20px rgba(102, 126, 234, 0.3) !important;
        }}
        
        /* INPUTS MEJORADOS - más visibles */
        div[data-baseweb="input"], div[data-baseweb="select"], .stSelectbox div, .stTextInput div {{
            background-color: rgba(255, 255, 255, 0.25) !important;
            border: 2px solid rgba(255, 255, 255, 0.4) !important;
            border-radius: 12px !important;
            color: white !important;
            transition: all 0.3s ease !important;
        }}
        
        div[data-baseweb="input"]:hover, div[data-baseweb="select"]:hover {{
            background-color: rgba(255, 255, 255, 0.35) !important;
            border-color: rgba(255, 255, 255, 0.6) !important;
            box-shadow: 0 0 15px rgba(102, 126, 234, 0.4) !important;
        }}
        
        /* Texto en inputs con sombra para mejor legibilidad */
        input {{
            color: white !important;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5) !important;
            font-weight: 500 !important;
        }}
        
        /* Placeholders más visibles */
        input::placeholder {{
            color: rgba(255, 255, 255, 0.8) !important;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5) !important;
            font-weight: 400 !important;
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
    # 1. Configurar Fondo
    bg_file = "frontend/assets/landing_bg.jpg"
    if not os.path.exists(bg_file):
        bg_file = "frontend/assets/landing_bg.png"
    
    set_png_as_page_bg(bg_file)

    # 2. Espaciador Vertical
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    
    # Columnas para centrar el bloque
    col1, col2, col3 = st.columns([1.2, 1, 1.2])
    
    with col2:
        st.markdown("<h1 style='margin-bottom: 0;'>BRACO</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='margin-top: 0; font-weight: 200; letter-spacing: 5px;'>ENERGY</h3>", unsafe_allow_html=True)
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

        st.markdown("<div style='text-align: center; color: rgba(255,255,255,0.3); font-size: 0.7rem; margin-top: 25px;'>© 2026 Braco Energy System</div>", unsafe_allow_html=True)
