"""
Administración de Datos Maestros Financieros
Módulo: Finanzas & Control Contractual
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.financial_service_mock import financial_service


def render_view():
    """Renderiza la vista de administración de datos maestros financieros"""
    
    st.title("Administración - Datos Maestros Financieros")
    st.markdown("---")
    
    # Verificar permisos
    user_role = st.session_state.get('user_role', 'Administrativo')
    if user_role not in ['Administrativo', 'Gerente', 'Finanzas']:
        st.error("No tiene permisos para acceder a esta sección.")
        return
    
    # Tabs principales
    tab1, tab2, tab3, tab4 = st.tabs([
        "Gestión de Contratos",
        "Parámetros Macro", 
        "Configuración General",
        "Auditoría"
    ])
    
    with tab1:
        render_contracts_management()
    
    with tab2:
        render_macro_parameters()
    
    with tab3:
        render_general_settings()
    
    with tab4:
        render_audit_log()


def render_contracts_management():
    """Gestión completa de contratos"""
    
    st.subheader("Gestión de Contratos")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Lista de contratos existentes
        st.markdown("#### Contratos Existentes")
        
        contratos = financial_service.get_contratos()
        if contratos:
            for contrato in contratos:
                with st.expander(f"{contrato['NOMBRE_CONTRATO']}"):
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        st.write(f"**ID:** {contrato['ID_CONTRATO']}")
                        st.write(f"**Cliente:** {contrato['CLIENTE']}")
                        st.write(f"**Estado:** {contrato['ESTADO']}")
                        st.write(f"**Plazo Pago:** {contrato['PLAZO_PAGO_DIAS']} días")
                    
                    with col_b:
                        st.write(f"**Monto Total:** ${contrato['MONTO_TOTAL_CONTRACTUAL']:,.2f}")
                        st.write(f"**Backlog:** ${contrato['BACKLOG_RESTANTE']:,.2f}")
                        st.write(f"**Pozos:** {contrato['CANTIDAD_POZOS']}")
                        st.write(f"**Certificaciones:** {contrato['total_certificaciones']}")
                    
                    st.write(f"**Pozos Asignados:** {', '.join(contrato.get('pozos_asignados', []))}")
                    
                    # Solo permitir editar si no tiene certificaciones
                    if contrato['total_certificaciones'] == 0:
                        if st.button("Editar Contrato", key=f"edit_contract_{contrato['ID_CONTRATO']}"):
                            st.session_state['editing_contract'] = contrato['ID_CONTRATO']
                    else:
                        st.info("No se puede editar: tiene certificaciones registradas")
        else:
            st.info("No hay contratos registrados")
    
    with col2:
        # Crear nuevo contrato
        st.markdown("#### Crear Nuevo Contrato")
        
        with st.form("nuevo_contrato_master"):
            nombre = st.text_input("Nombre del Contrato *")
            cliente = st.text_input("Cliente *")
            
            col_c, col_d = st.columns(2)
            with col_c:
                cantidad_pozos = st.number_input("Cantidad Pozos *", min_value=1, value=1)
            with col_d:
                valor_unitario = st.number_input("Valor Unitario USD *", min_value=0.0, value=185000.0)
            
            plazo_pago = st.number_input("Plazo de Pago (días) *", min_value=1, value=30)
            
            col_e, col_f = st.columns(2)
            with col_e:
                fecha_inicio = st.date_input("Fecha Inicio *", value=datetime.now())
            with col_f:
                fecha_fin = st.date_input("Fecha Fin *", value=datetime.now() + timedelta(days=365))
            
            # Asignar pozos
            pozos_disponibles = financial_service.get_pozos()
            pozos_options = [p['ID_WELL'] for p in pozos_disponibles]
            pozos_seleccionados = st.multiselect(
                "Asignar Pozos *",
                options=pozos_options,
                max_selections=cantidad_pozos
            )
            
            monto_total = cantidad_pozos * valor_unitario
            st.info(f"**Monto Total:** ${monto_total:,.2f}")
            
            submitted = st.form_submit_button("Crear Contrato", type="primary")
            
            if submitted:
                if not nombre or not cliente:
                    st.error("Complete los campos obligatorios")
                elif len(pozos_seleccionados) != cantidad_pozos:
                    st.error(f"Debe seleccionar exactamente {cantidad_pozos} pozo(s)")
                else:
                    nuevo_contrato = {
                        'ID_CONTRATO': len(financial_service.contratos) + 1,
                        'NOMBRE_CONTRATO': nombre,
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
                    
                    st.success(f"Contrato '{nombre}' creado exitosamente!")
                    st.rerun()


def render_macro_parameters():
    """Gestión de parámetros macro económicos"""
    
    st.subheader("Parámetros Macro")
    st.info("Estos parámetros se utilizan para proyecciones financieras y cálculos automáticos.")
    
    # Parámetros actuales (simulados)
    parametros = {
        'COTIZACION_DOLAR': {'valor': 1050.00, 'unidad': 'ARS/USD', 'descripcion': 'Cotización referencial del dólar'},
        'INFLACION_ANUAL_ESTIMADA': {'valor': 25.50, 'unidad': '%', 'descripcion': 'Inflación anual estimada'},
        'TASA_INTERES_ANUAL': {'valor': 45.00, 'unidad': '%', 'descripcion': 'Tasa de interés anual para cálculos'},
        'COSTO_OPORTUNIDAD': {'valor': 12.00, 'unidad': '%', 'descripcion': 'Costo de oportunidad del capital'},
        'FACTOR_RIESGO_PAIS': {'valor': 850.00, 'unidad': 'puntos', 'descripcion': 'Riesgo país referencial'},
        'AJUSTE_POR_INFLACION': {'valor': 2.1, 'unidad': '% mensual', 'descripcion': 'Ajuste mensual por inflación'},
    }
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### Parámetros Actuales")
        
        for key, data in parametros.items():
            with st.expander(f"{key}"):
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    nuevo_valor = st.number_input(
                        "Valor",
                        value=float(data['valor']),
                        key=f"param_val_{key}"
                    )
                
                with col_b:
                    st.text_input("Unidad", value=data['unidad'], disabled=True, key=f"param_unit_{key}")
                
                with col_c:
                    if st.button("Actualizar", key=f"param_update_{key}"):
                        st.success(f"Parámetro {key} actualizado a {nuevo_valor}")
                
                st.caption(data['descripcion'])
    
    with col2:
        st.markdown("#### Agregar Nuevo Parámetro")
        
        with st.form("nuevo_parametro"):
            nombre_param = st.text_input("Nombre del Parámetro *")
            valor_param = st.number_input("Valor *", value=0.0)
            unidad_param = st.text_input("Unidad *")
            desc_param = st.text_area("Descripción")
            
            submitted = st.form_submit_button("Agregar Parámetro")
            
            if submitted:
                if nombre_param and unidad_param:
                    st.success(f"Parámetro '{nombre_param}' agregado")
                else:
                    st.error("Complete los campos obligatorios")


def render_general_settings():
    """Configuración general del módulo financiero"""
    
    st.subheader("Configuración General")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Plazos de Pago por Defecto")
        
        plazos = {
            'SureOil Argentina S.A.': 30,
            'YPF S.A.': 45,
            'Petrobras Argentina S.A.': 30,
            'Pluspetrol S.A.': 30,
            'Pan American Energy': 45,
        }
        
        for cliente, plazo in plazos.items():
            nuevo_plazo = st.number_input(
                f"{cliente}",
                min_value=1,
                max_value=180,
                value=plazo,
                key=f"plazo_{cliente}"
            )
        
        if st.button("Guardar Plazos"):
            st.success("Plazos de pago actualizados")
    
    with col2:
        st.markdown("#### Alertas y Umbrales")
        
        umbral_dias_cobertura = st.number_input(
            "Umbral Días de Cobertura (Alerta)",
            min_value=1,
            max_value=365,
            value=45,
            help="Se mostrará alerta cuando los días de cobertura sean menores a este valor"
        )
        
        umbral_backlog = st.number_input(
            "Umbral Backlog Mínimo (USD)",
            min_value=0,
            value=500000,
            step=100000,
            help="Se mostrará advertencia cuando el backlog sea menor a este valor"
        )
        
        notificaciones = st.multiselect(
            "Activar Notificaciones",
            ["Facturas vencidas", "Backlog bajo", "Certificaciones pendientes", "Cobros recibidos"],
            default=["Facturas vencidas", "Backlog bajo"]
        )
        
        if st.button("Guardar Configuración"):
            st.success("Configuración guardada")


def render_audit_log():
    """Registro de auditoría de cambios financieros"""
    
    st.subheader("Auditoría de Cambios")
    
    # Datos de auditoría simulados
    auditoria = [
        {
            'fecha': '2025-02-14 15:30:22',
            'usuario': 'admin',
            'accion': 'CREAR',
            'tabla': 'CONTRATOS',
            'registro': 'Contrato YPF - Abandono Integral',
            'detalle': 'Creación de nuevo contrato'
        },
        {
            'fecha': '2025-02-14 14:15:10',
            'usuario': 'finanzas',
            'accion': 'ACTUALIZAR',
            'tabla': 'PARAMETROS_MACRO',
            'registro': 'COTIZACION_DOLAR',
            'detalle': 'Valor actualizado: 1050.00 → 1080.00'
        },
        {
            'fecha': '2025-02-14 11:45:33',
            'usuario': 'admin',
            'accion': 'CREAR',
            'tabla': 'CERTIFICACIONES',
            'registro': 'Certificación #3',
            'detalle': 'Certificación de pozo A-321'
        },
        {
            'fecha': '2025-02-13 16:20:45',
            'usuario': 'gerente',
            'accion': 'ACTUALIZAR',
            'tabla': 'CONTRATOS',
            'registro': 'Contrato SureOil - Lote Norte',
            'detalle': 'Modificación plazo de pago: 30 → 45 días'
        },
        {
            'fecha': '2025-02-13 09:10:15',
            'usuario': 'sistema',
            'accion': 'GENERAR',
            'tabla': 'FACTURAS',
            'registro': 'F-2025-1003',
            'detalle': 'Factura generada automáticamente desde certificación'
        }
    ]
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filtro_usuario = st.selectbox(
            "Filtrar por usuario:",
            ["Todos"] + list(set([a['usuario'] for a in auditoria]))
        )
    
    with col2:
        filtro_tabla = st.selectbox(
            "Filtrar por tabla:",
            ["Todos"] + list(set([a['tabla'] for a in auditoria]))
        )
    
    with col3:
        filtro_accion = st.selectbox(
            "Filtrar por acción:",
            ["Todos", "CREAR", "ACTUALIZAR", "ELIMINAR", "GENERAR"]
        )
    
    # Aplicar filtros
    auditoria_filtrada = auditoria
    if filtro_usuario != "Todos":
        auditoria_filtrada = [a for a in auditoria_filtrada if a['usuario'] == filtro_usuario]
    if filtro_tabla != "Todos":
        auditoria_filtrada = [a for a in auditoria_filtrada if a['tabla'] == filtro_tabla]
    if filtro_accion != "Todos":
        auditoria_filtrada = [a for a in auditoria_filtrada if a['accion'] == filtro_accion]
    
    # Mostrar tabla
    if auditoria_filtrada:
        df = pd.DataFrame(auditoria_filtrada)
        st.dataframe(df, width='stretch')
    else:
        st.info("No hay registros con los filtros seleccionados")
    
    # Exportar
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        if st.button("Exportar a Excel"):
            st.info("Exportación generada (simulado)")
    with col_exp2:
        if st.button("Exportar a PDF"):
            st.info("Reporte PDF generado (simulado)")


if __name__ == "__main__":
    render_view()
