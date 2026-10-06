# =============================================================================
# CyberLearn — Configuration pytest
# =============================================================================

import pytest
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Event loop partagé pour tous les tests async."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
