"""
Per-user_type prompt templates with the legal disclaimer instruction baked in.

See PLAN.md Section 5 and TASKS.md T27.
"""

DISCLAIMER_INSTRUCTION = (
    "Always remind the user that this answer is not a substitute for licensed "
    "legal counsel and does not constitute binding legal advice."
)

# TODO: define real layperson / law_student / lawyer prompt templates (e.g.
# via langchain_core.prompts.ChatPromptTemplate), each embedding
# DISCLAIMER_INSTRUCTION in the system message and adjusting explanation
# depth/tone per TASKS.md T27 acceptance criteria.

USER_TYPE_TEMPLATES: dict[str, str] = {
    "layperson": "",
    "law_student": "",
    "lawyer": "",
}
