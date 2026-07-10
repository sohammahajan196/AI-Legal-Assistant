"""
Gemini LLM client wrapper (ChatGoogleGenerativeAI).

See PLAN.md Section 5 and TASKS.md T22.
"""

from app.core.config import settings


def get_llm():
    """Return a configured `ChatGoogleGenerativeAI` client.

    TODO: implement using `langchain_google_genai.ChatGoogleGenerativeAI`
    with `settings.gemini_model` and `settings.google_api_key`. Expose both
    sync and async (`ainvoke`) usage.
    """
    raise NotImplementedError
