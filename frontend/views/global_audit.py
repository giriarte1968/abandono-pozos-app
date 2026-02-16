import streamlit as st
import pandas as pd
import json
from services.audit_service import AuditService

def show_event_details(ev):
    """Muestra los detalles de un evento de auditoría con formato mejorado"""
    with st.container(border=True):
        st.success("Registro Certificado e Inmutable por Blockchain")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### {ev['tipo_evento']}")
        with col2:
            st.caption(f"ID: #{ev['id']}")
            st.caption(f"Fecha: {ev['timestamp_utc'].strftime('%d/%m/%Y %H:%M:%S')}")
        
        st.markdown(f"**Usuario:** {ev.get('id_usuario', 'Sistema')}")
        if ev.get('entidad') and ev.get('entidad'):
            st.markdown(f"**Entidad Afectada:** {ev['entidad']} {ev.get('entidad_id', '')}")
        
        # Mostrar evidencia si es upload
        if ev['tipo_evento'] == "EVIDENCE_UPLOAD":
            st.markdown("---")
            st.markdown("##### Evidencia Certificada")
            try:
                import os
                state = json.loads(ev['estado_nuevo']) if isinstance(ev['estado_nuevo'], str) else ev['estado_nuevo']
                file_name = state.get('file_name') or state.get('file')
                if file_name:
                    local_path = os.path.join(os.getcwd(), "storage", "evidence", file_name)
                    if os.path.exists(local_path):
                        st.image(local_path, caption=f"Evidencia: {file_name}")
                    else:
                        st.info(f"Archivo registrado: {file_name}")
            except Exception as ex:
                st.error(f"Error al cargar evidencia: {str(ex)}")
        
        # Mostrar comparación de estados si hay cambios
        if ev.get('estado_anterior') or ev.get('estado_nuevo'):
            st.markdown("---")
            st.markdown("##### Comparación de Estados")
            
            try:
                anterior = json.loads(ev['estado_anterior']) if isinstance(ev['estado_anterior'], str) and ev['estado_anterior'] else ev.get('estado_anterior', {})
                nuevo = json.loads(ev['estado_nuevo']) if isinstance(ev['estado_nuevo'], str) and ev['estado_nuevo'] else ev.get('estado_nuevo', {})
                
                if anterior and nuevo:
                    # Crear tabla comparativa
                    st.markdown("<table style='width:100%; border-collapse: collapse;'>", unsafe_allow_html=True)
                    st.markdown("<tr style='background-color: #1e1e1e;'>"
                              "<th style='padding: 10px; border: 1px solid #333;'>Campo</th>"
                              "<th style='padding: 10px; border: 1px solid #333;'>Estado Anterior</th>"
                              "<th style='padding: 10px; border: 1px solid #333;'>Estado Nuevo</th>"
                              "</tr>", unsafe_allow_html=True)
                    
                    # Mostrar campos que cambiaron
                    all_keys = set(anterior.keys()) | set(nuevo.keys())
                    for key in all_keys:
                        val_ant = anterior.get(key, '-')
                        val_nue = nuevo.get(key, '-')
                        
                        # Determinar si cambió
                        if val_ant != val_nue:
                            row_style = "background-color: #1e3a5f;"
                        else:
                            row_style = ""
                        
                        st.markdown(f"<tr style='{row_style}'>"
                                  f"<td style='padding: 8px; border: 1px solid #333;'><strong>{key}</strong></td>"
                                  f"<td style='padding: 8px; border: 1px solid #333;'>{val_ant}</td>"
                                  f"<td style='padding: 8px; border: 1px solid #333; color: #22c55e;'>{val_nue}</td>"
                                  f"</tr>", unsafe_allow_html=True)
                    
                    st.markdown("</table>", unsafe_allow_html=True)
                else:
                    # Mostrar como JSON si no es comparación
                    c1, c2 = st.columns(2)
                    if anterior:
                        c1.markdown("**Estado Anterior:**")
                        c1.json(anterior)
                    if nuevo:
                        c2.markdown("**Estado Nuevo:**")
                        c2.json(nuevo)
                        
            except Exception as e:
                st.error(f"Error al mostrar comparación: {e}")
                # Fallback a visualización simple
                c1, c2 = st.columns(2)
                if ev.get('estado_anterior'):
                    c1.markdown("**Estado Anterior:**")
                    c1.write(ev['estado_anterior'])
                if ev.get('estado_nuevo'):
                    c2.markdown("**Estado Nuevo:**")
                    c2.write(ev['estado_nuevo'])
        
        # Metadatos adicionales
        if ev.get('metadata'):
            st.markdown("---")
            st.markdown("##### Metadatos Adicionales")
            try:
                metadata = json.loads(ev['metadata']) if isinstance(ev['metadata'], str) else ev['metadata']
                st.json(metadata)
            except:
                st.write(ev['metadata'])
        
        # Botón para cerrar
        if st.button("Cerrar Detalle", key="btn_close_detail"):
            del st.session_state['selected_audit_event']
            st.rerun()

