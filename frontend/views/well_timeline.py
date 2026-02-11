import streamlit as st
import pandas as pd
import json
from services.audit_service import AuditService

def render_timeline(project_id):
    """
    Renderiza la línea de tiempo de auditoría para un pozo.
    Visualización inmutable y certificable.
    """
    audit = st.session_state.get('audit_service')
    if not audit:
        audit = AuditService()
        st.session_state['audit_service'] = audit

    st.markdown("### 📜 Línea de Tiempo Regulatoria (Truth Log)")
    st.caption("Registro inmutable de eventos encadenados por Hash SHA256.")

    events = audit.get_events_for_well(project_id)

    if not events:
        st.info("No hay eventos registrados para este pozo.")
        return

    # Botón para Verificar Integridad
    if st.button("🔍 Verificar Integridad de Cadena", key="verify_audit"):
        is_ok, errors = audit.verify_integrity()
        if is_ok:
            st.success("✅ Integridad de Auditoría Verificada: La cadena es válida y no ha sido alterada.")
        else:
            st.error(f"🚨 ALERTA DE INTEGRIDAD: Se detectaron {len(errors)} inconsistencias.")
            for err in errors:
                st.write(f"- {err}")

    st.markdown("---")

    for event in events:
        with st.container(border=True):
            col1, col2 = st.columns([1, 4])
            
            # Icono según tipo de evento
            icon = "📝"
            if "LOGIN" in event['tipo_evento']: icon = "🔐"
            if "SIGNAL" in event['tipo_evento']: icon = "📡"
            if "OVERRIDE" in event['tipo_evento']: icon = "⚠️"
            if "EVIDENCE" in event['tipo_evento']: icon = "📁"
            if "DATA" in event['tipo_evento']: icon = "💾"

            col1.markdown(f"#### {icon}")
            
            # Header del Evento
            ts = event['timestamp_utc'].strftime("%Y-%m-%d %H:%M:%S")
            col2.markdown(f"**{event['tipo_evento']}** | `{ts}`")
            col2.caption(f"Usuario: {event['id_usuario']} ({event['rol_usuario']})")

            # Expander para detalles técnicos (Hashes y JSON)
            with col2.expander("Ver Detalles Técnicos (Hash & Payload)"):
                st.code(f"ID: {event['id']}\nHash: {event['hash_evento']}\nPrev: {event['hash_previo']}", language="markdown")
                
                c_json1, c_json2 = st.columns(2)
                if event['estado_anterior']:
                    c_json1.markdown("**Estado Anterior:**")
                    c_json1.json(json.loads(event['estado_anterior']))
                
                if event['estado_nuevo']:
                    c_json2.markdown("**Estado Nuevo:**")
                    c_json2.json(json.loads(event['estado_nuevo']))
                
                if event['metadata']:
                    st.markdown("**Metadata:**")
                    st.json(json.loads(event['metadata']))

    st.markdown("---")
    st.caption("v0.1.0 | Blockchain-Light Audit Trail enabled")
