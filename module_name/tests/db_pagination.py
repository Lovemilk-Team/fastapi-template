from pydantic import BaseModel
from fastapi import APIRouter, Request
from sqlmodel import select, Session, SQLModel, Field


# 在导入 database 前定义以保证 Model 被加到 metadata
class TestModel(SQLModel, table=True):
    __tablename__ = 'test'
    id: int | None = Field(default=None, primary_key=True)
    name: str
    age: int


class CreateTestModel(BaseModel):
    name: str
    age: int


from ..database import dbsession_depend
from ..structs.responses import BaseResponseModel
from ..decorators.database_pagination import use_limit_pagination

router = APIRouter(prefix='/test/pagination')


@router.get('/', description='test pagination for database')
# FastAPI 仅支持 pydantic 类型进行泛型标记
@use_limit_pagination(handle_select=True, return_annotation=BaseResponseModel[list[TestModel]])
def get_model(
        request: Request,
):
    assert isinstance(request, Request), 'failed to inject depends'

    return select(TestModel)


@router.post('/', description='add test model to database')
def add_model(model_params: CreateTestModel, session: Session = dbsession_depend) -> TestModel:
    db_model = TestModel.model_validate(model_params)

    session.add(db_model)
    session.commit()
    session.refresh(db_model)

    return db_model
