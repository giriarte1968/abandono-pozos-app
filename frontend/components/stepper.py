import streamlit as st

def render_stepper(current_status_code):
    steps = [
        {"code": "INIT", "label": "Inicio"},
        {"code": "PLANNING", "label": "Planificación"},
        {"code": "LOGISTICS", "label": "Logística"},
        {"code": "EXECUTION", "label": "Ejecución"},
        {"code": "CLOSING", "label": "Cierre"}
    ]
    
    status_map = {
        "WAITING_JUSTIFICATION": 0,
        "PLANIFICADO": 1,
        "WAITING_DTM_ASSIGNMENT": 2,
        "EN_EJECUCION": 3,
        "WAITING_DAILY_REPORT": 3,
        "BLOCKED_BY_INCIDENT": 3,
        "WAITING_FINAL_APPROVAL": 4,
        "FINALIZADO": 4
    }
    
    current_idx = status_map.get(current_status_code, 0)

    st.markdown("""
<style>
    .stepper-wrapper {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin: 30px 0 40px 0;
        padding: 0 20px;
    }
    .step-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        flex: 1;
        position: relative;
    }
    .step-circle {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: linear-gradient(145deg, #2a2a3a, #1a1a2a);
        border: 3px solid #3a3a4a;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        z-index: 2;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .step-item.completed .step-circle {
        background: linear-gradient(145deg, #22c55e, #16a34a);
        border-color: #22c55e;
        box-shadow: 0 4px 20px rgba(34, 197, 94, 0.4);
    }
    .step-item.active .step-circle {
        background: linear-gradient(145deg, #3b82f6, #2563eb);
        border-color: #3b82f6;
        box-shadow: 0 4px 25px rgba(59, 130, 246, 0.5);
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { box-shadow: 0 4px 25px rgba(59, 130, 246, 0.5); }
        50% { box-shadow: 0 4px 35px rgba(59, 130, 246, 0.8); }
    }
    .step-connector {
        position: absolute;
        top: 25px;
        left: calc(50% + 30px);
        width: calc(100% - 60px);
        height: 4px;
        background: linear-gradient(90deg, #3a3a4a, #2a2a3a);
        z-index: 1;
        border-radius: 2px;
    }
    .step-item.completed .step-connector {
        background: linear-gradient(90deg, #22c55e, #16a34a);
    }
    .step-item:last-child .step-connector {
        display: none;
    }
    .step-label {
        margin-top: 12px;
        font-size: 13px;
        font-weight: 500;
        color: #666;
        text-align: center;
        transition: all 0.3s ease;
    }
    .step-item.completed .step-label {
        color: #22c55e;
        font-weight: 600;
    }
    .step-item.active .step-label {
        color: #3b82f6;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)
    
    html = '<div class="stepper-wrapper">'
    
    for idx, step in enumerate(steps):
        css_class = ""
        icon = ""
        
        if idx < current_idx:
            css_class = "completed"
            icon = "✓"
        elif idx == current_idx:
            css_class = "active"
            icon = "◆"
        else:
            icon = "○"
        
        html += f'''
        <div class="step-item {css_class}">
            <div class="step-connector"></div>
            <div class="step-circle">{icon}</div>
            <div class="step-label">{step["label"]}</div>
        </div>'''
    
    html += '</div>'
    
    st.markdown(html, unsafe_allow_html=True)
