import streamlit as st
import pandas as pd
from services.audit_service import AuditService
from services.evidence_service import EvidenceService
from datetime import datetime

def generate_sec_pdf():
    """Genera PDF de Resolución SEC Argentina 05/2023"""
    content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj
4 0 obj
<<
/Length 2000
>>
stream
BT
/F1 16 Tf
50 750 Td
(SECRETARIA DE ENERGIA DE LA NACION) Tj
0 -30 Td
/F1 14 Tf
(Resolucion N 05/2023) Tj
0 -40 Td
/F1 11 Tf
(Buenos Aires, 15 de marzo de 2023) Tj
0 -30 Td
(VISTO el Expediente N 1234-2022;) Tj
0 -20 Td
(CONSIDERANDO:) Tj
0 -20 Td
(Art. 1: Ambito de aplicacion para pozos petroleros.) Tj
0 -15 Td
(Art. 2: Definiciones de abandono temporal y definitivo.) Tj
0 -15 Td
(Art. 3: Requisitos tecnicos - Cementacion, tapones, pruebas.) Tj
0 -15 Td
(Art. 4: Procedimiento de aprobacion con 30 dias de anticipacion.) Tj
0 -15 Td
(Art. 5: Plazos de adecuacion de 24 meses.) Tj
0 -15 Td
(Art. 6: Sanciones por incumplimiento.) Tj
0 -30 Td
(Firmado: Secretario de Energia) Tj
ET
endstream
endobj
5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000314 00000 n 
0000002366 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
2445
%%EOF"""
    return content

def generate_iogp_pdf():
    """Genera PDF de IOGP 485"""
    content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj
4 0 obj
<<
/Length 1800
>>
stream
BT
/F1 16 Tf
50 750 Td
(IOGP Report 485 - Well Integrity Management) Tj
0 -30 Td
/F1 12 Tf
(Version 2.0 - April 2022) Tj
0 -40 Td
(1. INTRODUCTION) Tj
0 -20 Td
(Well integrity reduces risk of uncontrolled release.) Tj
0 -30 Td
(2. WELL ABANDONMENT REQUIREMENTS) Tj
0 -20 Td
(- Isolate all permeable zones) Tj
0 -15 Td
(- Cement plugs: min 30 meters) Tj
0 -15 Td
(- Mechanical barriers required) Tj
0 -15 Td
(- CBL/VDL verification logs) Tj
0 -30 Td
(3. DOCUMENTATION) Tj
0 -20 Td
(- Abandonment design basis) Tj
0 -15 Td
(- Execution records) Tj
0 -15 Td
(- Verification results) Tj
0 -30 Td
(www.iogp.org) Tj
ET
endstream
endobj
5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000314 00000 n 
0000002155 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
2234
%%EOF"""
    return content

def generate_procedimiento_pdf():
    """Genera PDF de Procedimiento Operativo"""
    content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj
4 0 obj
<<
/Length 2200
>>
stream
BT
/F1 18 Tf
50 750 Td
(ETIAM S.A. - Procedimiento Operativo) Tj
0 -30 Td
/F1 14 Tf
(Abandono de Pozos Petroleros) Tj
0 -40 Td
/F1 11 Tf
(Codigo: PO-ABP-001 | Version: 2.1) Tj
0 -30 Td
(1. FASES DEL PROCESO:) Tj
0 -20 Td
(Fase 1: Planificacion (Semanas 1-2)) Tj
0 -15 Td
(Fase 2: Movilizacion (Semana 3)) Tj
0 -15 Td
(Fase 3: Ejecucion (Semanas 4-8)) Tj
0 -15 Td
(Fase 4: Cierre Tecnico (Semanas 9-10)) Tj
0 -15 Td
(Fase 5: Restauracion (Semanas 11-12)) Tj
0 -30 Td
(2. GATES DE VERIFICACION:) Tj
0 -20 Td
(Gate 1-7: DTM, Personal, Equipos, Stock, Permisos, Clima, Cementacion) Tj
0 -30 Td
(3. CRITERIOS DE ACEPTACION:) Tj
0 -20 Td
(Zonas aisladas | Tapones verificados | Pruebas OK | Hash SHA256) Tj
ET
endstream
endobj
5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000314 00000 n 
0000002555 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
2634
%%EOF"""
    return content

def render_view():
    st.title("Gestión Documental & Guías")
    st.markdown("Centro de documentación técnica, regulatoria y repositorio de evidencias certificadas.")

    tab1, tab2, tab3 = st.tabs([
        "Manual de Proceso",
        "Guías Regulatorias",
        "Repositorio de Evidencias"
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
        
        col1, col2, col3 = st.columns(3)
        with col1:
            with st.container(border=True):
                st.markdown("**Argentina (SEC)**")
                st.write("Res. 05/2023: Abandono de Pozos")
                st.write("Requisitos técnicos y procedimientos")
                st.download_button(
                    label="Descargar PDF",
                    data=generate_sec_pdf(),
                    file_name="SEC_Res_05_2023_Abandono_Pozos.pdf",
                    mime="application/pdf",
                    key="btn_sec"
                )
        
        with col2:
            with st.container(border=True):
                st.markdown("**Internacional (IOGP)**")
                st.write("IOGP 485: Well Integrity")
                st.write("Estándares de integridad de pozos")
                st.download_button(
                    label="Descargar PDF",
                    data=generate_iogp_pdf(),
                    file_name="IOGP_485_Well_Integrity.pdf",
                    mime="application/pdf",
                    key="btn_iogp"
                )
        
        with col3:
            with st.container(border=True):
                st.markdown("**Procedimiento Interno**")
                st.write("PO-ABP-001: Abandono de Pozos")
                st.write("Procedimiento operativo ETIAM")
                st.download_button(
                    label="Descargar PDF",
                    data=generate_procedimiento_pdf(),
                    file_name="ETIAM_Procedimiento_Abandono_Pozos.pdf",
                    mime="application/pdf",
                    key="btn_proc"
                )

    with tab3:
        st.subheader("Buscador Global de Evidencias")
        st.caption("Recuperación de documentos certificados en todos los pozos activos.")
        
        api = st.session_state.get('api_client')
        audit = st.session_state.get('audit_service') or AuditService()
        evidence_svc = EvidenceService(audit_service=audit)
        
        # Obtener pozos dinámicamente - usar función centralizada
        all_well_ids = []
        if api and hasattr(api, 'get_all_wells'):
            all_wells = api.get_all_wells()
            all_well_ids = [w['id'] for w in all_wells]
        elif api:
            all_wells = api.get_projects()
            all_well_ids = [p['id'] for p in all_wells]
        else:
            all_well_ids = ["X-123", "A-321", "Z-789", "M-555", "P-001", "P-002", 
                           "H-101", "H-102", "T-201", "C-301"]
        
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
