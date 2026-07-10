"""
Per-token rate limiting backed by Redis.

See PLAN.md Section 8 and TASKS.md T35.
"""

# TODO: integrate a slowapi Limiter keyed by the authenticated bearer token
# (see app.core.security.verify_bearer_token), backed by the Redis instance
# at app.core.config.settings.redis_url, with limits from
# settings.rate_limit_per_minute per tier.
