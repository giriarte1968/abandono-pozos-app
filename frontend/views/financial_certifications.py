"""
Vista de Certificaciones - Gestión de Certificaciones INTEGRADA
Módulo: Finanzas & Control Contractual
Integración con sistema operativo
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.financial_service_mock import financial_service


def render_certifications_view():
    """Renderiza la vista de gestión de certificaciones"""
    
    st.title("Certificaciones de Obra")
    st.markdown("---")
    
    # Banner de integración
    st.info("""
    **Integración con Operaciones:** Los pozos se obtienen en tiempo real desde el sistema operativo. 
    Solo los pozos en estado 'COMPLETADO' pueden ser certificados.
    """)
    
    # Tabs
    tab1, tab2 = st.tabs(["Historial de Certificaciones", "Nueva Certificación"])
    
    with tab1:
        render_certifications_history()
    
    with tab2:
        render_new_certification_form()


def render_certifications_history():
    """Renderiza el historial de certificaciones"""
    
    st.subheader("Historial de Certificaciones")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        contratos = financial_service.get_contratos()
        opciones_contratos = ["Todos"] + [c['NOMBRE_CONTRATO'] for c in contratos]
        filtro_contrato = st.selectbox("Filtrar por contrato:", opciones_contratos)
    
    with col2:
        filtro_estado = st.selectbox(
            "Filtrar por estado:",
            ["Todos", "PENDIENTE_FACTURA", "FACTURADO", "COBRADO"]
        )
    
    with col3:
        pozos = financial_service.get_pozos()
        opciones_pozos = ["Todos"] + [p['ID_WELL'] for p in pozos]
        filtro_pozo = st.selectbox("Filtrar por pozo:", opciones_pozos)
    
    # Obtener certificaciones
    certificaciones = financial_service.get_certificaciones()
    
    # Aplicar filtros
    if filtro_contrato != "Todos":
        contrato = next((c for c in contratos if c['NOMBRE_CONTRATO'] == filtro_contrato), None)
        if contrato:
            certificaciones = [c for c in certificaciones if c['ID_CONTRATO'] == contrato['ID_CONTRATO']]
    
    if filtro_estado != "Todos":
        certificaciones = [c for c in certificaciones if c['ESTADO'] == filtro_estado]
    
    if filtro_pozo != "Todos":
        certificaciones = [c for c in certificaciones if c['ID_WELL'] == filtro_pozo]
    
    if not certificaciones:
        st.info("No se encontraron certificaciones con los filtros seleccionados.")
        return
    
    # Mostrar tabla con información de integración
    cert_df = pd.DataFrame(certificaciones)
    
    # Agregar nombre de contrato
    cert_df['CONTRATO'] = cert_df['ID_CONTRATO'].apply(
        lambda x: next((c['NOMBRE_CONTRATO'] for c in contratos if c['ID_CONTRATO'] == x), f"Contrato {x}")
    )
    
    # Agregar info de sincronización
    cert_df['SINCRONIZADO'] = cert_df['SINCRONIZADO_OPERACIONES'].apply(
        lambda x: '✅' if x else '⏳'
    )
    
    # Mostrar datos
    st.dataframe(
        cert_df[['ID_CERTIFICACION', 'CONTRATO', 'ID_WELL', 'WELL_NAME',
                'FECHA_CERTIFICACION', 'MONTO_CERTIFICADO', 'ESTADO', 'SINCRONIZADO']],
        width='stretch'
    )
    
    # Resumen
    st.markdown("---")
    st.subheader("Resumen")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Certificaciones", len(certificaciones))
    
    with col2:
        total_certificado = sum(c['MONTO_CERTIFICADO'] for c in certificaciones)
        st.metric("Monto Total Certificado", f"${total_certificado:,.2f}")
    
    with col3:
        sincronizados = len([c for c in certificaciones if c.get('SINCRONIZADO_OPERACIONES', False)])
        st.metric("Sincronizados con Operaciones", sincronizados)
    
    with col4:
        pendientes = len(certificaciones) - sincronizados
        if pendientes > 0:
            st.metric("Pendientes de Sincronización", pendientes)
        else:
            st.metric("Estado", "✅ Sincronizado")
    
    # Detalle por certificación
    st.markdown("---")
    st.subheader("Detalle de Certificación")
    
    cert_seleccionada = st.selectbox(
        "Seleccionar certificación para ver detalle:",
        options=cert_df['ID_CERTIFICACION'].tolist(),
        format_func=lambda x: f"Certificación #{x}"
    )
    
    if cert_seleccionada:
        cert = next((c for c in certificaciones if c['ID_CERTIFICACION'] == cert_seleccionada), None)
        if cert:
            # Obtener información del pozo desde operaciones
            pozo_operaciones = financial_service.get_pozo_by_id(cert['ID_WELL'])
            
            with st.expander(f"Detalle de Certificación #{cert_seleccionada}", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"**Contrato:** {cert['ID_CONTRATO']}")
                    st.markdown(f"**Pozo:** {cert['ID_WELL']}")
                    st.markdown(f"**Nombre:** {cert['WELL_NAME']}")
                    st.markdown(f"**Fecha:** {cert['FECHA_CERTIFICACION']}")
                
                with col2:
                    st.markdown(f"**Monto:** ${cert['MONTO_CERTIFICADO']:,.2f}")
                    st.markdown(f"**% Avance:** {cert['PORCENTAJE_AVANCE']:.1f}%")
                    st.markdown(f"**Estado:** {cert['ESTADO']}")
                
                with col3:
                    # Información desde operaciones
                    if pozo_operaciones:
                        st.markdown("**📍 Estado en Operaciones:**")
                        st.markdown(f"- Estado: {pozo_operaciones['ESTADO_PROYECTO']}")
                        st.markdown(f"- Progreso: {pozo_operaciones.get('PROGRESO', 0)}%")
                        st.markdown(f"- Yacimiento: {pozo_operaciones.get('YACIMIENTO', 'N/A')}")
                    
                    # Estado de sincronización
                    if cert.get('SINCRONIZADO_OPERACIONES', False):
                        st.success("✅ Sincronizado con Operaciones")
                    else:
                        st.warning("⏳ Pendiente de Sincronización")
                
                # Costos asociados desde operaciones
                if pozo_operaciones:
                    costos = financial_service.get_costos_pozo(cert['ID_WELL'])
                    if costos:
                        st.markdown("---")
                        st.markdown("**💰 Costos Registrados (desde Operaciones):**")
                        total_costos = sum(c['MONTO_USD'] for c in costos)
                        for costo in costos:
                            st.write(f"- {costo['CONCEPTO']}: ${costo['MONTO_USD']:,.2f}")
                        st.write(f"**Total Costos:** ${total_costos:,.2f}")
                        
                        margen = cert['MONTO_CERTIFICADO'] - total_costos
                        margen_pct = (margen / cert['MONTO_CERTIFICADO'] * 100) if cert['MONTO_CERTIFICADO'] > 0 else 0
                        st.write(f"**Margen:** ${margen:,.2f} ({margen_pct:.1f}%)")
                
                # Mostrar factura asociada
                factura = next((f for f in financial_service.get_facturas() if f['ID_CERTIFICACION'] == cert_seleccionada), None)
                if factura:
                    st.markdown("---")
                    st.markdown(f"**📄 Factura Generada:** {factura['NUMERO_FACTURA']}")
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        st.write(f"**Fecha Emisión:** {factura['FECHA_FACTURA']}")
                        st.write(f"**Monto Factura:** ${factura['MONTO']:,.2f}")
                    with col_f2:
                        st.write(f"**Fecha Vencimiento:** {factura['FECHA_VENCIMIENTO']}")
                        st.write(f"**Estado:** {factura['ESTADO']}")
                else:
                    st.info("No hay factura generada para esta certificación.")


def render_new_certification_form():
    """Renderiza el formulario para crear nueva certificación"""
    
    st.subheader("Nueva Certificación de Obra")
    
    st.info("""
    **Flujo de Certificación:**
    1. Seleccionar Contrato con backlog disponible
    2. Seleccionar Pozo en estado 'COMPLETADO' en operaciones
    3. Verificar costos desde operaciones
    4. Generar certificación y factura automática
    """)
    
    with st.form("nueva_certificacion"):
        # Paso 1: Seleccionar Contrato
        st.markdown("### Paso 1: Seleccionar Contrato")
        
        contratos = financial_service.get_contratos()
        contratos_con_backlog = [c for c in contratos if c['BACKLOG_RESTANTE'] > 0]
        
        if not contratos_con_backlog:
            st.error("No hay contratos con backlog disponible para certificar.")
            return
        
        contrato_seleccionado = st.selectbox(
            "Seleccionar contrato *",
            options=contratos_con_backlog,
            format_func=lambda x: f"{x['NOMBRE_CONTRATO']} (Backlog: ${x['BACKLOG_RESTANTE']:,.0f})"
        )
        
        if contrato_seleccionado:
            # Mostrar información del contrato
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Cliente:** {contrato_seleccionado['CLIENTE']}")
                st.write(f"**Monto Total:** ${contrato_seleccionado['MONTO_TOTAL_CONTRACTUAL']:,.0f}")
            with col2:
                st.write(f"**Backlog Restante:** ${contrato_seleccionado['BACKLOG_RESTANTE']:,.0f}")
                st.write(f"**Plazo Pago:** {contrato_seleccionado['PLAZO_PAGO_DIAS']} días")
        
        st.markdown("---")
        
        # Paso 2: Seleccionar Pozo (integrado con operaciones)
        st.markdown("### Paso 2: Seleccionar Pozo desde Operaciones")
        
        # Obtener pozos ya certificados en este contrato
        certificaciones_existentes = [
            c for c in financial_service.get_certificaciones() 
            if c['ID_CONTRATO'] == contrato_seleccionado['ID_CONTRATO']
        ]
        pozos_certificados = [c['ID_WELL'] for c in certificaciones_existentes]
        
        # Obtener información de pozos desde operaciones
        pozos_operaciones = financial_service.get_pozos()
        
        # Filtrar pozos disponibles (asignados al contrato, no certificados aún)
        pozos_asignados = contrato_seleccionado.get('pozos_asignados', [])
        
        # Mostrar tabla de pozos disponibles con info de operaciones
        st.markdown("**Pozos Asignados al Contrato (desde Operaciones):**")
        
        pozos_info = []
        for well_id in pozos_asignados:
            pozo = next((p for p in pozos_operaciones if p['ID_WELL'] == well_id), None)
            if pozo:
                ya_certificado = well_id in pozos_certificados
                puede_certificar = pozo['ESTADO_PROYECTO'] == 'COMPLETADO' and not ya_certificado
                
                pozos_info.append({
                    'ID_WELL': well_id,
                    'NOMBRE': pozo['WELL_NAME'],
                    'ESTADO_OP': pozo['ESTADO_PROYECTO'],
                    'PROGRESO': f"{pozo.get('PROGRESO', 0)}%",
                    'YACIMIENTO': pozo.get('YACIMIENTO', 'N/A'),
                    'CERTIFICABLE': '✅ Sí' if puede_certificar else ('❌ Ya certificado' if ya_certificado else '❌ No completado'),
                    'PUEDE_CERTIFICAR': puede_certificar
                })
        
        if pozos_info:
            df_pozos = pd.DataFrame(pozos_info)
            st.dataframe(df_pozos[['ID_WELL', 'NOMBRE', 'ESTADO_OP', 'PROGRESO', 'YACIMIENTO', 'CERTIFICABLE']], 
                        width='stretch')
            
            # Filtrar solo los que se pueden certificar
            pozos_certificables = [p['ID_WELL'] for p in pozos_info if p['PUEDE_CERTIFICAR']]
            
            if pozos_certificables:
                pozo_seleccionado = st.selectbox(
                    "Seleccionar pozo a certificar *",
                    options=pozos_certificables,
                    format_func=lambda x: f"{x} - {next((p['NOMBRE'] for p in pozos_info if p['ID_WELL'] == x), x)}"
                )
                
                # Mostrar detalle del pozo seleccionado
                pozo_info = next((p for p in pozos_info if p['ID_WELL'] == pozo_seleccionado), None)
                if pozo_info:
                    col_p1, col_p2 = st.columns(2)
                    with col_p1:
                        st.write(f"**Estado Operativo:** {pozo_info['ESTADO_OP']}")
                        st.write(f"**Progreso:** {pozo_info['PROGRESO']}")
                    with col_p2:
                        st.write(f"**Yacimiento:** {pozo_info['YACIMIENTO']}")
                        
                        # Mostrar costos
                        costos = financial_service.get_costos_pozo(pozo_seleccionado)
                        if costos:
                            total_costos = sum(c['MONTO_USD'] for c in costos)
                            st.write(f"**Costos Acumulados:** ${total_costos:,.2f}")
                
                st.success("✅ Este pozo está listo para certificación")
            else:
                st.warning("""
                **No hay pozos disponibles para certificación.**
                
                Posibles causas:
                - Todos los pozos ya fueron certificados
                - Los pozos no están en estado 'COMPLETADO' en operaciones
                
                Verifique el estado de los pozos en el módulo de Operaciones.
                """)
                pozo_seleccionado = None
        else:
            st.error("No se encontraron pozos asignados al contrato en el sistema operativo.")
            pozo_seleccionado = None
        
        st.markdown("---")
        
        # Paso 3: Información de Certificación
        if pozo_seleccionado:
            st.markdown("### Paso 3: Información de Certificación")
            
            col1, col2 = st.columns(2)
            
            with col1:
                fecha_certificacion = st.date_input(
                    "Fecha de Certificación *",
                    value=datetime.now()
                )
            
            with col2:
                # Sugerir % de avance basado en el progreso del pozo
                pozo_op = financial_service.get_pozo_by_id(pozo_seleccionado)
                progreso_sugerido = min(100, pozo_op.get('PROGRESO', 100) if pozo_op else 100)
                
                porcentaje_avance = st.slider(
                    "Porcentaje de Avance *",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(progreso_sugerido),
                    step=5.0
                )
            
            # Monto de certificación (valor unitario del contrato)
            monto_maximo = contrato_seleccionado['VALOR_UNITARIO_BASE_USD']
            
            # Calcular sugerencia basada en % de avance
            monto_sugerido = monto_maximo * (porcentaje_avance / 100)
            
            monto_certificado = st.number_input(
                "Monto a Certificar (USD) *",
                min_value=0.0,
                max_value=float(monto_maximo),
                value=float(monto_sugerido),
                step=1000.0,
                format="%.2f"
            )
            
            # Preview de factura
            st.markdown("---")
            st.markdown("### Vista Previa de Factura")
            
            fecha_venc = datetime.combine(fecha_certificacion, datetime.min.time()) + timedelta(days=contrato_seleccionado['PLAZO_PAGO_DIAS'])
            
            col3, col4 = st.columns(2)
            with col3:
                st.write(f"**Fecha Emisión:** {fecha_certificacion}")
                st.write(f"**Monto:** ${monto_certificado:,.2f}")
            with col4:
                st.write(f"**Fecha Vencimiento:** {fecha_venc.date()}")
                st.write(f"**Plazo:** {contrato_seleccionado['PLAZO_PAGO_DIAS']} días")
            
            # Observaciones
            observaciones = st.text_area(
                "Observaciones",
                placeholder="Notas adicionales sobre esta certificación..."
            )
            
            # Botón de envío
            st.markdown("---")
            submitted = st.form_submit_button("Crear Certificación y Generar Factura", type="primary")
            
            if submitted:
                try:
                    # Crear certificación usando el método integrado
                    resultado = financial_service.certificar_pozo(
                        id_contrato=contrato_seleccionado['ID_CONTRATO'],
                        well_id=pozo_seleccionado,
                        monto=monto_certificado,
                        porcentaje_avance=porcentaje_avance
                    )
                    
                    st.success(f"✅ {resultado['mensaje']}")
                    st.success(f"📄 Factura generada: {resultado['factura_generada']['NUMERO_FACTURA']}")
                    
                    # Mostrar resumen
                    st.markdown("---")
                    st.markdown("**Resumen de la Certificación:**")
                    st.write(f"• Pozo certificado: {pozo_seleccionado}")
                    st.write(f"• Monto certificado: ${monto_certificado:,.2f}")
                    st.write(f"• Factura #{resultado['factura_generada']['NUMERO_FACTURA']}")
                    st.write(f"• Vencimiento: {resultado['factura_generada']['FECHA_VENCIMIENTO'].strftime('%d/%m/%Y')}")
                    
                    # Actualizar backlog mostrado
                    nuevo_backlog = contrato_seleccionado['BACKLOG_RESTANTE'] - monto_certificado
                    st.info(f"📊 Backlog actualizado: ${nuevo_backlog:,.2f}")
                    
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Error al crear certificación: {str(e)}")


if __name__ == "__main__":
    render_certifications_view()
