#!/usr/bin/env python3
"""Small, deterministic helpers for the unified code-review report."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any


VALID_STATUSES = {"complete", "failed", "partial", "not-applicable"}


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _semantic_value(finding: Mapping[str, Any]) -> str:
    for key in ("semantic", "finding", "description", "title", "problem"):
        value = _clean(finding.get(key))
        if value:
            return value
    return "(unspecified finding)"


def _location(finding: Mapping[str, Any]) -> tuple[str, str]:
    file = _clean(finding.get("file") or finding.get("path"))
    line = _clean(finding.get("line") or finding.get("start"))
    return file, line


def _semantic_key(finding: Mapping[str, Any]) -> tuple[str, str, str]:
    file, line = _location(finding)
    semantic = re.sub(r"[^a-z0-9]+", " ", _semantic_value(finding).lower()).strip()
    return file.replace("\\", "/").lower(), line, semantic


def _qt_reference(finding: Mapping[str, Any]) -> dict[str, Any] | None:
    source = _clean(finding.get("source")).lower()
    values = {
        key: finding[key]
        for key in ("id", "rule", "confidence")
        if key in finding and finding[key] not in (None, "")
    }
    if not values and "qt" not in source:
        return None
    return values


def deduplicate_findings(findings: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Merge only findings with the same file, line and normalized semantics."""

    merged: dict[tuple[str, str, str], dict[str, Any]] = {}
    for original in findings:
        finding = dict(original)
        key = _semantic_key(finding)
        source = _clean(finding.get("source")) or "generic review"
        item = merged.get(key)
        if item is None:
            item = {
                key_name: finding[key_name]
                for key_name in ("file", "line", "severity", "title", "finding", "description")
                if key_name in finding
            }
            if not any(key in item for key in ("title", "finding", "description")):
                item["finding"] = _semantic_value(finding)
            item["sources"] = [source]
            item["qtReferences"] = []
            merged[key] = item
        elif source not in item["sources"]:
            item["sources"].append(source)
        reference = _qt_reference(finding)
        if reference is not None and reference not in item["qtReferences"]:
            item["qtReferences"].append(reference)
    return list(merged.values())


def compute_conclusion(
    generic_status: str,
    qt_cpp_status: str,
    qml_status: str,
    has_critical: bool,
) -> str:
    """Apply the review gate without mapping Qt confidence to severity."""

    statuses = (generic_status, qt_cpp_status, qml_status)
    if has_critical:
        return "REQUEST_CHANGES"
    if any(status not in VALID_STATUSES for status in statuses):
        return "INCOMPLETE"
    if any(status in {"failed", "partial"} for status in statuses):
        return "INCOMPLETE"
    if generic_status != "complete":
        return "INCOMPLETE"
    return "APPROVE"


def aggregate_report(
    findings: Iterable[Mapping[str, Any]],
    *,
    generic_status: str,
    qt_cpp_status: str = "not-applicable",
    qml_status: str = "not-applicable",
    has_critical: bool = False,
) -> dict[str, Any]:
    """Build the portable status portion used by the Markdown report writer."""

    return {
        "statuses": {
            "genericReview": generic_status,
            "qtCppReview": qt_cpp_status,
            "qmlReview": qml_status,
        },
        "conclusion": compute_conclusion(
            generic_status, qt_cpp_status, qml_status, has_critical
        ),
        "findings": deduplicate_findings(findings),
    }
