import streamlit as st
import pandas as pd
from datetime import date
from services.compliance_service import ComplianceService
from services.audit_service import AuditService


def render_view():
    """Vista principal del Motor de Cumplimiento Regulatorio."""
    st.title("📜 Cumplimiento Regulatorio")
    st.caption("Motor de validación multi-jurisdicción con control de overrides")

    audit = AuditService()
    compliance = ComplianceService(audit_service=audit)
    user_role = st.session_state.get("user_role", "")

    tab1, tab2, tab3 = st.tabs([
        "🚦 Panel de Cumplimiento",
        "📋 Reglas por Jurisdicción",
        "🔍 Detalle por Pozo",
    ])

    # ─── TAB 1: Panel Semáforo ──────────────────────────────────
    with tab1:
        st.subheader("Estado de Cumplimiento por Pozo")
        summaries = compliance.get_all_compliance_summaries()

        if not summaries:
            st.info("No hay pozos con regulación asignada.")
            return

        # KPIs superiores
        total_pozos = len(summaries)
        pozos_ok = len([s for s in summaries if s["puede_avanzar"] and s["no_cumple"] == 0])
        pozos_warn = len([s for s in summaries if s["puede_avanzar"] and s["advertencia"] > 0])
        pozos_block = len([s for s in summaries if not s["puede_avanzar"]])

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Pozos", total_pozos)
        col2.metric("🟢 Cumple", pozos_ok)
        col3.metric("🟡 Advertencia", pozos_warn)
        col4.metric("🔴 Bloqueados", pozos_block)

        st.divider()

        # Tabla semáforo
        rows = []
        for s in summaries:
            jurisdiccion = compliance.get_jurisdiccion_para_pozo(s["pozo_id"])
            jur_nombre = jurisdiccion["nombre"] if jurisdiccion else "Sin asignar"

            if not s["puede_avanzar"]:
                semaforo = "🔴"
            elif s["advertencia"] > 0:
                semaforo = "🟡"
            else:
                semaforo = "🟢"

            rows.append({
                "Estado": semaforo,
                "Pozo": s["pozo_id"],
                "Jurisdicción": jur_nombre,
                "Reglas": s["total_reglas"],
                "Cumple": s["cumple"],
                "Advrt.": s["advertencia"],
                "Falla": s["no_cumple"],
                "Overrides": s["overrides"],
                "Resumen": s["resumen"],
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ─── TAB 2: Reglas por Jurisdicción ─────────────────────────
    with tab2:
        st.subheader("Marco Regulatorio por Jurisdicción")
        jurisdicciones = compliance.get_jurisdicciones()

        if not jurisdicciones:
            st.info("No hay jurisdicciones configuradas.")
            return

        jur_nombres = {j["jurisdiccion_id"]: f"{j['nombre']} ({j['pais']})" for j in jurisdicciones}
        selected_jur_id = st.selectbox(
            "Seleccione Jurisdicción",
            options=list(jur_nombres.keys()),
            format_func=lambda x: jur_nombres[x],
        )

        version = compliance.get_version_vigente(selected_jur_id)
        if not version:
            st.warning("No hay versión vigente para esta jurisdicción.")
            return

        st.success(f"**Versión Vigente:** {version['nombre_version']}  \nDesde: {version['fecha_vigencia_desde']}")

        reglas = compliance.get_reglas_por_version(version["version_regulacion_id"])
        if reglas:
            regla_rows = []
            for r in reglas:
                bloq_icon = "🚫" if r["es_bloqueante"] == "S" else "ℹ️"
                sev_icon = {"ERROR": "🔴", "ADVERTENCIA": "🟡", "INFO": "🔵"}.get(r["severidad"], "⚪")

                rango = ""
                if r.get("valor_minimo") is not None and r.get("valor_maximo") is not None:
                    rango = f"{r['valor_minimo']} - {r['valor_maximo']} {r.get('unidad', '')}"
                elif r.get("valor_minimo") is not None:
                    rango = f"≥ {r['valor_minimo']} {r.get('unidad', '')}"
                elif r.get("valor_maximo") is not None:
                    rango = f"≤ {r['valor_maximo']} {r.get('unidad', '')}"
                else:
                    rango = r["tipo_regla"]

                regla_rows.append({
                    "Sev.": sev_icon,
                    "Bloq.": bloq_icon,
                    "Código": r["codigo_regla"],
                    "Descripción": r["descripcion"],
                    "Tipo": r["tipo_regla"],
                    "Criterio": rango,
                })

            df_reglas = pd.DataFrame(regla_rows)
            st.dataframe(df_reglas, use_container_width=True, hide_index=True)

            st.info(f"🔒 Las reglas de versiones **VIGENTES** son inmutables. Para modificarlas, se debe crear una nueva versión regulatoria.")
        else:
            st.info("No hay reglas definidas para esta versión.")

    # ─── TAB 3: Detalle por Pozo ────────────────────────────────
    with tab3:
        st.subheader("Evaluación Detallada por Pozo")
        summaries = compliance.get_all_compliance_summaries()
        pozo_ids = [s["pozo_id"] for s in summaries]

        if not pozo_ids:
            st.info("No hay pozos con regulación asignada.")
            return

        selected_pozo = st.selectbox("Seleccione Pozo", options=pozo_ids)
        summary = next((s for s in summaries if s["pozo_id"] == selected_pozo), None)

        if not summary:
            return

        # Header con semáforo
        jurisdiccion = compliance.get_jurisdiccion_para_pozo(selected_pozo)
        version = compliance.get_version_asignada_pozo(selected_pozo)

        col_a, col_b = st.columns([2, 1])
        with col_a:
            st.markdown(f"### {summary['resumen']}")
            if jurisdiccion:
                st.caption(f"Jurisdicción: **{jurisdiccion['nombre']}** | Versión: **{version['nombre_version'] if version else 'N/A'}**")

        with col_b:
            st.metric("Reglas Evaluadas", summary["total_reglas"])

        st.divider()

        # Resultados detallados
        for r in summary["resultados"]:
            estado_icon = {"CUMPLE": "🟢", "NO_CUMPLE": "🔴", "ADVERTENCIA": "🟡"}.get(r["estado"], "⚪")
            override_tag = " *(OVERRIDE ACTIVO)*" if r["override_aplicado"] == "S" else ""

            with st.expander(f"{estado_icon} {r['codigo_regla']} — {r['descripcion']}{override_tag}"):
                c1, c2, c3 = st.columns(3)
                c1.metric("Valor Evaluado", f"{r['valor_evaluado']} {r.get('unidad', '')}")

                if r.get("valor_minimo_esperado") is not None:
                    c2.metric("Mínimo", f"{r['valor_minimo_esperado']} {r.get('unidad', '')}")
                if r.get("valor_maximo_esperado") is not None:
                    c3.metric("Máximo", f"{r['valor_maximo_esperado']} {r.get('unidad', '')}")

                st.caption(f"Severidad: **{r['severidad']}** | Bloqueante: **{'Sí' if r['es_bloqueante'] == 'S' else 'No'}**")

                if r["override_aplicado"] == "S":
                    st.warning("⚠️ Override aplicado — el incumplimiento no bloquea el avance.")

                # Permitir override solo a Gerente y si hay incumplimiento sin override
                if (
                    r["estado"] == "NO_CUMPLE"
                    and r["override_aplicado"] == "N"
                    and user_role == "Gerente"
                ):
                    st.markdown("---")
                    st.markdown("**Aplicar Override (Supervisor Regulatorio)**")
                    motivo = st.text_area(
                        "Motivo obligatorio",
                        key=f"motivo_{r['regla_regulatoria_id']}_{selected_pozo}",
                    )
                    vencimiento = st.date_input(
                        "Vencimiento del override",
                        value=date.today(),
                        key=f"venc_{r['regla_regulatoria_id']}_{selected_pozo}",
                    )
                    if st.button(
                        "✅ Aplicar Override",
                        key=f"btn_{r['regla_regulatoria_id']}_{selected_pozo}",
                    ):
                        # Find resultado_cumplimiento_id from mock data
                        data = compliance._load_mock_data()
                        res_id = None
                        for res in data["resultados"]:
                            if (
                                res["pozo_id"] == selected_pozo
                                and res["regla_regulatoria_id"] == r["regla_regulatoria_id"]
                            ):
                                res_id = res["resultado_cumplimiento_id"]
                                break

                        if res_id:
                            ok, msg = compliance.apply_override(
                                resultado_id=res_id,
                                motivo=motivo,
                                vencimiento=str(vencimiento),
                                user_id=st.session_state.get("user_id", "unknown"),
                                user_role=user_role,
                            )
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
