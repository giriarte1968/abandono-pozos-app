"""
Vista de Contratos - Gestión Contractual
Módulo: Finanzas & Control Contractual
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.financial_service_mock import financial_service


def render_contracts_view():
    """Renderiza la vista de gestión de contratos"""
    
    st.title("Gestión de Contratos")
    st.markdown("---")
    
    # Tabs
    tab1, tab2 = st.tabs(["Lista de Contratos", "Nuevo Contrato"])
    
    with tab1:
        render_contracts_list()
    
    with tab2:
        render_new_contract_form()


def render_contracts_list():
    """Renderiza la lista de contratos"""
    
    st.subheader("Contratos Activos")
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        filtro_estado = st.selectbox(
            "Filtrar por estado:",
            ["Todos", "ACTIVO", "SUSPENDIDO", "FINALIZADO"]
        )
    
    with col2:
        busqueda = st.text_input("Buscar contrato o cliente:")
    
    # Obtener contratos
    contratos = financial_service.get_contratos()
    
    # Aplicar filtros
    if filtro_estado != "Todos":
        contratos = [c for c in contratos if c['ESTADO'] == filtro_estado]
    
    if busqueda:
        busqueda_lower = busqueda.lower()
        contratos = [
            c for c in contratos 
            if busqueda_lower in c['NOMBRE_CONTRATO'].lower() 
            or busqueda_lower in c['CLIENTE'].lower()
        ]
    
    if not contratos:
        st.info("No se encontraron contratos con los filtros seleccionados.")
        return
    
    # Mostrar contratos como cards
    for contrato in contratos:
        with st.expander(f"{contrato['NOMBRE_CONTRATO']}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"**Cliente:** {contrato['CLIENTE']}")
                st.markdown(f"**Estado:** {contrato['ESTADO']}")
                st.markdown(f"**Plazo pago:** {contrato['PLAZO_PAGO_DIAS']} días")
            
            with col2:
                st.markdown(f"**Cantidad pozos:** {contrato['CANTIDAD_POZOS']}")
                st.markdown(f"**Valor unitario:** ${contrato['VALOR_UNITARIO_BASE_USD']:,.0f}")
                st.markdown(f"**Certificaciones:** {contrato['total_certificaciones']}")
            
            with col3:
                st.markdown(f"**Monto total:** ${contrato['MONTO_TOTAL_CONTRACTUAL']:,.0f}")
                
                # Calcular avance
                monto_certificado = contrato['MONTO_TOTAL_CONTRACTUAL'] - contrato['BACKLOG_RESTANTE']
                avance = (monto_certificado / contrato['MONTO_TOTAL_CONTRACTUAL'] * 100) if contrato['MONTO_TOTAL_CONTRACTUAL'] > 0 else 0
                
                st.markdown(f"**Backlog:** ${contrato['BACKLOG_RESTANTE']:,.0f}")
                st.markdown(f"**Avance:** {avance:.1f}%")
                st.progress(avance / 100)
            
            # Acciones
            st.markdown("---")
            col4, col5 = st.columns(2)
            
            with col4:
                if st.button(f"Ver Detalle", key=f"detail_{contrato['ID_CONTRATO']}"):
                    st.session_state['contrato_seleccionado'] = contrato['ID_CONTRATO']
                    st.session_state['vista_contrato'] = 'detalle'
            
            with col5:
                # Solo permitir editar si no tiene certificaciones
                if contrato['total_certificaciones'] == 0:
                    if st.button(f"Editar", key=f"edit_{contrato['ID_CONTRATO']}"):
                        st.session_state['contrato_seleccionado'] = contrato['ID_CONTRATO']
                        st.session_state['vista_contrato'] = 'editar'
                else:
                    st.button(f"Editar (Bloqueado)", disabled=True, 
                             help="No se puede editar: tiene certificaciones registradas",
                             key=f"blocked_{contrato['ID_CONTRATO']}")
            
            # Mostrar pozos asignados
            st.markdown("**Pozos Asignados:**")
            pozos_str = ", ".join(contrato.get('pozos_asignados', []))
            st.text(pozos_str)
    
    # Resumen
    st.markdown("---")
    st.subheader("Resumen General")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_contratos = len(contratos)
    total_monto = sum(c['MONTO_TOTAL_CONTRACTUAL'] for c in contratos)
    total_backlog = sum(c['BACKLOG_RESTANTE'] for c in contratos)
    total_pozos = sum(c['CANTIDAD_POZOS'] for c in contratos)
    
    with col1:
        st.metric("Total Contratos", total_contratos)
    with col2:
        st.metric("Monto Total", f"${total_monto:,.0f}")
    with col3:
        st.metric("Backlog Total", f"${total_backlog:,.0f}")
    with col4:
        st.metric("Total Pozos", total_pozos)


def render_new_contract_form():
    """Renderiza el formulario para crear nuevo contrato"""
    
    st.subheader("Crear Nuevo Contrato")
    
    with st.form("nuevo_contrato"):
        # Información básica
        col1, col2 = st.columns(2)
        
        with col1:
            nombre_contrato = st.text_input(
                "Nombre del Contrato *",
                placeholder="Ej: Contrato YPF - Lote Norte"
            )
            
            cliente = st.text_input(
                "Cliente *",
                placeholder="Ej: YPF S.A."
            )
            
            cantidad_pozos = st.number_input(
                "Cantidad de Pozos *",
                min_value=1,
                max_value=100,
                value=1
            )
        
        with col2:
            valor_unitario = st.number_input(
                "Valor Unitario Base (USD) *",
                min_value=0.0,
                value=185000.0,
                step=1000.0,
                format="%.2f"
            )
            
            plazo_pago = st.number_input(
                "Plazo de Pago (días) *",
                min_value=1,
                max_value=180,
                value=30
            )
        
        # Fechas
        col3, col4 = st.columns(2)
        
        with col3:
            fecha_inicio = st.date_input(
                "Fecha de Inicio *",
                value=datetime.now()
            )
        
        with col4:
            fecha_fin = st.date_input(
                "Fecha de Fin *",
                value=datetime.now() + timedelta(days=365)
            )
        
        # Cálculo automático del monto total
        monto_total = cantidad_pozos * valor_unitario
        st.info(f"**Monto Total Contractual:** ${monto_total:,.2f}")
        
        # Selección de pozos
        st.markdown("---")
        st.subheader("Asignación de Pozos")
        
        pozos_disponibles = financial_service.get_pozos()
        pozos_seleccionados = st.multiselect(
            "Seleccionar pozos para este contrato:",
            options=[p['ID_WELL'] for p in pozos_disponibles],
            format_func=lambda x: f"{x} - {next((p['WELL_NAME'] for p in pozos_disponibles if p['ID_WELL'] == x), x)}"
        )
        
        # Validación
        if len(pozos_seleccionados) != cantidad_pozos:
            st.warning(f"Debe seleccionar exactamente {cantidad_pozos} pozo(s). Seleccionados: {len(pozos_seleccionados)}")
        
        # Observaciones
        observaciones = st.text_area(
            "Observaciones",
            placeholder="Notas adicionales sobre el contrato..."
        )
        
        # Botón de envío
        submitted = st.form_submit_button("Guardar Contrato", type="primary")
        
        if submitted:
            if not nombre_contrato or not cliente:
                st.error("Por favor complete los campos obligatorios (*)")
            elif len(pozos_seleccionados) != cantidad_pozos:
                st.error(f"Debe seleccionar exactamente {cantidad_pozos} pozo(s)")
            else:
                # Crear nuevo contrato
                nuevo_contrato = {
                    'ID_CONTRATO': len(financial_service.contratos) + 1,
                    'NOMBRE_CONTRATO': nombre_contrato,
                    'CLIENTE': cliente,
                    'CANTIDAD_POZOS': cantidad_pozos,
                    'VALOR_UNITARIO_BASE_USD': valor_unitario,
                    'MONTO_TOTAL_CONTRACTUAL': monto_total,
                    'BACKLOG_RESTANTE': monto_total,
                    'PLAZO_PAGO_DIAS': plazo_pago,
                    'FECHA_INICIO': datetime.combine(fecha_inicio, datetime.min.time()),
                    'FECHA_FIN': datetime.combine(fecha_fin, datetime.min.time()),
                    'ESTADO': 'ACTIVO',
                    'total_certificaciones': 0,
                    'pozos_asignados': pozos_seleccionados
                }
                
                financial_service.contratos.append(nuevo_contrato)
                financial_service._persist_data()
                
                st.success(f"Contrato '{nombre_contrato}' creado exitosamente!")
                st.balloons()


if __name__ == "__main__":
    render_contracts_view()
