"""
HuggingFace embedding model wrapper.

See PLAN.md Section 3 and TASKS.md T14.
"""

from app.core.config import settings


def get_embedding_model():
    """Return a configured embedding model instance.

    TODO: wrap `langchain_huggingface.HuggingFaceEmbeddings` using
    `settings.embedding_model`. Model name must remain config-driven, not
    hardcoded.
    """
    raise NotImplementedError
