from sqlmodel import select, Session
from fastapi import APIRouter, Request

from ..decorators.database_pagination import use_limit_pagination
from ..database import TestModel, CreateTestModel, dbsession_depend

router = APIRouter(prefix='/test/pagination')


@router.get('/')
@use_limit_pagination(handle_select=True)
def pagination_test(
        request: Request,
):
    assert isinstance(request, Request), 'failed to inject depends'

    return select(TestModel)


@router.post('/add')
def add_model(model_params: CreateTestModel, session: Session = dbsession_depend) -> TestModel:
    db_model = TestModel.model_validate(model_params)

    session.add(db_model)
    session.commit()
    session.refresh(db_model)

    return db_model
