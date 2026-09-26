"""MongoDB connection and index setup."""

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
client: AsyncIOMotorClient | None = None
db = None


async def connect_to_mongo():
    """Called once when FastAPI starts."""
    global client, db
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.database_name]

    # Fail fast if the connection string or password is wrong
    await client.admin.command("ping")

    await create_indexes()
    print(f"MongoDB connected: {settings.database_name}")


async def close_mongo_connection():
    """Called once when FastAPI shuts down."""
    if client:
        client.close()
        print("MongoDB connection closed")


async def create_indexes():
    """Indexes make queries fast and enforce uniqueness. Safe to re-run."""
    await db.doctors.create_index("email", unique=True)
    await db.doctors.create_index("googleId", sparse=True)

    await db.patients.create_index([("doctorId", 1), ("createdAt", -1)])

    await db.analyses.create_index([("doctorId", 1), ("createdAt", -1)])
    await db.analyses.create_index([("patientId", 1), ("createdAt", -1)])


def get_database():
    """Used by routes and services to reach the collections."""
    return db