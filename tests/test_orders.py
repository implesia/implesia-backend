from httpx import AsyncClient

from tests.test_pricing import MODEL, PACKAGE
from tests.test_services import VALID_SERVICE

VALID_ORDER = {
    "full_name": "Jonathan Reid",
    "email": "j.reid@acme.com",
    "phone": "+44 20 7946 0000",
    "organisation": "Acme Corporation",
    "message": "We want to start with the SaaS architecture package next month.",
    "source_page": "/services/saas-architecture",
}


async def _publish_service(client: AsyncClient, auth_headers: dict[str, str]) -> str:
    response = await client.post("/api/v1/admin/services", json=VALID_SERVICE, headers=auth_headers)
    assert response.status_code == 201, response.text
    return str(response.json()["id"])


async def test_submit_order_creates_inbox_row(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    service_id = await _publish_service(client, auth_headers)
    response = await client.post("/api/v1/orders", json={**VALID_ORDER, "service_id": service_id})
    assert response.status_code == 201, response.text
    order_id = response.json()["id"]

    inbox = await client.get("/api/v1/admin/orders", headers=auth_headers)
    assert inbox.status_code == 200
    assert inbox.json()["total"] == 1
    assert inbox.json()["items"][0]["id"] == order_id
    assert inbox.json()["items"][0]["service"]["slug"] == "saas-architecture"
    assert inbox.json()["items"][0]["status"] == "new"


async def test_website_field_does_not_cancel_order(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    service_id = await _publish_service(client, auth_headers)
    response = await client.post(
        "/api/v1/orders",
        json={
            **VALID_ORDER,
            "service_id": service_id,
            "website": "https://autofill.example",
        },
    )
    assert response.status_code == 201, response.text

    inbox = await client.get("/api/v1/admin/orders", headers=auth_headers)
    assert inbox.json()["items"][0]["status"] == "new"


async def test_cannot_order_unpublished_service(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    created = await client.post(
        "/api/v1/admin/services",
        json={**VALID_SERVICE, "is_published": False},
        headers=auth_headers,
    )
    response = await client.post(
        "/api/v1/orders", json={**VALID_ORDER, "service_id": created.json()["id"]}
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "catalog_unavailable"


async def test_order_idempotency(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    service_id = await _publish_service(client, auth_headers)
    headers = {"Idempotency-Key": "order-1"}
    first = await client.post(
        "/api/v1/orders", json={**VALID_ORDER, "service_id": service_id}, headers=headers
    )
    second = await client.post(
        "/api/v1/orders", json={**VALID_ORDER, "service_id": service_id}, headers=headers
    )
    assert first.json()["id"] == second.json()["id"]


async def test_admin_can_update_order_status(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    service_id = await _publish_service(client, auth_headers)
    created = await client.post("/api/v1/orders", json={**VALID_ORDER, "service_id": service_id})
    order_id = created.json()["id"]

    updated = await client.patch(
        f"/api/v1/admin/orders/{order_id}",
        json={"status": "in_progress", "internal_notes": "Assigned to Nazrul."},
        headers=auth_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "in_progress"


async def test_cannot_delete_service_with_orders(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    service_id = await _publish_service(client, auth_headers)
    await client.post("/api/v1/orders", json={**VALID_ORDER, "service_id": service_id})
    deleted = await client.delete(f"/api/v1/admin/services/{service_id}", headers=auth_headers)
    assert deleted.status_code == 409


async def test_listing_orders_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/admin/orders")).status_code == 401


async def test_submit_order_for_published_package(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    created = await client.post(
        "/api/v1/admin/pricing/packages", json=PACKAGE, headers=auth_headers
    )
    assert created.status_code == 201, created.text
    package_id = created.json()["id"]

    response = await client.post("/api/v1/orders", json={**VALID_ORDER, "package_id": package_id})
    assert response.status_code == 201, response.text

    inbox = await client.get(
        "/api/v1/admin/orders", params={"package_id": package_id}, headers=auth_headers
    )
    assert inbox.status_code == 200
    assert inbox.json()["total"] == 1
    assert inbox.json()["items"][0]["package"]["slug"] == "product-landing-page"
    assert inbox.json()["items"][0]["service"] is None


async def test_submit_order_for_published_model(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    created = await client.post("/api/v1/admin/pricing/models", json=MODEL, headers=auth_headers)
    model_id = created.json()["id"]
    response = await client.post("/api/v1/orders", json={**VALID_ORDER, "model_id": model_id})
    assert response.status_code == 201, response.text
    detail = await client.get(
        f"/api/v1/admin/orders/{response.json()['id']}", headers=auth_headers
    )
    assert detail.json()["model"]["slug"] == "discovery-sprint"


async def test_cannot_order_unpublished_package(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    created = await client.post(
        "/api/v1/admin/pricing/packages",
        json={**PACKAGE, "is_published": False},
        headers=auth_headers,
    )
    response = await client.post(
        "/api/v1/orders", json={**VALID_ORDER, "package_id": created.json()["id"]}
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "catalog_unavailable"


async def test_order_requires_a_catalog_target(client: AsyncClient) -> None:
    response = await client.post("/api/v1/orders", json=VALID_ORDER)
    assert response.status_code == 422


async def test_admin_can_log_manual_order(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    service_id = await _publish_service(client, auth_headers)
    created = await client.post(
        "/api/v1/admin/orders",
        json={**VALID_ORDER, "service_id": service_id, "source_page": "whatsapp"},
        headers=auth_headers,
    )
    assert created.status_code == 201, created.text
    assert created.json()["status"] == "new"
    assert created.json()["service"]["id"] == service_id


async def test_admin_can_mark_order_quoted(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    service_id = await _publish_service(client, auth_headers)
    created = await client.post("/api/v1/orders", json={**VALID_ORDER, "service_id": service_id})
    updated = await client.patch(
        f"/api/v1/admin/orders/{created.json()['id']}",
        json={"status": "quoted", "internal_notes": "Sent the Discovery quote."},
        headers=auth_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "quoted"


async def test_cannot_delete_package_with_orders(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    created = await client.post(
        "/api/v1/admin/pricing/packages", json=PACKAGE, headers=auth_headers
    )
    package_id = created.json()["id"]
    await client.post("/api/v1/orders", json={**VALID_ORDER, "package_id": package_id})
    deleted = await client.delete(
        f"/api/v1/admin/pricing/packages/{package_id}", headers=auth_headers
    )
    assert deleted.status_code == 409
