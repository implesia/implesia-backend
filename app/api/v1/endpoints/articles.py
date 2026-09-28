import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.api.deps import DbSession, require_editor
from app.schemas.article import (
    ArticleAdmin,
    ArticleCreate,
    ArticleMedia,
    ArticlePublic,
    ArticlesPagePublic,
    ArticlesPageRead,
    ArticlesPageUpdate,
    ArticleUpdate,
)
from app.services.article_media import save_article_image
from app.schemas.common import Message, Page, PaginationParams
from app.services import article_service

public_router = APIRouter()
admin_router = APIRouter(dependencies=[Depends(require_editor)])


@public_router.get("", response_model=ArticlesPagePublic)
async def read_public_articles(db: DbSession, topic: str | None = None) -> ArticlesPagePublic:
    page = await article_service.get_page(db)
    featured = await article_service.get_featured_article(db)
    articles = await article_service.list_published_articles(db, topic=topic)
    body = ArticlesPagePublic.model_validate(page)
    body.featured = ArticlePublic.model_validate(featured) if featured is not None else None
    body.articles = [ArticlePublic.model_validate(item) for item in articles]
    return body


@public_router.get("/slug/{slug}", response_model=ArticlePublic)
async def read_published_article_by_slug(db: DbSession, slug: str) -> ArticlePublic:
    item = await article_service.get_article_by_slug(db, slug, published_only=True)
    return ArticlePublic.model_validate(item)


@public_router.get("/{article_id}", response_model=ArticlePublic)
async def read_published_article(db: DbSession, article_id: uuid.UUID) -> ArticlePublic:
    item = await article_service.get_article_by_id(db, article_id, published_only=True)
    return ArticlePublic.model_validate(item)


@admin_router.get("", response_model=ArticlesPageRead)
async def read_articles_page(db: DbSession) -> ArticlesPageRead:
    page = await article_service.get_or_create_page(db)
    return ArticlesPageRead.model_validate(page)


@admin_router.patch("", response_model=ArticlesPageRead)
async def update_articles_page(db: DbSession, payload: ArticlesPageUpdate) -> ArticlesPageRead:
    page = await article_service.get_or_create_page(db)
    updated = await article_service.update_page(db, page, payload)
    return ArticlesPageRead.model_validate(updated)


@admin_router.get("/posts", response_model=Page[ArticleAdmin])
async def list_articles(
    db: DbSession,
    pagination: Annotated[PaginationParams, Depends()],
    search: str | None = None,
    topic: str | None = None,
    published_only: bool = False,
) -> Page[ArticleAdmin]:
    items, total = await article_service.list_articles(
        db,
        pagination.offset,
        pagination.page_size,
        published_only=published_only,
        search=search,
        topic=topic,
    )
    return Page[ArticleAdmin](
        items=[ArticleAdmin.model_validate(item) for item in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@admin_router.post("/media", response_model=ArticleMedia, status_code=status.HTTP_201_CREATED)
async def upload_article_image(
    db: DbSession, image: UploadFile = File(...)
) -> ArticleMedia:
    image_url = await save_article_image(db, image)
    await db.commit()
    return ArticleMedia(image_url=image_url)


@admin_router.post("/posts", response_model=ArticleAdmin, status_code=status.HTTP_201_CREATED)
async def create_article(db: DbSession, payload: ArticleCreate) -> ArticleAdmin:
    item = await article_service.create_article(db, payload)
    return ArticleAdmin.model_validate(item)


@admin_router.get("/posts/{post_id}", response_model=ArticleAdmin)
async def read_article(db: DbSession, post_id: uuid.UUID) -> ArticleAdmin:
    item = await article_service.get_article_by_id(db, post_id)
    return ArticleAdmin.model_validate(item)


@admin_router.patch("/posts/{post_id}", response_model=ArticleAdmin)
async def update_article(db: DbSession, post_id: uuid.UUID, payload: ArticleUpdate) -> ArticleAdmin:
    item = await article_service.get_article_by_id(db, post_id)
    updated = await article_service.update_article(db, item, payload)
    return ArticleAdmin.model_validate(updated)


@admin_router.delete("/posts/{post_id}", response_model=Message)
async def delete_article(db: DbSession, post_id: uuid.UUID) -> Message:
    item = await article_service.get_article_by_id(db, post_id)
    await article_service.delete_article(db, item)
    return Message(message="Article deleted")
