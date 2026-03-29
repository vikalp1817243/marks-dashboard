from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from config import DATABASE_URL, CONNECT_ARGS

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args=CONNECT_ARGS,
    # --- Performance Tuning (Fix #2) ---
    # Keep 20 persistent connections in the pool (up from default 5).
    pool_size=20,
    # Allow up to 30 extra connections during traffic spikes (up from default 10).
    max_overflow=30,
    # Recycle connections every 5 minutes to prevent stale TCP sockets to TiDB Cloud.
    pool_recycle=300,
    # Verify connection is alive before handing it to a request (avoids "server gone" errors).
    pool_pre_ping=True,
)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
