import streamlit as st
import pandas as pd
from datetime import date, datetime
from services.cementation_service import CementationService
from services.audit_service import AuditService


def render_view():
    """Vista principal de Control Inteligente de Cementación."""
    st.title("🧪 Control de Cementación")
    st.caption("Diseño aprobado vs Datos reales — Validación automática y auditable")

    audit = AuditService()
    cem = CementationService(audit_service=audit)
    user_role = st.session_state.get("user_role", "")
    user_id = st.session_state.get("username", "unknown")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📐 Diseños",
        "📊 Datos Reales",
        "✅ Validaciones",
        "📈 Dashboard",
    ])

    # ═══════════════════════════════════════════════════════════
    # TAB 1: DISEÑOS DE CEMENTACIÓN
    # ═══════════════════════════════════════════════════════════
    with tab1:
        st.subheader("Diseños de Cementación por Pozo")
        pozo_ids = cem.get_all_pozo_ids()

        # Lista de diseños existentes
        all_disenos = cem.get_disenos()
        if all_disenos:
            rows = []
            for d in all_disenos:
                estado_icon = {"BORRADOR": "📝", "APROBADO": "✅", "INACTIVO": "❌"}.get(d["estado_diseno"], "❓")
                rows.append({
                    "ID": d["diseno_cementacion_id"],
                    "Estado": f"{estado_icon} {d['estado_diseno']}",
                    "Pozo": d["id_pozo"],
                    "Lechada": d["tipo_lechada"],
                    "Vol. Teórico (m³)": d["volumen_teorico_m3"],
                    "Densidad (ppg)": d["densidad_objetivo_ppg"],
                    "P. Máx (psi)": d["presion_maxima_permitida_psi"],
                    "Intervalo": f"{d['intervalo_desde_m']} - {d['intervalo_hasta_m']} m",
                    "Aprobado por": d.get("aprobado_por", "—"),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            # Aprobar diseño en borrador
            borradores = [d for d in all_disenos if d["estado_diseno"] == "BORRADOR"]
            if borradores and user_role in ["Gerente", "Administrativo"]:
                st.divider()
                st.markdown("**Aprobar Diseño en Borrador**")
                borr_opciones = {d["diseno_cementacion_id"]: f"#{d['diseno_cementacion_id']} — {d['id_pozo']} ({d['tipo_lechada']})" for d in borradores}
                sel_borr = st.selectbox("Seleccionar diseño", options=list(borr_opciones.keys()), format_func=lambda x: borr_opciones[x])
                if st.button("✅ Aprobar Diseño", type="primary"):
                    ok, msg = cem.aprobar_diseno(sel_borr, user_id)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            st.info("No hay diseños registrados.")

        # Formulario de nuevo diseño
        st.divider()
        with st.expander("➕ Nuevo Diseño de Cementación", expanded=False):
            with st.form("form_diseno"):
                col1, col2 = st.columns(2)
                with col1:
                    pozo = st.text_input("ID Pozo *", placeholder="Ej: X-123")
                    vol = st.number_input("Volumen Teórico (m³) *", min_value=0.1, value=8.0, step=0.5)
                    densidad = st.number_input("Densidad Objetivo (ppg) *", min_value=5.0, value=15.8, step=0.1)
                    presion = st.number_input("Presión Máx Permitida (psi) *", min_value=100.0, value=3500.0, step=100.0)
                with col2:
                    desde = st.number_input("Intervalo Desde (m) *", min_value=0.0, value=500.0, step=50.0)
                    hasta = st.number_input("Intervalo Hasta (m) *", min_value=0.0, value=1200.0, step=50.0)
                    lechada = st.selectbox("Tipo Lechada *", ["Clase G Estándar", "Clase G + Microesfera", "Clase H Premium", "Clase H + Látex", "Espumada"])

                submitted = st.form_submit_button("💾 Guardar como Borrador")
                if submitted:
                    if not pozo.strip():
                        st.error("El ID de pozo es obligatorio")
                    elif hasta <= desde:
                        st.error("El intervalo 'Hasta' debe ser mayor que 'Desde'")
                    else:
                        nuevo = {
                            "id_pozo": pozo.strip(),
                            "volumen_teorico_m3": vol,
                            "densidad_objetivo_ppg": densidad,
                            "presion_maxima_permitida_psi": presion,
                            "intervalo_desde_m": desde,
                            "intervalo_hasta_m": hasta,
                            "tipo_lechada": lechada,
                        }
                        cem.upsert_diseno(nuevo, user_id)
                        st.success("Diseño guardado como BORRADOR")
                        st.rerun()

    # ═══════════════════════════════════════════════════════════
    # TAB 2: DATOS REALES
    # ═══════════════════════════════════════════════════════════
    with tab2:
        st.subheader("Carga de Datos Reales del Proveedor")

        aprobados = [d for d in cem.get_disenos() if d["estado_diseno"] == "APROBADO"]
        if not aprobados:
            st.warning("No hay diseños aprobados. Apruebe un diseño primero.")
        else:
            # Datos existentes
            all_datos = []
            for d in aprobados:
                datos_d = cem.get_datos_reales(diseno_id=d["diseno_cementacion_id"])
                for dr in datos_d:
                    dr["_pozo"] = d["id_pozo"]
                    dr["_lechada"] = d["tipo_lechada"]
                all_datos.extend(datos_d)

            if all_datos:
                st.markdown("**Datos Registrados**")
                rows_dr = []
                for dr in all_datos:
                    rows_dr.append({
                        "ID": dr["dato_real_cementacion_id"],
                        "Pozo": dr["_pozo"],
                        "Lechada": dr["_lechada"],
                        "Vol. Real (m³)": dr["volumen_real_m3"],
                        "Densidad Real (ppg)": dr["densidad_real_ppg"],
                        "P. Máx Reg. (psi)": dr["presion_maxima_registrada_psi"],
                        "Tiempo (min)": dr.get("tiempo_bombeo_min", "—"),
                        "Proveedor": dr["proveedor_servicio"],
                        "Fecha": dr["fecha_ejecucion"],
                    })
                st.dataframe(pd.DataFrame(rows_dr), use_container_width=True, hide_index=True)
                st.divider()

            # Carga manual
            with st.expander("➕ Cargar Datos Reales (Manual)", expanded=not all_datos):
                diseno_opciones = {
                    d["diseno_cementacion_id"]: f"#{d['diseno_cementacion_id']} — Pozo {d['id_pozo']} ({d['tipo_lechada']}) | Vol: {d['volumen_teorico_m3']} m³"
                    for d in aprobados
                }
                with st.form("form_datos_reales"):
                    sel_diseno = st.selectbox("Diseño de Referencia *", options=list(diseno_opciones.keys()), format_func=lambda x: diseno_opciones[x])
                    col1, col2 = st.columns(2)
                    with col1:
                        vol_real = st.number_input("Volumen Real (m³) *", min_value=0.1, value=8.0, step=0.5)
                        dens_real = st.number_input("Densidad Real (ppg) *", min_value=5.0, value=15.8, step=0.1)
                        pres_real = st.number_input("Presión Máx Registrada (psi) *", min_value=0.0, value=3000.0, step=100.0)
                    with col2:
                        tiempo = st.number_input("Tiempo de Bombeo (min)", min_value=0.0, value=120.0, step=5.0)
                        proveedor = st.text_input("Proveedor de Servicio *", placeholder="Ej: Halliburton")
                        fecha_ej = st.date_input("Fecha de Ejecución *", value=date.today())

                    submitted_dr = st.form_submit_button("📤 Cargar y Validar Automáticamente", type="primary")
                    if submitted_dr:
                        if not proveedor.strip():
                            st.error("El proveedor es obligatorio")
                        else:
                            datos_nuevos = {
                                "diseno_cementacion_id": sel_diseno,
                                "volumen_real_m3": vol_real,
                                "densidad_real_ppg": dens_real,
                                "presion_maxima_registrada_psi": pres_real,
                                "tiempo_bombeo_min": tiempo,
                                "proveedor_servicio": proveedor.strip(),
                                "fecha_ejecucion": str(fecha_ej),
                            }
                            ok, msg, val = cem.cargar_datos_reales(datos_nuevos, user_id)
                            if ok:
                                resultado = val["resultado_validacion"]
                                icon = {"OK": "🟢", "ALERTA": "🟡", "CRITICO": "🔴"}[resultado]
                                st.success(f"{msg} — Resultado: {icon} **{resultado}**")
                                st.rerun()
                            else:
                                st.error(msg)

            # Carga CSV
            with st.expander("📂 Importar CSV de Datos Reales"):
                st.markdown("""
                **Formato esperado del CSV:** `diseno_id, volumen_real, densidad_real, presion_max, tiempo_bombeo, proveedor, fecha_ejecucion`
                """)
                csv_file = st.file_uploader("Seleccionar archivo CSV", type=["csv"], key="csv_cem")
                if csv_file:
                    try:
                        df_csv = pd.read_csv(csv_file)
                        st.dataframe(df_csv, use_container_width=True)
                        if st.button("▶️ Procesar CSV"):
                            ok_count, err_count = 0, 0
                            for _, row in df_csv.iterrows():
                                datos_csv = {
                                    "diseno_cementacion_id": int(row.iloc[0]),
                                    "volumen_real_m3": float(row.iloc[1]),
                                    "densidad_real_ppg": float(row.iloc[2]),
                                    "presion_maxima_registrada_psi": float(row.iloc[3]),
                                    "tiempo_bombeo_min": float(row.iloc[4]) if len(row) > 4 else 0,
                                    "proveedor_servicio": str(row.iloc[5]) if len(row) > 5 else "CSV Import",
                                    "fecha_ejecucion": str(row.iloc[6]) if len(row) > 6 else str(date.today()),
                                }
                                ok, _, _ = cem.cargar_datos_reales(datos_csv, user_id)
                                if ok:
                                    ok_count += 1
                                else:
                                    err_count += 1
                            st.success(f"CSV procesado: {ok_count} registros OK, {err_count} errores")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error al procesar CSV: {e}")

    # ═══════════════════════════════════════════════════════════
    # TAB 3: VALIDACIONES
    # ═══════════════════════════════════════════════════════════
    with tab3:
        st.subheader("Resultados de Validación Automática")

        data = cem._load_mock_data()
        validaciones = data["validaciones"]

        if not validaciones:
            st.info("No hay validaciones registradas. Cargue datos reales para generar validaciones automáticas.")
        else:
            for v in validaciones:
                # Obtener contexto
                dato = next((d for d in data["datos_reales"] if d["dato_real_cementacion_id"] == v["dato_real_cementacion_id"]), None)
                diseno = None
                if dato:
                    diseno = cem.get_diseno(dato["diseno_cementacion_id"])

                resultado = v["resultado_validacion"]
                icon = {"OK": "🟢", "ALERTA": "🟡", "CRITICO": "🔴"}[resultado]
                override_tag = " *(OVERRIDE)* " if v.get("override_aplicado") == "S" else ""
                pozo_label = diseno["id_pozo"] if diseno else "?"

                with st.expander(f"{icon} Validación #{v['validacion_cementacion_id']} — Pozo {pozo_label} — {resultado}{override_tag}", expanded=(resultado == "CRITICO")):
                    # Barras de desvío visual
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        desvio_vol = v["desvio_volumen_pct"]
                        color_vol = "normal" if desvio_vol <= 10 else ("off" if desvio_vol <= 20 else "inverse")
                        st.metric("Desvío Volumen", f"{desvio_vol:.1f}%",
                                  delta=f"{'⚠️' if desvio_vol > 10 else '✅'} Umbral: 10%/20%",
                                  delta_color=color_vol)
                        st.progress(min(desvio_vol / 25, 1.0))

                    with col2:
                        desvio_dens = v["desvio_densidad_pct"]
                        color_dens = "normal" if desvio_dens <= 5 else ("off" if desvio_dens <= 8 else "inverse")
                        st.metric("Desvío Densidad", f"{desvio_dens:.1f}%",
                                  delta=f"{'⚠️' if desvio_dens > 5 else '✅'} Umbral: 5%/8%",
                                  delta_color=color_dens)
                        st.progress(min(desvio_dens / 12, 1.0))

                    with col3:
                        pres_icon = "🔴 EXCEDIDA" if v["exceso_presion"] == "SI" else "🟢 OK"
                        st.metric("Presión vs Máx.", pres_icon)
                        if dato and diseno:
                            st.caption(f"Real: {dato['presion_maxima_registrada_psi']} psi / Máx: {diseno['presion_maxima_permitida_psi']} psi")

                    if dato and diseno:
                        st.divider()
                        dc1, dc2 = st.columns(2)
                        with dc1:
                            st.markdown("**Diseño Aprobado**")
                            st.caption(f"Vol: {diseno['volumen_teorico_m3']} m³ | Dens: {diseno['densidad_objetivo_ppg']} ppg | P.Máx: {diseno['presion_maxima_permitida_psi']} psi")
                        with dc2:
                            st.markdown("**Datos Reales**")
                            st.caption(f"Vol: {dato['volumen_real_m3']} m³ | Dens: {dato['densidad_real_ppg']} ppg | P.Máx: {dato['presion_maxima_registrada_psi']} psi")
                            st.caption(f"Proveedor: {dato['proveedor_servicio']} | Fecha: {dato['fecha_ejecucion']}")

                    # Override
                    if v.get("override_aplicado") == "S":
                        st.warning(f"⚠️ Override por **{v.get('usuario_override')}** — {v.get('motivo_override')} (vence: {v.get('vencimiento_override')})")

                    elif resultado == "CRITICO" and user_role == "Gerente":
                        st.markdown("---")
                        st.markdown("**Aplicar Override (Supervisor)**")
                        motivo = st.text_area("Motivo obligatorio", key=f"ov_mot_{v['validacion_cementacion_id']}")
                        venc = st.date_input("Vencimiento", value=date.today(), key=f"ov_venc_{v['validacion_cementacion_id']}")
                        if st.button("✅ Aplicar Override", key=f"ov_btn_{v['validacion_cementacion_id']}"):
                            ok, msg = cem.apply_override(v["validacion_cementacion_id"], motivo, str(venc), user_id, user_role)
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

    # ═══════════════════════════════════════════════════════════
    # TAB 4: DASHBOARD
    # ═══════════════════════════════════════════════════════════
    with tab4:
        st.subheader("Dashboard de Cementación")
        stats = cem.get_dashboard_stats()

        if stats["total"] == 0:
            st.info("No hay validaciones registradas para mostrar estadísticas.")
        else:
            # KPIs
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Total Validaciones", stats["total"])
            k2.metric("🟢 OK", f"{stats['ok']} ({stats['pct_ok']}%)")
            k3.metric("🟡 Alerta", f"{stats['alerta']} ({stats['pct_alerta']}%)")
            k4.metric("🔴 Crítico", f"{stats['critico']} ({stats['pct_critico']}%)")

            st.divider()

            # Tabla resumen por pozo
            st.markdown("**Estado por Pozo**")
            pozo_ids = cem.get_all_pozo_ids()
            resumen_rows = []
            for pid in sorted(pozo_ids):
                estado = cem.get_estado_cementacion_pozo(pid)
                resumen_rows.append({
                    "Pozo": pid,
                    "Estado": estado["resumen"],
                    "Puede Avanzar": "✅" if estado["puede_avanzar"] else "🚫",
                })
            st.dataframe(pd.DataFrame(resumen_rows), use_container_width=True, hide_index=True)

            st.divider()

            # Historial de eventos
            st.markdown("**Historial de Eventos**")
            eventos = cem.get_eventos()
            if eventos:
                ev_rows = []
                for e in eventos[:20]:
                    tipo_icon = {
                        "DISENO_APROBADO": "📐",
                        "DATOS_CARGADOS": "📊",
                        "VALIDACION_OK": "🟢",
                        "VALIDACION_ALERTA": "🟡",
                        "VALIDACION_CRITICA": "🔴",
                        "OVERRIDE_MANUAL": "⚠️",
                    }.get(e["tipo_evento"], "📋")
                    ev_rows.append({
                        "Fecha": e["fecha_evento"][:19] if isinstance(e["fecha_evento"], str) else str(e["fecha_evento"]),
                        "Tipo": f"{tipo_icon} {e['tipo_evento']}",
                        "Pozo": e["id_pozo"],
                        "Detalle": e["detalle_evento"][:120],
                        "Usuario": e["usuario_evento"],
                    })
                st.dataframe(pd.DataFrame(ev_rows), use_container_width=True, hide_index=True)
