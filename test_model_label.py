"""The reported model label and cost follow the active backend (provenance).

Regression for the 2026-09-11 finding: on the production/Bastion profile the
draft reported `model: gpt-4o` and gpt-4o-priced cost even though BastionGPT
served it.
"""

from profile import active_model_label, set_active_backend
from provider import compute_cost_usd


def test_label_and_cost_follow_bastion_backend():
    set_active_backend("bastion")
    try:
        assert active_model_label("gpt-4o") == "bastiongpt-api-v2.0"
        assert active_model_label("gpt-4o-mini") == "bastiongpt-api-v2.0"
        # Bastion is not per-token billed to this app — report 0.0, not a
        # fabricated OpenAI-priced figure. Token counts stay real elsewhere.
        assert compute_cost_usd("bastiongpt-api-v2.0", 2000, 1000) == 0.0
    finally:
        set_active_backend("openai")


def test_label_passthrough_on_openai_backend():
    set_active_backend("openai")
    assert active_model_label("gpt-4o") == "gpt-4o"
    assert active_model_label("gpt-4o-mini") == "gpt-4o-mini"
    assert compute_cost_usd("gpt-4o", 1000, 0) == 0.0025
