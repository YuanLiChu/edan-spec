#!/usr/bin/env python3
"""Classify a fixed code-review scope for the Qt specialist skills.

The classifier is deliberately conservative: QML is identified by its file
type, while C++ requires an explicit Qt include, type/macro, signal/slot
construct, or a Qt build declaration that names the source file.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable, Mapping, Sequence


CPP_EXTENSIONS = {".cpp", ".cc", ".cxx", ".h", ".hh", ".hpp", ".hxx"}
QML_EXTENSIONS = {".qml", ".qmltypes"}
BUILD_FILENAMES = {
    "CMakeLists.txt",
    "cmakelists.txt",
    "meson.build",
    "meson_options.txt",
}
BUILD_EXTENSIONS = {".cmake", ".pro", ".pri"}

QT_EVIDENCE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "Qt include",
        re.compile(
            r"#\s*include\s*[<\"](?:Qt[A-Za-z0-9_]+/|Q[A-Z][A-Za-z0-9_]*|q[a-z][A-Za-z0-9_]*)"
        ),
    ),
    (
        "Qt macro",
        re.compile(r"\b(?:Q_OBJECT|Q_GADGET|Q_NAMESPACE|Q_PROPERTY|Q_INVOKABLE)\b"),
    ),
    (
        "Qt type",
        re.compile(
            r"\b(?:QObject|Q_GADGET|QAbstractItemModel|QModelIndex|QVariant|QString|QList|QHash|QThread|QTimer|QUrl|QJsonDocument|QNetworkReply|QQmlEngine|QQuickItem)\b"
        ),
    ),
    (
        "Qt signal/slot construct",
        re.compile(r"(?m)^\s*(?:signals?|slots?)\s*:|\bemit\s+[A-Za-z_]\w*\s*\("),
    ),
)
QT_BUILD_PATTERN = re.compile(
    r"\b(?:find_package\s*\(\s*Qt6|qt_add_(?:executable|library|qml_module)|"
    r"qt_(?:internal_)?add_module)\b[^\r\n]*",
    re.IGNORECASE,
)


def _is_cpp(path: Path) -> bool:
    return path.suffix.lower() in CPP_EXTENSIONS


def _is_qml(path: Path) -> bool:
    return path.suffix.lower() in QML_EXTENSIONS


def _is_build_file(path: Path) -> bool:
    return path.name in BUILD_FILENAMES or path.suffix.lower() in BUILD_EXTENSIONS


def _scope_files(inputs: Iterable[str | Path]) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for value in inputs:
        path = Path(value)
        candidates = sorted(path.rglob("*")) if path.is_dir() else [path]
        for candidate in candidates:
            if not candidate.is_file() or candidate in seen:
                continue
            seen.add(candidate)
            files.append(candidate)
    return files


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _direct_evidence(text: str) -> list[str]:
    evidence: list[str] = []
    for label, pattern in QT_EVIDENCE_PATTERNS:
        match = pattern.search(text)
        if match is not None:
            evidence.append(f"{label}: {match.group(0).strip()}")
    return evidence


def _build_evidence(path: Path, build_files: Mapping[Path, str]) -> list[str]:
    evidence: list[str] = []
    candidates = {
        path.name,
        path.stem,
        path.as_posix(),
        path.name.replace("\\", "/"),
    }
    for build_path, text in build_files.items():
        for match in QT_BUILD_PATTERN.finditer(text):
            declaration = match.group(0).strip()
            def names_source(candidate: str) -> bool:
                if not candidate:
                    return False
                if "/" in candidate or "\\" in candidate:
                    return candidate.replace("\\", "/") in declaration.replace("\\", "/")
                return re.search(
                    rf"(?<![A-Za-z0-9_]){re.escape(candidate)}(?![A-Za-z0-9_])",
                    declaration,
                    re.IGNORECASE,
                ) is not None

            if any(names_source(candidate) for candidate in candidates):
                evidence.append(
                    f"Qt build declaration ({build_path.name}): {declaration}"
                )
    return evidence


def classify_scope(inputs: Sequence[str | Path]) -> dict[str, object]:
    """Return the stable routing contract consumed by ``edanspec-code-review``."""

    paths = _scope_files(inputs)
    all_files = [str(path) for path in paths]
    texts = {path: _read_text(path) for path in paths}
    build_files = {
        path: texts[path]
        for path in paths
        if _is_build_file(path) and texts[path]
    }
    evidence: dict[str, list[str]] = {str(path): [] for path in paths}
    qt_cpp_files: list[str] = []
    qml_files: list[str] = []

    for path in paths:
        key = str(path)
        if _is_qml(path):
            qml_files.append(key)
            evidence[key].append(f"QML file type: {path.suffix.lower()}")
        if not _is_cpp(path):
            continue
        evidence[key].extend(_direct_evidence(texts[path]))
        evidence[key].extend(_build_evidence(path, build_files))
        if evidence[key]:
            qt_cpp_files.append(key)

    return {
        "allFiles": all_files,
        "qtCppFiles": qt_cpp_files,
        "qmlFiles": qml_files,
        "evidence": evidence,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Classify a fixed code-review scope for Qt specialist skills."
    )
    parser.add_argument("paths", nargs="+", help="Files or directories in review scope")
    parser.add_argument("--json", action="store_true", help="Emit JSON (the default)")
    args = parser.parse_args()
    result = classify_scope(args.paths)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
