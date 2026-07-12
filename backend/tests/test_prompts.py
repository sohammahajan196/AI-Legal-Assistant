"""Unit tests for app.rag.prompts. See TASKS.md T27."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from app.rag.prompts import (
    DEFAULT_USER_TYPE,
    DISCLAIMER_INSTRUCTION,
    USER_TYPE_TEMPLATES,
    build_prompt,
    get_prompt_template,
)

ALL_USER_TYPES = ["layperson", "law_student", "lawyer"]


# --- distinct templates per user_type ----------------------------------------


def test_exactly_three_user_types_are_defined():
    assert set(USER_TYPE_TEMPLATES.keys()) == set(ALL_USER_TYPES)


def test_each_user_type_maps_to_a_distinct_system_prompt():
    rendered = {user_type: USER_TYPE_TEMPLATES[user_type] for user_type in ALL_USER_TYPES}
    assert len(set(rendered.values())) == len(ALL_USER_TYPES)


# --- disclaimer instruction always present -----------------------------------


def test_every_user_type_system_prompt_contains_disclaimer_instruction():
    for user_type in ALL_USER_TYPES:
        assert DISCLAIMER_INSTRUCTION in USER_TYPE_TEMPLATES[user_type]


def test_every_rendered_chat_template_system_message_contains_disclaimer():
    for user_type in ALL_USER_TYPES:
        messages = build_prompt(user_type, query="What is theft?", context="Section 378: ...")
        system_messages = [m for m in messages if isinstance(m, SystemMessage)]
        assert len(system_messages) == 1
        assert DISCLAIMER_INSTRUCTION in system_messages[0].content


# --- placeholder substitution -------------------------------------------------


def test_build_prompt_substitutes_query_and_context_placeholders():
    query = "What is the punishment for theft under IPC?"
    context = "[ipc-378-0] Section 378. Theft. Whoever intends to take dishonestly..."

    for user_type in ALL_USER_TYPES:
        messages = build_prompt(user_type, query=query, context=context)

        assert len(messages) == 2
        system_message, human_message = messages
        assert isinstance(system_message, SystemMessage)
        assert isinstance(human_message, HumanMessage)

        assert query in human_message.content
        assert context in human_message.content
        # Placeholders must be fully substituted, never left as literal braces.
        assert "{query}" not in human_message.content
        assert "{context}" not in human_message.content


def test_build_prompt_returns_system_message_before_human_message():
    messages = build_prompt("lawyer", query="q", context="c")
    assert isinstance(messages[0], SystemMessage)
    assert isinstance(messages[1], HumanMessage)


# --- fallback behavior ---------------------------------------------------------


def test_unknown_user_type_falls_back_to_default_template():
    fallback_template = get_prompt_template("not-a-real-user-type")
    default_template = get_prompt_template(DEFAULT_USER_TYPE)
    assert fallback_template.messages == default_template.messages


def test_build_prompt_with_unknown_user_type_still_contains_disclaimer():
    messages = build_prompt("not-a-real-user-type", query="q", context="c")
    system_message = messages[0]
    assert DISCLAIMER_INSTRUCTION in system_message.content


# --- audience tone differs across templates -----------------------------------


def test_layperson_and_lawyer_templates_have_different_audience_guidance():
    assert "layperson" in USER_TYPE_TEMPLATES["layperson"].lower()
    assert "practicing lawyer" in USER_TYPE_TEMPLATES["lawyer"].lower()
    assert "law student" in USER_TYPE_TEMPLATES["law_student"].lower()
