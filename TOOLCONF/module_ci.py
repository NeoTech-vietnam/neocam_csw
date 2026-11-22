#!/usr/bin/env python3
"""Validate module-triggered development builds before fetching dependencies."""
import argparse
import json
import os
from pathlib import Path
import re

import yaml


def validate(packages, package, sha, source_repository, ref, default_branch):
    branch = ref.removeprefix("refs/heads/")
    if (not ref.startswith("refs/heads/") or branch == default_branch
            or not re.fullmatch(r"(?:feat|feature|fix|dev)/[A-Za-z0-9][A-Za-z0-9._/-]*", branch)
            or ".." in branch or "//" in branch or branch.endswith("/")
            or any(part.startswith(".") or part.endswith((".", ".lock")) for part in branch.split("/"))):
        raise ValueError("Module CI requires a development branch; main/default branches and tags are forbidden")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Module CI requires the exact pushed module SHA, not a branch or tag")
    if not re.fullmatch(r"NeoTech-vietnam/[A-Za-z0-9_.-]+", source_repository):
        raise ValueError("Invalid source module repository")
    selected = packages.get(package)
    expected = f"https://github.com/{source_repository}".casefold()
    if not isinstance(selected, dict) or selected.get("repo", "").removesuffix(".git").casefold() != expected:
        raise ValueError("Package must exist in packages.yml and belong to the requesting module repository")
    return {"package": package, "module_sha": sha, "source_repository": source_repository,
            "project_branch": branch, "project_sha": os.environ.get("GITHUB_SHA", "")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--source-repository", required=True)
    args = parser.parse_args()
    try:
        if os.environ.get("GITHUB_EVENT_NAME") != "workflow_dispatch":
            raise ValueError("Module integration requires workflow_dispatch")
        packages = yaml.safe_load(Path("packages.yml").read_text(encoding="utf-8"))["packages"]
        report = validate(packages, args.package, args.sha, args.source_repository,
                          os.environ.get("GITHUB_REF", ""), os.environ.get("DEFAULT_BRANCH", "main"))
        output = Path("_out/module-ci-request.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
    except (ValueError, OSError, KeyError, TypeError, yaml.YAMLError) as error:
        parser.exit(1, f"Module CI rejected: {error}\n")


if __name__ == "__main__":
    main()
