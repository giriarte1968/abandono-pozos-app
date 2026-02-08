"""pytest configuration and fixtures"""
import pytest
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_expediente_data():
    """Sample expediente data for testing"""
    return {
        "id_expediente": "EXP-TEST-001",
        "id_pozo": "X-TEST-001",
        "id_campana": "CAMP-TEST-2026",
        "responsable_tecnico": "Ing. Test"
    }
