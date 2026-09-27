import uuid
from datetime import datetime
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HeroMetric(BaseModel):
    value: str = Field(min_length=1, max_length=40)
    label: str = Field(min_length=1, max_length=80)


class CategoryChip(BaseModel):
    slug: str = Field(min_length=2, max_length=40)
    label: str = Field(min_length=2, max_length=80)


class ImpactStat(BaseModel):
    value: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=2, max_length=120)
    body: str = Field(default="", max_length=400)


class DeliveryPillar(BaseModel):
    kicker: str = Field(default="", max_length=40)
    title: str = Field(min_length=2, max_length=120)
    body: str = Field(min_length=8, max_length=800)
    deliverables: list[str] = Field(default_factory=list)


class Outcome(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=400)


def _http_url(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("live_url must be an http or https URL")
    return value


class PortfolioPageBase(BaseModel):
    slug: str = Field(default="portfolio", min_length=2, max_length=80)
    hero_heading: str = Field(min_length=4, max_length=200)
    hero_body: str = Field(min_length=8, max_length=2000)
    hero_metrics: list[HeroMetric] = Field(default_factory=list)
    hero_highlights: list[str] = Field(default_factory=list)
    featured_kicker: str = Field(default="", max_length=120)
    featured_heading: str = Field(default="", max_length=200)
    featured_body: str = Field(default="", max_length=800)
    archive_kicker: str = Field(default="", max_length=120)
    archive_heading: str = Field(default="", max_length=200)
    archive_body: str = Field(default="", max_length=800)
    categories: list[CategoryChip] = Field(default_factory=list)
    impact_kicker: str = Field(default="", max_length=120)
    impact_heading: str = Field(default="", max_length=200)
    impact_body: str = Field(default="", max_length=800)
    impact_stats: list[ImpactStat] = Field(default_factory=list)
    pillars_kicker: str = Field(default="", max_length=120)
    pillars_heading: str = Field(default="", max_length=200)
    pillars_body: str = Field(default="", max_length=800)
    pillars: list[DeliveryPillar] = Field(default_factory=list)
    engagement_highlights: list[str] = Field(default_factory=list)
    cta_heading: str = Field(default="", max_length=200)
    cta_body: str = Field(default="", max_length=800)
    cta_highlights: list[str] = Field(default_factory=list)
    cta_primary_label: str = Field(default="", max_length=80)
    cta_secondary_label: str = Field(default="", max_length=80)
    seo_title: str | None = Field(None, max_length=80)
    seo_description: str | None = Field(None, max_length=200)


class PortfolioPageUpdate(BaseModel):
    hero_heading: str | None = Field(None, min_length=4, max_length=200)
    hero_body: str | None = Field(None, min_length=8, max_length=2000)
    hero_metrics: list[HeroMetric] | None = None
    hero_highlights: list[str] | None = None
    featured_kicker: str | None = Field(None, max_length=120)
    featured_heading: str | None = Field(None, max_length=200)
    featured_body: str | None = Field(None, max_length=800)
    archive_kicker: str | None = Field(None, max_length=120)
    archive_heading: str | None = Field(None, max_length=200)
    archive_body: str | None = Field(None, max_length=800)
    categories: list[CategoryChip] | None = None
    impact_kicker: str | None = Field(None, max_length=120)
    impact_heading: str | None = Field(None, max_length=200)
    impact_body: str | None = Field(None, max_length=800)
    impact_stats: list[ImpactStat] | None = None
    pillars_kicker: str | None = Field(None, max_length=120)
    pillars_heading: str | None = Field(None, max_length=200)
    pillars_body: str | None = Field(None, max_length=800)
    pillars: list[DeliveryPillar] | None = None
    engagement_highlights: list[str] | None = None
    cta_heading: str | None = Field(None, max_length=200)
    cta_body: str | None = Field(None, max_length=800)
    cta_highlights: list[str] | None = None
    cta_primary_label: str | None = Field(None, max_length=80)
    cta_secondary_label: str | None = Field(None, max_length=80)
    seo_title: str | None = Field(None, max_length=80)
    seo_description: str | None = Field(None, max_length=200)


class PortfolioPageRead(PortfolioPageBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class PortfolioProjectBase(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    slug: str | None = Field(None, min_length=2, max_length=180)
    tagline: str = Field(min_length=4, max_length=200)
    category: str = Field(min_length=2, max_length=40)
    year: int = Field(ge=1990, le=2100)
    status: str = Field(default="Completed", max_length=40)
    summary: str = Field(min_length=8, max_length=2000)
    tech_stack: list[str] = Field(default_factory=list)
    live_url: str | None = Field(None, max_length=255)
    live_label: str | None = Field(None, max_length=120)
    outcomes: list[Outcome] = Field(default_factory=list)
    icon: str | None = Field(None, max_length=80)
    is_featured: bool = False
    is_published: bool = True
    sort_order: int = 0

    @field_validator("live_url")
    @classmethod
    def _safe_live_url(cls, value: str | None) -> str | None:
        return _http_url(value)


class PortfolioProjectCreate(PortfolioProjectBase):
    internal_notes: str | None = Field(None, max_length=4000)


class PortfolioProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=160)
    slug: str | None = Field(None, min_length=2, max_length=180)
    tagline: str | None = Field(None, min_length=4, max_length=200)
    category: str | None = Field(None, min_length=2, max_length=40)
    year: int | None = Field(None, ge=1990, le=2100)
    status: str | None = Field(None, max_length=40)
    summary: str | None = Field(None, min_length=8, max_length=2000)
    tech_stack: list[str] | None = None
    live_url: str | None = Field(None, max_length=255)
    live_label: str | None = Field(None, max_length=120)
    outcomes: list[Outcome] | None = None
    icon: str | None = Field(None, max_length=80)
    is_featured: bool | None = None
    is_published: bool | None = None
    sort_order: int | None = None
    internal_notes: str | None = Field(None, max_length=4000)

    @field_validator("live_url")
    @classmethod
    def _safe_live_url(cls, value: str | None) -> str | None:
        return _http_url(value)


class PortfolioProjectPublic(PortfolioProjectBase):
    """Public card. Never includes internal_notes."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    image_url: str | None = None
    created_at: datetime
    updated_at: datetime


class PortfolioProjectAdmin(PortfolioProjectPublic):
    internal_notes: str | None = None


class PortfolioPagePublic(PortfolioPageRead):
    featured: PortfolioProjectPublic | None = None
    projects: list[PortfolioProjectPublic] = Field(default_factory=list)
