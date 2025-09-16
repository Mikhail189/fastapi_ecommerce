from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import DATABASE_URL

#engine = create_async_engine('postgresql+asyncpg://ecommerce:postgres@localhost:5432/ecommerce', echo=True)
# engine = create_async_engine('postgresql+asyncpg://postgres_user:postgres_password@185.250.44.62:5432/postgres_database',
#                              echo=False)
# engine = create_async_engine('postgresql+asyncpg://postgres_user:postgres_password@185.250.44.62:5433/postgres_test_database',
#                               echo=False)
engine = create_async_engine(DATABASE_URL, echo=False)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class Base(DeclarativeBase):
    pass
