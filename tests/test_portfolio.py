import json

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserRole
from app.schemas.user import UserCreate
from app.services import user_service
from tests.conftest import TEST_PASSWORD

PAGE_PATCH = {
    "hero_heading": "Production software that delivers.",
    "cta_heading": "Ready to build something remarkable?",
}

PROJECT = {
    "name": "Gulf Franchise",
    "slug": "gulf-franchise",
    "tagline": "Franchise & Franchisor Shop Buy/Rent",
    "category": "marketplace",
    "year": 2025,
    "status": "Completed",
    "summary": "Full-stack franchise discovery platform with listings and lead workflows.",
    "tech_stack": ["Next.js", "Tailwind CSS", "Laravel"],
    "live_url": "https://gulffranchisehub.com",
    "live_label": "gulffranchisehub.com",
    "outcomes": [{"title": "Live", "description": "Production deployment"}],
    "is_featured": True,
    "is_published": True,
    "sort_order": 10,
    "internal_notes": "Do not show this note on the public website.",
}

# 1×1 PNG
_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0P"
    b"\x0f\x00\x01\x01\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _project_request(overrides: dict | None = None, *, image: bool = True) -> dict:
    source = {**PROJECT, **(overrides or {})}
    data = {
        "name": source["name"],
        "slug": source["slug"],
        "tagline": source["tagline"],
        "category": source["category"],
        "year": str(source["year"]),
        "status": source["status"],
        "summary": source["summary"],
        "tech_stack": ",".join(source["tech_stack"]),
        "live_url": source["live_url"] or "",
        "live_label": source["live_label"] or "",
        "outcomes": json.dumps(source["outcomes"]),
        "is_featured": "true" if source["is_featured"] else "false",
        "is_published": "true" if source["is_published"] else "false",
        "sort_order": str(source["sort_order"]),
        "internal_notes": source["internal_notes"] or "",
    }
    files = {"image": ("card.png", _PNG, "image/png")} if image else None
    return {"data": data, "files": files}


async def test_public_hides_drafts_and_internal_notes(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await client.patch("/api/v1/admin/portfolio", json=PAGE_PATCH, headers=auth_headers)
    created = await client.post(
        "/api/v1/admin/portfolio/projects", headers=auth_headers, **_project_request()
    )
    assert created.status_code == 201, created.text
    assert created.json()["internal_notes"].startswith("Do not show")
    assert created.json()["image_url"].startswith("/media/portfolio/")
    image = await client.get(created.json()["image_url"])
    assert image.status_code == 200
    assert image.headers["content-type"].startswith("image/")

    draft = await client.post(
        "/api/v1/admin/portfolio/projects",
        headers=auth_headers,
        **_project_request(
            {"name": "Draft Case", "slug": "draft-case", "is_published": False},
            image=False,
        ),
    )
    assert draft.status_code == 201

    public = await client.get("/api/v1/portfolio")
    assert public.status_code == 200, public.text
    body = public.json()
    slugs = [item["slug"] for item in body["projects"]]
    assert slugs == ["gulf-franchise"]
    assert body["featured"]["slug"] == "gulf-franchise"
    assert "internal_notes" not in body["featured"]
    assert "internal_notes" not in body["projects"][0]

    project_id = created.json()["id"]
    card = await client.get(f"/api/v1/portfolio/projects/{project_id}")
    assert card.status_code == 200
    assert "internal_notes" not in card.json()
    assert (await client.get("/api/v1/portfolio/projects/gulf-franchise")).status_code == 422
    assert (await client.get(f"/api/v1/portfolio/projects/{draft.json()['id']}")).status_code == 404


async def test_public_rejects_javascript_live_url(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/admin/portfolio/projects",
        headers=auth_headers,
        **_project_request({"slug": "bad-url", "live_url": "javascript:alert(1)"}, image=False),
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


async def test_admin_crud_and_auth_boundaries(
    client: AsyncClient, auth_headers: dict[str, str], db_session: AsyncSession
) -> None:
    created = await client.post(
        "/api/v1/admin/portfolio/projects", headers=auth_headers, **_project_request()
    )
    assert created.status_code == 201
    project_id = created.json()["id"]
    admin_get = await client.get(
        f"/api/v1/admin/portfolio/projects/{project_id}", headers=auth_headers
    )
    assert admin_get.json()["internal_notes"].startswith("Do not show")

    patched = await client.patch(
        f"/api/v1/admin/portfolio/projects/{project_id}",
        data={"status": "Completed", "year": "2025"},
        headers=auth_headers,
    )
    assert patched.status_code == 200

    assert (await client.get("/api/v1/admin/portfolio")).status_code == 401
    assert (await client.get("/api/v1/admin/portfolio/projects")).status_code == 401

    await user_service.create_user(
        db_session,
        UserCreate(
            email="viewer@implesia.com",
            full_name="Viewer",
            password=TEST_PASSWORD,
            role=UserRole.VIEWER,
        ),
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "viewer@implesia.com", "password": TEST_PASSWORD},
    )
    assert login.status_code == 200
    viewer = {"Authorization": f"Bearer {login.json()['access_token']}"}
    forbidden = await client.get("/api/v1/admin/portfolio/projects", headers=viewer)
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "forbidden"

    deleted = await client.delete(
        f"/api/v1/admin/portfolio/projects/{project_id}", headers=auth_headers
    )
    assert deleted.status_code == 200


async def test_form_body_on_json_route_stays_a_validation_error(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.patch(
        "/api/v1/admin/portfolio",
        headers=auth_headers,
        files={"hero_heading": (None, "Hello from a form")},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


async def test_duplicate_project_slug_conflicts(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    assert (
        await client.post(
            "/api/v1/admin/portfolio/projects", headers=auth_headers, **_project_request()
        )
    ).status_code == 201
    again = await client.post(
        "/api/v1/admin/portfolio/projects", headers=auth_headers, **_project_request()
    )
    assert again.status_code == 409
