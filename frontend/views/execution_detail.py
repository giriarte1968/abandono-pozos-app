import streamlit as st
import pandas as pd
import time
from services.mock_api_client import MockApiClient
from components.stepper import render_stepper
from services.weather_service import WeatherService
from services.evidence_service import EvidenceService
from views.well_timeline import render_timeline
import folium
from streamlit_folium import st_folium

def render_view(project_id):
    # Usar cliente de sesion para persistencia (evitar reset en cada rerun)
    api = st.session_state.get('api_client')
    if not api:
        api = MockApiClient()
        st.session_state['api_client'] = api
        
    weather_service = WeatherService()
    evidence_service = EvidenceService(api.db, api.audit)
    
    username = st.session_state.get('username', 'unknown')
    user_role = st.session_state.get('user_role', 'unknown')
    
    # 1. Obtener datos del proyecto
    project = api.get_project_detail(project_id)
    
    if not project:
        st.error("Proyecto no encontrado")
        if st.button("Volver al Dashboard"):
            st.session_state['current_page'] = 'Dashboard'
            st.rerun()
        return

    # 2. Header y Navegacion
    col_nav1, col_nav2 = st.columns([1, 5])
    with col_nav1:
        if st.button("⬅ Volver"):
            st.session_state['current_page'] = 'Dashboard'
            st.rerun()
    with col_nav2:
        st.title(f"📂 Expediente de Abandono: Pozo {project['well']}")
    
    # --- CONTEXTO OPERATIVO (Informativo) ---
    with st.container(border=True):
        col_ctx1, col_ctx2, col_ctx3 = st.columns(3)
        col_ctx1.metric("🎯 Campaña", project.get('campana', 'N/A'))
        col_ctx2.metric("📅 Fecha Operativa", "2026-02-01")
        col_ctx3.metric("👥 Responsable", project.get('responsable', 'N/A'))

    # --- REGULATORY GATES (Hybrid Model) ---
    st.markdown("##### 🛡️ Status de Gates Regulatorios (External Truth)")
    if not api.is_online():
        st.warning("📡 **MODO OFFLINE**: Mostrando último estado conocido. Los 'Overrides' se sincronizarán al recuperar señal.")
    
    g_col1, g_col2, g_col3 = st.columns(3)
    
    # Cache de Overrides
    cache = api._offline_cache.get(project_id, {})

    # Gate 1: DTM
    dtm_ok = project.get('dtm_confirmado', False) or cache.get('GATE_DTM')
    g_col1.markdown(f"**Gate DTM / Apertura:**")
    g_col1.markdown(f"{'🟢 ABIERTO' if dtm_ok else '🔴 BLOQUEADO'}")
    if not dtm_ok and not api.is_online():
        if g_col1.button("Forzar Apertura (Offline)", key="ov_dtm"):
             api.manual_override_gate(project_id, "GATE_DTM", "Apertura forzada por falta de señal en locación.", user_id=username, user_role=user_role)
             st.rerun()
    
    # Gate 2: Personal
    pers_ok = project.get('personal_confirmado_hoy', False) or cache.get('GATE_PERS')
    g_col2.markdown(f"**Gate Personal Presente:**")
    g_col2.markdown(f"{'🟢 ABIERTO' if pers_ok else '🔴 BLOQUEADO'}")
    if not pers_ok and not api.is_online():
        if g_col2.button("Forzar Apertura (Offline)", key="ov_pers"):
             api.manual_override_gate(project_id, "GATE_PERS", "Ingreso manual validado físicamente (Sin señal).", user_id=username, user_role=user_role)
             st.rerun()

    # Gate 3: HSE
    hse_ok = (not any(p['critical'] and (not p.get('medical_ok') or not p.get('induction_ok')) for p in project.get('personnel_list', []))) or cache.get('GATE_HSE')
    g_col3.markdown(f"**Gate HSE Compliance:**")
    g_col3.markdown(f"{'🟢 CUMPLIDO' if hse_ok else '🚨 FALLA CRÍTICA'}")
    if not hse_ok and not api.is_online():
        if g_col3.button("Forzar Apertura (Offline)", key="ov_hse"):
             api.manual_override_gate(project_id, "GATE_HSE", "Cumplimiento validado por supervisor (Sin señal).", user_id=username, user_role=user_role)
             st.rerun()

    # Gate 4: Cumplimiento Regulatorio
    from services.compliance_service import ComplianceService
    _compliance = ComplianceService(audit_service=api.audit)
    _comp_summary = _compliance.get_compliance_summary(project_id)
    
    st.markdown("##### 📜 Cumplimiento Regulatorio")
    gc1, gc2, gc3 = st.columns(3)
    gc1.markdown(f"**{_comp_summary['resumen']}**")
    gc2.metric("Reglas Evaluadas", _comp_summary['total_reglas'])
    gc3.metric("Overrides Activos", _comp_summary['overrides'])

    # Gate 5: Control de Cementación
    from services.cementation_service import CementationService
    _cementation = CementationService(audit_service=api.audit)
    _cem_estado = _cementation.get_estado_cementacion_pozo(project_id)

    st.markdown("##### 🧪 Control de Cementación")
    cc1, cc2 = st.columns([3, 1])
    cc1.markdown(f"**{_cem_estado['resumen']}**")
    cc2.markdown(f"**Avance:** {'✅ Habilitado' if _cem_estado['puede_avanzar'] else '🚫 Bloqueado'}")

    # Gate 6: Cierre Técnico
    from services.closure_service import ClosureService
    _closure = ClosureService(audit_service=api.audit, cementation_service=_cementation)
    _cierre_estado = _closure.get_estado_cierre_pozo(project_id)

    st.markdown("##### 🏁 Cierre Técnico")
    ct1, ct2 = st.columns([3, 1])
    ct1.markdown(f"**{_cierre_estado['resumen']}**")
    ct2.markdown(f"**Regulador:** {'✅ Listo' if _cierre_estado['estado'] == 'CERRADO_DEFENDIBLE' else '🔄 Pendiente'}")

    # 3. Stepper de Progreso (mejorado con tooltips)
    render_stepper(project['status'])

    # --- Lógica Global de Estado Operativo ---
    # Se calcula ANTES de renderizar para mostrar el banner superior
    
    # 1. Personal
    personal_data = project.get('personnel_list', [])
    criticos_missing = [p for p in personal_data if p['critical'] and (not p.get('medical_ok') or not p.get('induction_ok'))] # Simulado check inicial
    # Nota: El check de "Presente" se hace en el loop de UI, aquí asumimos default True para el cálculo inicial o leemos de DB si existiera.
    # Para el MVP, el estado dinámico depende de la interacción del usuario, por lo que el cálculo final se hace al final del render o usamos st.session_state.
    # Simplificación MVP: Asumimos estado base "Con Riesgo" si hay criticos fallando en DB.
    
    # --- UI RENDER START ---

    # Banner de Estado Operativo (Placeholder inicial, se actualiza dinámicamente o se renderiza con datos guardados)
    # En este MVP stateless, calculamos en tiempo real.
    
    # --- CLIMA Y MAPA EN FILA (Side-by-Side) ---
    col_geo1, col_geo2 = st.columns(2)
    
    with col_geo1:
        # --- CLIMA EN LOCACIÓN ---
        with st.container(border=True, height=450):
            st.markdown(f"**📍 Meteorología** ({project.get('lat', 0)}, {project.get('lon', 0)})")
            
            # Fetch weather data
            weather = weather_service.get_weather(project.get('lat', -46.0), project.get('lon', -67.0))
            weather_alert = False

            if weather:
                w_c1, w_c2 = st.columns(2)
                w_c1.metric("Temp", weather['temp_actual'])
                w_c2.metric("Viento", weather['viento_actual'], delta_color="inverse" if weather['alerta_viento'] else "normal")
                st.caption(f"Forecast: Max {weather['max_temp']} / Min {weather['min_temp']}")
                st.caption(f"Precipitación: {weather['precip_actual']}")
                
                weather_alert = weather['alerta_viento']
                if weather['alerta_viento']:
                    st.warning("⚠️ ALERTA DE VIENTO")
            else:
                st.write("Datos no disponibles.")

    with col_geo2:
        # --- MAPA DE GEOLOCALIZACIÓN ---
        with st.container(border=True, height=450):
            st.markdown("**🗺️ Ubicación Geográfica**")
            
            lat = project.get('lat', -46.5)
            lon = project.get('lon', -68.0)
            well_id = project.get('well', project.get('id', 'N/A'))
            
            m = folium.Map(location=[lat, lon], zoom_start=12, tiles='OpenStreetMap')
            folium.Marker([lat, lon], tooltip=well_id, icon=folium.Icon(color='red')).add_to(m)
            
            st_folium(m, use_container_width=True, height=280, returned_objects=[])
            st.caption(f"Lat: {lat}, Lon: {lon}")
    
    # --- Disclaimer Obligatorio (Legal) ---
    st.markdown("""
    <div style="background-color: #fff3cd; padding: 10px; border-radius: 5px; font-size: 0.8em; color: #856404; margin-bottom: 20px;">
        <strong>⚠️ AVISO LEGAL IMPORTANTE:</strong> Datos meteorológicos referenciales obtenidos por ubicación geográfica cercana (Open-Meteo). 
        <strong>No sustituyen mediciones onsite ni informes oficiales.</strong> El Supervisor es responsable de validar condiciones con instrumental calibrado en campo.
    </div>
    """, unsafe_allow_html=True)
    
    # --- INFO POZO HORIZONTAL BAR ---
    with st.container(border=True):
        col_hdr1, col_hdr2, col_hdr3, col_hdr4 = st.columns(4)
        col_hdr1.markdown(f"**Pozo ID:**\n{project['well']}")
        col_hdr2.markdown(f"**Yacimiento:**\n{project.get('yacimiento', 'N/A')}")
        col_hdr3.markdown(f"**Estado:**\n`{project['status']}`")
        col_hdr4.markdown(f"**Legajo:**\nv2.1 (Digital)")
    
    # --- TELEMETRÍA EN VIVO (EDR) ---
    telemetry = project.get('rig_telemetry')
    if telemetry:
        with st.container(border=True):
            st.markdown(f"#### 🛰️ AbandonPro EDR: Telemetría de Alta Fidelidad")
            
            # Badge de Estado Rig
            rig_state = telemetry['rig_state']
            if rig_state == 'ALARM_STOP':
                st.error("🚨 RIG STATUS: EMERGENCY STOP / ALARM")
            else:
                st.success(f"🟢 RIG STATUS: {rig_state}")

            # --- FILA 1: MECÁNICA & HOISTING ---
            st.markdown("##### 🏗️ Mechanical & Hoisting")
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("Hook Load", f"{telemetry['hook_load']:.1f} {telemetry['hook_load_unit']}")
            m_col2.metric("Weight on Bit", f"{telemetry['wob']:.1f} {telemetry['wob_unit']}")
            m_col3.metric("Torque", f"{telemetry['torque']:.1f} {telemetry['torque_unit']}")
            m_col4.metric("Bit Depth", f"{telemetry['bit_depth']:.1f} {telemetry['bit_depth_unit']}")

            # --- FILA 2: HIDRÁULICA & PILETAS ---
            st.markdown("##### 🧪 Hydraulic & Pits (PVT)")
            h_col1, h_col2, h_col3, h_col4 = st.columns(4)
            h_col1.metric("Pump Pressure", f"{telemetry['pump_pressure']:.1f} {telemetry['pump_pressure_unit']}")
            h_col2.metric("Pump SPM", f"{telemetry['spm']} spm")
            h_col3.metric("Pit Volume", f"{telemetry['pit_volume']:.1f} {telemetry['pit_volume_unit']}")
            h_col4.metric("Trip Tank", f"{telemetry['trip_tank']:.1f} {telemetry['trip_tank_unit']}")

            # --- FILA 3: INTEGRIDAD & GAS ---
            st.markdown("##### 🛡️ Integrity & Safety")
            s_col1, s_col2, s_col3 = st.columns([1, 1, 2])
            s_col1.metric("Annular Pressure", f"{telemetry['annular_pressure']:.1f} {telemetry['annular_pressure_unit']}")
            s_col2.metric("Total Gas", f"{telemetry['gas_total']:.2f} {telemetry['gas_unit']}")
            s_col3.info(f"Última transmisión: {telemetry['last_update']} (High Frequency Stream)")

    st.subheader("⚡ Control Operativo Diario")
    
    # --- TAB DE OPERACIONES ---
    tab_personal, tab_equipos, tab_logistica, tab_stock, tab_permisos, tab_truth, tab_reporte = st.tabs([
        "👷 Personal", "🚜 Equipos", "🚚 Logística", "📦 Insumos", "🪪 Permisos", "🗂️ Truth Log", "📝 Parte Diario"
    ])

    # Variables de control de estado
    state_personal = True
    state_equipos = True
    state_logistica = True
    state_stock = True
    state_permisos = True
    
    cause_list = []

    # --- 1. PERSONAL ---
    with tab_personal:
        st.caption("Dotación y Habilitaciones HSE (Directo e Indirecto)")
        
        # Resumen de Dotación (Cálculo Meta vs Real)
        p_summary = project.get('personnel_summary', {"direct": 0, "indirect": 0, "total": 0})
        df_per = pd.DataFrame(project.get('personnel_list', []))
        
        # Validaciones Aptas
        val_direct = len(df_per[(df_per['category'] == 'DIRECTO') & (df_per['medical_ok']) & (df_per['induction_ok'])])
        val_indirect = len(df_per[(df_per['category'] == 'INDIRECTO') & (df_per['medical_ok']) & (df_per['induction_ok'])])
        
        c_pers1, c_pers2, c_pers3 = st.columns(3)
        c_pers1.metric("👷 Directo (Habilitado)", f"{val_direct}/{p_summary['direct']}")
        c_pers2.metric("🚛 Indirecto (Habilitado)", f"{val_indirect}/{p_summary['indirect']}")
        c_pers3.metric("👥 Total Proyecto", p_summary['total'])
        
        # Selector de Vista
        view_cat = st.radio("Filtrar por Categoría:", ["DIRECTO", "INDIRECTO", "TODOS"], horizontal=True)
        if view_cat != "TODOS":
            df_view = df_per[df_per['category'] == view_cat]
        else:
            df_view = df_per

        # Asegurar que existan las columnas necesarias para evitar KeyError
        for col in ['name', 'role', 'critical', 'medical_ok', 'induction_ok', 'present']:
            if col not in df_view.columns:
                df_view[col] = False if col in ['critical', 'medical_ok', 'induction_ok', 'present'] else "N/A"
        
        # Formatear columnas para visualización clara
        df_view['Status HSE'] = df_view.apply(lambda x: "✅ OK" if x['medical_ok'] and x['induction_ok'] else "🚨 BLOQUEADO", axis=1)
        df_view['Crítico'] = df_view['critical'].apply(lambda x: "⭐ SI" if x else "NO")
        
        # Renderizar Grilla
        st.dataframe(
            df_view[['name', 'role', 'Crítico', 'Status HSE', 'present']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "name": st.column_config.TextColumn("Nombre y Apellido"),
                "role": st.column_config.TextColumn("Función"),
                "Crítico": st.column_config.TextColumn("Crítico", help="Personal esencial"),
                "present": st.column_config.CheckboxColumn("Presente"),
                "Status HSE": st.column_config.TextColumn("Habilitación")
            }
        )
        
        # Gestión de Reemplazos / Overrides HSE
        with st.expander("🔄 Gestión de Personal / Reemplazos & Overrides"):
            st.markdown("Asignación de reemplazos validados por sistema HSE o Overrides Manuales (Gobernados):")
            col_r1, col_r2 = st.columns([2, 1])
            no_aptos = [p['name'] for p in project.get('personnel_list', []) if not p['medical_ok'] or not p['induction_ok']]
            selected_p = col_r1.selectbox("Recurso / Falla:", no_aptos if no_aptos else ["Todos Aptos"], disabled=not no_aptos)
            
            if no_aptos:
                st.date_input("Vencimiento de Excepción (MANDATORIO):", key="ov_expired_p")
                st.text_area("Justificación Técnica (Auditoría):", key="ov_just_p")
                
            if col_r2.button("Ejecutar Acción HSE", type="primary", use_container_width=True, disabled=not no_aptos):
                st.toast(f"Evento 'OVERRIDE_MANUAL' enviado para {selected_p}")

        # Lógica de bloqueo
        state_personal = not any(p['critical'] and (not p.get('medical_ok', False) or not p.get('induction_ok', False)) for p in project.get('personnel_list', []))
        if not state_personal:
            cause_list.append("Personal crítico con habilitación HSE vencida")

    # --- 2. EQUIPOS ---
    with tab_equipos:
        st.caption("Inventario de Activos y Cumplimiento de Cuotas")
        
        # --- NEW: Quota Progress Section ---
        with st.container(border=True):
            st.markdown("##### 📊 Cumplimiento de Cuotas")
            q_cols = st.columns(4)
            quotas = project.get('quotas', {}).get('DIRECTO', {})
            
            for i, (q_type, q_val) in enumerate(quotas.items()):
                target = q_val['target']
                current = q_val['current']
                status_color = "green" if current >= target else "red"
                q_cols[i % 4].metric(f"{q_type}", f"{current}/{target}", 
                                     delta="COMPLETO" if current >= target else f"FALTA {target-current}",
                                     delta_color="normal" if current >= target else "inverse")

        eq_list = project.get('equipment_list', [])
        
        # Agrupar por Categoría para visualización limpia
        for cat in ["DIRECTO", "INDIRECTO"]:
            st.markdown(f"#### 🛠️ EQUIPOS {cat}S")
            cat_eqs = [e for e in eq_list if e.get('category') == cat]
            
            if not cat_eqs:
                st.info(f"No hay equipos {cat.lower()}s registrados.")
                continue
                
            for eq in cat_eqs:
                with st.container(border=True):
                    col_eq1, col_eq2 = st.columns([2, 1])
                    col_eq1.markdown(f"**{eq['name']}**")
                    col_eq1.caption(f"Tipo: {eq.get('type', 'N/A')}")
                    
                    # Validation Source Badge
                    source = eq.get('validation_source', 'AUTOMATIC')
                    if source == 'MANUAL':
                        col_eq2.caption(f":orange[VALIDADO MANUALMENTE]")
                    else:
                        col_eq2.caption(f":green[{source}]")
                    
                    c1, c2, c3 = st.columns([2, 2, 2])
                        
                    # Estado de asignación y arribo
                    is_assigned = eq.get('assigned', False)
                    is_on_loc = c1.checkbox("En Locación", value=eq.get('is_on_location', False), key=f"eq_loc_{eq['name']}")
                    
                    # Determinación de estado visual
                    if not is_assigned:
                        c1.error("🚫 NO ASIGNADO")
                        state_equipos = False
                        cause_list.append(f"Equipo No Asignado: {eq['name']}")
                    elif not is_on_loc:
                        c1.warning("⏳ ASIGNADO - NO ARRIBÓ")
                        state_equipos = False
                        cause_list.append(f"Equipo Ausente: {eq['name']}")
                    else:
                        c1.success("✅ EN LOCACIÓN")
                    
                    # Estado operativo
                    status_opts = ["OPERATIVO", "FALLA MENOR", "FALLA CRITICA"]
                    curr_status = eq.get('status', 'OPERATIVO')
                    idx = status_opts.index(curr_status) if curr_status in status_opts else 0
                    status_eq = c2.selectbox("Estado", status_opts, index=idx, key=f"eq_st_{eq['name']}")
                    
                    # Evaluación de estado operativo
                    if status_eq == "FALLA CRITICA":
                        st.error(f"⛔ INOPERABLE")
                        state_equipos = False
                        cause_list.append(f"Falla Crítica Equipo: {eq['name']}")
                    elif status_eq == "FALLA MENOR":
                        st.warning(f"⚠️ Restringido")
                    
                    # Audit Trail for Manual
                    if source == 'MANUAL':
                        with c3.expander("🔍 Trazabilidad"):
                            st.text(f"Por: {eq.get('validated_by', 'N/A')}")
                            st.text(f"Fecha: {eq.get('validated_at', 'N/A')}")
                            if eq.get('justification'):
                                st.info(f"{eq['justification']}")

    # --- 3. LOGISTICA ---
    with tab_logistica:
        st.caption("Planificación vs Realidad (Transporte y Movilización)")
        for tr in project.get('transport_list', []):
            with st.container(border=True):
                col_t1, col_t2, col_t3 = st.columns([2, 2, 2])
                
                col_t1.markdown(f"**{tr['type']}**")
                col_t1.caption(f"Chofer: {tr['driver']}")
                
                # Tiempos Planificados vs Reales
                col_t2.markdown("**🕒 Hora Planificada**")
                col_t2.caption(f"{tr.get('time_plan', '--:--')} (Fuente: DTM)")
                
                arrival_time = col_t2.text_input("🕓 Hora Real Arribo", value=tr.get('time_arrival', '') or '', 
                                                  key=f"tr_time_{tr['id']}", placeholder="HH:MM")
                
                # Estado de arribo
                status_tr = col_t3.selectbox("Estado Arribo", ["PROGRAMADO", "EN RUTA", "ARRIBO", "NO ARRIBO"], 
                                              key=f"tr_st_{tr['id']}")
                
                # Evaluación de bloqueos
                if status_tr == "NO ARRIBO":
                    reason = col_t3.text_input("Motivo (Obligatorio)", key=f"tr_reas_{tr['id']}")
                    if not reason:
                        st.error("⛔ REQUERIDO: Justificar ausencia de transporte")
                        state_logistica = False
                        cause_list.append(f"Transporte {tr['type']}: Ausencia sin justificar")
                    else:
                        st.warning(f"⚠️ Transporte no disponible: {reason}")
                        # Dependiendo de criticidad del transporte, podría bloquear
                        if tr['type'] in ['Minibus']:  # Personal es crítico
                            state_logistica = False
                elif status_tr == "EN RUTA":
                    st.info("🚚 En tránsito hacia locación")

    # --- 4. STOCK ---
    with tab_stock:
        st.caption("Consumibles Críticos (Stock Inicial y Proyección)")
        for stock in project.get('stock_list', []):
            with st.container(border=True):
                col_s1, col_s2, col_s3 = st.columns([3, 2, 2])
                col_s1.markdown(f"**{stock['item']}**")
                
                curr = float(stock['current'])
                min_stock = float(stock['min'])
                unit = stock['unit']
                
                col_s2.metric("📦 Stock Inicial", f"{curr} {unit}")
                cons = col_s3.number_input(f"Consumo Previsto ({unit})", value=0.0, key=f"st_cons_{stock['item']}")
                
                remanente = curr - cons
                if remanente < min_stock:
                    st.error(f"⚠️ PROYECCIÓN POST-OP: {remanente} {unit} (DEBAJO DEL MÍNIMO: {min_stock})")
                    st.caption("🚨 Alerta: Requiere reabastecimiento")
                elif remanente < min_stock * 1.5:
                    st.warning(f"🟡 Proyección Post-Op: {remanente} {unit} (Cerca del mínimo)")
                else:
                    st.success(f"🟢 Proyección Post-Op: {remanente} {unit} (Stock Adecuado)")

    # --- 5. PERMISOS ---
    with tab_permisos:
        st.caption("Matriz de Permisos de Trabajo")
        for pt in project.get('permits_list', []):
            with st.container(border=True):
                col_p1, col_p2 = st.columns([3, 1])
                col_p1.markdown(f"**{pt['type']}**")
                col_p1.caption(f"Vence: {pt['expires']}")
                
                # Validation Source
                source = pt.get('validation_source', 'AUTOMATIC')
                if source == 'MANUAL':
                    col_p2.warning(":orange[MANUAL]")
                else:
                    col_p2.success(f":green[{source}]")
                
                # Status
                status = pt.get('status', 'VIGENTE')
                if status == 'VENCIDO':
                    st.error("⛔ VENCIDO")
                    state_permisos = False
                    cause_list.append(f"Permiso Vencido: {pt['type']}")
                else:
                    st.success("✅ VIGENTE")

    # --- 6. TRUTH LOG (AUDIT TIMELINE) ---
    with tab_truth:
        render_timeline(project_id)

    # --- 7. PARTE DIARIO ---
    with tab_reporte:
        # Consolidación final de estado operativo
        is_operable = state_personal and state_equipos and state_logistica and state_permisos
        
        if not is_operable:
            st.error("⛔ OPERACIÓN BLOQUEADA")
            with st.expander("Ver Causas de Bloqueo", expanded=True):
                for c in cause_list:
                    st.write(f"🔴 {c}")
            st.info("Debe resolver los bloqueos operativos para habilitar el reporte.")
        else:
            if weather_alert:
                st.warning("⚠️ OPERABLE CON RIESGO (Alerta Meteorológica)")
            else:
                st.success("✅ POZO HABILITADO")
                
            allowed_ops = project.get('allowed_operations', ["ESPERA"])
            
            with st.form("daily_rep"):
                st.subheader("Borrador de Parte Diario")
                
                # Operaciones habilitadas dinámicamente
                op = st.selectbox("Operación", allowed_ops, help="Operaciones filtradas por disponibilidad de equipos (Cisternas, Set Apertura, etc.)")
                
                # Advertencia si faltan operaciones comunes
                if "CEMENTACION" not in allowed_ops:
                    st.caption("ℹ️ *Cementación deshabilitada (Falta Cisterna operativa en locación)*")
                if "DTM" not in allowed_ops:
                    st.caption("ℹ️ *DTM deshabilitado (Falta Set de Apertura operativo)*")
                
                desc = st.text_area("Descripción de Actividades")
                
                # --- NUEVO: Selección de Canal de Comunicación ---
                st.divider()
                st.markdown("##### 📡 Canal de Transmisión")
                channels = ["INTERNET", "SMS (GSM)", "SATELITAL (Iridium/Garmin)"]
                if not api.is_online():
                    st.info("💡 Detectado: **MODO OFFLINE**. Puedes guardar en cola o usar una salida de emergencia.")
                
                selected_ch_label = st.radio("Seleccionar Vía de Envío:", channels, horizontal=True)
                channel_map = {"INTERNET": "INTERNET", "SMS (GSM)": "SMS", "SATELITAL (Iridium/Garmin)": "SATELITAL"}
                target_channel = channel_map[selected_ch_label]

                if target_channel != "INTERNET":
                    encoded_preview = api.encode_for_emergency_channel(project['id'], {"op": op, "desc": desc})
                    st.code(encoded_preview, language="markdown")
                    st.caption("☝️ *Mensaje comprimido generado para canal de bajo ancho de banda.*")

                # --- NUEVA SECCIÓN: CARGA DE EVIDENCIA ---
                st.divider()
                st.markdown("##### 📁 Evidencia Digital (Mandatorio)")
                st.caption("Cargue fotos o videos (máx 90s) para certificar la operación.")
                
                uploaded_file = st.file_uploader("Adjuntar Evidencia", type=["jpg", "png", "jpeg", "mp4", "pdf"])
                if uploaded_file:
                    if st.button("Confirmar Carga de Evidencia", type="secondary"):
                        res_ev = evidence_service.upload_evidence(
                            uploaded_file, project_id, project['status'], 
                            user_id=username, user_role=user_role
                        )
                        st.success(f"Evidencia certificada: {res_ev['hash'][:10]}...")

                if st.form_submit_button("Presentar Parte (Final)", type="primary"):
                    res = api.send_signal_parte_diario(
                        project['id'], 
                        {"op": op, "desc": desc}, 
                        channel=target_channel,
                        user_id=username,
                        user_role=user_role
                    )
                    
                    if res.get('status') == 'QUEUED':
                        st.info(f"📥 {res['msg']}")
                        st.warning("El reporte se enviará automáticamente cuando recuperes conexión.")
                    elif res.get('status') == 'EMERGENCY_SENT':
                        st.success(f"📟 {res['msg']}")
                        st.toast("Transmisión de emergencia completada")
                    else:
                        st.balloons()
                        st.success(res['msg'])
                    
                    time.sleep(2)
                    st.rerun()
    
    # Disclaimer Weather Footer
    st.markdown("---")
    st.caption("⚠️ **Aviso Legal:** Datos climáticos referenciales. No sustituyen mediciones en sitio.")
    
    # Disclaimer Weather Footer
    st.markdown("---")
    st.caption("⚠️ **Aviso Legal:** Datos climáticos referenciales. No sustituyen mediciones en sitio.")
