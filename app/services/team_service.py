import uuid

from slugify import slugify
from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.team import TeamMember, TeamPage
from app.schemas.team import TeamMemberCreate, TeamMemberUpdate, TeamPageUpdate
from app.services.team_media import delete_team_image

DEFAULT_PAGE_SLUG = "team"


def _unique_slug(name: str, explicit: str | None) -> str:
    slug = slugify(explicit or name, max_length=180)
    if not slug:
        raise ConflictError("Could not build a URL slug from the name")
    return slug


async def get_page(db: AsyncSession, slug: str = DEFAULT_PAGE_SLUG) -> TeamPage:
    result = await db.execute(select(TeamPage).where(TeamPage.slug == slug))
    page = result.scalar_one_or_none()
    if page is None:
        raise NotFoundError("Team page not found")
    return page


async def get_or_create_page(db: AsyncSession, slug: str = DEFAULT_PAGE_SLUG) -> TeamPage:
    try:
        return await get_page(db, slug)
    except NotFoundError:
        page = TeamPage(
            slug=slug,
            hero_heading="Senior engineers. Accountable delivery.",
            hero_body=(
                "Implesia IT is built around experienced practitioners—not layers "
                "of handoffs. Our teams integrate directly with yours."
            ),
        )
        db.add(page)
        await db.commit()
        await db.refresh(page)
        return page


async def upsert_page(db: AsyncSession, payload: dict[str, object]) -> TeamPage:
    slug = str(payload.get("slug") or DEFAULT_PAGE_SLUG)
    try:
        page = await get_page(db, slug)
    except NotFoundError:
        page = TeamPage(**payload)
        db.add(page)
        await db.commit()
        await db.refresh(page)
        return page
    for field, value in payload.items():
        setattr(page, field, value)
    await db.commit()
    await db.refresh(page)
    return page


async def update_page(db: AsyncSession, page: TeamPage, payload: TeamPageUpdate) -> TeamPage:
    data = payload.model_dump(mode="json", exclude_unset=True)
    for field, value in data.items():
        setattr(page, field, value)
    await db.commit()
    await db.refresh(page)
    return page


async def get_member_by_id(
    db: AsyncSession, member_id: uuid.UUID, *, published_only: bool = False
) -> TeamMember:
    item = await db.get(TeamMember, member_id)
    if item is None or (published_only and not item.is_published):
        raise NotFoundError("Team member not found")
    return item


async def get_member_by_slug(
    db: AsyncSession, slug: str, *, published_only: bool = False
) -> TeamMember:
    query = select(TeamMember).where(TeamMember.slug == slug)
    if published_only:
        query = query.where(TeamMember.is_published.is_(True))
    result = await db.execute(query)
    item = result.scalar_one_or_none()
    if item is None:
        raise NotFoundError("Team member not found")
    return item


async def get_member_by_ref(
    db: AsyncSession, ref: str, *, published_only: bool = False
) -> TeamMember:
    try:
        return await get_member_by_id(db, uuid.UUID(ref), published_only=published_only)
    except ValueError:
        return await get_member_by_slug(db, ref, published_only=published_only)


async def list_members(
    db: AsyncSession,
    offset: int,
    limit: int,
    *,
    published_only: bool = False,
    search: str | None = None,
) -> tuple[list[TeamMember], int]:
    filters: list[ColumnElement[bool]] = []
    if published_only:
        filters.append(TeamMember.is_published.is_(True))
    if search:
        pattern = f"%{search.lower()}%"
        filters.append(
            or_(
                func.lower(TeamMember.name).like(pattern),
                func.lower(TeamMember.slug).like(pattern),
                func.lower(TeamMember.role).like(pattern),
            )
        )
    total = await db.scalar(select(func.count()).select_from(TeamMember).where(*filters)) or 0
    result = await db.execute(
        select(TeamMember)
        .where(*filters)
        .order_by(TeamMember.is_featured.desc(), TeamMember.sort_order.asc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all()), total


async def list_published_members(db: AsyncSession) -> list[TeamMember]:
    items, _ = await list_members(db, 0, 100, published_only=True)
    return items


async def get_featured_member(db: AsyncSession) -> TeamMember | None:
    result = await db.execute(
        select(TeamMember)
        .where(TeamMember.is_published.is_(True), TeamMember.is_featured.is_(True))
        .order_by(TeamMember.sort_order.asc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _assert_slug_free(
    db: AsyncSession, slug: str, *, exclude_id: uuid.UUID | None = None
) -> None:
    query = select(TeamMember.id).where(TeamMember.slug == slug)
    if exclude_id is not None:
        query = query.where(TeamMember.id != exclude_id)
    taken = await db.scalar(query)
    if taken is not None:
        raise ConflictError("A team member with this slug already exists")


async def create_member(db: AsyncSession, payload: TeamMemberCreate) -> TeamMember:
    slug = _unique_slug(payload.name, payload.slug)
    await _assert_slug_free(db, slug)
    data = payload.model_dump()
    data["slug"] = slug
    item = TeamMember(**data)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def update_member(
    db: AsyncSession, item: TeamMember, payload: TeamMemberUpdate
) -> TeamMember:
    data = payload.model_dump(exclude_unset=True)
    if "slug" in data:
        new_slug = _unique_slug(data.get("name", item.name), data["slug"])
        await _assert_slug_free(db, new_slug, exclude_id=item.id)
        data["slug"] = new_slug
    previous_image = item.image_url
    for field, value in data.items():
        setattr(item, field, value)
    if "image_url" in data and previous_image and previous_image != item.image_url:
        await delete_team_image(db, previous_image)
    await db.commit()
    await db.refresh(item)
    return item


async def delete_member(db: AsyncSession, item: TeamMember) -> None:
    await delete_team_image(db, item.image_url)
    await db.delete(item)
    await db.commit()
