#!/usr/bin/env python3
import importlib.metadata
import json
import re
import sys
import tomllib
from pathlib import Path


def normalize_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def requirement_name(requirement: str) -> str | None:
    value = requirement.strip()
    if not value or value.startswith("#") or value.startswith(("-r ", "--requirement ")):
        return None
    if value.startswith(("-e ", "--editable ")):
        value = value.split(maxsplit=1)[1]
    if value.startswith((".", "/", "git+", "http://", "https://")):
        return None
    match = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9_.-]*)", value)
    return normalize_name(match.group(1)) if match else None


def direct_dependencies(project_dir: Path) -> set[str]:
    dependencies: set[str] = set()

    requirements = project_dir / "requirements.txt"
    if requirements.is_file():
        for line in requirements.read_text(encoding="utf-8").splitlines():
            name = requirement_name(line)
            if name:
                dependencies.add(name)

    pyproject = project_dir / "pyproject.toml"
    if pyproject.is_file():
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        project = data.get("project") or {}
        for requirement in project.get("dependencies") or []:
            name = requirement_name(requirement)
            if name:
                dependencies.add(name)

        poetry_dependencies = (
            ((data.get("tool") or {}).get("poetry") or {}).get("dependencies") or {}
        )
        for name in poetry_dependencies:
            if normalize_name(name) != "python":
                dependencies.add(normalize_name(name))

    return dependencies


def package_name(package: dict) -> str | None:
    name = package.get("name")
    return normalize_name(name) if isinstance(name, str) else None


def package_spdx_id_by_name(document: dict) -> dict[str, str]:
    result: dict[str, str] = {}
    for package in document.get("packages") or []:
        name = package_name(package)
        spdx_id = package.get("SPDXID")
        if name and isinstance(spdx_id, str):
            result.setdefault(name, spdx_id)
    return result


def relationship_key(relationship: dict) -> tuple[str, str, str]:
    return (
        relationship.get("spdxElementId", ""),
        relationship.get("relationshipType", ""),
        relationship.get("relatedSpdxElement", ""),
    )


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "usage: enrich-python-spdx-dependencies.py <project_dir> <spdx_file>",
            file=sys.stderr,
        )
        return 2

    project_dir = Path(sys.argv[1]).resolve()
    spdx_file = Path(sys.argv[2]).resolve()

    document = json.loads(spdx_file.read_text(encoding="utf-8"))
    direct = direct_dependencies(project_dir)
    if not direct:
        return 0

    by_name = package_spdx_id_by_name(document)
    direct_ids = sorted(by_name[name] for name in direct if name in by_name)
    if not direct_ids:
        return 0

    root_name = project_dir.name or "project"
    root_spdx_id = "SPDXRef-RootPackage"
    packages = document.setdefault("packages", [])

    if not any(package.get("SPDXID") == root_spdx_id for package in packages):
        packages.insert(
            0,
            {
                "SPDXID": root_spdx_id,
                "name": root_name,
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": False,
                "licenseConcluded": "NOASSERTION",
                "licenseDeclared": "NOASSERTION",
                "copyrightText": "NOASSERTION",
                "versionInfo": "NOASSERTION",
            },
        )

    relationships = document.setdefault("relationships", [])
    existing = {relationship_key(relationship) for relationship in relationships}

    for direct_id in direct_ids:
        relationship = {
            "spdxElementId": root_spdx_id,
            "relationshipType": "DEPENDS_ON",
            "relatedSpdxElement": direct_id,
        }
        key = relationship_key(relationship)
        if key not in existing:
            relationships.append(relationship)
            existing.add(key)

    document["documentDescribes"] = [root_spdx_id]
    spdx_file.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
