import streamlit as st
import pandas as pd
from datetime import datetime
from services.mock_api_client import MockApiClient
from services.compliance_service import ComplianceService

def render_view():
    st.title("⚙️ Administración de Datos Maestros")
    st.caption("Gestión centralizada de Datos Maestros y Configuración Regulatoria. (Solo Administradores)")

    api = st.session_state.get('api_client', MockApiClient())
    
    # Instanciar servicio de cumplimiento con auditoría (usando audit del api si existe)
    audit_svc = getattr(api, 'audit', None)
    comp_svc = ComplianceService(audit_service=audit_svc)

    # --- TABS DE GESTIÓN ---
    tab_pozos, tab_personal, tab_equipos, tab_insumos, tab_campanas, tab_normativa = st.tabs([
        "📍 Pozos", "👷 Personal", "🚜 Equipos", "📦 Insumos", "📅 Campañas", "⚖️ Normativa"
    ])

    def ensure_df_columns(df, expected_cols):
        if df.empty:
            return pd.DataFrame(columns=expected_cols)
        # Asegurar que todas las columnas existan (aunque sea con None)
        for col in expected_cols:
            if col not in df.columns:
                df[col] = None
        return df[expected_cols]

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
        cols_pozos = ['id', 'nombre', 'yacimiento', 'estado_proyecto', 'responsable']
        df_pozos_display = ensure_df_columns(df_pozos, cols_pozos)
        st.dataframe(df_pozos_display, use_container_width=True)

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

        cols_per = ['name', 'role', 'category', 'medical_ok', 'induction_ok']
        df_per_display = ensure_df_columns(df_per, cols_per)
        st.dataframe(df_per_display, use_container_width=True)

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

        cols_eq = ['name', 'type', 'category', 'status']
        df_eq_display = ensure_df_columns(df_eq, cols_eq)
        st.dataframe(df_eq_display, use_container_width=True)

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

        cols_ins = ['item', 'unit', 'min']
        df_ins_display = ensure_df_columns(df_ins, cols_ins)
        st.dataframe(df_ins_display, use_container_width=True)

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

    # --- 6. NORMATIVA (NUEVO) ---
    with tab_normativa:
        st.subheader("Configuración de Cumplimiento Regulatorio")
        
        nt1, nt2, nt3 = st.tabs(["🏛️ Jurisdicciones", "📜 Versiones de Regulación", "📏 Reglas Específicas"])
        
        # --- JURISDICCIONES ---
        with nt1:
            juris = comp_svc.get_jurisdicciones()
            df_juris = pd.DataFrame(juris)
            
            with st.expander("➕ Nueva Jurisdicción"):
                with st.form("form_juris"):
                    j_nombre = st.text_input("Nombre Jurisdicción", placeholder="Ej: Neuquén - Cuenca Neuquina")
                    j_pais = st.text_input("País", value="Argentina")
                    j_prov = st.text_input("Provincia / Estado", value="Neuquén")
                    
                    if st.form_submit_button("Guardar Jurisdicción"):
                        if j_nombre:
                            comp_svc.upsert_jurisdiccion({
                                "nombre": j_nombre, "pais": j_pais, "provincia": j_prov, "activo": "S"
                            })
                            st.success(f"Jurisdicción {j_nombre} guardada")
                            st.rerun()
                        else:
                            st.error("El nombre es obligatorio")
            
            if not df_juris.empty:
                st.dataframe(df_juris[['jurisdiccion_id', 'nombre', 'pais', 'provincia']], use_container_width=True, hide_index=True)
            else:
                st.info("No hay jurisdicciones cargadas.")

        # --- VERSIONES ---
        with nt2:
            if not juris:
                st.warning("Cargue jurisdicciones primero.")
            else:
                juris_opts = {j['jurisdiccion_id']: j['nombre'] for j in juris}
                sel_juris_v = st.selectbox("Filtrar por Jurisdicción", list(juris_opts.keys()), format_func=lambda x: juris_opts[x], key="sel_jur_ver")
                
                versiones = comp_svc.get_versiones_por_jurisdiccion(sel_juris_v)
                
                with st.expander("➕ Nueva Versión Regulatoria"):
                    with st.form("form_version"):
                        v_nombre = st.text_input("Nombre Versión", placeholder="Ej: Res. 34/2025")
                        v_desc = st.text_area("Descripción/Alcance")
                        v_estado = st.selectbox("Estado Inicial", ["BORRADOR", "VIGENTE"])
                        
                        if st.form_submit_button("Crear Versión"):
                            if v_nombre:
                                comp_svc.upsert_version_regulacion({
                                    "jurisdiccion_id": sel_juris_v,
                                    "version_nombre": v_nombre,
                                    "fecha_vigencia": datetime.now().strftime("%Y-%m-%d"),
                                    "estado": v_estado,
                                    "descripcion": v_desc
                                })
                                st.success(f"Versión {v_nombre} creada")
                                st.rerun()
                            else:
                                st.error("Nombre requerido")

                if versiones:
                    df_ver = pd.DataFrame(versiones)
                    cols_ver = ['version_regulacion_id', 'version_nombre', 'estado', 'fecha_vigencia']
                    df_ver_display = ensure_df_columns(df_ver, cols_ver)
                    st.dataframe(df_ver_display, use_container_width=True, hide_index=True)
                else:
                    st.info("No hay versiones para esta jurisdicción.")

        # --- REGLAS ---
        with nt3:
            if not juris:
                st.warning("Configure Jurisdicciones y Versiones primero.")
            else:
                # Selector en cascada
                c1, c2 = st.columns(2)
                sel_jur_r = c1.selectbox("Jurisdicción", list(juris_opts.keys()), format_func=lambda x: juris_opts[x], key="sel_jur_reg")
                versiones_r = comp_svc.get_versiones_por_jurisdiccion(sel_jur_r)
                
                if not versiones_r:
                    st.warning("Esta jurisdicción no tiene versiones definidas.")
                    ver_opts = {v.get('version_regulacion_id'): v.get('version_nombre', f"Ver {v.get('version_regulacion_id')}") for v in versiones_r}
                    sel_ver_r = c2.selectbox("Versión Regulatoria", list(ver_opts.keys()), format_func=lambda x: ver_opts[x], key="sel_ver_reg")
                    
                    reglas = comp_svc.get_reglas_por_version(sel_ver_r)
                    
                    with st.expander("➕ Nueva Regla Regulatoria"):
                        with st.form("form_regla"):
                            r_cod = st.text_input("Código Regla", placeholder="Ej: REG-001")
                            r_desc = st.text_area("Descripción de la Regla")
                            r_param = st.text_input("Parámetro Técnico (Key)", placeholder="Ej: volumen_cemento_m3")
                            
                            c1, c2 = st.columns(2)
                            r_tipo = c1.selectbox("Tipo de Regla", ["VALOR_MINIMO", "VALOR_MAXIMO", "RANGO", "BOOLEANO", "REQUERIDO"])
                            r_sev = c2.selectbox("Severidad", ["ERROR", "ADVERTENCIA"])
                            
                            c3, c4 = st.columns(2)
                            r_min = c3.number_input("Valor Mínimo (si aplica)", value=0.0)
                            r_max = c4.number_input("Valor Máximo (si aplica)", value=0.0)
                            
                            r_bloq = st.checkbox("¿Es Bloqueante del Workflow?", value=(r_sev == "ERROR"))
                            
                            if st.form_submit_button("Guardar Regla"):
                                if r_cod and r_param:
                                    comp_svc.upsert_regla({
                                        "version_regulacion_id": sel_ver_r,
                                        "codigo_regla": r_cod,
                                        "descripcion": r_desc,
                                        "tipo_regla": r_tipo,
                                        "parametro": r_param,
                                        "valor_minimo": r_min if r_tipo in ["VALOR_MINIMO", "RANGO"] else None,
                                        "valor_maximo": r_max if r_tipo in ["VALOR_MAXIMO", "RANGO"] else None,
                                        "unidad": "unidad", # Simplificado
                                        "severidad": r_sev,
                                        "es_bloqueante": "S" if r_bloq else "N"
                                    })
                                    st.success(f"Regla {r_cod} guardada")
                                    st.rerun()
                                else:
                                    st.error("Código y Parámetro son obligatorios")
                    
                    if reglas:
                        df_rules = pd.DataFrame(reglas)
                        st.dataframe(df_rules[['codigo_regla', 'descripcion', 'tipo_regla', 'parametro', 'severidad']], use_container_width=True, hide_index=True)
                    else:
                        st.info("No hay reglas cargadas en esta versión.")

    # --- IMPORTACIÓN CSV ---
    st.divider()
    with st.expander("📥 Importación Masiva (CSV)"):
        st.write("Carga inicial de datos maestros vía archivos CSV.")
        up_file = st.file_uploader("Seleccionar archivo CSV", type=["csv"])
        if up_file:
            st.warning("Funcionalidad de procesamiento CSV en desarrollo.")
