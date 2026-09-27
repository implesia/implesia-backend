import uuid

from slugify import slugify
from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.portfolio import PortfolioPage, PortfolioProject
from app.schemas.portfolio import (
    PortfolioPageUpdate,
    PortfolioProjectCreate,
    PortfolioProjectUpdate,
)
from app.services.portfolio_media import delete_portfolio_image

DEFAULT_PAGE_SLUG = "portfolio"


def _unique_slug(name: str, explicit: str | None) -> str:
    slug = slugify(explicit or name, max_length=180)
    if not slug:
        raise ConflictError("Could not build a URL slug from the name")
    return slug


async def get_page(db: AsyncSession, slug: str = DEFAULT_PAGE_SLUG) -> PortfolioPage:
    result = await db.execute(select(PortfolioPage).where(PortfolioPage.slug == slug))
    page = result.scalar_one_or_none()
    if page is None:
        raise NotFoundError("Portfolio page not found")
    return page


async def get_or_create_page(db: AsyncSession, slug: str = DEFAULT_PAGE_SLUG) -> PortfolioPage:
    try:
        return await get_page(db, slug)
    except NotFoundError:
        page = PortfolioPage(
            slug=slug,
            hero_heading="Production software that delivers.",
            hero_body=(
                "A curated portfolio of full-stack web platforms, marketplaces, "
                "SaaS products, and healthcare systems — each built with modern "
                "architectures and delivered to production."
            ),
        )
        db.add(page)
        await db.commit()
        await db.refresh(page)
        return page


async def upsert_page(db: AsyncSession, payload: dict[str, object]) -> PortfolioPage:
    slug = str(payload.get("slug") or DEFAULT_PAGE_SLUG)
    try:
        page = await get_page(db, slug)
    except NotFoundError:
        page = PortfolioPage(**payload)
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
    db: AsyncSession, page: PortfolioPage, payload: PortfolioPageUpdate
) -> PortfolioPage:
    data = payload.model_dump(mode="json", exclude_unset=True)
    for field, value in data.items():
        setattr(page, field, value)
    await db.commit()
    await db.refresh(page)
    return page


async def get_project_by_id(
    db: AsyncSession, project_id: uuid.UUID, *, published_only: bool = False
) -> PortfolioProject:
    item = await db.get(PortfolioProject, project_id)
    if item is None or (published_only and not item.is_published):
        raise NotFoundError("Portfolio project not found")
    return item


async def get_project_by_slug(
    db: AsyncSession, slug: str, *, published_only: bool = False
) -> PortfolioProject:
    query = select(PortfolioProject).where(PortfolioProject.slug == slug)
    if published_only:
        query = query.where(PortfolioProject.is_published.is_(True))
    result = await db.execute(query)
    item = result.scalar_one_or_none()
    if item is None:
        raise NotFoundError("Portfolio project not found")
    return item


async def get_project_by_ref(
    db: AsyncSession, ref: str, *, published_only: bool = False
) -> PortfolioProject:
    try:
        return await get_project_by_id(db, uuid.UUID(ref), published_only=published_only)
    except ValueError:
        return await get_project_by_slug(db, ref, published_only=published_only)


async def list_projects(
    db: AsyncSession,
    offset: int,
    limit: int,
    *,
    published_only: bool = False,
    search: str | None = None,
    category: str | None = None,
) -> tuple[list[PortfolioProject], int]:
    filters: list[ColumnElement[bool]] = []
    if published_only:
        filters.append(PortfolioProject.is_published.is_(True))
    if category:
        filters.append(PortfolioProject.category == category)
    if search:
        pattern = f"%{search.lower()}%"
        filters.append(
            or_(
                func.lower(PortfolioProject.name).like(pattern),
                func.lower(PortfolioProject.slug).like(pattern),
                func.lower(PortfolioProject.category).like(pattern),
            )
        )
    total = await db.scalar(select(func.count()).select_from(PortfolioProject).where(*filters)) or 0
    result = await db.execute(
        select(PortfolioProject)
        .where(*filters)
        .order_by(
            PortfolioProject.is_featured.desc(),
            PortfolioProject.sort_order.asc(),
            PortfolioProject.year.desc(),
        )
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all()), total


async def list_published_projects(
    db: AsyncSession, *, category: str | None = None
) -> list[PortfolioProject]:
    items, _ = await list_projects(db, 0, 100, published_only=True, category=category)
    return items


async def get_featured_project(db: AsyncSession) -> PortfolioProject | None:
    result = await db.execute(
        select(PortfolioProject)
        .where(
            PortfolioProject.is_published.is_(True),
            PortfolioProject.is_featured.is_(True),
        )
        .order_by(PortfolioProject.sort_order.asc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _assert_slug_free(
    db: AsyncSession, slug: str, *, exclude_id: uuid.UUID | None = None
) -> None:
    query = select(PortfolioProject.id).where(PortfolioProject.slug == slug)
    if exclude_id is not None:
        query = query.where(PortfolioProject.id != exclude_id)
    taken = await db.scalar(query)
    if taken is not None:
        raise ConflictError("A portfolio project with this slug already exists")


async def create_project(
    db: AsyncSession,
    payload: PortfolioProjectCreate,
    *,
    image_url: str | None = None,
) -> PortfolioProject:
    slug = _unique_slug(payload.name, payload.slug)
    await _assert_slug_free(db, slug)
    data = payload.model_dump(mode="json")
    data["slug"] = slug
    data["image_url"] = image_url
    item = PortfolioProject(**data)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def update_project(
    db: AsyncSession,
    item: PortfolioProject,
    payload: PortfolioProjectUpdate,
    *,
    image_url: str | None = None,
    replace_image: bool = False,
) -> PortfolioProject:
    data = payload.model_dump(mode="json", exclude_unset=True)
    if "slug" in data:
        new_slug = _unique_slug(data.get("name", item.name), data["slug"])
        await _assert_slug_free(db, new_slug, exclude_id=item.id)
        data["slug"] = new_slug
    previous_image = item.image_url
    for field, value in data.items():
        setattr(item, field, value)
    if replace_image:
        item.image_url = image_url
    await db.commit()
    await db.refresh(item)
    if replace_image and previous_image and previous_image != item.image_url:
        delete_portfolio_image(previous_image)
    return item


async def delete_project(db: AsyncSession, item: PortfolioProject) -> None:
    image_url = item.image_url
    await db.delete(item)
    await db.commit()
    delete_portfolio_image(image_url)
