import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HeroMetric(BaseModel):
    value: str = Field(min_length=1, max_length=40)
    label: str = Field(min_length=1, max_length=80)


class PracticeArea(BaseModel):
    number: str = Field(default="", max_length=8)
    icon: str | None = Field(None, max_length=80)
    kicker: str = Field(default="", max_length=80)
    title: str = Field(min_length=2, max_length=160)
    body: str = Field(min_length=8, max_length=800)
    skills: list[str] = Field(default_factory=list)


class Principle(BaseModel):
    icon: str | None = Field(None, max_length=80)
    title: str = Field(min_length=2, max_length=160)
    body: str = Field(min_length=8, max_length=800)


class TeamPageBase(BaseModel):
    slug: str = Field(default="team", min_length=2, max_length=80)
    hero_kicker: str = Field(default="", max_length=120)
    hero_heading: str = Field(min_length=4, max_length=200)
    hero_body: str = Field(min_length=8, max_length=2000)
    hero_metrics: list[HeroMetric] = Field(default_factory=list)
    hero_highlights: list[str] = Field(default_factory=list)
    members_kicker: str = Field(default="", max_length=120)
    members_heading: str = Field(default="", max_length=200)
    members_body: str = Field(default="", max_length=800)
    practices_kicker: str = Field(default="", max_length=120)
    practices_heading: str = Field(default="", max_length=200)
    practices_body: str = Field(default="", max_length=800)
    practices_highlights: list[str] = Field(default_factory=list)
    practices: list[PracticeArea] = Field(default_factory=list)
    principles_kicker: str = Field(default="", max_length=120)
    principles_heading: str = Field(default="", max_length=200)
    principles_body: str = Field(default="", max_length=800)
    principles: list[Principle] = Field(default_factory=list)
    principles_cta_label: str = Field(default="", max_length=80)
    principles_cta_secondary: str = Field(default="", max_length=80)
    meet_heading: str = Field(default="", max_length=200)
    meet_body: str = Field(default="", max_length=800)
    meet_highlights: list[str] = Field(default_factory=list)
    meet_cta_label: str = Field(default="", max_length=80)
    cta_heading: str = Field(default="", max_length=200)
    cta_body: str = Field(default="", max_length=800)
    cta_highlights: list[str] = Field(default_factory=list)
    cta_primary_label: str = Field(default="", max_length=80)
    cta_secondary_label: str = Field(default="", max_length=80)
    seo_title: str | None = Field(None, max_length=80)
    seo_description: str | None = Field(None, max_length=200)


class TeamPageUpdate(BaseModel):
    hero_kicker: str | None = Field(None, max_length=120)
    hero_heading: str | None = Field(None, min_length=4, max_length=200)
    hero_body: str | None = Field(None, min_length=8, max_length=2000)
    hero_metrics: list[HeroMetric] | None = None
    hero_highlights: list[str] | None = None
    members_kicker: str | None = Field(None, max_length=120)
    members_heading: str | None = Field(None, max_length=200)
    members_body: str | None = Field(None, max_length=800)
    practices_kicker: str | None = Field(None, max_length=120)
    practices_heading: str | None = Field(None, max_length=200)
    practices_body: str | None = Field(None, max_length=800)
    practices_highlights: list[str] | None = None
    practices: list[PracticeArea] | None = None
    principles_kicker: str | None = Field(None, max_length=120)
    principles_heading: str | None = Field(None, max_length=200)
    principles_body: str | None = Field(None, max_length=800)
    principles: list[Principle] | None = None
    principles_cta_label: str | None = Field(None, max_length=80)
    principles_cta_secondary: str | None = Field(None, max_length=80)
    meet_heading: str | None = Field(None, max_length=200)
    meet_body: str | None = Field(None, max_length=800)
    meet_highlights: list[str] | None = None
    meet_cta_label: str | None = Field(None, max_length=80)
    cta_heading: str | None = Field(None, max_length=200)
    cta_body: str | None = Field(None, max_length=800)
    cta_highlights: list[str] | None = None
    cta_primary_label: str | None = Field(None, max_length=80)
    cta_secondary_label: str | None = Field(None, max_length=80)
    seo_title: str | None = Field(None, max_length=80)
    seo_description: str | None = Field(None, max_length=200)


class TeamPageRead(TeamPageBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class TeamMemberBase(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    slug: str | None = Field(None, min_length=2, max_length=180)
    role: str = Field(min_length=2, max_length=120)
    bio: str = Field(min_length=8, max_length=2000)
    skills: list[str] = Field(default_factory=list)
    image_url: str | None = Field(None, max_length=255)
    is_featured: bool = False
    is_published: bool = True
    sort_order: int = 0


class TeamMemberCreate(TeamMemberBase):
    internal_notes: str | None = Field(None, max_length=4000)


class TeamMemberUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=160)
    slug: str | None = Field(None, min_length=2, max_length=180)
    role: str | None = Field(None, min_length=2, max_length=120)
    bio: str | None = Field(None, min_length=8, max_length=2000)
    skills: list[str] | None = None
    image_url: str | None = Field(None, max_length=255)
    is_featured: bool | None = None
    is_published: bool | None = None
    sort_order: int | None = None
    internal_notes: str | None = Field(None, max_length=4000)


class TeamMemberPublic(TeamMemberBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    created_at: datetime
    updated_at: datetime


class TeamMemberAdmin(TeamMemberPublic):
    internal_notes: str | None = None


class TeamMedia(BaseModel):
    image_url: str


class TeamPagePublic(TeamPageRead):
    featured: TeamMemberPublic | None = None
    members: list[TeamMemberPublic] = Field(default_factory=list)
