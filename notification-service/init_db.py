"""
Initialize the notification service database.
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import init_database

async def main():
    """Initialize the database."""
    print("Initializing notification service database...")
    await init_database()
    print("Database initialized successfully!")

if __name__ == "__main__":
    asyncio.run(main())