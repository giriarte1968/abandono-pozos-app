import streamlit as st
import pandas as pd
from services.mock_api_client import MockApiClient

def render_view():
    st.title("⚙️ Administración de Datos Maestros")
    st.caption("Gestión centralizada de Pozos, Personal, Equipos e Insumos. (Solo Administradores)")

    api = st.session_state.get('api_client', MockApiClient())

    # --- TABS DE GESTIÓN ---
    tab_pozos, tab_personal, tab_equipos, tab_insumos, tab_campanas = st.tabs([
        "📍 Pozos", "👷 Personal", "🚜 Equipos", "📦 Insumos", "📅 Campañas"
    ])

    # --- 1. POZOS ---
    with tab_pozos:
        st.subheader("Gestión de Pozos")
        pozos = api.get_projects() # Usamos la lista de proyectos para simular pozos
        df_pozos = pd.DataFrame(pozos)
        
        # Formulario de Alta/Edición
        with st.expander("➕ Registrar / Editar Pozo"):
            with st.form("form_pozo", clear_on_submit=True):
                col1, col2 = st.columns(2)
                p_id = col1.text_input("ID Pozo", placeholder="Ej: X-123")
                p_nombre = col2.text_input("Nombre", placeholder="Ej: Pozo Los Perales 123")
                p_yac = col1.text_input("Yacimiento")
                p_tipo = col2.selectbox("Tipo Abandonado", ["TEMPORAL", "DEFINITIVO"])
                p_lat = col1.number_input("Latitud", format="%.6f", value=-46.0)
                p_lon = col2.number_input("Longitud", format="%.6f", value=-67.0)
                p_resp = st.text_input("Responsable Asignado")
                
                if st.form_submit_button("Guardar Pozo", type="primary"):
                    api.upsert_well({
                        "id": p_id, "nombre": p_nombre, "yacimiento": p_yac, 
                        "tipo_abandono": p_tipo, "lat": p_lat, "lon": p_lon, 
                        "responsable": p_resp, "estado_proyecto": "PLANIFICADO"
                    })
                    st.success(f"Pozo {p_id} guardado correctamente")
                    st.rerun()

        # Listado Actual
        st.dataframe(df_pozos[['id', 'nombre', 'yacimiento', 'estado_proyecto', 'responsable']], use_container_width=True)

    # --- 2. PERSONAL ---
    with tab_personal:
        st.subheader("Catálogo de Personal")
        personal = api.get_master_personnel()
        df_per = pd.DataFrame(personal)

        with st.expander("➕ Alta de Personal"):
            with st.form("form_personal", clear_on_submit=True):
                col1, col2 = st.columns(2)
                per_name = col1.text_input("Nombre Completo")
                per_dni = col2.text_input("DNI / Legajo")
                per_rol = col1.selectbox("Rol Principal", ["Supervisor", "HSE", "Operario", "Chofer", "Mecánico"])
                per_cat = col2.radio("Categoría", ["DIRECTO", "INDIRECTO"], horizontal=True)
                per_emp = st.text_input("Empresa Contratista")
                
                st.markdown("**Habilitaciones Iniciales (MVP Manual)**")
                c1, c2 = st.columns(2)
                h_med = c1.checkbox("Apto Médico Vigente")
                h_hse = c2.checkbox("Inducción HSE Vigente")
                
                if st.form_submit_button("Registrar Persona", type="primary"):
                    api.upsert_person({
                        "name": per_name, "dni": per_dni, "role": per_rol,
                        "category": per_cat, "empresa": per_emp,
                        "medical_ok": h_med, "induction_ok": h_hse
                    })
                    st.success(f"Recurso {per_name} registrado")
                    st.rerun()

        st.dataframe(df_per[['name', 'role', 'category', 'medical_ok', 'induction_ok']], use_container_width=True)

    # --- 3. EQUIPOS ---
    with tab_equipos:
        st.subheader("Inventario de Equipos")
        equipos = api.get_master_equipment()
        df_eq = pd.DataFrame(equipos)

        with st.expander("➕ Registrar Equipo"):
            with st.form("form_equipos", clear_on_submit=True):
                col1, col2 = st.columns(2)
                e_name = col1.text_input("Nombre/ID Equipo")
                e_tipo = col2.selectbox("Tipo", ["PULLING", "CISTERNA", "CEMENTADOR", "WIRELINE", "GRUA", "APERTURA"])
                e_cap = col1.text_input("Capacidad (Ej: 25m3, 500HP)")
                e_cat = col2.selectbox("Categoría", ["DIRECTO", "INDIRECTO"])
                e_status = st.selectbox("Estado Inicial", ["DISPONIBLE", "EN_MANTENIMIENTO"])
                
                if st.form_submit_button("Guardar Equipo", type="primary"):
                    api.upsert_equipment({
                        "name": e_name, "type": e_tipo, "capacity": e_cap,
                        "category": e_cat, "status": e_status, "assigned": False
                    })
                    st.success(f"Equipo {e_name} registrado")
                    st.rerun()

        st.dataframe(df_eq[['name', 'type', 'category', 'status']], use_container_width=True)

    # --- 4. INSUMOS ---
    with tab_insumos:
        st.subheader("Catálogo de Insumos")
        insumos = api.get_master_supplies()
        df_ins = pd.DataFrame(insumos)

        with st.expander("➕ Nuevo Insumo"):
            with st.form("form_insumos", clear_on_submit=True):
                i_name = st.text_input("Nombre Insumo")
                i_uni = st.selectbox("Unidad de Medida", ["u", "m3", "lts", "kgs", "bolsas"])
                i_ref = st.number_input("Stock de Referencia (Base)", value=100.0)
                
                if st.form_submit_button("Guardar Insumo", type="primary"):
                    api.upsert_supply({
                        "item": i_name, "unit": i_uni, "min": i_ref
                    })
                    st.success(f"Insumo {i_name} guardado")
                    st.rerun()

        st.dataframe(df_ins[['item', 'unit', 'min']], use_container_width=True)

    # --- 5. CAMPAÑAS ---
    with tab_campanas:
        st.subheader("Proyectos y Campañas")
        st.info("Asociación de Pozos a Campañas de Abandono.")
        
        with st.form("form_campana", clear_on_submit=True):
            c_name = st.text_input("Nombre de la Campaña")
            c_resp = st.text_input("Responsable de Campaña")
            c_range = st.date_input("Rango de Fechas", [])
            c_pozos = st.multiselect("Seleccionar Pozos", [p['nombre'] for p in pozos])
            
            if st.form_submit_button("Crear Campaña", type="primary"):
                api.upsert_campaign({
                    "name": c_name, "responsable": c_resp, 
                    "dates": c_range, "pozos": c_pozos
                })
                st.success(f"Campaña '{c_name}' creada con {len(c_pozos)} pozos.")

    # --- IMPORTACIÓN CSV ---
    st.divider()
    with st.expander("📥 Importación Masiva (CSV)"):
        st.write("Carga inicial de datos maestros vía archivos CSV.")
        up_file = st.file_uploader("Seleccionar archivo CSV", type=["csv"])
        if up_file:
            st.warning("Funcionalidad de procesamiento CSV en desarrollo.")
