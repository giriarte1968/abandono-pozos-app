import streamlit as st

def render_stepper(current_status_code):
    """
    Renderiza una barra de progreso visual (Stepper).
    
    NOTA: Este componente NO define el orden del proceso. 
    Solo visualiza el estado actual que reporta el Workflow de Temporal.
    """
    
    # Mapeo de Estados Internos -> Pasos Visuales
    # El orden es puramente visual para el usuario
    steps = [
        {"code": "INIT", "label": "Inicio Trámite"},
        {"code": "PLANNING", "label": "Planificación"},
        {"code": "LOGISTICS", "label": "Logística (DTM)"},
        {"code": "EXECUTION", "label": "Ejecución"},
        {"code": "CLOSING", "label": "Cierre"}
    ]
    
    # Determinar índice actual basado en mapeo simple
    # En producción esto vendría de una lógica de negocio más robusta
    current_idx = 0
    
    # Mapeo simple de los estados del Mock a los pasos visuales
    status_map = {
        "WAITING_JUSTIFICATION": 0,
        "PLANIFICADO": 1,
        "WAITING_DTM_ASSIGNMENT": 2,
        "EN_EJECUCION": 3,
        "WAITING_DAILY_REPORT": 3,
        "BLOCKED_BY_INCIDENT": 3, # Se queda en ejecución pero rojo
        "WAITING_FINAL_APPROVAL": 4,
        "FINALIZADO": 4
    }
    
    # Intentar buscar por estado de proyecto o estado de workflow
    # Aquí asumimos que recibimos algo mapeable
    current_idx = status_map.get(current_status_code, 0)

    # Renderizado CSS custom para simular stepper
    st.markdown("""
<style>
    .step-container {
        display: flex;
        justify_content: space-between;
        margin-bottom: 20px;
    }
    .step {
        text-align: center;
        flex: 1;
        position: relative;
    }
    .step-circle {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background-color: #e0e0e0;
        color: #666;
        display: flex;
        align-items: center;
        justify_content: center;
        margin: 0 auto 5px;
        font-weight: bold;
        z-index: 2;
        position: relative;
    }
    .step.active .step-circle {
        background-color: #007bff;
        color: white;
        border: 2px solid #0056b3;
    }
    .step.completed .step-circle {
        background-color: #28a745;
        color: white;
    }
    .step-line {
        position: absolute;
        top: 15px;
        left: -50%;
        width: 100%;
        height: 2px;
        background-color: #e0e0e0;
        z-index: 1;
    }
    .step:first-child .step-line {
        display: none;
    }
    .step.completed .step-line {
        background-color: #28a745;
    }
    .step-label {
        font-size: 0.8em;
        color: #666;
    }
    .step.active .step-label {
        color: #007bff;
        font-weight: bold;
    }
</style>
    """, unsafe_allow_html=True)
    
    html_steps = '<div class="step-container">'
    
    for idx, step in enumerate(steps):
        css_class = ""
        if idx < current_idx:
            css_class = "completed"
        elif idx == current_idx:
            css_class = "active"
            
        html_steps += f'<div class="step {css_class}"><div class="step-line"></div><div class="step-circle">{idx + 1}</div><div class="step-label">{step["label"]}</div></div>'
    
    html_steps += '</div>'
    
    st.markdown(html_steps, unsafe_allow_html=True)
