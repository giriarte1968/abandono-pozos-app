import streamlit as st
import pandas as pd
import altair as alt

def render_view():
    api = st.session_state['api_client']
    stats = api.get_dashboard_stats()
    
    st.title("Tablero de Comando - Operaciones P&A")
    st.markdown(f"*Datos al: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}*")

    # 1. KPIs Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Activos", stats['total_activos'])
    with col2:
        st.metric("En Planificación", stats['en_planificacion'])
    with col3:
        st.metric("En Ejecución", stats['en_ejecucion'], delta=2)
    with col4:
        st.metric("Alertas Activas", stats['alertas_activas'], delta_color="inverse", delta=1)

    st.divider()

    # 2. Resumen de Flota (Mock Visual)
    st.subheader("Estado de Flota (Recursos Críticos)")
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        # Gráfico simple de recursos
        usage_data = pd.DataFrame({
            'Equipo': ['Pulling', 'Cementadoras', 'Cisternas', 'Wireline'],
            'Uso': [80, 50, 90, 20]
        })
        
        chart = alt.Chart(usage_data).mark_bar().encode(
            x='Uso:Q',
            y=alt.Y('Equipo:N', sort='-x'),
            color=alt.condition(
                alt.datum.Uso > 75,
                alt.value('orange'),  # The positive color
                alt.value('steelblue')  # The negative color
            )
        ).properties(height=200)
        
        st.altair_chart(chart, use_container_width=True)

    with col_f2:
        st.expander("⚠️ Alertas Operativas Recientes", expanded=True).warning("""
        - **Pozo Z-789**: Bloqueo por Incidencia HSE (Derrame menor).
        - **Pozo A-321**: Demora en entrega de cemento (Logística).
        """)

    st.info("Para ver detalle individual, navegue a 'Proyectos'.")
