import uuid

from slugify import slugify
from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.article import Article, ArticlesPage
from app.schemas.article import ArticleCreate, ArticlesPageUpdate, ArticleUpdate
from app.services.article_media import delete_article_image

DEFAULT_PAGE_SLUG = "articles"


def _unique_slug(name: str, explicit: str | None) -> str:
    slug = slugify(explicit or name, max_length=180)
    if not slug:
        raise ConflictError("Could not build a URL slug from the title")
    return slug


async def get_page(db: AsyncSession, slug: str = DEFAULT_PAGE_SLUG) -> ArticlesPage:
    result = await db.execute(select(ArticlesPage).where(ArticlesPage.slug == slug))
    page = result.scalar_one_or_none()
    if page is None:
        raise NotFoundError("Articles page not found")
    return page


async def get_or_create_page(db: AsyncSession, slug: str = DEFAULT_PAGE_SLUG) -> ArticlesPage:
    try:
        return await get_page(db, slug)
    except NotFoundError:
        page = ArticlesPage(
            slug=slug,
            hero_heading="Technical insights for engineering leaders.",
            hero_body=(
                "Architecture decisions, security frameworks, and delivery practices "
                "— written for teams building enterprise-grade software at scale."
            ),
        )
        db.add(page)
        await db.commit()
        await db.refresh(page)
        return page


async def upsert_page(db: AsyncSession, payload: dict[str, object]) -> ArticlesPage:
    slug = str(payload.get("slug") or DEFAULT_PAGE_SLUG)
    try:
        page = await get_page(db, slug)
    except NotFoundError:
        page = ArticlesPage(**payload)
        db.add(page)
        await db.commit()
        await db.refresh(page)
        return page
    for field, value in payload.items():
        setattr(page, field, value)
    await db.commit()
    await db.refresh(page)
    return page


async def update_page(
    db: AsyncSession, page: ArticlesPage, payload: ArticlesPageUpdate
) -> ArticlesPage:
    data = payload.model_dump(mode="json", exclude_unset=True)
    for field, value in data.items():
        setattr(page, field, value)
    await db.commit()
    await db.refresh(page)
    return page


async def get_article_by_id(
    db: AsyncSession, article_id: uuid.UUID, *, published_only: bool = False
) -> Article:
    item = await db.get(Article, article_id)
    if item is None or (published_only and not item.is_published):
        raise NotFoundError("Article not found")
    return item


async def get_article_by_slug(
    db: AsyncSession, slug: str, *, published_only: bool = False
) -> Article:
    query = select(Article).where(Article.slug == slug)
    if published_only:
        query = query.where(Article.is_published.is_(True))
    result = await db.execute(query)
    item = result.scalar_one_or_none()
    if item is None:
        raise NotFoundError("Article not found")
    return item


async def get_article_by_ref(
    db: AsyncSession, ref: str, *, published_only: bool = False
) -> Article:
    try:
        return await get_article_by_id(db, uuid.UUID(ref), published_only=published_only)
    except ValueError:
        return await get_article_by_slug(db, ref, published_only=published_only)


async def list_articles(
    db: AsyncSession,
    offset: int,
    limit: int,
    *,
    published_only: bool = False,
    search: str | None = None,
    topic: str | None = None,
) -> tuple[list[Article], int]:
    filters: list[ColumnElement[bool]] = []
    if published_only:
        filters.append(Article.is_published.is_(True))
    if topic:
        filters.append(Article.topic == topic)
    if search:
        pattern = f"%{search.lower()}%"
        filters.append(
            or_(
                func.lower(Article.title).like(pattern),
                func.lower(Article.slug).like(pattern),
                func.lower(Article.topic).like(pattern),
            )
        )
    total = await db.scalar(select(func.count()).select_from(Article).where(*filters)) or 0
    result = await db.execute(
        select(Article)
        .where(*filters)
        .order_by(
            Article.is_featured.desc(),
            Article.published_at.desc(),
            Article.sort_order.asc(),
        )
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all()), total


async def list_published_articles(db: AsyncSession, *, topic: str | None = None) -> list[Article]:
    items, _ = await list_articles(db, 0, 100, published_only=True, topic=topic)
    return items


async def get_featured_article(db: AsyncSession) -> Article | None:
    result = await db.execute(
        select(Article)
        .where(Article.is_published.is_(True), Article.is_featured.is_(True))
        .order_by(Article.sort_order.asc(), Article.published_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _assert_slug_free(
    db: AsyncSession, slug: str, *, exclude_id: uuid.UUID | None = None
) -> None:
    query = select(Article.id).where(Article.slug == slug)
    if exclude_id is not None:
        query = query.where(Article.id != exclude_id)
    taken = await db.scalar(query)
    if taken is not None:
        raise ConflictError("An article with this slug already exists")


async def create_article(db: AsyncSession, payload: ArticleCreate) -> Article:
    slug = _unique_slug(payload.title, payload.slug)
    await _assert_slug_free(db, slug)
    data = payload.model_dump()
    data["slug"] = slug
    item = Article(**data)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def update_article(db: AsyncSession, item: Article, payload: ArticleUpdate) -> Article:
    data = payload.model_dump(exclude_unset=True)
    if "slug" in data:
        new_slug = _unique_slug(data.get("title", item.title), data["slug"])
        await _assert_slug_free(db, new_slug, exclude_id=item.id)
        data["slug"] = new_slug
    previous_image = item.image_url
    for field, value in data.items():
        setattr(item, field, value)
    if "image_url" in data and previous_image and previous_image != item.image_url:
        await delete_article_image(db, previous_image)
    await db.commit()
    await db.refresh(item)
    return item


async def delete_article(db: AsyncSession, item: Article) -> None:
    await delete_article_image(db, item.image_url)
    await db.delete(item)
    await db.commit()
