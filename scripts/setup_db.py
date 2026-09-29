"""
Module   : DB Setup Script
Owner    : Database Engineer
Purpose  : Initializes DB schema + pgvector extension.
"""

import asyncio
import sys
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import settings
from backend.database.connection import init_db


async def main():
    print(f"[setup_db] Using database: {settings.database_url}")
    print("[setup_db] Initializing database...")
    await init_db()
    print("[setup_db] Database initialized successfully!")


if __name__ == "__main__":
    asyncio.run(main())
