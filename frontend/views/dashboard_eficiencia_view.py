"""
Dashboard de Eficiencia Operativa
Muestra KPIs de eficiencia económica y operativa por pozo.

Datos fuente:
- tbl_asignacion_operativa_detalle (costos reales)
- tbl_contrato_pozos (relación con contratos)
- CONTRATOS (valor contractual base)

No modifica el módulo financiero existente.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

# Importar servicios
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.financial_service_mock import financial_service
from services.asignacion_operativa_service import asignacion_operativa_service


def render_dashboard_eficiencia():
    """Renderiza el dashboard de eficiencia operativa"""
    
    st.title("📊 Dashboard de Eficiencia Operativa")
    st.markdown("---")
    
    # Permisos
    user_role = st.session_state.get('user_role', 'Usuario')
    if user_role not in ['Gerente', 'Administrativo', 'Finanzas', 'Supervisor']:
        st.error("No tienes acceso a este módulo.")
        return
    
    # Obtener datos
    asignaciones = _get_all_asignaciones()
    contratos_pozos = financial_service.get_all_contrato_pozos()
    contratos = financial_service.get_contratos()
    
    # Procesar datos por pozo
    df_pozos = _procesar_datos_pozos(asignaciones, contratos_pozos, contratos)
    
    if df_pozos.empty:
        st.warning("No hay datos de asignaciones operativas para mostrar.")
        return
    
    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN 1: KPIs PRINCIPALES
    # ═══════════════════════════════════════════════════════════════════
    st.markdown("### 📈 KPIs Principales")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Pozos Activos", len(df_pozos))
    with col2:
        total_costo = df_pozos['costo_real'].sum()
        st.metric("Costo Total Ejecutado", f"${total_costo:,.0f}")
    with col3:
        margen_promedio = df_pozos['margen_bruto'].mean()
        st.metric("Margen Bruto Promedio", f"${margen_promedio:,.0f}")
    with col4:
        total_standby = df_pozos['horas_standby'].sum()
        st.metric("Horas Standby Totales", f"{total_standby:.1f} hrs")
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN 2: TABLA DE EFICIENCIA POR POZO
    # ═══════════════════════════════════════════════════════════════════
    st.markdown("### 📋 Eficiencia por Pozo")
    
    # Preparar dataframe para mostrar
    df_display = df_pozos.copy()
    df_display['eficiencia_pct'] = df_display['eficiencia_pct'].apply(lambda x: f"{x:.1f}%")
    df_display['margen_bruto'] = df_display['margen_bruto'].apply(lambda x: f"${x:,.0f}")
    df_display['costo_real'] = df_display['costo_real'].apply(lambda x: f"${x:,.0f}")
    df_display['valor_contractual'] = df_display['valor_contractual'].apply(lambda x: f"${x:,.0f}")
    df_display['horas_standby'] = df_display['horas_standby'].apply(lambda x: f"{x:.1f}")
    
    st.dataframe(
        df_display[['pozo', 'cliente', 'costo_real', 'valor_contractual', 'margen_bruto', 'eficiencia_pct', 'horas_standby']],
        hide_index=True,
        use_container_width=True
    )
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN 3: RANKING DE EFICIENCIA
    # ═══════════════════════════════════════════════════════════════════
    st.markdown("### 🏆 Top 10 Pozos Menos Eficientes")
    
    df_ranking = df_pozos.sort_values('eficiencia_pct', ascending=False).head(10)
    
    col_rank1, col_rank2 = st.columns([2, 1])
    
    with col_rank1:
        fig_ranking = px.bar(
            df_ranking, 
            x='pozo', 
            y='eficiencia_pct',
            color='eficiencia_pct',
            color_continuous_scale='RdYlGn_r',
            title="Eficiencia % (mayor = menos eficiente)",
            labels={'pozo': 'Pozo', 'eficiencia_pct': 'Eficiencia %'}
        )
        fig_ranking.add_hline(y=80, line_dash="dash", line_color="green", annotation_text="80% meta")
        fig_ranking.add_hline(y=95, line_dash="dash", line_color="red", annotation_text="95% riesgo")
        st.plotly_chart(fig_ranking, use_container_width=True)
    
    with col_rank2:
        st.markdown("**Leyenda de Estado:**")
        st.success("🟢 < 80%: Muy eficiente")
        st.warning("🟡 80-95%: Normal")
        st.error("🔴 > 95%: Riesgo de pérdida")
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN 4: GRÁFICO COMPARATIVO
    # ═══════════════════════════════════════════════════════════════════
    st.markdown("### 📊 Costo Real vs Valor Contractual")
    
    fig_comparativo = px.bar(
        df_pozos.sort_values('costo_real', ascending=False),
        x='pozo',
        y=['costo_real', 'valor_contractual'],
        barmode='group',
        title="Comparación: Costo Real vs Valor Contractual por Pozo",
        labels={'value': 'USD', 'pozo': 'Pozo', 'variable': 'Tipo'},
        color_discrete_map={'costo_real': '#ef4444', 'valor_contractual': '#22c55e'}
    )
    st.plotly_chart(fig_comparativo, use_container_width=True)
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN 5: ALERTAS OPERATIVAS
    # ═══════════════════════════════════════════════════════════════════
    st.markdown("### ⚠️ Alertas Operativas")
    
    # Detectar pozos con sobrecosto
    df_alertas = df_pozos[df_pozos['costo_real'] > df_pozos['valor_contractual']]
    
    if not df_alertas.empty:
        st.error(f"🚨 {len(df_alertas)} pozo(s) con sobrecosto detectado:")
        for _, row in df_alertas.iterrows():
            sobrecosto = row['costo_real'] - row['valor_contractual']
            st.markdown(f"- **{row['pozo']}**: ${sobrecosto:,.0f} de sobrecosto ({row['eficiencia_pct']:.1f}% de eficiencia)")
    else:
        st.success("✅ No hay pozos con sobrecosto")
    
    # Detectar alto standby
    df_standby = df_pozos[df_pozos['horas_standby'] > 10]
    if not df_standby.empty:
        st.warning(f"⚠️ {len(df_standby)} pozo(s) con más de 10 horas standby:")
        for _, row in df_standby.iterrows():
            st.markdown(f"- **{row['pozo']}**: {row['horas_standby']:.1f} horas standby")


def _get_all_asignaciones():
    """Obtiene todas las asignaciones de todos los pozos"""
    # Obtener lista de pozos únicos
    all_data = asignacion_operativa_service._load_mock_data()
    return all_data.get('asignaciones', [])


def _procesar_datos_pozos(asignaciones, contratos_pozos, contratos):
    """Procesa datos y calcula métricas por pozo"""
    
    # Crear diccionario de valor contractual por pozo
    valor_por_pozo = {}
    for cp in contratos_pozos:
        if cp['estado'] == 'ACTIVO':
            contrato = financial_service.get_contrato_by_id(cp['contrato_id'])
            if contrato:
                valor_por_pozo[cp['pozo_id']] = {
                    'valor_contractual': contrato['VALOR_UNITARIO_BASE_USD'],
                    'cliente': contrato['CLIENTE'],
                    'contrato_id': cp['contrato_id']
                }
    
    # Agrupar asignaciones por pozo
    data_pozo = {}
    for asig in asignaciones:
        pozo_id = asig['id_expediente']
        if pozo_id not in data_pozo:
            data_pozo[pozo_id] = {
                'costo_real': 0,
                'horas_standby': 0,
                'horas_totales': 0
            }
        
        data_pozo[pozo_id]['costo_real'] += asig.get('costo_total_calculado', 0)
        data_pozo[pozo_id]['horas_totales'] += asig.get('horas_imputadas', 0)
        
        if asig.get('tipo_actividad') == 'STANDBY':
            data_pozo[pozo_id]['horas_standby'] += asig.get('horas_imputadas', 0)
    
    # Calcular métricas
    results = []
    for pozo_id, datos in data_pozo.items():
        valor_info = valor_por_pozo.get(pozo_id, {'valor_contractual': 0, 'cliente': 'N/A'})
        valor_contractual = valor_info['valor_contractual']
        
        margen_bruto = valor_contractual - datos['costo_real']
        
        eficiencia_pct = (datos['costo_real'] / valor_contractual * 100) if valor_contractual > 0 else 0
        
        results.append({
            'pozo': pozo_id,
            'cliente': valor_info['cliente'],
            'costo_real': datos['costo_real'],
            'valor_contractual': valor_contractual,
            'margen_bruto': margen_bruto,
            'eficiencia_pct': eficiencia_pct,
            'horas_standby': datos['horas_standby'],
            'horas_totales': datos['horas_totales']
        })
    
    return pd.DataFrame(results)


# Para testing directo
if __name__ == "__main__":
    render_dashboard_eficiencia()
