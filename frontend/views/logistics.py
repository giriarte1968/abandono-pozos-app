import streamlit as st
import pandas as pd

def render_view():
    st.title("🚚 Centro de Control Logístico")
    st.caption("Visión global de transportes, movilizaciones e inventario de campo.")

    api = st.session_state.get('api_client')
    
    # 1. KPIs Rápidos
    col1, col2, col3 = st.columns(3)
    logistics = api.get_all_logistics()
    supplies = api.get_all_supplies_status()

    def get_status_label(status):
        labels = {
            "PROGRAMADO": "🗓️ Programado",
            "CARGANDO_RECURSOS": "👷 Cargando Recursos",
            "DEMORADO_CHECKPOINT": "🛑 Demorado Checkpoint",
            "EN RUTA": "🚚 En Ruta",
            "ARRIBO": "✅ Arribo",
            "NO ARRIBO": "❌ No Arribo"
        }
        return labels.get(status, status)
    
    if logistics:
        df_log_raw = pd.DataFrame(logistics)
        df_log_raw['Estado'] = df_log_raw['status'].apply(get_status_label)
    
    col1.metric("Transportes Activos", len([t for t in logistics if t['status'] != 'ARRIBO']))
    col2.metric("En Camino", len([t for t in logistics if t['status'] == 'EN RUTA']))
    col3.metric("Alertas Stock Bajo", len([s for s in supplies if s['current'] < s['min']]))

    st.divider()

    tab1, tab2, tab3 = st.tabs(["🚛 Seguimiento de Flota", "📦 Balance de Insumos", "📡 Recepción de Emergencia"])

    with tab1:
        # ... (contenido existente de tab1) ...
        st.subheader("Estado de Movilizaciones (Diario)")
        if not logistics:
            st.info("No hay movimientos logísticos registrados para hoy.")
        else:
            # Formatear datos para incluir GPS
            df_log_raw['📍 GPS'] = df_log_raw.apply(lambda x: f"📡 {x['dist_to_well']:.1f} km (ETA: {x['eta_minutes']} min)" if x.get('gps_active') and x['status'] == 'EN RUTA' else "---", axis=1)
            
            st.dataframe(
                df_log_raw[['project_id', 'type', 'driver', 'Estado', 'time_plan', '📍 GPS']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "project_id": "Proyecto",
                    "type": "Vehículo",
                    "driver": "Asignado/Chofer",
                    "Estado": "Situación",
                    "time_plan": "Hora Plan",
                    "📍 GPS": st.column_config.TextColumn("Telemetría / ETA", help="Información de telemetría automática")
                }
            )

    with tab2:
        # ... (contenido existente de tab2) ...
        st.subheader("Inventario Consolidado por Proyecto")
        if not supplies:
            st.info("No hay datos de stock para los proyectos actuales.")
        else:
            df_sup = pd.DataFrame(supplies)
            
            # Formatear para visualización
            df_sup['Estado'] = df_sup.apply(lambda x: "🚨 CRÍTICO" if x['current'] < x['min'] else "✅ OK", axis=1)
            
            st.dataframe(
                df_sup[['project_id', 'item', 'current', 'unit', 'min', 'Estado']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "project_id": "Proyecto",
                    "item": "Insumo",
                    "current": "Stock Actual",
                    "unit": "Unidad",
                    "min": "Mínimo",
                    "Estado": st.column_config.TextColumn("Alerta")
                }
            )

    with tab3:
        st.subheader("Inbox de Mensajería de Emergencia (SMS/SAT)")
        st.caption("Central de decodificación de mensajes de bajo ancho de banda.")
        
        emergency_msgs = api.get_emergency_inbox()
        if not emergency_msgs:
            st.info("No se han recibido transmisiones de emergencia en las últimas 24 horas.")
        else:
            # Preparar DF para visualización
            display_data = []
            for m in emergency_msgs:
                data = m['decoded_data']
                display_data.append({
                    "Timestamp": m['ts'],
                    "Canal": m['channel'],
                    "Pozo": m['project_id'],
                    "Código Recibido": m['raw_code'],
                    "Contenido Decodificado": f"Operación: {data.get('op')} | {data.get('desc')[:30]}..."
                })
            
            st.table(display_data)
            st.success(f"Se han procesado {len(emergency_msgs)} señales de emergencia automáticamente.")

    st.info("💡 Consejo: Haz clic en el nombre de un proyecto en 'Proyectos' para ver el detalle técnico específico.")
