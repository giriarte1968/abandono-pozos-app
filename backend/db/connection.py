"""Database connection management"""
import os
import aiomysql
from typing import Optional


class Database:
    """Database connection manager"""
    
    def __init__(self):
        self.pool: Optional[aiomysql.Pool] = None
    
    async def connect(self):
        """Create database connection pool"""
        self.pool = await aiomysql.create_pool(
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", 3306)),
            user=os.getenv("MYSQL_USER", "pna_user"),
            password=os.getenv("MYSQL_PASSWORD", "pna_pass"),
            db=os.getenv("MYSQL_DATABASE", "pna_system"),
            autocommit=True,
            minsize=1,
            maxsize=10
        )
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
    
    async def execute(self, query: str, params=None):
        """Execute a query"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params or ())
                return cur
    
    async def fetch_one(self, query: str, params=None):
        """Fetch one row"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, params or ())
                return await cur.fetchone()
    
    async def fetch_all(self, query: str, params=None):
        """Fetch all rows"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, params or ())
                return await cur.fetchall()


# Global database instance
db = Database()


async def get_db_connection():
    """Get database connection"""
    if not db.pool:
        await db.connect()
    return db
