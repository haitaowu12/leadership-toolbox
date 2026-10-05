#!/usr/bin/env python3
"""Validate public-file boundaries, links, versions and structured method profiles."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "skills" / "leadership-toolbox"
DENIED = re.compile(r"(?:/(?:Users|home)/|[A-Z]:\\Users\\|(?:sediment|file)://|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----|AKIA[0-9A-Z]{16})", re.I)
PRIVATE_NAMES = {"profile.json", "practice.jsonl", ".user-data"}


def public_file(root, name):
    if not isinstance(name, str) or not name or "\\" in name or ":" in name:
        raise ValueError("invalid public path")
    relative = PurePosixPath(name)
    if relative.is_absolute() or ".." in relative.parts or relative.as_posix() != name:
        raise ValueError(f"unsafe public path: {name}")
    path = root / name
    if any(part.is_symlink() for part in [path, *path.parents]) or not path.is_file():
        raise ValueError(f"unsafe/missing public file: {name}")
    if root not in path.resolve().parents:
        raise ValueError(f"outside public root: {name}")
    return path


def strings(value, allow_empty=False):
    return isinstance(value, list) and (allow_empty or bool(value)) and all(isinstance(item, str) and item.strip() for item in value) and len(value) == len(set(value))


def https_url(value):
    if not isinstance(value, str):
        return False
    try:
        parts = urlsplit(value)
        return parts.scheme == "https" and bool(parts.netloc) and parts.username is None and parts.password is None
    except ValueError:
        return False


def validate_catalog(catalog, dimensions, files):
    """Return structural errors without ranking methods or inferring effectiveness."""
    errors = []
    if not isinstance(catalog, dict) or not isinstance(dimensions, dict):
        return ["catalog and dimensions must be objects"]
    if type(catalog.get("schema_version")) is not int or catalog["schema_version"] != 2 or type(catalog.get("matching_schema_version")) is not int or catalog["matching_schema_version"] != 1:
        errors.append("unsupported catalog/matching schema")
    version = catalog.get("package_version")
    if not isinstance(version, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        errors.append("invalid package version")
    definitions = dimensions.get("dimensions")
    if type(dimensions.get("schema_version")) is not int or dimensions["schema_version"] != 1 or not isinstance(definitions, list) or not definitions:
        return errors + ["invalid dimension schema"]
    allowed_values = {}
    for definition in definitions:
        if not isinstance(definition, dict):
            errors.append("dimension must be an object")
            continue
        dimension_id = definition.get("id")
        if not isinstance(dimension_id, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", dimension_id) or dimension_id in allowed_values:
            errors.append("invalid/duplicate dimension ID")
            continue
        allowed_values[dimension_id] = set()
        if definition.get("type") not in ("duration", "ordinal", "nominal", "categorical", "multi_select") or not isinstance(definition.get("description"), str) or not definition["description"].strip():
            errors.append(f"invalid dimension metadata: {dimension_id}")
        values = definition.get("values")
        if not isinstance(values, list):
            errors.append(f"invalid dimension values: {dimension_id}")
            continue
        if dimension_id == "time_runway":
            if definition.get("type") != "duration" or values:
                errors.append("time_runway must be a duration with no categorical values")
        elif not values or definition.get("type") == "duration":
            errors.append(f"dimension needs categorical/ordinal values: {dimension_id}")
        for value in values:
            if not isinstance(value, dict) or any(not isinstance(value.get(key), str) or not value[key].strip() for key in ("id", "label", "anchor")):
                errors.append(f"invalid value definition: {dimension_id}")
                continue
            if value["id"] in allowed_values[dimension_id]:
                errors.append(f"duplicate value ID: {dimension_id}")
            allowed_values[dimension_id].add(value["id"])
    if "time_runway" not in allowed_values:
        errors.append("missing time_runway dimension")

    methods = catalog.get("methods")
    if not isinstance(methods, list) or not methods:
        return errors + ["methods must be a nonempty list"]
    if type(catalog.get("method_count")) is not int or catalog["method_count"] != len(methods):
        errors.append("method_count does not match methods")
    ids = [method.get("id") if isinstance(method, dict) else None for method in methods]
    valid_ids = all(isinstance(value, str) and re.fullmatch(r"L[0-9]{2,}", value) and int(value[1:]) > 0 and value == f"L{int(value[1:]):02}" for value in ids)
    if not valid_ids:
        errors.append("invalid method IDs")
    elif len(ids) != len(set(ids)) or ids != sorted(ids, key=lambda value: int(value[1:])):
        errors.append("method IDs must be unique and ordered")
    id_set = {value for value in ids if isinstance(value, str)}
    referenced = []
    for method in methods:
        if not isinstance(method, dict):
            errors.append("method must be an object")
            continue
        method_id = method.get("id", "unknown")
        for key in ("title", "job", "evidence"):
            if not isinstance(method.get(key), str) or not method[key].strip():
                errors.append(f"missing method {key}: {method_id}")
        if method.get("version") != version or not https_url(method.get("source")):
            errors.append(f"invalid method version/source: {method_id}")
        licence = method.get("license")
        if licence not in ("MIT", "CC-BY-SA-4.0") or (method_id in ("L05", "L27") and licence != "CC-BY-SA-4.0"):
            errors.append(f"invalid licence boundary: {method_id}")
        name = method.get("file")
        if not isinstance(name, str) or name not in files or PurePosixPath(name).parent.as_posix() != "references/methods" or not PurePosixPath(name).name.startswith(f"{method_id}-") or not name.endswith(".md"):
            errors.append(f"invalid catalog path: {method_id}")
        else:
            referenced.append(name)
            card = files[name]
            if not card.startswith(f"# {method_id} · ") or f"Version: {version} · Licence: {licence}" not in card:
                errors.append(f"card ID/version/licence mismatch: {method_id}")
            if f"({name.removeprefix('references/')})" not in files.get("references/catalog.md", ""):
                errors.append(f"card not linked in readable catalog: {method_id}")
        profile = method.get("profile")
        if not isinstance(profile, dict):
            errors.append(f"missing method profile: {method_id}")
            continue
        for key in ("jobs", "preconditions", "avoid"):
            if not strings(profile.get(key)):
                errors.append(f"invalid profile {key}: {method_id}")
        for key in ("output", "outcome", "guardrail"):
            if not isinstance(profile.get(key), str) or not profile[key].strip():
                errors.append(f"missing profile {key}: {method_id}")
        if method.get("kind") not in ("sensemaking", "decision_support", "development", "coordination", "action_or_conversation"):
            errors.append(f"invalid method kind: {method_id}")
        contract = profile.get("metric_contract")
        contract_keys = {"immediate_output", "later_outcome", "balancing_indicator", "baseline_or_proxy_caveat", "review_timing"}
        if not isinstance(contract, dict) or set(contract) != contract_keys or any(not isinstance(value, str) or not value.strip() for value in contract.values()):
            errors.append(f"invalid metric contract: {method_id}")
        minutes = profile.get("time_minutes")
        if not isinstance(minutes, list) or len(minutes) != 2 or any(type(value) is not int for value in minutes) or not 0 <= minutes[0] <= minutes[1] or minutes[1] == 0:
            errors.append(f"invalid time_minutes range: {method_id}")
        alternatives = profile.get("alternative_ids")
        if not strings(alternatives) or any(value not in id_set or value == method_id for value in alternatives):
            errors.append(f"invalid alternative IDs: {method_id}")
        descriptors = profile.get("dimensions")
        if not isinstance(descriptors, dict) or len(descriptors) < 2:
            errors.append(f"profile needs at least two relevant dimensions: {method_id}")
            continue
        for dimension_id, descriptor in descriptors.items():
            if dimension_id not in allowed_values or dimension_id == "time_runway":
                errors.append(f"unknown/noncategorical profile dimension: {method_id}: {dimension_id}")
                continue
            if not isinstance(descriptor, dict) or set(descriptor) != {"fit", "caution", "reason"}:
                errors.append(f"invalid dimension descriptor: {method_id}: {dimension_id}")
                continue
            fit, caution = descriptor["fit"], descriptor["caution"]
            if not strings(fit, allow_empty=True) or not strings(caution, allow_empty=True):
                errors.append(f"invalid fit/caution labels: {method_id}: {dimension_id}")
                continue
            if not fit and not caution or set(fit) & set(caution) or not set(fit + caution) <= allowed_values[dimension_id]:
                errors.append(f"unknown/contradictory fit/caution labels: {method_id}: {dimension_id}")
            if not isinstance(descriptor["reason"], str) or not descriptor["reason"].strip():
                errors.append(f"missing dimension reason: {method_id}: {dimension_id}")
    cards = {name for name in files if name.startswith("references/methods/") and name.endswith(".md")}
    if len(referenced) != len(set(referenced)) or set(referenced) != cards:
        errors.append("catalog/card coverage mismatch or duplicate paths")
    return errors


def validate_evidence(library, mapping, catalog, files):
    """Check source provenance and complete method mapping, not research truth."""
    errors = []
    if not isinstance(library, dict) or (type(library.get("schema_version")) is not int or library["schema_version"] != 1) or not isinstance(library.get("sources"), list):
        return ["invalid source library schema"]
    if not isinstance(mapping, dict) or (type(mapping.get("schema_version")) is not int or mapping["schema_version"] != 1) or not isinstance(mapping.get("methods"), list):
        return ["invalid evidence map schema"]
    if not isinstance(catalog, dict) or not isinstance(catalog.get("methods"), list):
        return ["invalid catalog for evidence mapping"]
    method_ids = {item["id"] for item in catalog["methods"] if isinstance(item, dict) and isinstance(item.get("id"), str)}
    sources = {}
    access_values = {"full_text", "partial_text", "abstract_only", "metadata_only", "prior_review"}
    for source in library["sources"]:
        if not isinstance(source, dict):
            errors.append("source record must be an object")
            continue
        sid = source.get("id")
        if not isinstance(sid, str) or not re.fullmatch(r"[EBP][0-9]{2,}", sid) or sid in sources:
            errors.append("invalid/duplicate source ID")
            continue
        sources[sid] = source
        for field in ("title", "authors", "source_type", "inspected_scope", "claim_limit", "reuse"):
            if not isinstance(source.get(field), str) or not source[field].strip():
                errors.append(f"missing source {field}: {sid}")
        if source.get("access") not in access_values or (sid.startswith(("E", "B")) and source.get("access") == "prior_review"):
            errors.append(f"invalid source access: {sid}")
        if not https_url(source.get("url")):
            errors.append(f"invalid source URL: {sid}")
        if source.get("doi") is not None and (not isinstance(source["doi"], str) or not re.fullmatch(r"10\.\d{4,9}/\S+", source["doi"])):
            errors.append(f"invalid DOI: {sid}")
        if source.get("year") is not None and (type(source["year"]) is not int or not 1500 <= source["year"] <= 2100):
            errors.append(f"invalid source year: {sid}")
        if not strings(source.get("topics")) or not strings(source.get("methods")) or not set(source.get("methods", [])) <= method_ids:
            errors.append(f"invalid source topics/methods: {sid}")
        note = source.get("notes_file")
        if not isinstance(note, str) or note not in files:
            errors.append(f"missing source notes: {sid}")
        elif not re.search(r"^## " + re.escape(sid) + r"(?:\s|$)", files[note], re.M):
            errors.append(f"missing stable source heading: {sid}")
    seen = set()
    for entry in mapping["methods"]:
        if not isinstance(entry, dict):
            errors.append("evidence mapping must be an object")
            continue
        mid = entry.get("method_id")
        if not isinstance(mid, str) or mid not in method_ids or mid in seen:
            errors.append("invalid/duplicate method evidence mapping")
            continue
        seen.add(mid)
        for field in ("evidence_summary", "application_limit", "open_question"):
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                errors.append(f"missing evidence {field}: {mid}")
        for field, prefixes in (("provenance_ids", ("P", "E")), ("research_ids", ("E",)), ("book_ids", ("B",))):
            values = entry.get(field)
            if not strings(values, allow_empty=field != "provenance_ids"):
                errors.append(f"invalid evidence {field}: {mid}")
                continue
            for sid in values:
                if sid not in sources or not sid.startswith(prefixes):
                    errors.append(f"unknown/wrong-role evidence ID: {mid}: {sid}")
                elif not isinstance(sources[sid].get("methods"), list) or mid not in sources[sid]["methods"]:
                    errors.append(f"asymmetric method/source mapping: {mid}: {sid}")
                elif field == "research_ids" and sources[sid].get("access") == "metadata_only":
                    errors.append(f"metadata-only research cannot support a claim: {mid}: {sid}")
        knowledge = entry.get("knowledge_file")
        if not isinstance(knowledge, str) or not knowledge.startswith("references/knowledge/") or knowledge not in files:
            errors.append(f"missing knowledge route: {mid}")
        method = next((item for item in catalog["methods"] if item.get("id") == mid), {})
        expected_ids = {sid for field in ("provenance_ids", "research_ids", "book_ids") for sid in entry.get(field, []) if isinstance(sid, str)} if all(isinstance(entry.get(field), list) for field in ("provenance_ids", "research_ids", "book_ids")) else set()
        if not strings(method.get("source_ids")) or set(method.get("source_ids", [])) != expected_ids:
            errors.append(f"catalog/source mapping mismatch: {mid}")
        if method.get("knowledge_file") != knowledge or method.get("evidence_map") != "references/evidence-map.md#" + mid.lower():
            errors.append(f"catalog evidence route mismatch: {mid}")
        card = method.get("file")
        if card not in files or "(../evidence-map.md#" + mid.lower() + ")" not in files[card]:
            errors.append(f"card missing evidence map link: {mid}")
        if not re.search(r"^## " + re.escape(mid) + r"(?:\s|$)", files.get("references/evidence-map.md", ""), re.M):
            errors.append(f"missing readable evidence mapping: {mid}")
    if seen != method_ids:
        errors.append("method evidence coverage mismatch")
    if not sources:
        errors.append("empty source library")
    return errors


def validate(root=ROOT):
    root = Path(root).resolve()
    errors = []
    allowed = [line.strip() for line in public_file(root, "RELEASE_FILES.txt").read_text(encoding="utf-8").splitlines() if line.strip() and not line.lstrip().startswith("#")]
    if len(allowed) != len(set(allowed)):
        errors.append("duplicate allowlist paths")
    skip = {".git", "__pycache__", "dist", ".venv"}
    actual = {path.relative_to(root).as_posix() for path in root.rglob("*") if (path.is_file() or path.is_symlink()) and not any(part in skip for part in path.relative_to(root).parts) and path.suffix != ".pyc"}
    has_manifest = "RELEASE_MANIFEST.json" in actual
    actual.discard("RELEASE_MANIFEST.json")
    if actual != set(allowed):
        errors.append(f"allowlist mismatch: unreviewed={sorted(actual-set(allowed))}; missing={sorted(set(allowed)-actual)}")
    files = {}
    for name in allowed:
        try:
            path = public_file(root, name)
            if any(part in PRIVATE_NAMES or part == ".env" or part.startswith(".env.") for part in PurePosixPath(name).parts):
                errors.append(f"private state/configuration release path: {name}")
            text = path.read_text(encoding="utf-8")
            files[name] = text
            if DENIED.search(text):
                errors.append(f"private path or credential marker: {name}")
            if path.suffix == ".json":
                json.loads(text)
            if path.suffix == ".md":
                for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
                    link = link.strip("<>")
                    parts = urlsplit(link)
                    if parts.scheme or parts.netloc:
                        if not https_url(link):
                            errors.append(f"unexpected link scheme: {name}")
                        continue
                    target = (path.parent / unquote(parts.path)).resolve() if parts.path else path.resolve()
                    if root not in target.parents or not target.is_file():
                        errors.append(f"broken/outside link: {name}: {link}")
        except (ValueError, OSError) as error:
            errors.append(f"{name}: {error}")

    prefix = "skills/leadership-toolbox/"
    package_files = {name.removeprefix(prefix): text for name, text in files.items() if name.startswith(prefix)}
    try:
        catalog = json.loads(package_files.get("references/catalog.json", "null"))
        dimensions = json.loads(package_files.get("references/dimensions.json", "null"))
        errors.extend(validate_catalog(catalog, dimensions, package_files))
        if isinstance(catalog, dict):
            library = json.loads(package_files.get("references/sources.json", "null"))
            mapping = json.loads(package_files.get("references/evidence-map.json", "null"))
            errors.extend(validate_evidence(library, mapping, catalog, package_files))
    except ValueError as error:
        errors.append(f"invalid catalog/dimension JSON: {error}")
        catalog = None
    version = catalog.get("package_version") if isinstance(catalog, dict) else None
    skill = package_files.get("SKILL.md", "")
    front = re.match(r"\A---\n(.*?)\n---(?:\n|\Z)", skill, re.S)
    if not front or not re.search(r"^name: leadership-toolbox$", front[1], re.M) or not re.search(r"^description: .+", front[1], re.M):
        errors.append("invalid skill frontmatter")
    if front and (not isinstance(version, str) or not re.search(r'^  version: [\"\']?' + re.escape(version) + r'[\"\']?$', front[1], re.M)):
        errors.append("skill/catalog version mismatch")
    if "$leadership-toolbox" not in package_files.get("agents/openai.yaml", ""):
        errors.append("missing invocation prompt")
    build_version = re.search(r'^VERSION = "([^"]+)"$', files.get("scripts/build_release.py", ""), re.M)
    if not build_version or build_version[1] != version:
        errors.append("release/catalog version mismatch")
    if has_manifest:
        try:
            manifest = json.loads(public_file(root, "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
            if not isinstance(manifest, dict) or set(manifest) != {"version", "files"} or not isinstance(manifest.get("files"), dict):
                raise ValueError("invalid checksum manifest schema")
            if manifest["version"] != version or set(manifest["files"]) != set(allowed):
                errors.append("checksum manifest version/file list mismatch")
            for name, expected in manifest["files"].items():
                if name not in files or not isinstance(expected, str) or not re.fullmatch(r"[a-f0-9]{64}", expected):
                    errors.append(f"invalid checksum entry: {name}")
                    continue
                if hashlib.sha256(public_file(root, name).read_bytes()).hexdigest() != expected:
                    errors.append(f"checksum mismatch: {name}")
        except (ValueError, OSError) as error:
            errors.append(f"manifest: {error}")
    if errors:
        raise ValueError("\n".join(errors))
    return len(allowed), len(catalog["methods"])


if __name__ == "__main__":
    try:
        files, methods = validate()
        print(f"PASS: {files} reviewed files; {methods} methods; links, JSON, versions and structured profiles")
        print("Leak checks are heuristic. External sources and human outcomes require separate review.")
    except (ValueError, OSError) as error:
        sys.exit(str(error))
