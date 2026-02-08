import streamlit as st

def render_view():
    """
    Vista de Login (Mock).
    Permite seleccionar rol para probar los distintos flujos.
    """
    st.markdown("## 🔐 Ingreso al Sistema SureOil - P&A")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.container(border=True):
            st.image("frontend/assets/logo_stylized.png", use_container_width=True) # Logo Braco Energy Stylized
            
            st.info("⚠️ Entorno de Desarrollo (Mock)")
            
            role = st.selectbox(
                "Seleccione su Rol para continuar:",
                ["Ingeniero Campo", "Administrativo", "Gerente"],
                index=0
            )
            
            user = st.text_input("Usuario", value="usuario.demo")
            password = st.text_input("Contraseña", type="password", value="123456")
            
            if st.button("Iniciar Sesión", type="primary", use_container_width=True):
                # Simular autenticación exitosa
                st.session_state['user_role'] = role
                st.session_state['current_page'] = 'Dashboard'
                st.success(f"Bienvenido {user} ({role})")
                st.rerun()

            st.caption("Sistema de Gestión Integral de Abandono de Pozos V1.0")
