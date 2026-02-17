import streamlit as st

def load_custom_css():
    st.markdown("""
        <style>
        /* Escalar toda la aplicación al 80% */
        .stApp {
            zoom: 80%;
            -moz-transform: scale(0.8);
            -moz-transform-origin: 0 0;
        }
        
        /* Tipografía más moderna */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        html, body, [class*="css"]  {
            font-family: 'Inter', sans-serif;
        }
        
        /* ============================================ */
        /* SELECTBOX / LOV - Tamaño consistente */
        /* ============================================ */
        
        /* Selector input - tamaño de fuente */
        div[data-baseweb="select"] > div {
            font-size: 14px !important;
        }
        
        /* Texto dentro del selector */
        div[data-baseweb="select"] input {
            font-size: 14px !important;
        }
        
        /* Dropdown panel - mismo ancho que selector */
        div[data-baseweb="select"] + div[data-baseweb="popover"],
        div[data-baseweb="popover"]:has(ul[role="listbox"]) {
            min-width: unset !important;
            width: max-content !important;
            max-width: 300px !important;
        }
        
        /* Items del dropdown - mismo tamaño de fuente */
        ul[role="listbox"] {
            font-size: 14px !important;
        }
        
        ul[role="listbox"] li {
            font-size: 14px !important;
            padding: 8px 12px !important;
        }
        
        ul[role="listbox"] li > div,
        ul[role="listbox"] li span {
            font-size: 14px !important;
        }
        
        /* Títulos con gradiente */
        h1, h2, h3 {
            background: -webkit-linear-gradient(45deg, #007bff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700 !important;
        }

        /* Tarjetas (Cards) para métricas y contenedores */
        div[data-testid="stMetric"], div.stExpander, div.stForm {
            background-color: #1e1e1e; /* Fondo oscuro suave */
            border-radius: 12px;
            padding: 1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            border: 1px solid #333;
            transition: transform 0.2s;
        }
        
        div[data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,123,255,0.2);
            border-color: #007bff;
        }

        /* Botones más estilizados */
        .stButton button {
            border-radius: 8px;
            font-weight: 600;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
        }
        
        /* Botón primario con gradiente */
        .stButton button[kind="primary"] {
            background: linear-gradient(90deg, #007bff 0%, #0056b3 100%);
            border: none;
        }

        /* Tablas más limpias */
        .stDataFrame {
            border: 1px solid #333;
            border-radius: 8px;
            overflow: hidden;
        }
        
        /* Sidebar mejorado */
        section[data-testid="stSidebar"] {
            background-color: #111;
            border-right: 1px solid #222;
        }
        
        /* Alertas personalizadas */
        div.stAlert {
            border-radius: 8px;
            border-left: 4px solid;
        }

        </style>
    """, unsafe_allow_html=True)

def card_container(title, content):
    st.markdown(f"""
    <div style="
        background-color: #1e1e1e;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #333;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    ">
        <h4 style="margin-top: 0; color: #fff;">{title}</h4>
        <div style="color: #ccc;">{content}</div>
    </div>
    """, unsafe_allow_html=True)
