import sys
from pathlib import Path

ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest


def _reset_singletons():
    import backend.dependencies as deps
    deps._dialogue_manager = None
    deps._notification_service = None
    deps._ocr_service = None
    deps._asr_service = None
    deps._tts_service = None
    deps._redflag_detector = None


@pytest.fixture(autouse=True)
def reset_singletons():
    _reset_singletons()
    yield
    _reset_singletons()


@pytest.fixture
def temp_db_url():
    return "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session(temp_db_url):
    from backend.database.connection import get_engine, get_session_factory, init_db
    engine = get_engine(temp_db_url)
    await init_db(engine)
    SessionLocal = get_session_factory(engine)
    async with SessionLocal() as session:
        yield session
    await engine.dispose()
