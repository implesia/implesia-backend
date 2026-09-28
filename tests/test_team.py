from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserRole
from app.schemas.user import UserCreate
from app.services import user_service
from tests.conftest import TEST_PASSWORD

PAGE_PATCH = {
    "hero_heading": "Senior engineers. Accountable delivery.",
    "cta_heading": "Ready to build?",
}

MEMBER = {
    "name": "Tushar Hossen",
    "slug": "tushar-hossen",
    "role": "Founder and CEO",
    "bio": "Leads company vision, client partnerships, and delivery strategy.",
    "skills": ["Leadership", "Strategy"],
    "is_featured": True,
    "is_published": True,
    "sort_order": 10,
    "internal_notes": "Do not show this note on the public website.",
}


async def test_public_hides_drafts_and_internal_notes(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await client.patch("/api/v1/admin/team", json=PAGE_PATCH, headers=auth_headers)
    created = await client.post("/api/v1/admin/team/members", json=MEMBER, headers=auth_headers)
    assert created.status_code == 201, created.text
    assert created.json()["internal_notes"].startswith("Do not show")

    draft = await client.post(
        "/api/v1/admin/team/members",
        json={
            **MEMBER,
            "name": "Draft Engineer",
            "slug": "draft-engineer",
            "is_published": False,
            "is_featured": False,
        },
        headers=auth_headers,
    )
    assert draft.status_code == 201

    public = await client.get("/api/v1/team")
    assert public.status_code == 200, public.text
    body = public.json()
    slugs = [item["slug"] for item in body["members"]]
    assert slugs == ["tushar-hossen"]
    assert body["featured"]["slug"] == "tushar-hossen"
    assert "internal_notes" not in body["featured"]
    assert "internal_notes" not in body["members"][0]

    member_id = created.json()["id"]
    card = await client.get(f"/api/v1/team/members/{member_id}")
    assert card.status_code == 200
    assert "internal_notes" not in card.json()
    assert (await client.get("/api/v1/team/members/tushar-hossen")).status_code == 422
    assert (await client.get(f"/api/v1/team/members/{draft.json()['id']}")).status_code == 404


_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0P"
    b"\x0f\x00\x01\x01\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


async def test_portrait_is_served_with_the_member(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    uploaded = await client.post(
        "/api/v1/admin/team/media",
        headers=auth_headers,
        files={"image": ("portrait.png", _PNG, "image/png")},
    )
    assert uploaded.status_code == 201, uploaded.text
    image_url = uploaded.json()["image_url"]
    assert image_url.startswith("/media/team/")

    created = await client.post(
        "/api/v1/admin/team/members",
        json={**MEMBER, "slug": "portrait-member", "name": "Portrait Member", "image_url": image_url},
        headers=auth_headers,
    )
    assert created.status_code == 201, created.text
    assert created.json()["image_url"] == image_url

    image = await client.get(image_url)
    assert image.status_code == 200
    assert image.headers["content-type"].startswith("image/")

    saved = await client.get(
        f"/api/v1/admin/team/members/{created.json()['id']}",
        headers=auth_headers,
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["image_url"] == image_url


async def test_admin_crud_and_auth_boundaries(
    client: AsyncClient, auth_headers: dict[str, str], db_session: AsyncSession
) -> None:
    created = await client.post("/api/v1/admin/team/members", json=MEMBER, headers=auth_headers)
    assert created.status_code == 201
    member_id = created.json()["id"]
    admin_get = await client.get(f"/api/v1/admin/team/members/{member_id}", headers=auth_headers)
    assert admin_get.json()["internal_notes"].startswith("Do not show")

    patched = await client.patch(
        f"/api/v1/admin/team/members/{member_id}",
        json={"role": "Founder and CEO", "is_published": True},
        headers=auth_headers,
    )
    assert patched.status_code == 200

    assert (await client.get("/api/v1/admin/team")).status_code == 401
    assert (await client.get("/api/v1/admin/team/members")).status_code == 401

    await user_service.create_user(
        db_session,
        UserCreate(
            email="viewer-team@implesia.com",
            full_name="Viewer",
            password=TEST_PASSWORD,
            role=UserRole.VIEWER,
        ),
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "viewer-team@implesia.com", "password": TEST_PASSWORD},
    )
    assert login.status_code == 200
    viewer = {"Authorization": f"Bearer {login.json()['access_token']}"}
    forbidden = await client.get("/api/v1/admin/team/members", headers=viewer)
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "forbidden"

    deleted = await client.delete(f"/api/v1/admin/team/members/{member_id}", headers=auth_headers)
    assert deleted.status_code == 200


async def test_duplicate_member_slug_conflicts(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    assert (
        await client.post("/api/v1/admin/team/members", json=MEMBER, headers=auth_headers)
    ).status_code == 201
    again = await client.post("/api/v1/admin/team/members", json=MEMBER, headers=auth_headers)
    assert again.status_code == 409
