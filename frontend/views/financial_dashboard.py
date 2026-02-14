"""
Dashboard Financiero - Vista Principal
Módulo: Finanzas & Control Contractual
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

# Agregar path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.financial_service_mock import financial_service


def render_financial_dashboard():
    """Renderiza el dashboard financiero principal"""
    
    st.title("💼 Finanzas & Control Contractual")
    st.markdown("---")
    
    # Verificar permisos (simulado)
    user_role = st.session_state.get('user_role', 'Administrativo')
    allowed_roles = ['Administrativo', 'Gerente', 'Finanzas']
    
    if user_role not in allowed_roles:
        st.error("⚠️ No tiene permisos para acceder a este módulo.")
        return
    
    # Tabs principales
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Dashboard Principal",
        "📈 Flujo de Fondos",
        "📋 KPIs Detallados",
        "⚠️ Alertas"
    ])
    
    with tab1:
        render_main_dashboard()
    
    with tab2:
        render_cash_flow_analysis()
    
    with tab3:
        render_detailed_kpis()
    
    with tab4:
        render_alerts()


def render_main_dashboard():
    """Renderiza el dashboard principal con KPIs"""
    
    st.subheader("Dashboard Financiero - Resumen Ejecutivo")
    
    # Obtener KPIs
    kpis = financial_service.get_kpis_dashboard()
    
    # Fila de KPIs principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Backlog Contractual",
            value=f"${kpis['backlog_contractual']:,.0f}",
            delta=f"${kpis['backlog_contractual']/1000000:.1f}M"
        )
    
    with col2:
        st.metric(
            label="Avance Físico",
            value=f"{kpis['avance_fisico_pct']:.1f}%"
        )
    
    with col3:
        st.metric(
            label="Avance Financiero",
            value=f"{kpis['avance_financiero_pct']:.1f}%"
        )
    
    with col4:
        alert_color = "🚨" if kpis['alerta_cobertura'] else "✅"
        st.metric(
            label=f"{alert_color} Días Cobertura",
            value=f"{kpis['dias_cobertura']:.0f} días",
            delta="Alerta" if kpis['alerta_cobertura'] else "Normal"
        )
    
    st.markdown("---")
    
    # Segunda fila de métricas
    col5, col6, col7 = st.columns(3)
    
    with col5:
        st.metric(
            label="Capital Trabajo Req.",
            value=f"${kpis['capital_trabajo']:,.0f}",
            delta=f"${kpis['capital_trabajo']/1000000:.1f}M"
        )
    
    with col6:
        st.metric(
            label="Saldo Caja",
            value=f"${kpis['saldo_caja']:,.0f}",
            delta=f"${kpis['saldo_caja']/1000:.0f}k"
        )
    
    with col7:
        # Calcular contratos activos
        contratos_activos = len([c for c in financial_service.contratos if c['ESTADO'] == 'ACTIVO'])
        st.metric(
            label="Contratos Activos",
            value=contratos_activos
        )
    
    st.markdown("---")
    
    # Gráfico comparativo de Ingresos vs Egresos
    st.subheader("Ingresos vs Egresos - Proyección 12 Meses")
    
    flujo = financial_service.get_flujo_fondos(12)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Ingresos Proyectados',
        x=flujo['PERIODO'],
        y=flujo['INGRESOS_PROYECTADOS'],
        marker_color='green'
    ))
    
    fig.add_trace(go.Bar(
        name='Egresos Operativos',
        x=flujo['PERIODO'],
        y=flujo['EGRESOS_OPERATIVOS'],
        marker_color='red'
    ))
    
    fig.update_layout(
        barmode='group',
        title='Proyección Mensual',
        xaxis_title='Período',
        yaxis_title='Monto (USD)',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Resumen de contratos
    st.subheader("Resumen de Contratos")
    
    contratos_df = pd.DataFrame(financial_service.contratos)
    contratos_display = contratos_df[[
        'NOMBRE_CONTRATO', 'CLIENTE', 'CANTIDAD_POZOS', 
        'MONTO_TOTAL_CONTRACTUAL', 'BACKLOG_RESTANTE', 'ESTADO'
    ]].copy()
    
    st.dataframe(contratos_display, width='stretch')


def render_cash_flow_analysis():
    """Renderiza análisis detallado de flujo de fondos"""
    
    st.subheader("Análisis de Flujo de Fondos")
    
    # Selector de período
    periodo_vista = st.selectbox(
        "Período de análisis:",
        ["12 meses", "6 meses", "3 meses"],
        index=0
    )
    
    meses = 12 if periodo_vista == "12 meses" else (6 if periodo_vista == "6 meses" else 3)
    
    flujo = financial_service.get_flujo_fondos(meses)
    
    # Gráfico de curva acumulada
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Saldo Acumulado', 'Flujo Mensual'),
        vertical_spacing=0.15
    )
    
    # Curva acumulada
    fig.add_trace(
        go.Scatter(
            x=flujo['PERIODO'],
            y=flujo['ACUMULADO'],
            mode='lines+markers',
            name='Saldo Acumulado',
            line=dict(color='blue', width=3)
        ),
        row=1, col=1
    )
    
    # Línea de cero
    fig.add_hline(y=0, line_dash="dash", line_color="red", row=1, col=1)
    
    # Flujo mensual
    colors = ['green' if x >= 0 else 'red' for x in flujo['SALDO_MENSUAL']]
    fig.add_trace(
        go.Bar(
            x=flujo['PERIODO'],
            y=flujo['SALDO_MENSUAL'],
            name='Saldo Mensual',
            marker_color=colors
        ),
        row=2, col=1
    )
    
    fig.update_layout(height=600, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabla de datos
    st.subheader("Detalle de Proyección")
    st.dataframe(flujo, width='stretch')


def render_detailed_kpis():
    """Renderiza KPIs detallados"""
    
    st.subheader("KPIs Detallados")
    
    # KPIs por contrato
    st.markdown("### KPIs por Contrato")
    
    contratos_kpis = []
    for contrato in financial_service.contratos:
        certificados_contrato = [
            cert for cert in financial_service.certificaciones 
            if cert['ID_CONTRATO'] == contrato['ID_CONTRATO']
        ]
        
        monto_certificado = sum(cert['MONTO_CERTIFICADO'] for cert in certificados_contrato)
        avance_financiero = (monto_certificado / contrato['MONTO_TOTAL_CONTRACTUAL'] * 100) if contrato['MONTO_TOTAL_CONTRACTUAL'] > 0 else 0
        avance_fisico = (len(certificados_contrato) / contrato['CANTIDAD_POZOS'] * 100) if contrato['CANTIDAD_POZOS'] > 0 else 0
        
        contratos_kpis.append({
            'Contrato': contrato['NOMBRE_CONTRATO'],
            'Total (USD)': f"${contrato['MONTO_TOTAL_CONTRACTUAL']:,.0f}",
            'Certificado (USD)': f"${monto_certificado:,.0f}",
            'Backlog (USD)': f"${contrato['BACKLOG_RESTANTE']:,.0f}",
            'Avance Físico %': f"{avance_fisico:.1f}%",
            'Avance Financiero %': f"{avance_financiero:.1f}%",
            'Pozos Certificados': len(certificados_contrato),
            'Pozos Pendientes': contrato['CANTIDAD_POZOS'] - len(certificados_contrato)
        })
    
    df_kpis = pd.DataFrame(contratos_kpis)
    st.dataframe(df_kpis, width='stretch')
    
    # Gráfico de backlog por contrato
    st.markdown("### Distribución de Backlog")
    
    fig = px.pie(
        df_kpis,
        values=[float(x.replace('$', '').replace(',', '')) for x in df_kpis['Backlog (USD)']],
        names='Contrato',
        title='Backlog Restante por Contrato'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Facturas pendientes
    st.markdown("### Facturas Pendientes")
    
    facturas_pendientes = [
        f for f in financial_service.facturas 
        if f['ESTADO'] in ['EMITIDA', 'PENDIENTE']
    ]
    
    if facturas_pendientes:
        facturas_df = pd.DataFrame(facturas_pendientes)
        st.dataframe(facturas_df[['NUMERO_FACTURA', 'CLIENTE', 'FECHA_VENCIMIENTO', 'MONTO', 'ESTADO']], 
                    width='stretch')
    else:
        st.info("No hay facturas pendientes")


def render_alerts():
    """Renderiza alertas y notificaciones"""
    
    st.subheader("Alertas y Notificaciones")
    
    kpis = financial_service.get_kpis_dashboard()
    alerts = []
    
    # Alerta de cobertura
    if kpis['dias_cobertura'] < 45:
        alerts.append({
            'tipo': 'CRÍTICA',
            'mensaje': f"Días de cobertura bajos: {kpis['dias_cobertura']:.0f} días",
            'accion': 'Revisar proyección de cobros y evaluar línea de crédito'
        })
    
    # Alerta de backlog
    total_backlog = kpis['backlog_contractual']
    if total_backlog < 500000:
        alerts.append({
            'tipo': 'ADVERTENCIA',
            'mensaje': f"Backlog bajo: ${total_backlog:,.0f}",
            'accion': 'Buscar nuevos contratos para mantener operaciones'
        })
    
    # Alertas de facturas vencidas
    from datetime import datetime
    hoy = datetime.now()
    facturas_vencidas = [
        f for f in financial_service.facturas 
        if f['ESTADO'] == 'EMITIDA' and f['FECHA_VENCIMIENTO'] < hoy
    ]
    
    if facturas_vencidas:
        total_vencido = sum(f['MONTO'] for f in facturas_vencidas)
        alerts.append({
            'tipo': 'CRÍTICA',
            'mensaje': f"{len(facturas_vencidas)} facturas vencidas por ${total_vencido:,.0f}",
            'accion': 'Contactar clientes para gestionar cobranzas'
        })
    
    # Mostrar alertas
    if alerts:
        for alert in alerts:
            with st.expander(f"{alert['tipo']}: {alert['mensaje']}"):
                st.write(f"**Acción recomendada:** {alert['accion']}")
    else:
        st.success("No hay alertas activas. Situación financiera estable.")
    
    # Resumen de estado
    st.markdown("---")
    st.markdown("### Estado General")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Facturas Pendientes", len([f for f in financial_service.facturas if f['ESTADO'] == 'PENDIENTE']))
    
    with col2:
        st.metric("Facturas Cobradas", len([f for f in financial_service.facturas if f['ESTADO'] == 'COBRADA']))
    
    with col3:
        cert_pendientes = len([c for c in financial_service.certificaciones if c['ESTADO'] == 'PENDIENTE_FACTURA'])
        st.metric("Certificaciones Pendientes", cert_pendientes)


if __name__ == "__main__":
    render_financial_dashboard()
