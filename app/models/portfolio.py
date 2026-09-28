from __future__ import annotations

from typing import Any

from sqlalchemy import Boolean, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PortfolioPage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Chrome for /portfolio: hero, featured copy, filters, impact, pillars, CTA."""

    __tablename__ = "portfolio_pages"

    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    hero_heading: Mapped[str] = mapped_column(String(200), nullable=False)
    hero_body: Mapped[str] = mapped_column(Text, nullable=False)
    hero_metrics: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    hero_highlights: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    featured_kicker: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    featured_heading: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    featured_body: Mapped[str] = mapped_column(Text, nullable=False, default="")

    archive_kicker: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    archive_heading: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    archive_body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    categories: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)

    impact_kicker: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    impact_heading: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    impact_body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    impact_stats: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)

    pillars_kicker: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    pillars_heading: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    pillars_body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    pillars: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    engagement_highlights: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    cta_heading: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    cta_body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    cta_highlights: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    cta_primary_label: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    cta_secondary_label: Mapped[str] = mapped_column(String(80), nullable=False, default="")

    seo_title: Mapped[str | None] = mapped_column(String(80))
    seo_description: Mapped[str | None] = mapped_column(String(200))

    def __repr__(self) -> str:
        return f"<PortfolioPage {self.slug}>"


class PortfolioProject(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One case-study card on /portfolio."""

    __tablename__ = "portfolio_projects"

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True, nullable=False)
    tagline: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="Completed")
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    tech_stack: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    live_url: Mapped[str | None] = mapped_column(String(255))
    live_label: Mapped[str | None] = mapped_column(String(120))
    outcomes: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    icon: Mapped[str | None] = mapped_column(String(80))
    image_url: Mapped[str | None] = mapped_column(String(255))
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    internal_notes: Mapped[str | None] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<PortfolioProject {self.slug}>"


class PortfolioImage(Base):
    """Card photo bytes. The API disk does not survive a restart."""

    __tablename__ = "portfolio_images"

    name: Mapped[str] = mapped_column(String(80), primary_key=True)
    content_type: Mapped[str] = mapped_column(String(40), nullable=False)
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    def __repr__(self) -> str:
        return f"<PortfolioImage {self.name}>"
