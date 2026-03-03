import streamlit as st
import pandas as pd
from datetime import datetime, date
from services.recurso_estado_service import recurso_estado_service
from services.mock_api_client import MockApiClient

def render_view():
    st.title("📊 Estado Operativo de Recursos")
    st.caption("Seguimiento diario del estado de Personal y Equipos (Sin modificar su configuración en el Catálogo Maestro).")

    # Filtros Globales
    st.subheader("Filtros de Búsqueda")
    col_fil1, col_fil2 = st.columns(2)
    with col_fil1:
        fecha_filtro = st.date_input("Fecha de Operación", value=date.today())
    with col_fil2:
        tipo_filtro = st.selectbox("Tipo de Recurso", ["TODOS", "PERSONAL", "EQUIPO"])

    st.divider()

    # Obtener datos de estados
    estados = recurso_estado_service.get_estados(fecha=fecha_filtro, tipo_recurso=tipo_filtro)
    resumen = recurso_estado_service.get_resumen_indicadores(fecha=fecha_filtro)

    # Indicadores Resumen
    st.subheader("📈 Resumen del Día")
    
    col_r1, col_r2 = st.columns(2)
    
    with col_r1:
        st.markdown("**Personal**")
        c1, c2, c3 = st.columns(3)
        c1.metric("Activos / Asignados", resumen['PERSONAL'].get('ACTIVO', 0) + resumen['PERSONAL'].get('ASIGNADO', 0))
        c2.metric("Standby", resumen['PERSONAL']['STANDBY'])
        c3.metric("Licencia / Franco", resumen['PERSONAL'].get('LICENCIA', 0) + resumen['PERSONAL'].get('FRANCO', 0))
        
    with col_r2:
        st.markdown("**Equipos**")
        c4, c5, c6 = st.columns(3)
        c4.metric("Activos / Asignados", resumen['EQUIPO'].get('ACTIVO', 0) + resumen['EQUIPO'].get('ASIGNADO', 0))
        c5.metric("Standby", resumen['EQUIPO']['STANDBY'])
        c6.metric("En Mantenimiento", resumen['EQUIPO']['MANTENIMIENTO'])

    st.divider()

    # Tabla de Resultados
    st.subheader("📝 Listado de Estados")
    
    if estados:
        df_estados = pd.DataFrame(estados)
        
        # Para hacer la tabla más amigable, traemos los nombres del catálogo a través de un diccionario
        api = st.session_state.get('api_client', MockApiClient())
        
        # Diccionarios de resolución
        personas_dict = {p['id'] if 'id' in p else p['name']: p['name'] for p in api.get_master_personnel()}
        equipos_dict = {e['id'] if 'id' in e else e['name']: e['name'] for e in api.get_master_equipment()}
        
        def resolve_name(row):
            if row['tipo_recurso'] == 'PERSONAL':
                return personas_dict.get(row['id_recurso'], row['id_recurso'])
            return equipos_dict.get(row['id_recurso'], row['id_recurso'])
            
        df_estados['nombre_recurso'] = df_estados.apply(resolve_name, axis=1)
        
        # Reordenar y formatear columnas
        cols_display = ['fecha', 'tipo_recurso', 'nombre_recurso', 'estado_operativo', 'id_pozo', 'observaciones']
        df_display = df_estados[cols_display].copy()
        df_display.rename(columns={
            'fecha': 'Fecha', 
            'tipo_recurso': 'Tipo', 
            'nombre_recurso': 'Recurso',
            'estado_operativo': 'Estado Operativo', 
            'id_pozo': 'Pozo Asignado',
            'observaciones': 'Observaciones'
        }, inplace=True)
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info(f"No hay estados registrados para el {fecha_filtro.strftime('%d/%m/%Y')} con los filtros seleccionados.")

    # Formulario de Alta Rápida
    with st.expander("➕ Cargar / Actualizar Estado"):
        with st.form("form_estado", clear_on_submit=True):
            api = st.session_state.get('api_client', MockApiClient())
            
            c_f1, c_f2 = st.columns(2)
            f_tipo = c_f1.selectbox("Tipo", ["PERSONAL", "EQUIPO"])
            
            # Dinámico según tipo
            if f_tipo == "PERSONAL":
                opciones = [p['name'] for p in api.get_master_personnel()]
                f_recurso = c_f2.selectbox("Recurso", opciones)
                estados_posibles = ['ACTIVO', 'STANDBY', 'LICENCIA', 'FRANCO']
            else:
                opciones = [e['name'] for e in api.get_master_equipment()]
                f_recurso = c_f2.selectbox("Recurso", opciones)
                estados_posibles = ['ACTIVO', 'STANDBY', 'MANTENIMIENTO', 'ASIGNADO']
            
            c_f3, c_f4 = st.columns(2)
            f_estado = c_f3.selectbox("Estado", estados_posibles)
            
            proyectos = api.get_projects()
            opciones_pozo = [""] + [p['id'] for p in proyectos]
            f_pozo = c_f4.selectbox("Pozo Asignado (Opcional)", opciones_pozo)
            
            f_obs = st.text_input("Observaciones")
            
            if st.form_submit_button("Guardar Estado Diaro", type="primary"):
                if not f_recurso:
                    st.error("Debe seleccionar un recurso válido existente en el maestro.")
                else:
                    pozo_val = f_pozo if f_pozo != "" else None
                    res = recurso_estado_service.add_estado(
                        id_recurso=f_recurso,
                        tipo_recurso=f_tipo,
                        fecha=fecha_filtro,
                        estado_operativo=f_estado,
                        id_pozo=pozo_val,
                        observaciones=f_obs
                    )
                    if res['success']:
                        st.success(res['msg'])
                        st.rerun()
                    else:
                        st.error(res['msg'])
