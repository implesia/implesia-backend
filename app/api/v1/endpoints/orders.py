import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Request, status

from app.api.deps import DbSession, client_ip, require_editor
from app.core.config import settings
from app.core.exceptions import AppError, NotFoundError
from app.core.logging import get_logger
from app.models.order import OrderStatus
from app.models.pricing import EngagementModel, PricingPackage
from app.models.service import Service
from app.rate_limit import limiter
from app.schemas.common import Page, PaginationParams
from app.schemas.order import OrderCreate, OrderRead, OrderSubmissionResponse, OrderUpdate
from app.services import email, order_service, pricing_service, service_service
from app.services.turnstile import verify_turnstile

logger = get_logger(__name__)

public_router = APIRouter()
admin_router = APIRouter(dependencies=[Depends(require_editor)])


class SpamRejectedError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "spam_rejected"


class UnpublishedCatalogError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "catalog_unavailable"


async def _resolve_targets(
    db: DbSession,
    payload: OrderCreate,
    *,
    published_only: bool,
) -> tuple[Service | None, PricingPackage | None, EngagementModel | None]:
    service = None
    package = None
    model = None
    try:
        if payload.service_id is not None:
            service = await service_service.get_by_id(
                db, payload.service_id, published_only=published_only
            )
        if payload.package_id is not None:
            package = await pricing_service.get_package_by_id(
                db, payload.package_id, published_only=published_only
            )
        if payload.model_id is not None:
            model = await pricing_service.get_model_by_id(
                db, payload.model_id, published_only=published_only
            )
    except NotFoundError as exc:
        raise UnpublishedCatalogError("This item is not available to order") from exc
    return service, package, model


@public_router.post(
    "",
    response_model=OrderSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Place an order for a published service, package, or model",
)
@limiter.limit(settings.rate_limit_orders)
async def submit_order(
    request: Request,
    db: DbSession,
    payload: OrderCreate,
    background: BackgroundTasks,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> OrderSubmissionResponse:
    if idempotency_key:
        existing = await order_service.get_by_idempotency_key(db, idempotency_key)
        if existing is not None:
            return OrderSubmissionResponse(id=existing.id)

    service, package, model = await _resolve_targets(db, payload, published_only=True)

    ip = client_ip(request)
    if not await verify_turnstile(payload.turnstile_token, ip):
        raise SpamRejectedError("Bot verification failed. Please reload the page and try again.")

    order = await order_service.create_order(
        db,
        payload,
        service=service,
        package=package,
        model=model,
        ip_address=ip,
        user_agent=request.headers.get("user-agent"),
        idempotency_key=idempotency_key,
        status=OrderStatus.NEW,
    )

    logger.info("order_created", order_id=str(order.id))
    background.add_task(email.notify_team_of_order, order)
    background.add_task(email.acknowledge_order, order)

    return OrderSubmissionResponse(id=order.id)


@admin_router.get("", response_model=Page[OrderRead])
async def list_orders(
    db: DbSession,
    pagination: Annotated[PaginationParams, Depends()],
    status_filter: OrderStatus | None = None,
    service_id: uuid.UUID | None = None,
    package_id: uuid.UUID | None = None,
    model_id: uuid.UUID | None = None,
    search: str | None = None,
) -> Page[OrderRead]:
    orders, total = await order_service.list_orders(
        db,
        pagination.offset,
        pagination.page_size,
        status_filter,
        service_id,
        package_id,
        model_id,
        search,
    )
    return Page[OrderRead](
        items=[OrderRead.model_validate(order) for order in orders],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@admin_router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    db: DbSession,
    payload: OrderCreate,
) -> OrderRead:
    service, package, model = await _resolve_targets(db, payload, published_only=False)
    order = await order_service.create_order(
        db,
        payload,
        service=service,
        package=package,
        model=model,
        ip_address=None,
        user_agent="admin-dashboard",
        idempotency_key=None,
    )
    return OrderRead.model_validate(order)


@admin_router.get("/stats", response_model=dict[str, int])
async def order_stats(db: DbSession) -> dict[str, int]:
    return await order_service.count_by_status(db)


@admin_router.get("/{order_id}", response_model=OrderRead)
async def read_order(db: DbSession, order_id: uuid.UUID) -> OrderRead:
    order = await order_service.get_by_id(db, order_id)
    return OrderRead.model_validate(order)


@admin_router.patch("/{order_id}", response_model=OrderRead)
async def update_order(db: DbSession, order_id: uuid.UUID, payload: OrderUpdate) -> OrderRead:
    order = await order_service.get_by_id(db, order_id)
    updated = await order_service.update_order(db, order, payload)
    return OrderRead.model_validate(updated)
