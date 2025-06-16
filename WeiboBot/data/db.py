from pathlib import Path

from tortoise import Tortoise


async def init_db(db_path: Path):
    await Tortoise.init(
        db_url=f"sqlite://{db_path}",
        modules={"models": ["WeiboBot.data.record"]},
    )
    await Tortoise.generate_schemas()
