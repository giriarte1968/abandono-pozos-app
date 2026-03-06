"""
Vista de Análisis Operacional - Root Cause Analysis
Muestra análisis de eficiencia y detección de patrones de ineficiencia por pozo.
"""

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.analisis_operacional_service import analisis_operacional_service


def render_analisis_operacional():
    """Renderiza la vista de análisis operacional"""
    
    st.title("🔍 Análisis Operacional - Root Cause Analysis")
    st.markdown("---")
    
    # Permisos
    user_role = st.session_state.get('user_role', 'Usuario')
    if user_role not in ['Gerente', 'Supervisor', 'Ingeniero Campo', 'Administrativo']:
        st.error("No tienes acceso a este módulo.")
        return
    
    # Selector de pozo
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown("### Seleccionar Pozo")
        pozo_seleccionado = st.selectbox(
            "Pozo a analizar",
            ['X-123', 'P-001', 'A-321'],
            index=0
        )
    
    # Ejecutar análisis
    analisis = analisis_operacional_service.analizar_eficiencia_pozo(pozo_seleccionado)
    
    if 'error' in analisis:
        st.error(analisis['error'])
        return
    
    # Mostrar resultados
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN 1: KPIs DE ANÁLISIS
    # ═══════════════════════════════════════════════════════════════════
    st.markdown("### 📊 Métricas del Período")
    
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    
    with col_k1:
        st.metric("Días Analizados", f"{analisis['periodo_dias']}")
    with col_k2:
        st.metric("Horas Totales", f"{analisis['horas_totales']:.1f}")
    with col_k3:
        st.metric("Horas Standby", f"{analisis['horas_standby']:.1f}")
    with col_k4:
        patrones_count = len(analisis['patrones'])
        delta_color = "inverse" if patrones_count > 0 else "normal"
        st.metric("Patrones Detectados", f"{patrones_count}", 
                  delta="⚠️" if patrones_count > 0 else "✅", delta_color=delta_color)
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN 2: PROMEDIOS DE TELEMETRÍA
    # ═══════════════════════════════════════════════════════════════
    st.markdown("### 📈 Parámetros de Telemetría (Promedio)")
    
    promedios = analisis['promedios']
    
    col_t1, col_t2, col_t3, col_t4 = st.columns(4)
    
    with col_t1:
        hl = promedios['hook_load']
        hl_color = "inverse" if hl > 22 else "normal"
        st.metric("Hook Load (tn)", f"{hl:.1f}", delta=f"{hl-22:.1f}" if hl > 22 else None, delta_color=hl_color)
    with col_t2:
        ap = promedios['annular_pressure']
        ap_color = "inverse" if ap > 100 else "normal"
        st.metric("Presión Anular (psi)", f"{ap:.0f}", delta=f"{ap-100:.0f}" if ap > 100 else None, delta_color=ap_color)
    with col_t3:
        ts = promedios['trip_speed']
        ts_color = "inverse" if ts < 150 else "normal"
        st.metric("Trip Speed (m/h)", f"{ts:.0f}", delta=f"{ts-150:.0f}" if ts < 150 else None, delta_color=ts_color)
    with col_t4:
        pp = promedios['pump_pressure']
        pp_color = "inverse" if pp > 1000 else "normal"
        st.metric("Pump Pressure (psi)", f"{pp:.0f}", delta=f"{pp-1000:.0f}" if pp > 1000 else None, delta_color=pp_color)
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN 3: PATRONES DETECTADOS
    # ═══════════════════════════════════════════════════════════════════
    st.markdown("### ⚠️ Factores de Ineficiencia Detectados")
    
    if analisis['patrones']:
        for i, patron in enumerate(analisis['patrones'], 1):
            severity = patron.get('severidad', 'medio')
            
            if severity == 'alto':
                st.error(f"**{i}. {patron['nombre']}** (CRÍTICO)")
            elif severity == 'medio':
                st.warning(f"**{i}. {patron['nombre']}** (MEDIO)")
            else:
                st.info(f"**{i}. {patron['nombre']}**")
            
            with st.container():
                col_p1, col_p2 = st.columns([2, 1])
                
                with col_p1:
                    st.write(f"📊 **Valor:** {patron['valor']:.1f} (umbral: {patron['umbral']})")
                    st.write(f"🔍 **Causa probable:** {patron['causa_probable']}")
                
                with col_p2:
                    st.write(f"⏱️ **Impacto:** +{patron['impacto_horas']} horas")
                    st.write(f"💰 **Costo:** +{patron['impacto_costo_pct']}%")
            
            st.divider()
    else:
        st.success("✅ No se detectaron patrones de ineficiencia significativos.")
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN 4: IMPACTO TOTAL
    # ═══════════════════════════════════════════════════════════════════
    st.markdown("### 📉 Impacto Estimado Total")
    
    impacto = analisis['impacto']
    
    col_i1, col_i2, col_i3 = st.columns(3)
    
    with col_i1:
        es_critico = impacto['es_critico']
        st.metric(
            "Horas Extras Estimadas", 
            f"+{impacto['horas_extras_estimadas']:.1f} hrs",
            delta="CRÍTICO" if es_critico else "Normal",
            delta_color="inverse" if es_critico else "normal"
        )
    with col_i2:
        st.metric(
            "Costo Adicional (%)", 
            f"+{impacto['costo_adicional_estimado_pct']:.1f}%"
        )
    with col_i3:
        st.metric(
            "Costo Adicional (USD)", 
            f"+${impacto['costo_adicional_estimado_usd']:,.0f}"
        )
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN 5: RECOMENDACIONES
    # ═══════════════════════════════════════════════════════════════════
    st.markdown("### 💡 Recomendaciones")
    
    if analisis['patrones']:
        recomendaciones_set = set()
        
        for p in analisis['patrones']:
            if p['tipo'] == 'hook_load_elevado':
                recomendaciones_set.add("- Reducir carga de izaje a <22 tn")
            elif p['tipo'] == 'presion_anular_alta':
                recomendaciones_set.add("- Revisar estado de wellbore y presión de kill line")
            elif p['tipo'] == 'tripping_lento':
                recomendaciones_set.add("- Optimizar velocidad de tripping")
            elif p['tipo'] == 'standby_alto':
                recomendaciones_set.add("- Revisar logística y planificación de recursos")
        
        for rec in recomendaciones_set:
            st.write(rec)
    else:
        st.info("Continuar con prácticas operativas actuales.")
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN 6: REPORTE COMPLETO
    # ═══════════════════════════════════════════════════════════════════
    with st.expander("📄 Ver Reporte Completo (Root Cause Analysis)"):
        reporte = analisis_operacional_service.generar_reporte_root_cause(pozo_seleccionado)
        st.code(reporte, language="markdown")


# Para testing directo
if __name__ == "__main__":
    render_analisis_operacional()
