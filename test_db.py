import asyncio
import asyncpg

DATABASE_URL = "postgresql://kufar:Im3W89N0LHP2j9VeMUN9EGwG9xuG8c8K@dpg-d8pevu4vikkc739ijib0-a.oregon-postgres.render.com/kufar"

async def main():
   
    conn = await asyncpg.connect(
        dsn=DATABASE_URL,
        ssl="require"
    )

    version = await conn.fetchval("SELECT version();")

    print(version)

    await conn.close()

asyncio.run(main())