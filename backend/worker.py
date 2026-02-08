"""Temporal Worker for P&A System"""
import asyncio
import logging
from temporalio.client import Client
from temporalio.worker import Worker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Main worker entry point"""
    logger.info("Starting P&A Temporal Worker...")
    
    # Connect to Temporal
    import os
    temporal_host = os.getenv("TEMPORAL_HOST", "temporal")
    temporal_port = os.getenv("TEMPORAL_PORT", "7233")
    connection_str = f"{temporal_host}:{temporal_port}"
    logger.info(f"Connecting to Temporal at {connection_str}...")
    client = await Client.connect(connection_str)
    
    logger.info("Connected to Temporal server")
    
    # TODO: Import workflows and activities when implemented
    # from backend.workflows.abandono_workflow import AbandonoPozoWorkflow
    # from backend.activities import (
    #     registrar_evento_auditoria,
    #     evaluar_habilitacion_operativa,
    #     ...
    # )
    
    # Create worker
    worker = Worker(
        client,
        task_queue="pna-tasks",
        workflows=[],  # Will add workflows here
        activities=[],  # Will add activities here
    )
    
    logger.info("Worker configured on task queue 'pna-tasks'")
    logger.info("Worker running... (press Ctrl+C to stop)")
    
    # Run worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
