from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os

app = FastAPI(title="P&A System API", version="1.0.0")

# --- Temporal Client Setup (Mock for now, will connect to Server) ---
# from temporalio.client import Client
# client = await Client.connect("localhost:7233")

# --- Pydantic Models ---
class ProjectSignal(BaseModel):
    project_id: str
    signal_name: str
    payload: dict

class DailyReport(BaseModel):
    project_id: str
    content: dict

# --- Endpoints ---

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "backend-api"}

@app.post("/signals/generic")
async def send_signal(signal: ProjectSignal):
    """
    Envia una señal genérica a un Workflow de Temporal.
    """
    # handle = client.get_workflow_handle(signal.project_id)
    # await handle.signal(signal.signal_name, signal.payload)
    return {"status": "signal_sent", "target": signal.project_id}

@app.post("/reports/daily")
async def submit_daily_report(report: DailyReport):
    """
    Endpoint específico para Partes Diarios.
    Dispara la señal 'ParteDiario' al workflow.
    """
    # handle = client.get_workflow_handle(report.project_id)
    # await handle.signal("ParteDiario", report.content)
    return {"status": "report_received", "id": report.project_id}

@app.get("/projects/{project_id}/status")
async def get_project_status(project_id: str):
    """
    Consulta el estado actual del Workflow via Query.
    """
    # handle = client.get_workflow_handle(project_id)
    # status = await handle.query("getEstadoActual")
    # return status
    return {
        "id": project_id, 
        "workflow_status": "MOCK_EXECUTING", 
        "current_step": "EJECUCION_CAMPO"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
