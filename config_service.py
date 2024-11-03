# config_service.py

from sqlalchemy.future import select
from sqlalchemy.orm import Session
from database import Configuration
import json

class ConfigService:
    def __init__(self, db: Session):
        self.db = db

    async def get_config(self, category: str, key: str, default=None):
        result = await self.db.execute(select(Configuration).filter_by(category=category, key=key))
        config = result.scalars().first()
        if config:
            return config.value
        return default

    async def set_config(self, category: str, key: str, value):
        result = await self.db.execute(select(Configuration).filter_by(category=category, key=key))
        config = result.scalars().first()
        if config:
            config.value = value
        else:
            config = Configuration(category=category, key=key, value=value)
            self.db.add(config)
        await self.db.commit()

    async def delete_config(self, category: str, key: str):
        result = await self.db.execute(select(Configuration).filter_by(category=category, key=key))
        config = result.scalars().first()
        if config:
            await self.db.delete(config)
            await self.db.commit()
