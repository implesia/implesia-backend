from __future__ import annotations

from typing import Any

from sqlalchemy import Boolean, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TeamPage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Chrome for /team: hero, leadership copy, practices, principles, CTA."""

    __tablename__ = "team_pages"

    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    hero_kicker: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    hero_heading: Mapped[str] = mapped_column(String(200), nullable=False)
    hero_body: Mapped[str] = mapped_column(Text, nullable=False)
    hero_metrics: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    hero_highlights: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    members_kicker: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    members_heading: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    members_body: Mapped[str] = mapped_column(Text, nullable=False, default="")

    practices_kicker: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    practices_heading: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    practices_body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    practices_highlights: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    practices: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)

    principles_kicker: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    principles_heading: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    principles_body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    principles: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    principles_cta_label: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    principles_cta_secondary: Mapped[str] = mapped_column(String(80), nullable=False, default="")

    meet_heading: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    meet_body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    meet_highlights: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    meet_cta_label: Mapped[str] = mapped_column(String(80), nullable=False, default="")

    cta_heading: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    cta_body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    cta_highlights: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    cta_primary_label: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    cta_secondary_label: Mapped[str] = mapped_column(String(80), nullable=False, default="")

    seo_title: Mapped[str | None] = mapped_column(String(80))
    seo_description: Mapped[str | None] = mapped_column(String(200))

    def __repr__(self) -> str:
        return f"<TeamPage {self.slug}>"


class TeamMember(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One person card on /team."""

    __tablename__ = "team_members"

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(120), nullable=False)
    bio: Mapped[str] = mapped_column(Text, nullable=False)
    skills: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(255))
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    internal_notes: Mapped[str | None] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<TeamMember {self.slug}>"


class TeamImage(Base):
    """Portrait bytes. The API disk does not survive a restart."""

    __tablename__ = "team_images"

    name: Mapped[str] = mapped_column(String(80), primary_key=True)
    content_type: Mapped[str] = mapped_column(String(40), nullable=False)
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    def __repr__(self) -> str:
        return f"<TeamImage {self.name}>"
