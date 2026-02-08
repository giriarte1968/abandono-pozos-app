import streamlit as st
import pandas as pd

def render_view():
    st.title("Listado de Proyectos de Abandono")
    
    api = st.session_state['api_client']
    
    # Filtros
    col1, col2 = st.columns([1, 3])
    with col1:
        filter_state = st.selectbox(
            "Filtrar por Estado:",
            ["Todos", "PLANIFICADO", "EN_EJECUCION", "BLOQUEADO", "FINALIZADO"]
        )
    
    # Obtener datos
    projects = api.get_projects(filter_state)
    df_projects = pd.DataFrame(projects)
    
    if df_projects.empty:
        st.warning("No se encontraron proyectos con los filtros seleccionados.")
        return

    # Formateo para la tabla
    display_cols = ["id", "nombre", "yacimiento", "estado_proyecto", "proximo_hito", "responsable", "progreso"]
    
    # Renderizar tabla interactiva
    st.dataframe(
        df_projects[display_cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "progreso": st.column_config.ProgressColumn(
                "Avance %",
                format="%d%%",
                min_value=0,
                max_value=100,
            ),
            "estado_proyecto": st.column_config.TextColumn(
                "Estado",
                help="Estado macro del proyecto",
                validate="^[a-zA-Z0-9_]+$"
            )
        }
    )
    
    # Selector de Acción
    st.divider()
    col_act1, col_act2 = st.columns([3, 1])
    with col_act1:
        st.caption("Seleccione el ID del proyecto para ver detalle y ejecutar acciones.")
        selected_id = st.selectbox("Seleccionar Proyecto:", df_projects['id'].tolist())
    
    with col_act2:
        st.write("") # Spacer
        st.write("")
        if st.button("Ver Detalle / Operar", type="primary"):
            st.session_state['selected_project_id'] = selected_id
            st.session_state['current_page'] = 'Detalle Proyecto'
            st.rerun()
