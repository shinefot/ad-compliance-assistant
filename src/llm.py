"""llm.py — creates connections to Claude. Imported lazily so tests can run without an API key."""
from . import config


def get_llm(role: str):
    from langchain_anthropic import ChatAnthropic

    if role == "extractor":
        # temperature=0 makes extraction as repeatable as possible: important for audits.
        return ChatAnthropic(model=config.EXTRACT_MODEL, temperature=0, max_tokens=4096)
    # Newer models manage sampling themselves and reject a custom temperature,
    # so the analyst and reviewer use the model's default.
    return ChatAnthropic(model=config.REASON_MODEL, max_tokens=4096)


def model_name(role: str) -> str:
    return config.EXTRACT_MODEL if role == "extractor" else config.REASON_MODEL