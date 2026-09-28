import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.api.deps import DbSession, require_editor
from app.schemas.common import Message, Page, PaginationParams
from app.schemas.portfolio import (
    PortfolioPagePublic,
    PortfolioPageRead,
    PortfolioPageUpdate,
    PortfolioProjectAdmin,
    PortfolioProjectCreate,
    PortfolioProjectPublic,
    PortfolioProjectUpdate,
)
from app.services import portfolio_service
from app.services.portfolio_media import save_portfolio_image

public_router = APIRouter()
admin_router = APIRouter(dependencies=[Depends(require_editor)])


@public_router.get("", response_model=PortfolioPagePublic)
async def read_public_portfolio(db: DbSession, category: str | None = None) -> PortfolioPagePublic:
    page = await portfolio_service.get_page(db)
    featured = await portfolio_service.get_featured_project(db)
    projects = await portfolio_service.list_published_projects(db, category=category)
    body = PortfolioPagePublic.model_validate(page)
    body.featured = (
        PortfolioProjectPublic.model_validate(featured) if featured is not None else None
    )
    body.projects = [PortfolioProjectPublic.model_validate(item) for item in projects]
    return body


@public_router.get("/projects/{project_id}", response_model=PortfolioProjectPublic)
async def read_published_project(db: DbSession, project_id: uuid.UUID) -> PortfolioProjectPublic:
    item = await portfolio_service.get_project_by_id(db, project_id, published_only=True)
    return PortfolioProjectPublic.model_validate(item)


@admin_router.get("", response_model=PortfolioPageRead)
async def read_portfolio_page(db: DbSession) -> PortfolioPageRead:
    page = await portfolio_service.get_or_create_page(db)
    return PortfolioPageRead.model_validate(page)


@admin_router.patch("", response_model=PortfolioPageRead)
async def update_portfolio_page(db: DbSession, payload: PortfolioPageUpdate) -> PortfolioPageRead:
    page = await portfolio_service.get_or_create_page(db)
    updated = await portfolio_service.update_page(db, page, payload)
    return PortfolioPageRead.model_validate(updated)


