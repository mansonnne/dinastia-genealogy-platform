from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.auth.dependencies import get_current_user
from app.modules.books.schemas import BookCreate, BookRead
from app.modules.books.service import BookService, generate_book_in_background

router = APIRouter(tags=["books"])
current_user_dep = Depends(get_current_user)
db_session_dep = Depends(get_db_session)


@router.post(
    "/profiles/{profile_id}/book",
    response_model=BookRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_book(
    profile_id: UUID,
    data: BookCreate,
    background_tasks: BackgroundTasks,
    current_user=current_user_dep,
    db: AsyncSession = db_session_dep,
) -> BookRead:
    book = await BookService(db).create_book(profile_id, current_user)
    background_tasks.add_task(
        generate_book_in_background,
        book.id,
        profile_id,
        current_user.id,
        data.model_dump(mode="json"),
    )
    return BookRead.model_validate(book)


@router.get("/profiles/{profile_id}/books", response_model=list[BookRead])
async def list_books(
    profile_id: UUID,
    current_user=current_user_dep,
    db: AsyncSession = db_session_dep,
) -> list[BookRead]:
    books = await BookService(db).list_books(profile_id, current_user)
    return [BookRead.model_validate(b) for b in books]


@router.get("/profiles/{profile_id}/books/{book_id}/pdf")
async def download_book_pdf(
    profile_id: UUID,
    book_id: UUID,
    current_user=current_user_dep,
    db: AsyncSession = db_session_dep,
) -> Response:
    pdf, filename = await BookService(db).render_pdf(profile_id, book_id, current_user)
    headers = {
        "Content-Disposition": (
            f'attachment; filename="book.pdf"; filename*=UTF-8\'\'{quote(filename)}'
        )
    }
    return Response(content=pdf, media_type="application/pdf", headers=headers)
