from sqlmodel import SQLModel, Field


class TestModel(SQLModel, table=True):
    __tablename__ = 'test'
    id: int | None = Field(default=None, primary_key=True)
    name: str
    age: int
