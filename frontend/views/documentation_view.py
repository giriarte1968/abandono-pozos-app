import streamlit as st
import pandas as pd
from services.audit_service import AuditService
from services.evidence_service import EvidenceService

def render_view():
    st.title("📂 Gestión Documental & Guías")
    st.markdown("Centro de documentación técnica, regulatoria y repositorio de evidencias certificadas.")

    tab1, tab2, tab3 = st.tabs([
        "📖 Manual de Proceso",
        "⚖️ Guías Regulatorias",
        "📎 Repositorio de Evidencias"
    ])

    with tab1:
        st.subheader("Ciclo de Vida del Abandono (P&A)")
        st.info("El proceso se rige bajo la normativa SEC 2024 y estándares IOGP.")
        
        stages = [
            {"Etapa": "1. Inicio Trámite", "Descripción": "Carga de la Justificación Técnica y aprobación regulatoria inicial."},
            {"Etapa": "2. Planificación", "Descripción": "Asignación de recursos (Personal, Equipos, Logística) mediante señal DTM."},
            {"Etapa": "3. Ejecución", "Descripción": "Fase operativa con reporte de Parte Diario y telemetría en tiempo real."},
            {"Etapa": "4. Incidencias", "Descripción": "Gestión de bloqueos operativos por fallas HSE o técnicas."},
            {"Etapa": "5. Auditoría", "Descripción": "Carga y certificación de evidencias físicas (fotos/docs) con hash inmutable."},
            {"Etapa": "6. Cierre Técnico", "Descripción": "Validación final, firma digital y exportación de dossier defendible."}
        ]
        st.table(pd.DataFrame(stages))
        
        st.markdown("""
        ### Reglas de Seguridad (HSE)
        - **Aptitud Médica**: Validada automáticamente contra base corporativa.
        - **Inducción**: Requisito bloqueante para acceso a locación.
        - **Checklist de Izaje**: Obligatorio para maniobras de Pulling.
        """)

    with tab2:
        st.subheader("Marco Legal & Estándares")
        
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.markdown("#### Argentinas (SEC)")
                st.write("- Res. 05/2023: Abandono de Pozos")
                st.write("- Res. 12/2024: Integridad de Presión")
                st.button("Ver PDF (Simulado)", key="btn_sec")
        
        with col2:
            with st.container(border=True):
                st.markdown("#### Internacionales (IOGP)")
                st.write("- IOGP 485: Well Integrity Management")
                st.write("- ISO 16530-1: Well Life Cycle")
                st.button("Ver PDF (Simulado)", key="btn_iogp")

    with tab3:
        st.subheader("Buscador Global de Evidencias")
        st.caption("Recuperación de documentos certificados en todos los pozos activos.")
        
        api = st.session_state.get('api_client')
        audit = st.session_state.get('audit_service') or AuditService()
        evidence_svc = EvidenceService(audit_service=audit)
        
        # Obtener pozos dinámicamente
        all_well_ids = []
        if api:
            all_wells = api.get_projects()
            all_well_ids = [p['id'] for p in all_wells]
        else:
            all_well_ids = ["X-123", "Z-789", "M-555", "A-321"]
        
        all_evidence = []
        for wid in all_well_ids:
            well_ev = evidence_svc.get_evidence_for_well(wid)
            for e in well_ev:
                e['well_id'] = wid
                all_evidence.append(e)
        
        if all_evidence:
            df_ev = pd.DataFrame(all_evidence)
            # Renombrar para mayor claridad
            df_ev = df_ev.rename(columns={
                'well_id': 'Pozo',
                'nombre_archivo': 'Archivo',
                'etapa_workflow': 'Etapa',
                'timestamp_carga': 'Fecha Carga',
                'hash_sha256': 'Certificado (SHA256)'
            })
            
            st.dataframe(
                df_ev[['Pozo', 'Etapa', 'Archivo', 'Fecha Carga', 'Certificado (SHA256)']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("No se encontraron evidencias digitales registradas en el sistema.")
