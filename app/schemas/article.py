import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HeroMetric(BaseModel):
    value: str = Field(min_length=1, max_length=40)
    label: str = Field(min_length=1, max_length=80)


class TopicChip(BaseModel):
    slug: str = Field(min_length=2, max_length=40)
    label: str = Field(min_length=2, max_length=80)


class ArticlesPageBase(BaseModel):
    slug: str = Field(default="articles", min_length=2, max_length=80)
    hero_heading: str = Field(min_length=4, max_length=200)
    hero_body: str = Field(min_length=8, max_length=2000)
    hero_metrics: list[HeroMetric] = Field(default_factory=list)
    hero_highlights: list[str] = Field(default_factory=list)
    topics_heading: str = Field(default="", max_length=200)
    topics: list[TopicChip] = Field(default_factory=list)
    featured_kicker: str = Field(default="", max_length=120)
    library_kicker: str = Field(default="", max_length=120)
    library_heading: str = Field(default="", max_length=200)
    library_body: str = Field(default="", max_length=800)
    cta_heading: str = Field(default="", max_length=200)
    cta_body: str = Field(default="", max_length=800)
    cta_highlights: list[str] = Field(default_factory=list)
    cta_primary_label: str = Field(default="", max_length=80)
    cta_secondary_label: str = Field(default="", max_length=80)
    seo_title: str | None = Field(None, max_length=80)
    seo_description: str | None = Field(None, max_length=200)


class ArticlesPageUpdate(BaseModel):
    hero_heading: str | None = Field(None, min_length=4, max_length=200)
    hero_body: str | None = Field(None, min_length=8, max_length=2000)
    hero_metrics: list[HeroMetric] | None = None
    hero_highlights: list[str] | None = None
    topics_heading: str | None = Field(None, max_length=200)
    topics: list[TopicChip] | None = None
    featured_kicker: str | None = Field(None, max_length=120)
    library_kicker: str | None = Field(None, max_length=120)
    library_heading: str | None = Field(None, max_length=200)
    library_body: str | None = Field(None, max_length=800)
    cta_heading: str | None = Field(None, max_length=200)
    cta_body: str | None = Field(None, max_length=800)
    cta_highlights: list[str] | None = None
    cta_primary_label: str | None = Field(None, max_length=80)
    cta_secondary_label: str | None = Field(None, max_length=80)
    seo_title: str | None = Field(None, max_length=80)
    seo_description: str | None = Field(None, max_length=200)


class ArticlesPageRead(ArticlesPageBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ArticleBase(BaseModel):
    title: str = Field(min_length=8, max_length=220)
    slug: str | None = Field(None, min_length=2, max_length=180)
    excerpt: str = Field(min_length=8, max_length=400)
    body: str = Field(min_length=20, max_length=50000)
    topic: str = Field(min_length=2, max_length=40)
    topic_label: str = Field(min_length=2, max_length=40)
    tags: list[str] = Field(default_factory=list)
    author_name: str = Field(default="Implesia Engineering", max_length=120)
    author_role: str = Field(default="", max_length=120)
    reading_minutes: int = Field(default=10, ge=1, le=120)
    published_at: datetime
    seo_title: str | None = Field(None, max_length=80)
    seo_description: str | None = Field(None, max_length=200)
    image_url: str | None = Field(None, max_length=255)
    is_featured: bool = False
    is_published: bool = True
    sort_order: int = 0


class ArticleCreate(ArticleBase):
    internal_notes: str | None = Field(None, max_length=4000)


class ArticleUpdate(BaseModel):
    title: str | None = Field(None, min_length=8, max_length=220)
    slug: str | None = Field(None, min_length=2, max_length=180)
    excerpt: str | None = Field(None, min_length=8, max_length=400)
    body: str | None = Field(None, min_length=20, max_length=50000)
    topic: str | None = Field(None, min_length=2, max_length=40)
    topic_label: str | None = Field(None, max_length=40)
    tags: list[str] | None = None
    author_name: str | None = Field(None, max_length=120)
    author_role: str | None = Field(None, max_length=120)
    reading_minutes: int | None = Field(None, ge=1, le=120)
    published_at: datetime | None = None
    seo_title: str | None = Field(None, max_length=80)
    seo_description: str | None = Field(None, max_length=200)
    image_url: str | None = Field(None, max_length=255)
    is_featured: bool | None = None
    is_published: bool | None = None
    sort_order: int | None = None
    internal_notes: str | None = Field(None, max_length=4000)


class ArticlePublic(ArticleBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    created_at: datetime
    updated_at: datetime


class ArticleAdmin(ArticlePublic):
    internal_notes: str | None = None


class ArticleMedia(BaseModel):
    image_url: str


class ArticlesPagePublic(ArticlesPageRead):
    featured: ArticlePublic | None = None
    articles: list[ArticlePublic] = Field(default_factory=list)
