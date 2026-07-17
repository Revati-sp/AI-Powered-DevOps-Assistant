from __future__ import annotations

from typing import Any

import yaml

from app.core.exceptions import ValidationAppError


def validate_yaml_documents(content: str) -> list[dict[str, Any]]:
    try:
        documents = list(yaml.safe_load_all(content))
    except yaml.YAMLError as exc:
        raise ValidationAppError(
            "Generated YAML is invalid.",
            details={"error": str(exc)},
        ) from exc

    parsed: list[dict[str, Any]] = []
    for doc in documents:
        if doc is None:
            continue
        if not isinstance(doc, dict):
            raise ValidationAppError("Each YAML document must be a mapping/object.")
        parsed.append(doc)

    if not parsed:
        raise ValidationAppError("No YAML documents found.")
    return parsed


def dumps_multidoc(documents: list[dict[str, Any]]) -> str:
    return yaml.safe_dump_all(
        documents,
        sort_keys=False,
        default_flow_style=False,
    )
