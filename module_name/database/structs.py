from pydantic import BaseModel
from sqlmodel import SQLModel, Field


from ..shared import config
from .shared import db_logger

if config.app.enable_test:
    db_logger.debug('test is enabled, registering test models')


    class TestModel(SQLModel, table=True):
        __tablename__ = 'test'
        id: int | None = Field(default=None, primary_key=True)
        name: str
        age: int

    class CreateTestModel(BaseModel):
        name: str
        age: int
