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

def render_card(title, value, icon="📊", status_color=None):
    """Renderiza una card uniforme con icono, label y valor"""
    status_style = ""
    if status_color == "green":
        status_style = "background: linear-gradient(135deg, #1e3a2f 0%, #2d5a3d 100%); border-left: 4px solid #22c55e;"
    elif status_color == "red":
        status_style = "background: linear-gradient(135deg, #3a1e1e 0%, #5a2d2d 100%); border-left: 4px solid #ef4444;"
    elif status_color == "yellow":
        status_style = "background: linear-gradient(135deg, #3a3a1e 0%, #5a5a2d 100%); border-left: 4px solid #eab308;"
    else:
        status_style = "background: linear-gradient(135deg, #1e1e2e 0%, #2d2d3d 100%); border-left: 4px solid #3b82f6;"
    
    st.markdown(f"""
    <div style="{status_style} border-radius: 12px; padding: 20px; margin: 10px 0; height: 140px; display: flex; flex-direction: column; justify-content: space-between;">
        <div style="font-size: 24px; margin-bottom: 5px;">{icon}</div>
        <div style="font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px;">{title}</div>
        <div style="font-size: 20px; font-weight: 600; color: #fff;">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def render_gate_card(gate_name, status, icon, can_override=False, override_callback=None):
    """Renderiza una card de gate regulatorio con estado visual"""
    if status == "ABIERTO" or status == "CUMPLIDO":
        color = "green"
        badge = "🟢 ABIERTO"
        status_icon = "✓"
    elif status == "BLOQUEADO" or status == "FALLA CRÍTICA":
        color = "red"
        badge = "🔴 BLOQUEADO"
        status_icon = "✕"
    else:  # PENDIENTE
        color = "yellow"
        badge = "🟡 PENDIENTE"
        status_icon = "⏳"
    
    col1, col2 = st.columns([3, 1])
    with col1:
        render_card(gate_name, badge, icon, color)
    
    if can_override and (status == "BLOQUEADO" or status == "FALLA CRÍTICA"):
        with col2:
            if st.button("Forzar", key=f"ov_{gate_name}", use_container_width=True):
                if override_callback:
                    override_callback()

def render_view(project_id):
    # Usar cliente de sesion para persistencia
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

    # ═══════════════════════════════════════════════════════════════
    # HEADER PRINCIPAL
    # ═══════════════════════════════════════════════════════════════
    col_nav1, col_nav2 = st.columns([1, 8])
    with col_nav1:
        if st.button("⬅ Volver", use_container_width=True):
            st.session_state['current_page'] = 'Dashboard'
            st.rerun()
    with col_nav2:
        st.markdown(f"""
        <h1 style="margin: 0; padding: 0; background: linear-gradient(45deg, #3b82f6, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            📂 Expediente de Abandono: Pozo {project['well']}
        </h1>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════
    # SECCIÓN 1: INFORMACIÓN GENERAL (Grid 3 columnas)
    # ═══════════════════════════════════════════════════════════════
    st.markdown("##### 📋 Información General")
    
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        render_card("Campaña", project.get('campana', 'N/A'), "🎯")
    with col_info2:
        render_card("Fecha Operativa", "2026-02-01", "📅")
    with col_info3:
        render_card("Responsable", project.get('responsable', 'N/A'), "👥")
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════
    # SECCIÓN 2: GATES REGULATORIOS (External Truth)
    # ═══════════════════════════════════════════════════════════════
    st.markdown("##### 🛡️ Gates Regulatorios (External Truth)")
    
    # Cache de Overrides
    cache = api._offline_cache.get(project_id, {})
    
    col_gate1, col_gate2, col_gate3 = st.columns(3)
    
    with col_gate1:
        # Gate 1: DTM
        dtm_ok = project.get('dtm_confirmado', False) or cache.get('GATE_DTM')
        status = "ABIERTO" if dtm_ok else "BLOQUEADO"
        render_gate_card(
            "Gate DTM / Apertura", 
            status, 
            "🚪",
            can_override=not dtm_ok and not api.is_online(),
            override_callback=lambda: api.manual_override_gate(project_id, "GATE_DTM", "Apertura forzada por falta de señal en locación.", user_id=username, user_role=user_role)
        )
    
    with col_gate2:
        # Gate 2: Personal
        pers_ok = project.get('personal_confirmado_hoy', False) or cache.get('GATE_PERS')
        status = "ABIERTO" if pers_ok else "BLOQUEADO"
        render_gate_card(
            "Gate Personal Presente", 
            status, 
            "👷",
            can_override=not pers_ok and not api.is_online(),
            override_callback=lambda: api.manual_override_gate(project_id, "GATE_PERS", "Ingreso manual validado físicamente (Sin señal).", user_id=username, user_role=user_role)
        )
    
    with col_gate3:
        # Gate 3: HSE
        hse_ok = (not any(p['critical'] and (not p.get('medical_ok') or not p.get('induction_ok')) for p in project.get('personnel_list', []))) or cache.get('GATE_HSE')
        status = "CUMPLIDO" if hse_ok else "FALLA CRÍTICA"
        render_gate_card(
            "Gate HSE Compliance", 
            status, 
            "🛡️",
            can_override=not hse_ok and not api.is_online(),
            override_callback=lambda: api.manual_override_gate(project_id, "GATE_HSE", "Cumplimiento validado por supervisor (Sin señal).", user_id=username, user_role=user_role)
        )
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════
    # SECCIÓN 3: CUMPLIMIENTO REGULATORIO
    # ═══════════════════════════════════════════════════════════════
    st.markdown("##### 📜 Cumplimiento Regulatorio")
    
    from services.compliance_service import ComplianceService
    _compliance = ComplianceService(audit_service=api.audit)
    _comp_summary = _compliance.get_compliance_summary(project_id)
    
    col_comp_main, col_comp1, col_comp2 = st.columns([2, 1, 1])
    
    with col_comp_main:
        # Card resumen principal
        status_general = "CUMPLE" if _comp_summary['resumen'] == "CUMPLE" else "NO CUMPLE"
        color = "green" if status_general == "CUMPLE" else "red"
        render_card("Estado General", status_general, "✓" if status_general == "CUMPLE" else "✕", color)
        st.caption(f"**{_comp_summary['total_reglas']} reglas verificadas**")
    
    with col_comp1:
        render_card("Reglas Evaluadas", str(_comp_summary['total_reglas']), "📋")
    
    with col_comp2:
        render_card("Overrides Activos", str(_comp_summary['overrides']), "⚠️", "yellow" if _comp_summary['overrides'] > 0 else None)
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════
    # SECCIÓN 4: CONTROL DE CEMENTACIÓN
    # ═══════════════════════════════════════════════════════════════
    from services.cementation_service import CementationService
    _cementation = CementationService(audit_service=api.audit)
    _cem_estado = _cementation.get_estado_cementacion_pozo(project_id)
    
    st.markdown("##### 🧪 Control de Cementación")
    
    col_cem1, col_cem2 = st.columns([3, 1])
    with col_cem1:
        render_card("Estado Cementación", _cem_estado['resumen'], "🔧")
    with col_cem2:
        status = "✅ Habilitado" if _cem_estado['puede_avanzar'] else '🚫 Bloqueado'
        color = "green" if _cem_estado['puede_avanzar'] else "red"
        render_card("Avance", status, "▶", color)
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════
    # SECCIÓN 5: CIERRE TÉCNICO
    # ═══════════════════════════════════════════════════════════════
    from services.closure_service import ClosureService
    _closure = ClosureService(audit_service=api.audit, cementation_service=_cementation)
    _cierre_estado = _closure.get_estado_cierre_pozo(project_id)
    
    st.markdown("##### 🏁 Cierre Técnico")
    
    col_cierre1, col_cierre2 = st.columns([3, 1])
    with col_cierre1:
        render_card("Estado Cierre", _cierre_estado['resumen'], "🏁")
    with col_cierre2:
        status = '✅ Listo' if _cierre_estado['estado'] == 'CERRADO_DEFENDIBLE' else '🔄 Pendiente'
        color = "green" if _cierre_estado['estado'] == 'CERRADO_DEFENDIBLE' else "yellow"
        render_card("Regulador", status, "📋", color)
    
    st.markdown("---")
    
    # 3. Stepper de Progreso
    render_stepper(project['status'])
    
    # ═══════════════════════════════════════════════════════════════
    # SECCIÓN 6: CLIMA Y MAPA
    # ═══════════════════════════════════════════════════════════════
    weather_alert = False
    col_geo1, col_geo2 = st.columns(2)
    
    with col_geo1:
        st.markdown("##### 📍 Meteorología")
        with st.container(border=True):
            weather = weather_service.get_weather(project.get('lat', -46.0), project.get('lon', -67.0))
            
            if weather:
                weather_alert = weather.get('alerta_viento', False)
                w_c1, w_c2 = st.columns(2)
                w_c1.metric("Temp", weather['temp_actual'])
                w_c2.metric("Viento", weather['viento_actual'], delta_color="inverse" if weather['alerta_viento'] else "normal")
                st.caption(f"Forecast: Max {weather['max_temp']} / Min {weather['min_temp']}")
                st.caption(f"Precipitación: {weather['precip_actual']}")
                
                if weather['alerta_viento']:
                    st.warning("⚠️ ALERTA DE VIENTO")
            else:
                st.write("Datos no disponibles.")
    
    with col_geo2:
        st.markdown("##### 🗺️ Ubicación Geográfica")
        with st.container(border=True):
            lat = project.get('lat', -46.5)
            lon = project.get('lon', -68.0)
            well_id = project.get('well', project.get('id', 'N/A'))
            
            delta = 0.05
            lat_min = lat - delta
            lat_max = lat + delta
            lon_min = lon - delta
            lon_max = lon + delta
            
            st.markdown(f"""
            <div style="background-color: #1e1e1e; border-radius: 10px; padding: 10px;">
                <p style="margin: 0 0 10px 0; font-weight: bold;">🗺️ Mapa del pozo {well_id}</p>
                <iframe width="100%" height="280" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" 
                    src="https://www.openstreetmap.org/export/embed.html?bbox={lon_min}%2C{lat_min}%2C{lon_max}%2C{lat_max}&layer=mapnik&marker={lat}%2C{lon}" 
                    style="border-radius: 8px;">
                </iframe>
                <p style="margin: 5px 0 0 0; font-size: 12px; color: #888;">📍 {well_id} | Lat: {lat}, Lon: {lon}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Disclaimer Legal
    st.markdown("""
    <div style="background-color: #fff3cd; padding: 10px; border-radius: 5px; font-size: 0.8em; color: #856404; margin: 20px 0;">
        <strong>⚠️ AVISO LEGAL IMPORTANTE:</strong> Datos meteorológicos referenciales obtenidos por ubicación geográfica cercana (Open-Meteo). 
        <strong>No sustituyen mediciones onsite ni informes oficiales.</strong> El Supervisor es responsable de validar condiciones con instrumental calibrado en campo.
    </div>
    """, unsafe_allow_html=True)
    

    # ═══════════════════════════════════════════════════════════════
    # INFO POZO HORIZONTAL BAR
    # ═══════════════════════════════════════════════════════════════
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
                    
                    # time.sleep(2)
                    st.rerun()
    
    # Disclaimer Weather Footer
    st.markdown("---")
    st.caption("⚠️ **Aviso Legal:** Datos climáticos referenciales. No sustituyen mediciones en sitio.")
    
    # Disclaimer Weather Footer
    st.markdown("---")
    st.caption("⚠️ **Aviso Legal:** Datos climáticos referenciales. No sustituyen mediciones en sitio.")
