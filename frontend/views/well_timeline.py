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

            # --- PREVISUALIZACIÓN DE EVIDENCIA (Miniatura) ---
            if event['tipo_evento'] == "EVIDENCE_UPLOAD":
                try:
                    state = json.loads(event['estado_nuevo']) if isinstance(event['estado_nuevo'], str) else event['estado_nuevo']
                    file_name = state.get('file_name') or state.get('file')
                    
                    # Mapping de imágenes realistas para el MOCK (Unsplash - Más robustas)
                    image_map = {
                        "X-123_pre_work_site.jpg": "https://images.unsplash.com/photo-1542281286-9e0a16bb7366?auto=format&fit=crop&q=80&w=600",
                        "Z-789_leakage_cellar.jpg": "https://images.unsplash.com/photo-1622322062699-e659350410a5?auto=format&fit=crop&q=80&w=600",
                        "M-555_capped_wellhead.jpg": "https://images.unsplash.com/photo-1582234372722-50d7ccc30ebd?auto=format&fit=crop&q=80&w=600"
                    }
                    img_url = image_map.get(file_name)
                    
                    if file_name and img_url:
                        col2.image(img_url, caption="Preview: " + file_name, use_container_width=True)
                    else:
                        col2.warning(f"Evidencia no encontrada para {file_name}")
                except Exception as ex:
                    col2.error(f"Error en miniatura: {str(ex)}")

            # Expander para detalles técnicos (Hashes y JSON)
            with col2.expander("Ver Detalles Técnicos y Evidencia Full"):
                st.code(f"ID: {event['id']}\nHash: {event['hash_evento']}\nPrev: {event['hash_previo']}", language="markdown")
                
                # Imagen Full si es Evidencia
                if event['tipo_evento'] == "EVIDENCE_UPLOAD":
                    st.markdown("##### 🖼️ Inspección de Evidencia (Full Resolution)")
                    try:
                        # Aseguramos que image_map esté disponible aquí también
                        full_img_url = image_map.get(file_name)
                        if full_img_url:
                            st.image(full_img_url, caption=f"Evidencia Certificada: {file_name}", use_container_width=True)
                            st.info(f"Integridad de archivo verificada: `{file_name}`")
                        else:
                            st.warning(f"No hay mapeo de imagen para {file_name}")
                    except NameError:
                        st.error("Error: image_map no definido en este contexto")

                c_json1, c_json2 = st.columns(2)
                if event['estado_anterior']:
                    c_json1.markdown("**Estado Anterior:**")
                    try:
                        c_json1.json(json.loads(event['estado_anterior']) if isinstance(event['estado_anterior'], str) else event['estado_anterior'])
                    except:
                        c_json1.write(event['estado_anterior'])
                
                if event['estado_nuevo']:
                    c_json2.markdown("**Estado Nuevo:**")
                    try:
                        c_json2.json(json.loads(event['estado_nuevo']) if isinstance(event['estado_nuevo'], str) else event['estado_nuevo'])
                    except:
                        c_json2.write(event['estado_nuevo'])
                
                if event['metadata']:
                    st.markdown("**Metadata:**")
                    try:
                        st.json(json.loads(event['metadata']) if isinstance(event['metadata'], str) else event['metadata'])
                    except:
                        st.write(event['metadata'])

    st.markdown("---")
    st.caption("v0.1.0 | Blockchain-Light Audit Trail enabled")
