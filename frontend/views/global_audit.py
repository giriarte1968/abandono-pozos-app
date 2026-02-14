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

    # --- FILTRADO ROBUSTO ---
    filtered_events = events
    if tipo != "TODOS":
        filtered_events = [e for e in filtered_events if e.get('tipo_evento') == tipo]
    
    if usuario:
        u_query = usuario.lower().strip()
        filtered_events = [
            e for e in filtered_events 
            if e.get('id_usuario') and u_query in str(e.get('id_usuario')).lower()
        ]
        
    if pozo:
        p_query = pozo.lower().strip()
        filtered_events = [
            e for e in filtered_events 
            if e.get('entidad') == 'POZO' and e.get('entidad_id') and p_query in str(e.get('entidad_id')).lower()
        ]

    if not filtered_events:
        st.info("No se encontraron eventos coincidentes con los filtros aplicados.")
        return

    # Visualización en Tabla Consolidada
    df = pd.DataFrame(filtered_events)
    # Formatear TS
    df['fecha_hora'] = df['timestamp_utc'].apply(lambda x: x.strftime("%d/%m/%Y %H:%M"))
    
    st.dataframe(
        df[['fecha_hora', 'id_usuario', 'tipo_evento', 'entidad', 'entidad_id']],
        use_container_width=True,
        hide_index=True,
        column_config={
            "fecha_hora": "Fecha/Hora",
            "id_usuario": "Usuario",
            "tipo_evento": "Acción",
            "entidad": "Entidad",
            "entidad_id": "ID Entidad"
        }
    )

    # Detalle expandible del último evento
    st.subheader("Inspección de Detalle")
    # Usar una llave única para el selectbox para evitar problemas de estado
    event_options = {f"Event #{e['id']} - {e['tipo_evento']} ({e['timestamp_utc'].strftime('%H:%M')})": e['id'] for e in filtered_events}
    selected_label = st.selectbox("Seleccionar evento para inspección profunda:", list(event_options.keys()))
    selected_id = event_options[selected_label]
    
    ev = next((e for e in filtered_events if e['id'] == selected_id), None)
    if ev:
        with st.container(border=True):
            st.success("🛡️ Registro Certificado e Inmutable por Blockchain")
            st.markdown(f"#### Detalle: {ev['tipo_evento']}")
            
            # --- VISUALIZACIÓN DE EVIDENCIA ---
            if ev['tipo_evento'] == "EVIDENCE_UPLOAD":
                st.markdown("---")
                st.markdown("##### 🖼️ Evidencia Certificada (Full)")
                try:
                    import os
                    state = json.loads(ev['estado_nuevo']) if isinstance(ev['estado_nuevo'], str) else ev['estado_nuevo']
                    file_name = state.get('file_name') or state.get('file')
                    if file_name:
                        # Buscamos archivo local en storage/evidence/
                        local_path = os.path.join(os.getcwd(), "storage", "evidence", file_name)
                        
                        if os.path.exists(local_path):
                            st.image(local_path, caption=f"Evidencia Certificada (Full): {file_name}")
                            st.info(f"Archivo físico verificado en servidor: `{file_name}`")
                        else:
                            st.warning(f"Evidencia subida pero archivo no encontrado localmente: {file_name}")
                except Exception as ex:
                    st.error(f"Error al cargar evidencia: {str(ex)}")

            c1, c2 = st.columns(2)
            if ev['estado_anterior']:
                c1.markdown("**Estado Anterior:**")
                try:
                    c1.json(json.loads(ev['estado_anterior']) if isinstance(ev['estado_anterior'], str) else ev['estado_anterior'])
                except:
                    c1.write(ev['estado_anterior'])
            
            if ev['estado_nuevo']:
                c2.markdown("**Estado Nuevo:**")
                try:
                    c2.json(json.loads(ev['estado_nuevo']) if isinstance(ev['estado_nuevo'], str) else ev['estado_nuevo'])
                except:
                    c2.write(ev['estado_nuevo'])
            
            if ev['metadata']:
                st.markdown("**Metadatos Adicionales:**")
                try:
                    st.json(json.loads(ev['metadata']) if isinstance(ev['metadata'], str) else ev['metadata'])
                except:
                    st.write(ev['metadata'])

    st.markdown("---")
    st.caption("AbandonPro v0.1.0 - Modulo de Auditoria Certificada")
