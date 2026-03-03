import streamlit as st
import pandas as pd
from services.capacidad_contrato_service import CapacidadContratoService

def render_view():
    st.title("🛡️ Gestión de Capacidad Operativa")
    st.markdown("""
    Esta vista permite definir y monitorear la **Plantilla de Recursos** asignada a cada contrato. 
    Asegura que tengamos la capacidad humana y técnica requerida para cumplir con los objetivos contractuales.
    """)

    service = CapacidadContratoService()
    contracts = service.get_active_contracts()

    if not contracts:
        st.warning("No hay contratos activos definidos.")
        return

    # Selector de Contrato
    contract_names = [c['NOMBRE_CONTRATO'] for c in contracts]
    selected_name = st.selectbox("Seleccione Contrato para análisis:", contract_names)
    
    selected_contract = next((c for c in contracts if c['NOMBRE_CONTRATO'] == selected_name), None)
    
    if selected_contract:
        st.divider()
        st.subheader(f"Análisis de Capacidad: {selected_name}")
        
        # Métricas de cabecera
        col1, col2, col3 = st.columns(3)
        
        report_df = service.get_availability_report(selected_contract['ID_CONTRATO'])
        
        if not report_df.empty:
            total_req_pers = report_df[report_df['Tipo'] == 'PERSONAL']['Requerido'].sum()
            total_req_eq = report_df[report_df['Tipo'] == 'EQUIPO']['Requerido'].sum()
            
            with col1:
                st.metric("RRHH Requeridos", int(total_req_pers))
            with col2:
                st.metric("Equipos Requeridos", int(total_req_eq))
            with col3:
                # Datos del audio: 140 pozos año / 12 meses ~ 11-12 pozos mes
                st.metric("Pozos Objetivo / Mes", "12")

            st.write("### Comparativa Requerido vs Disponible en Catálogo")
            
            # Styling la tabla para resaltar faltantes
            def highlight_status(val):
                color = 'green' if '✅' in val else 'red'
                return f'color: {color}; font-weight: bold'

            styled_df = report_df.style.applymap(highlight_status, subset=['Estado'])
            st.table(styled_df)
            
            st.info("""
            **Nota:** La disponibilidad se calcula en base a los activos cargados en **Datos Maestros**. 
            Si falta capacidad, debe dar de alta nuevos recursos en el catálogo o desasignarlos de otros contratos.
            """)
        else:
            st.info("No hay una plantilla de capacidad definida para este contrato aún.")
            if st.button("Definir Plantilla Base (Automático)"):
                st.success("Plantilla base sugerida para abandono cargada (Pulling x3, Cementador x2...)")
                st.info("Funcionalidad de guardado en DB disponible en el siguiente sprint.")
