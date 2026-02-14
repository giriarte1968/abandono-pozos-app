import streamlit as st
from streamlit_float import *

def render_chat():
    """
    Renderiza el Asistente Virtual Flotante.
    """
    # Inicializar float si no está hecho
    float_init()

    # Estado del chat
    if 'chat_is_open' not in st.session_state:
        st.session_state['chat_is_open'] = False

    # Datos de sesión
    api = st.session_state.get('api_client')
    project_id = st.session_state.get('selected_project_id')
    user_role = st.session_state.get('user_role', 'Usuario')
    history_key = f"chat_hist_{project_id if project_id else 'global'}"
    
    if history_key not in st.session_state:
        st.session_state[history_key] = []

    # 1. Ventana de Chat (Solo visible si está abierta)
    if st.session_state['chat_is_open']:
        chat_container = st.container()
        with chat_container:
            # Header
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                st.markdown("##### 🤖 Asistente P&A")
            with col2:
                if st.button("✖", key="close_chat_x"):
                    st.session_state['chat_is_open'] = False
                    st.rerun()
            
            st.divider()
            
            # Area de Mensajes (Scrollable inner container)
            messages = st.container(height=300)
            with messages:
                if not st.session_state[history_key]:
                    st.info("👋 ¡Hola! Soy tu asistente de abandono de pozos. ¿En qué puedo ayudarte hoy?")
                
                for msg in st.session_state[history_key]:
                    role = msg.get('rol') or msg.get('role')
                    content = msg.get('msg')
                    
                    if role == 'user':
                        st.chat_message("user").write(content)
                    else:
                        st.chat_message("assistant", avatar="🤖").write(content)

            # Input (Fuera del container scrollable pero dentro del flotante)
            if prompt := st.chat_input("Escribí tu consulta...", key="float_chat_input"):
                # Guardar User Msg
                st.session_state[history_key].append({'rol': 'user', 'msg': prompt})
                
                # Llamada API (Mock)
                try:
                    resp = api.send_chat_message(project_id, user_role, prompt)
                    st.session_state[history_key].append({'rol': 'assistant', 'msg': resp['response']})
                except Exception as e:
                    st.session_state[history_key].append({'rol': 'assistant', 'msg': "Error conectando con IA."})
                
                st.rerun()

        # CSS para la Ventana Flotante
        # Fondo oscuro, borde, sombra, posición fija abajo derecha
        # z-index alto para estar sobre todo
        chat_window_css = """
            position: fixed;
            bottom: 90px;
            right: 20px;
            width: 400px;
            max-width: 90vw;
            background-color: #1e1e1e;
            border: 1px solid #444;
            border-radius: 12px;
            padding: 15px;
            z-index: 9999;
            box-shadow: 0 10px 40px rgba(0,0,0,0.6);
        """
        chat_container.float(chat_window_css)

    # 2. Botón Flotante (FAB)
    # Siempre visible. Si el chat está abierto, puede cambiar de icono o acción.
    
    # Creamos un container para el botón
    fab_container = st.container()
    with fab_container:
        # Usamos un botón de Streamlit
        # Truco: Emoji grande como label
        if st.button("💬", key="fab_main_btn", help="Abrir/Cerrar Asistente"):
            st.session_state['chat_is_open'] = not st.session_state['chat_is_open']
            st.rerun()

    # CSS para el Botón Flotante
    # Redondo, color primario, sombra
    fab_css = """
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 70px;
        height: 70px;
        z-index: 10000;
        background-color: transparent;
    """
    
    # Aplicamos float al container del botón
    fab_container.float(fab_css)

    # Inyeccion CSS extra para hacer el botón realmente redondo y bonito
    st.markdown("""
        <style>
        /* HACK FUERTE: Targetear el botón por su atributo title (help) o estructura interna */
        button[title="Abrir/Cerrar Asistente"] {
            width: 70px !important;
            height: 70px !important;
            border-radius: 50% !important;
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%) !important;
            color: white !important;
            border: 2px solid rgba(255,255,255,0.2) !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.4) !important;
            font-size: 30px !important;
            padding: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            z-index: 99999 !important;
        }
        button[title="Abrir/Cerrar Asistente"]:hover {
            transform: scale(1.05) !important;
            box-shadow: 0 6px 20px rgba(0,123,255,0.6) !important;
            background: linear-gradient(135deg, #0056b3 0%, #003d80 100%) !important;
            border-color: white !important;
        }
        /* Eliminar estilos internos del div del texto */
        button[title="Abrir/Cerrar Asistente"] div {
            display: inline !important;
        }
        </style>
    """, unsafe_allow_html=True)
```
