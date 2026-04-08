"""SaiSuite — AI: URLs"""
from django.urls import path

from apps.ai.views import (
    AIFeedbackView,
    KnowledgeIngestView,
    KnowledgeReindexView,
    KnowledgeSourceDeleteView,
    KnowledgeSourceListView,
    KnowledgeUploadView,
)

app_name = 'ai'

urlpatterns = [
    # ── Knowledge Base ────────────────────────────────────────────
    path('knowledge/ingest/', KnowledgeIngestView.as_view(), name='knowledge-ingest'),
    path('knowledge/upload/', KnowledgeUploadView.as_view(), name='knowledge-upload'),
    path('knowledge/sources/', KnowledgeSourceListView.as_view(), name='knowledge-sources'),
    path('knowledge/sources/<uuid:source_id>/', KnowledgeSourceDeleteView.as_view(), name='knowledge-source-delete'),
    path('knowledge/reindex/', KnowledgeReindexView.as_view(), name='knowledge-reindex'),
    # ── Feedback ──────────────────────────────────────────────────
    path('feedback/', AIFeedbackView.as_view(), name='feedback'),
]
