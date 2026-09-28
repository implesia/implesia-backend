from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ArticlesPage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Chrome for /articles: hero, topics, featured copy, library, CTA, SEO."""

    __tablename__ = "articles_pages"

    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    hero_heading: Mapped[str] = mapped_column(String(200), nullable=False)
    hero_body: Mapped[str] = mapped_column(Text, nullable=False)
    hero_metrics: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    hero_highlights: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    topics_heading: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    topics: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)

    featured_kicker: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    library_kicker: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    library_heading: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    library_body: Mapped[str] = mapped_column(Text, nullable=False, default="")

    cta_heading: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    cta_body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    cta_highlights: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    cta_primary_label: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    cta_secondary_label: Mapped[str] = mapped_column(String(80), nullable=False, default="")

    seo_title: Mapped[str | None] = mapped_column(String(80))
    seo_description: Mapped[str | None] = mapped_column(String(200))

    def __repr__(self) -> str:
        return f"<ArticlesPage {self.slug}>"


class Article(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One published article on /articles/{slug}."""

    __tablename__ = "articles"

    title: Mapped[str] = mapped_column(String(220), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True, nullable=False)
    excerpt: Mapped[str] = mapped_column(String(400), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    topic_label: Mapped[str] = mapped_column(String(40), nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    author_name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    author_role: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    reading_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    seo_title: Mapped[str | None] = mapped_column(String(80))
    seo_description: Mapped[str | None] = mapped_column(String(200))
    image_url: Mapped[str | None] = mapped_column(String(255))
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    internal_notes: Mapped[str | None] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<Article {self.slug}>"


class ArticleImage(Base):
    """Cover photo bytes. The API disk does not survive a restart."""

    __tablename__ = "article_images"

    name: Mapped[str] = mapped_column(String(80), primary_key=True)
    content_type: Mapped[str] = mapped_column(String(40), nullable=False)
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    def __repr__(self) -> str:
        return f"<ArticleImage {self.name}>"
