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
        bottom: 20px;
        right: 20px;
        width: 60px;
        height: 60px;
        z-index: 10000;
        background-color: transparent; /* El botón de streamlit tiene su propio estilo, ajustamos el container */
    """
    
    # Aplicamos float al container del botón
    fab_container.float(fab_css)

    # Inyeccion CSS extra para hacer el botón realmente redondo y bonito
    # Ya que st.button es rectangular por defecto.
    st.markdown("""
        <style>
        /* Selector específico para el botón FAB basado en su key o estructura */
        /* Nota: Streamlit genera IDs dinámicos, pero podemos intentar targetear por jerarquía si es único */
        
        div.stButton > button[kind="secondary"] {
            /* Estilos base para resetear */
        }
        
        /* Buscamos el botón dentro del web component flotante si es posible, o usamos un selector global seguro */
        /* HACK: Estilizar TODOS los botones que sean SOLAMENTE un emoji de chat 💬 */
        div.stButton > button:has(div p:contains('💬')) {
            width: 60px !important;
            height: 60px !important;
            border-radius: 30px !important;
            background-color: #007bff !important;
            color: white !important;
            border: none !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.4) !important;
            font-size: 24px !important;
            padding: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            transition: transform 0.2s !important;
        }
        div.stButton > button:has(div p:contains('💬')):hover {
            transform: scale(1.1) !important;
            background-color: #0056b3 !important;
        }
        </style>
    """, unsafe_allow_html=True)
