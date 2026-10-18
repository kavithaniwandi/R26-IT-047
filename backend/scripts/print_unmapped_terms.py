from __future__ import annotations

import argparse
import asyncio

from app.services.mongo_service import close_mongo, connect_mongo, get_unmapped_terms


async def _main(limit: int) -> None:
    await connect_mongo()
    try:
        rows = await get_unmapped_terms(limit=limit)
        print("term,count")
        for row in rows:
            print(f"{row['term']},{row['count']}")
    finally:
        await close_mongo()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Print frequent unmapped triage complaint terms.")
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()
    asyncio.run(_main(args.limit))
