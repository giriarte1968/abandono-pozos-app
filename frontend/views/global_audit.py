import streamlit as st
import pandas as pd
import json
from services.audit_service import AuditService

def render_view():
    """
    Vista global de auditoría para todos los pozos y acciones del sistema.
    """
    st.title("🛡️ Centro de Auditoría Regulatoria")
    st.markdown("Visión holística e inmutable de todas las operaciones del sistema.")

    audit = st.session_state.get('audit_service')
    if not audit:
        audit = AuditService()
        st.session_state['audit_service'] = audit

    # Estadísticas Rápidas
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    # Simulación de verificación global
    is_ok, errors = audit.verify_integrity()
    
    if is_ok:
        col1.success("✅ INTEGRIDAD GLOBAL OK")
    else:
        col1.error(f"🚨 INTEGRIDAD COMPROMETIDA ({len(errors)})")

    # Filtros
    st.subheader("Filtrar Eventos")
    f_col1, f_col2, f_col3 = st.columns(3)
    tipo = f_col1.selectbox("Tipo de Evento", ["TODOS", "LOGIN_SUCCESS", "SIGNAL_SENT", "OPERATIONAL_OVERRIDE", "EVIDENCE_UPLOAD", "DATA_CHANGE"])
    usuario = f_col2.text_input("Filtrar por Usuario (ID)")
    pozo = f_col3.text_input("Filtrar por Pozo (ID)")

    # Consulta resiliente (Mock Fallback incluido en el servicio)
    events = audit.get_all_events()

    if tipo != "TODOS":
        events = [e for e in events if e['tipo_evento'] == tipo]
    if usuario:
        events = [e for e in events if usuario.lower() in e['id_usuario'].lower()]
    if pozo:
        events = [e for e in events if e['entidad'] == 'POZO' and pozo.lower() in e['entidad_id'].lower()]

    if not events:
        st.info("No se encontraron eventos coincidentes.")
        return

    # Visualización en Tabla Consolidada
    df = pd.DataFrame(events)
    # Formatear TS
    df['fecha_hora'] = df['timestamp_utc'].apply(lambda x: x.strftime("%d/%m/%Y %H:%M"))
    
    st.dataframe(
        df[['fecha_hora', 'id_usuario', 'tipo_evento', 'entidad', 'entidad_id', 'hash_evento']],
        use_container_width=True,
        hide_index=True,
        column_config={
            "fecha_hora": "Fecha/Hora",
            "id_usuario": "Usuario",
            "tipo_evento": "Acción",
            "entidad": "Entidad",
            "entidad_id": "ID Entidad",
            "hash_evento": "Certificado (Hash)"
        }
    )

    # Detalle expandible del último evento
    st.subheader("Inspección de Detalle")
    selected_event_id = st.selectbox("Seleccionar ID para inspección profunda:", [e['id'] for e in events])
    
    ev = next((e for e in events if e['id'] == selected_event_id), None)
    if ev:
        with st.container(border=True):
            st.markdown(f"#### Evento #{ev['id']} - {ev['tipo_evento']}")
            st.code(f"Hash: {ev['hash_evento']}\nHash Previo: {ev['hash_previo']}", language="markdown")
            
            c1, c2 = st.columns(2)
            if ev['estado_anterior']:
                c1.markdown("**Estado Anterior:**")
                c1.json(json.loads(ev['estado_anterior']))
            if ev['estado_nuevo']:
                c2.markdown("**Estado Nuevo:**")
                c2.json(json.loads(ev['estado_nuevo']))
            
            if ev['metadata']:
                st.markdown("**Metadatos Adicionales:**")
                st.json(json.loads(ev['metadata']))

    st.markdown("---")
    st.caption("AbandonPro v0.1.0 - Modulo de Auditoria Certificada")
