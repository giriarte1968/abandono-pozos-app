import streamlit as st
import pandas as pd
from datetime import datetime
from services.closure_service import ClosureService
from services.export_service import ExportService
from services.cementation_service import CementationService
from services.audit_service import AuditService


def render_view():
    """Vista de Cierre Técnico + Exportación Regulatoria + Dashboard Ejecutivo."""
    st.title("🏁 Cierre Técnico & Exportación Regulatoria")
    st.caption("Ningún pozo cerrado sin validación técnica + evidencia certificada + calidad aprobada")

    audit = AuditService()
    cem_svc = CementationService(audit_service=audit)

    # Importar ComplianceService si disponible
    comp_svc = None
    try:
        from services.compliance_service import ComplianceService
        comp_svc = ComplianceService(audit_service=audit)
    except Exception:
        pass

    closure_svc = ClosureService(
        audit_service=audit,
        cementation_service=cem_svc,
        compliance_service=comp_svc,
    )
    export_svc = ExportService(
        closure_service=closure_svc,
        cementation_service=cem_svc,
        compliance_service=comp_svc,
    )

    user_role = st.session_state.get("user_role", "")
    user_id = st.session_state.get("username", "unknown")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Cierre Técnico",
        "📑 Dossier Regulatorio",
        "📈 Dashboard Ejecutivo",
        "📜 Trazabilidad",
    ])

    # ═══════════════════════════════════════════════════════════
    # TAB 1: CIERRE TÉCNICO
    # ═══════════════════════════════════════════════════════════
    with tab1:
        st.subheader("Proceso de Cierre Técnico por Pozo")

        # Selector de pozo - usar todos los pozos disponibles (10 pozos)
        api = st.session_state.get('api_client')
        if api:
            all_wells = api.get_all_wells()
            all_pozos = [w['id'] for w in all_wells]
        else:
            # Fallback: usar CementationService o lista completa
            all_pozos = cem_svc.get_all_pozo_ids()
            if not all_pozos:
                all_pozos = ["X-123", "A-321", "Z-789", "M-555", "P-001", "P-002", 
                           "H-101", "H-102", "T-201", "C-301"]
        
        pozo_sel = st.selectbox("Seleccionar Pozo", sorted(all_pozos), key="cierre_pozo")

        cierre = closure_svc.get_cierre(pozo_sel)

        if not cierre:
            st.info(f"No hay proceso de cierre iniciado para **{pozo_sel}**.")
            if user_role == "Gerente":
                if st.button("🚀 Iniciar Proceso de Cierre", type="primary"):
                    ok, msg, _ = closure_svc.iniciar_cierre(pozo_sel, user_id)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            else:
                st.warning("Solo el rol Gerente puede iniciar un proceso de cierre.")
        else:
            # Estado actual
            estado = cierre["estado_cierre"]
            estado_icons = {
                "EN_PROCESO": "🟡", "BLOQUEADO": "🔴",
                "APROBADO": "🟢", "CERRADO_DEFENDIBLE": "🟢",
            }
            st.markdown(f"### {estado_icons.get(estado, '❓')} Estado: **{estado}**")

            col1, col2, col3 = st.columns(3)
            col1.metric("Inicio", cierre["fecha_inicio_cierre"])
            col2.metric("Creado por", cierre["creado_por"])
            col3.metric("Hash Consolidado", cierre.get("hash_consolidado", "—")[:16] + "..." if cierre.get("hash_consolidado") else "Pendiente")

            if cierre.get("dictamen_final"):
                st.info(f"**Dictamen:** {cierre['dictamen_final']}")

            # Checklist
            st.divider()
            st.markdown("#### 📋 Checklist de Cierre Obligatorio")

            # Botón para re-evaluar
            if estado not in ("APROBADO", "CERRADO_DEFENDIBLE"):
                if st.button("🔄 Evaluar Checklist Automáticamente", type="secondary"):
                    checklist, tiene_bloqueo, err = closure_svc.evaluar_checklist(pozo_sel)
                    if err:
                        st.error(err)
                    else:
                        st.success("Checklist evaluado automáticamente" + (" — ⚠️ Hay bloqueos" if tiene_bloqueo else " — ✅ Sin bloqueos"))
                        st.rerun()

            checklist = closure_svc.get_checklist(cierre["cierre_tecnico_pozo_id"])
            for ch in checklist:
                estado_ch = ch["estado_item"]
                icon = {"OK": "✅", "PENDIENTE": "⏳", "RECHAZADO": "❌", "NO_APLICA": "➖"}[estado_ch]
                with st.expander(f"{icon} {ch['item_control']} — {estado_ch}"):
                    if ch.get("observacion"):
                        st.caption(ch["observacion"])
                    if ch.get("validado_por"):
                        st.caption(f"Validado por: {ch['validado_por']} | {ch.get('fecha_validacion', '')[:19]}")

                    # Manual override para "Acta firmada digitalmente"
                    if ch["item_control"] == "Acta firmada digitalmente" and estado_ch == "PENDIENTE":
                        if user_role == "Gerente":
                            if st.button(f"✅ Marcar como firmada", key=f"firma_{ch['checklist_cierre_id']}"):
                                ch["estado_item"] = "OK"
                                ch["observacion"] = f"Acta firmada digitalmente por {user_id}"
                                ch["validado_por"] = user_id
                                ch["fecha_validacion"] = datetime.now().isoformat()
                                closure_svc._save_mock_data()
                                st.success("Acta marcada como firmada")
                                st.rerun()

            # Aprobar cierre
            items_ok = all(ch["estado_item"] == "OK" for ch in checklist)
            if items_ok and estado not in ("APROBADO", "CERRADO_DEFENDIBLE") and user_role == "Gerente":
                st.divider()
                st.markdown("#### ✅ Aprobar Cierre Técnico Final")
                dictamen = st.text_area("Dictamen Final *", placeholder="Ej: Pozo abandonado conforme normativa SEC. Sin observaciones técnicas pendientes.")
                if st.button("🏁 Aprobar y Cerrar como DEFENDIBLE", type="primary"):
                    if not dictamen.strip():
                        st.error("El dictamen final es obligatorio")
                    else:
                        ok, msg = closure_svc.aprobar_cierre(pozo_sel, user_id, dictamen)
                        if ok:
                            st.success(msg)
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(msg)

            if estado == "CERRADO_DEFENDIBLE":
                st.success(f"🏁 **POZO CERRADO DEFENDIBLE** — Aprobado por {cierre['aprobado_por']} el {cierre['fecha_aprobacion']}")

        # Evidencia del pozo
        st.divider()
        st.markdown("#### 📎 Evidencia Certificada del Pozo")
        docs = closure_svc.get_documentos(pozo_sel)
        if docs:
            rows = []
            for d in docs:
                cert = closure_svc.get_certificacion(d["documento_evidencia_id"])
                rows.append({
                    "Tipo": d["tipo_documento"],
                    "Archivo": d["nombre_archivo"],
                    "Hash": d["hash_sha256"][:16] + "...",
                    "Certificado": f"✅ {cert['estado']}" if cert else "❌ Sin certificar",
                    "Cargado": d["cargado_en"][:10] if isinstance(d["cargado_en"], str) else str(d["cargado_en"]),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.warning("Sin documentos de evidencia para este pozo.")

    # ═══════════════════════════════════════════════════════════
    # TAB 2: DOSSIER REGULATORIO
    # ═══════════════════════════════════════════════════════════
    with tab2:
        st.subheader("Generación de Dossier Regulatorio")

        pozo_export = st.selectbox("Pozo", sorted(all_pozos), key="export_pozo")
        tipo_reg = st.selectbox("Regulador Destino", [
            "SEC_ARGENTINA", "IOGP_INTERNACIONAL", "EPA_ESTADOS_UNIDOS",
        ])

        col_e1, col_e2 = st.columns(2)

        with col_e1:
            st.markdown("**📄 Exportar JSON Técnico**")
            if st.button("Generar JSON", key="gen_json"):
                content, filename, hash_exp = export_svc.generar_dossier_json(pozo_export, tipo_reg)
                st.success(f"✅ {filename} generado")
                st.caption(f"Hash: `{hash_exp[:24]}...`")
                st.download_button(
                    "⬇️ Descargar JSON", content,
                    file_name=filename, mime="application/json",
                )

        with col_e2:
            st.markdown("**📄 Exportar XML Estructurado**")
            if st.button("Generar XML", key="gen_xml"):
                content, filename, hash_exp = export_svc.generar_dossier_xml(pozo_export, tipo_reg)
                st.success(f"✅ {filename} generado")
                st.caption(f"Hash: `{hash_exp[:24]}...`")
                st.download_button(
                    "⬇️ Descargar XML", content,
                    file_name=filename, mime="application/xml",
                )

        # Exportaciones anteriores
        st.divider()
        st.markdown("**📂 Historial de Exportaciones**")
        exports = closure_svc.get_exportaciones(pozo_export)
        if exports:
            exp_rows = []
            for e in exports:
                exp_rows.append({
                    "Formato": e["formato_generado"],
                    "Regulador": e["tipo_regulador"],
                    "Hash": e["hash_exportacion"][:16] + "...",
                    "Fecha (UTC)": e["fecha_generacion"][:19],
                    "Sistema": e["generado_por_sistema"],
                })
            st.dataframe(pd.DataFrame(exp_rows), use_container_width=True, hide_index=True)
        else:
            st.info("No hay exportaciones anteriores para este pozo.")

        # Vista previa XML
        with st.expander("👀 Vista previa XML"):
            preview, _, _ = export_svc.generar_dossier_xml(pozo_export, tipo_reg)
            st.code(preview, language="xml")

    # ═══════════════════════════════════════════════════════════
    # TAB 3: DASHBOARD EJECUTIVO
    # ═══════════════════════════════════════════════════════════
    with tab3:
        st.subheader("Dashboard Ejecutivo de Cierre")
        stats = closure_svc.get_dashboard_stats()

        # KPIs principales
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Pozos en Cierre", stats["total"])
        k2.metric("🟢 Listos para Regulador", f"{stats['listos']} ({stats['pct_listos']}%)")
        k3.metric("🔴 Con Bloqueo", f"{stats['bloqueados']} ({stats['pct_bloqueados']}%)")
        k4.metric("📎 Evidencia Incompleta", stats["evidencia_incompleta"])

        st.divider()

        c1, c2 = st.columns(2)
        with c1:
            st.metric("⏱️ Tiempo Promedio de Cierre", f"{stats['tiempo_promedio_dias']} días")
        with c2:
            st.metric("🔄 En Proceso", stats["en_proceso"])

        st.divider()

        # Estado por pozo
        st.markdown("**Estado por Pozo**")
        pozo_rows = []
        for pid in sorted(all_pozos):
            estado_cierre = closure_svc.get_estado_cierre_pozo(pid)
            cem_estado = cem_svc.get_estado_cementacion_pozo(pid)
            pozo_rows.append({
                "Pozo": pid,
                "Cierre": estado_cierre["resumen"],
                "Cementación": cem_estado["resumen"],
                "Regulador-Ready": "✅" if estado_cierre["estado"] == "CERRADO_DEFENDIBLE" else "🚫",
            })
        st.dataframe(pd.DataFrame(pozo_rows), use_container_width=True, hide_index=True)

    # ═══════════════════════════════════════════════════════════
    # TAB 4: TRAZABILIDAD
    # ═══════════════════════════════════════════════════════════
    with tab4:
        st.subheader("Trazabilidad Completa del Expediente")

        pozo_traza = st.selectbox("Pozo", sorted(all_pozos), key="traza_pozo")

        # Timeline integrada
        st.markdown("#### 📋 Evidencia Certificada")
        docs = closure_svc.get_documentos(pozo_traza)
        for d in docs:
            cert = closure_svc.get_certificacion(d["documento_evidencia_id"])
            cert_status = f"✅ Certificado ({cert['sello_tiempo_utc'][:19]})" if cert else "❌ Sin certificar"
            st.markdown(
                f"- **{d['tipo_documento']}** — `{d['nombre_archivo']}` | "
                f"Hash: `{d['hash_sha256'][:12]}...` | {cert_status}"
            )

        st.divider()

        # Eventos de cementación
        st.markdown("#### 🧪 Eventos de Cementación")
        eventos_cem = cem_svc.get_eventos(pozo_traza)
        if eventos_cem:
            for e in eventos_cem[:10]:
                tipo_icon = {
                    "DISENO_APROBADO": "📐", "DATOS_CARGADOS": "📊",
                    "VALIDACION_OK": "🟢", "VALIDACION_ALERTA": "🟡",
                    "VALIDACION_CRITICA": "🔴", "OVERRIDE_MANUAL": "⚠️",
                }.get(e["tipo_evento"], "📋")
                st.markdown(f"- {tipo_icon} `{e['fecha_evento'][:19]}` — **{e['tipo_evento']}** — {e['detalle_evento'][:100]}")
        else:
            st.info("Sin eventos de cementación")

        st.divider()

        # Hash consolidado
        st.markdown("#### 🔐 Hash Consolidado del Expediente")
        cierre_traza = closure_svc.get_cierre(pozo_traza)
        if cierre_traza and cierre_traza.get("hash_consolidado"):
            st.code(cierre_traza["hash_consolidado"], language="text")
            st.caption("Este hash SHA256 sella la integridad de todo el expediente del pozo.")
        else:
            hash_actual = export_svc.generar_hash_consolidado(pozo_traza)
            st.code(hash_actual, language="text")
            st.caption("Hash actual (no sellado — el cierre no ha sido aprobado aún).")
