"""聚合所有 content_team API 路由。"""
from __future__ import annotations

from fastapi import APIRouter

from hermes.content_team.api.analytics import router as analytics_router
from hermes.content_team.api.content import router as content_router
from hermes.content_team.api.content import (
    topics_content_router as content_topics_router,
)
from hermes.content_team.api.creative import (
    creation_router,
    directing_router,
    novels_router,
    scripts_router,
    storyboards_router,
)
from hermes.content_team.api.members import router as members_router
from hermes.content_team.api.publish import router as publish_router
from hermes.content_team.api.topics import router as topics_router
from hermes.content_team.creative.webui import router as dashboard_router

api_router = APIRouter()
api_router.include_router(topics_router, prefix="/api/topics", tags=["topics"])
api_router.include_router(members_router, prefix="/api/members", tags=["members"])
api_router.include_router(content_router, prefix="/api/content", tags=["content"])
# 基于选题创建内容：POST /api/topics/{id}/content
api_router.include_router(
    content_topics_router, prefix="/api/topics", tags=["content"]
)
# 平台账号与发布任务：/api/accounts, /api/publish
api_router.include_router(publish_router, prefix="/api", tags=["publish"])
# 数据分析与指标采集：/api/analytics
api_router.include_router(
    analytics_router, prefix="/api/analytics", tags=["analytics"]
)
# 创作能力：/api/novels, /api/scripts, /api/storyboards
api_router.include_router(novels_router, prefix="/api/novels", tags=["creative"])
api_router.include_router(scripts_router, prefix="/api/scripts", tags=["creative"])
api_router.include_router(
    storyboards_router, prefix="/api/storyboards", tags=["creative"]
)
# 导演/编导方案与创作循环：/api/directing-plans, /api/creation
api_router.include_router(
    directing_router, prefix="/api/directing-plans", tags=["creative"]
)
api_router.include_router(
    creation_router, prefix="/api/creation", tags=["creative"]
)
# 工作台（零构建单文件 HTML + 聚合概览）：/dashboard, /api/dashboard/overview
api_router.include_router(dashboard_router, tags=["dashboard"])