@admin_router.get("/projects", response_model=Page[PortfolioProjectAdmin])
async def list_projects(
    db: DbSession,
    pagination: Annotated[PaginationParams, Depends()],
    search: str | None = None,
    category: str | None = None,
    published_only: bool = False,
) -> Page[PortfolioProjectAdmin]:
    items, total = await portfolio_service.list_projects(
        db,
        pagination.offset,
        pagination.page_size,
        published_only=published_only,
        search=search,
        category=category,
    )
    return Page[PortfolioProjectAdmin](
        items=[PortfolioProjectAdmin.model_validate(item) for item in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


def _blank(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def _csv(value: str | None) -> list[str]:
    if not value or not value.strip():
        return []
    text = value.strip()
    if text.startswith("["):
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    return [part.strip() for part in text.split(",") if part.strip()]


def _outcomes(value: str | None) -> list[dict[str, str]]:
    if not value or not value.strip():
        return []
    parsed = json.loads(value)
    if not isinstance(parsed, list):
        raise RequestValidationError(
            [{"type": "list_type", "loc": ("outcomes",), "msg": "Outcomes must be a list", "input": value}]
        )
    return parsed


def _validate_create(data: dict[str, object]) -> PortfolioProjectCreate:
    try:
        return PortfolioProjectCreate.model_validate(data)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


def _validate_update(data: dict[str, object]) -> PortfolioProjectUpdate:
    try:
        return PortfolioProjectUpdate.model_validate(data)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


async def _stored_image(db: DbSession, image: UploadFile | None) -> str | None:
    if image is None or not image.filename:
        return None
    return await save_portfolio_image(db, image)


@admin_router.post(
    "/projects",
    response_model=PortfolioProjectAdmin,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    db: DbSession,
    name: Annotated[str, Form()],
    tagline: Annotated[str, Form()],
    category: Annotated[str, Form()],
    year: Annotated[int, Form()],
    summary: Annotated[str, Form()],
    slug: Annotated[str | None, Form()] = None,
    status_label: Annotated[str, Form(alias="status")] = "Completed",
    tech_stack: Annotated[str, Form()] = "",
    live_url: Annotated[str | None, Form()] = None,
    live_label: Annotated[str | None, Form()] = None,
    outcomes: Annotated[str, Form()] = "",
    icon: Annotated[str | None, Form()] = None,
    is_featured: Annotated[bool, Form()] = False,
    is_published: Annotated[bool, Form()] = True,
    sort_order: Annotated[int, Form()] = 0,
    internal_notes: Annotated[str | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
) -> PortfolioProjectAdmin:
    payload = _validate_create(
        {
            "name": name,
            "slug": _blank(slug),
            "tagline": tagline,
            "category": category,
            "year": year,
            "status": status_label,
            "summary": summary,
            "tech_stack": _csv(tech_stack),
            "live_url": _blank(live_url),
            "live_label": _blank(live_label),
            "outcomes": _outcomes(outcomes),
            "icon": _blank(icon),
            "is_featured": is_featured,
            "is_published": is_published,
            "sort_order": sort_order,
            "internal_notes": _blank(internal_notes),
        }
    )
    item = await portfolio_service.create_project(
        db, payload, image_url=await _stored_image(db, image)
    )
    return PortfolioProjectAdmin.model_validate(item)


@admin_router.get("/projects/{project_id}", response_model=PortfolioProjectAdmin)
async def read_project(db: DbSession, project_id: uuid.UUID) -> PortfolioProjectAdmin:
    item = await portfolio_service.get_project_by_id(db, project_id)
    return PortfolioProjectAdmin.model_validate(item)


@admin_router.patch("/projects/{project_id}", response_model=PortfolioProjectAdmin)
async def update_project(
    db: DbSession,
    project_id: uuid.UUID,
    name: Annotated[str | None, Form()] = None,
    tagline: Annotated[str | None, Form()] = None,
    category: Annotated[str | None, Form()] = None,
    year: Annotated[int | None, Form()] = None,
    summary: Annotated[str | None, Form()] = None,
    slug: Annotated[str | None, Form()] = None,
    status_label: Annotated[str | None, Form(alias="status")] = None,
    tech_stack: Annotated[str | None, Form()] = None,
    live_url: Annotated[str | None, Form()] = None,
    live_label: Annotated[str | None, Form()] = None,
    outcomes: Annotated[str | None, Form()] = None,
    icon: Annotated[str | None, Form()] = None,
    is_featured: Annotated[bool | None, Form()] = None,
    is_published: Annotated[bool | None, Form()] = None,
    sort_order: Annotated[int | None, Form()] = None,
    internal_notes: Annotated[str | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
) -> PortfolioProjectAdmin:
    raw: dict[str, object] = {}
    if name is not None:
        raw["name"] = name
    if slug is not None:
        raw["slug"] = _blank(slug)
    if tagline is not None:
        raw["tagline"] = tagline
    if category is not None:
        raw["category"] = category
    if year is not None:
        raw["year"] = year
    if status_label is not None:
        raw["status"] = status_label
    if summary is not None:
        raw["summary"] = summary
    if tech_stack is not None:
        raw["tech_stack"] = _csv(tech_stack)
    if live_url is not None:
        raw["live_url"] = _blank(live_url)
    if live_label is not None:
        raw["live_label"] = _blank(live_label)
    if outcomes is not None:
        raw["outcomes"] = _outcomes(outcomes)
    if icon is not None:
        raw["icon"] = _blank(icon)
    if is_featured is not None:
        raw["is_featured"] = is_featured
    if is_published is not None:
        raw["is_published"] = is_published
    if sort_order is not None:
        raw["sort_order"] = sort_order
    if internal_notes is not None:
        raw["internal_notes"] = _blank(internal_notes)

    item = await portfolio_service.get_project_by_id(db, project_id)
    image_url = await _stored_image(db, image)
    updated = await portfolio_service.update_project(
        db,
        item,
        _validate_update(raw),
        image_url=image_url,
        replace_image=image_url is not None,
    )
    return PortfolioProjectAdmin.model_validate(updated)


@admin_router.delete("/projects/{project_id}", response_model=Message)
async def delete_project(db: DbSession, project_id: uuid.UUID) -> Message:
    item = await portfolio_service.get_project_by_id(db, project_id)
    await portfolio_service.delete_project(db, item)
    return Message(message="Portfolio project deleted")