def render_view():
    """
    Vista global de auditoría para todos los pozos y acciones del sistema.
    """
    st.title("Centro de Auditoria Regulatoria")
    st.markdown("Vision holistica e inmutable de todas las operaciones del sistema.")

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
        col1.success("INTEGRIDAD GLOBAL OK")
    else:
        col1.error(f"INTEGRIDAD COMPROMETIDA ({len(errors)})")

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

    # Ordenar eventos por fecha (más reciente primero)
    filtered_events = sorted(filtered_events, key=lambda x: x['timestamp_utc'], reverse=True)

    # Visualización en Timeline
    st.subheader("Timeline de Eventos")
    st.caption("Visualizacion cronologica de operaciones con trazabilidad completa")

    for idx, ev in enumerate(filtered_events[:20]):  # Mostrar últimos 20 eventos
        timestamp = ev['timestamp_utc'].strftime("%d/%m/%Y %H:%M:%S")
        usuario = ev.get('id_usuario', 'Sistema')
        tipo = ev['tipo_evento']
        entidad = ev.get('entidad', '-')
        entidad_id = ev.get('entidad_id', '-')
        
        # Determinar color e icono según tipo de evento
        if tipo == 'LOGIN_SUCCESS':
            icono = '🔵'
            bg_color = '#1e3a5f'
            border_color = '#3b82f6'
        elif tipo == 'DATA_CHANGE':
            icono = '🟢'
            bg_color = '#14532d'
            border_color = '#22c55e'
        elif tipo == 'EVIDENCE_UPLOAD':
            icono = '🟡'
            bg_color = '#713f12'
            border_color = '#eab308'
        elif tipo == 'OPERATIONAL_OVERRIDE':
            icono = '🟠'
            bg_color = '#7c2d12'
            border_color = '#f97316'
        else:
            icono = '⚪'
            bg_color = '#374151'
            border_color = '#6b7280'
        
        with st.container():
            col1, col2, col3 = st.columns([1, 4, 2])
            
            with col1:
                st.markdown(f"**{timestamp}**")
                st.caption(f"ID: #{ev['id']}")
            
            with col2:
                st.markdown(
                    f"<div style='background-color: {bg_color}; border-left: 4px solid {border_color}; "
                    f"padding: 10px; border-radius: 5px; margin: 5px 0;'>"
                    f"{icono} <strong>{tipo}</strong> | Usuario: {usuario}"
                    f"</div>",
                    unsafe_allow_html=True
                )
                
                # Mostrar entidad afectada si aplica
                if entidad != '-':
                    st.caption(f"Entidad: {entidad} {entidad_id if entidad_id != '-' else ''}")
            
            with col3:
                # Botón para ver detalles
                if st.button("Ver Detalle", key=f"btn_detail_{ev['id']}"):
                    st.session_state['selected_audit_event'] = ev
                    st.rerun()
        
        st.divider()

    # Si hay un evento seleccionado, mostrar detalle
    if 'selected_audit_event' in st.session_state:
        ev = st.session_state['selected_audit_event']
        show_event_details(ev)

    st.markdown("---")
    st.caption("AbandonPro v2.1.0 - Modulo de Auditoria Certificada")
