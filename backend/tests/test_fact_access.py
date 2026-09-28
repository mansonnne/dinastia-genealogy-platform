from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.enums import UserRole
from app.modules.facts.service import FactService


def query_result(value):
    values = [] if value is None else ([value] if not isinstance(value, list) else value)
    scalars = SimpleNamespace(
        first=lambda: values[0] if values else None,
        all=lambda: values,
    )
    return SimpleNamespace(scalars=lambda: scalars)


@pytest.mark.asyncio
async def test_person_access_uses_profile_person_link() -> None:
    person = SimpleNamespace(id=uuid4())
    user = SimpleNamespace(id=uuid4(), role=UserRole.USER)
    db = AsyncMock()
    db.execute.side_effect = [
        query_result(person),
        query_result(SimpleNamespace(id=uuid4(), owner_user_id=user.id)),
    ]

    result = await FactService(db)._get_person_with_access(person.id, user)

    assert result is person
    assert db.execute.await_count == 2


@pytest.mark.asyncio
async def test_person_access_rejects_unrelated_user() -> None:
    person = SimpleNamespace(id=uuid4())
    user = SimpleNamespace(id=uuid4(), role=UserRole.USER)
    db = AsyncMock()
    db.execute.side_effect = [
        query_result(person),
        query_result([]),
    ]

    with pytest.raises(HTTPException) as error:
        await FactService(db)._get_person_with_access(person.id, user)

    assert error.value.status_code == 403
