import streamlit as st
import pandas as pd
import altair as alt

def render_view():
    """
    Dashboard Operativo - Launcher y Vista Principal
    Punto de entrada unificado para todas las operaciones de AbandonPro
    """
    api = st.session_state['api_client']
    stats = api.get_dashboard_stats()
    
    st.title("🏠 Dashboard Operativo - AbandonPro")
    st.markdown(f"## Sistema de Gestión de Abandono de Pozos")
    st.markdown(f"*Datos actualizados: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}*")
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN 1: MÓDULOS DEL SISTEMA (Launcher)
    # ═══════════════════════════════════════════════════════════════════
    st.markdown("### 📱 Acceso a Módulos")
    
    col_mod1, col_mod2, col_mod3, col_mod4 = st.columns(4)
    
    with col_mod1:
        with st.container(border=True):
            st.markdown("#### 📋 Expediente Digital")
            st.markdown("Gestión de proyectos y seguimiento operativo")
            if st.button("Ir a Proyectos", key="mod_proyectos"):
                st.session_state['current_page'] = 'Proyectos'
                st.rerun()
    
    with col_mod2:
        with st.container(border=True):
            st.markdown("#### 💰 Finanzas")
            st.markdown("Backlog, certificaciones y flujo de fondos")
            if st.button("Ir a Finanzas", key="mod_finanzas"):
                st.session_state['current_page'] = 'Dashboard Financiero'
                st.rerun()
    
    with col_mod3:
        with st.container(border=True):
            st.markdown("#### 📊 Eficiencia")
            st.markdown("Costos reales vs contractuales")
            if st.button("Ir a Eficiencia", key="mod_eficiencia"):
                st.session_state['current_page'] = 'Eficiencia Operativa'
                st.rerun()
    
    with col_mod4:
        with st.container(border=True):
            st.markdown("#### 🔍 Análisis Operacional")
            st.markdown("Root Cause Analysis")
            if st.button("Ir a Análisis", key="mod_analisis"):
                st.session_state['current_page'] = 'Análisis Operacional'
                st.rerun()
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN 2: KPIs OPERATIVOS EN TIEMPO REAL
    # ═══════════════════════════════════════════════════════════════════
    st.markdown("### 📈 Estado Operativo Actual")
    
    # Obtener datos reales
    from services.financial_service_mock import financial_service
    from services.asignacion_operativa_service import asignacion_operativa_service
    from services.analisis_operacional_service import analisis_operacional_service
    
    kpis_fin = financial_service.get_kpis_dashboard()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Pozos Activos", stats['total_activos'], delta=f"+{stats['en_ejecucion']} en ejecución")
    with col2:
        st.metric("En Ejecución", stats['en_ejecucion'])
    with col3:
        st.metric("Backlog Total", f"${kpis_fin['backlog_contractual']/1000000:.1f}M")
    with col4:
        alertas = stats.get('alertas_activas', 0)
        st.metric("Alertas Activas", alertas, delta_color="inverse" if alertas > 0 else "normal")
    
    # Segunda fila de KPIs
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric("Avance Físico", f"{kpis_fin['avance_fisico_pct']:.1f}%")
    with col6:
        st.metric("Avance Financiero", f"{kpis_fin['avance_financiero_pct']:.1f}%")
    with col7:
        st.metric("Días Cobertura Caja", f"{kpis_fin['dias_cobertura_caja']:.0f}")
    with col8:
        st.metric("Bloqueados", stats.get('bloqueados', 0), delta_color="inverse")
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN 3: ANÁLISIS DE EFICIENCIA (Del nuevo módulo)
    # ═══════════════════════════════════════════════════════════════════
    st.markdown("### ⚡ Análisis de Eficiencia - Top Pozos")
    
    try:
        resumen_eficiencia = analisis_operacional_service.get_resumen_global()
        
        if resumen_eficiencia:
            df_ef = pd.DataFrame(resumen_eficiencia)
            
            # Mostrar como tabla
            col_ef1, col_ef2 = st.columns([2, 1])
            
            with col_ef1:
                st.dataframe(
                    df_ef[['pozo', 'patrones_encontrados', 'impacto_horas', 'impacto_costo_pct']].rename(columns={
                        'pozo': 'Pozo',
                        'patrones_encontrados': 'Patrones',
                        'impacto_horas': 'Hrs Extra',
                        'impacto_costo_pct': '% Costo'
                    }),
                    hide_index=True,
                    use_container_width=True
                )
            
            with col_ef2:
                # Alertas críticas
                criticos = [p for p in resumen_eficiencia if p.get('es_critico')]
                if criticos:
                    st.error(f"⚠️ {len(criticos)} pozo(s) en estado CRÍTICO")
                    for c in criticos:
                        st.write(f"- **{c['pozo']}**: +{c['impacto_horas']:.1f} hrs")
                else:
                    st.success("✅ Sin alertas críticas")
        else:
            st.info("No hay datos de análisis disponibles")
    except Exception as e:
        st.warning(f"Análisis no disponible: {e}")
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN 4: RESUMEN DE FLOTA Y RECURSOS
    # ═══════════════════════════════════════════════════════════════════
    col_flota1, col_flota2 = st.columns(2)
    
    with col_flota1:
        st.markdown("#### 🚜 Estado de Equipos Críticos")
        
        # Datos de recursos
        equipos = api._generate_mock_equipment()
        
        # Contar por estado
        estado_equipos = {}
        for eq in equipos:
            status = eq.get('status', 'UNKNOWN')
            estado_equipos[status] = estado_equipos.get(status, 0) + 1
        
        # Mostrar como métricas
        col_eq1, col_eq2, col_eq3 = st.columns(3)
        with col_eq1:
            operativo = estado_equipos.get('OPERATIVO', 0) + estado_equipos.get('DISPONIBLE', 0)
            st.metric("Operativos", operativo)
        with col_eq2:
            st.metric("En Mantenimiento", estado_equipos.get('MANTENIMIENTO', 0))
        with col_eq3:
            falla = estado_equipos.get('FALLA CRITICA', 0)
            st.metric("Falla Crítica", falla, delta_color="inverse" if falla > 0 else "normal")
    
    with col_flota2:
        st.markdown("#### ⚠️ Alertas Recientes")
        
        # Obtener alertas de proyectos
        proyectos = api.get_all_wells()
        alertas = []
        
        for p in proyectos:
            if p.get('estado_proyecto') == 'BLOQUEADO':
                alertas.append(f"**{p['id']}**: {p.get('proximo_hito', 'Bloqueado')}")
        
        if alertas:
            for a in alertas[:3]:
                st.warning(a)
        else:
            st.success("Sin alertas operativas")
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN 5: INTEGRIDAD REGULATORIA
    # ═══════════════════════════════════════════════════════════════════
    st.markdown("#### 🛡️ Integridad Regulatoria")
    
    from services.audit_service import AuditService
    audit = AuditService(api.db)
    is_ok, errors = audit.verify_integrity()
    
    col_audit1, col_audit2 = st.columns([1, 2])
    if is_ok:
        col_audit1.success("✅ CADENA VÁLIDA")
        col_audit2.info("Todos los hashes de auditoría coinciden. Expedientes íntegros.")
    else:
        col_audit1.error(f"🚨 {len(errors)} ERRORES")
        col_audit2.warning(f"Inconsistencias detectadas: {errors[0] if errors else 'Revisar logs'}")
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════════
    # FOOTER
    # ═══════════════════════════════════════════════════════════════════
    st.caption("""
    🏭 **AbandonPro v2.1** - Sistema de Gestión de Abandono de Pozos
    
    Módulos disponibles:
    📋 Proyectos | 💰 Finanzas | 📊 Eficiencia | 🔍 Análisis Operacional | 
    📦 Logística | 🔧 Cementación | 📁 Cierre Técnico | 🛡️ Cumplimiento
    """)
