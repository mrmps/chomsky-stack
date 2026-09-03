#!/usr/bin/env python3
"""Find code-review leads for junk-detection. Output is triage, not a verdict."""

import argparse
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


CODE_EXTENSIONS = {
    ".c", ".cc", ".cpp", ".cs", ".css", ".ex", ".exs", ".go", ".h", ".hpp",
    ".java", ".js", ".jsx", ".kt", ".kts", ".lua", ".m", ".mm", ".php",
    ".py", ".rb", ".rs", ".scala", ".sh", ".sql", ".svelte", ".swift", ".ts",
    ".tsx", ".vue", ".zig",
}
EXCLUDED_PARTS = {
    ".git", ".next", ".output", ".turbo", ".venv", "build", "coverage", "dist",
    "generated", "node_modules", "target", "vendor", "venv",
}
EXCLUDED_SUFFIXES = (".min.js", ".min.css", ".snap")

MARKERS = {
    "compatibility": re.compile(
        r"\b(backwards?|compat(?:ibility)?|legacy|deprecated|migration|shim|fallback|old[-_ ]?(?:api|format|name|path|version))\b",
        re.IGNORECASE,
    ),
    "suppression": re.compile(
        r"@ts-(?:ignore|expect-error)|eslint-disable|type:\s*ignore|noqa|pragma:\s*no cover|istanbul ignore|\bas any\b",
        re.IGNORECASE,
    ),
    "evaluator": re.compile(
        r"PYTEST_CURRENT_TEST|NODE_ENV.{0,20}\btest\b|os\._exit\(0\)|assert\s+True\b|"
        r"(?:describe|it|test)\.only\b|(?:describe|it|test)\.skip\b|pytest\.mark\.(?:skip|xfail)",
        re.IGNORECASE,
    ),
    "stub": re.compile(
        r"\b(TODO|FIXME|not implemented|placeholder|hard[- ]?coded|temporary workaround|dummy data|mock data)\b",
        re.IGNORECASE,
    ),
}
BRANCHES = re.compile(
    r"\b(if|elif|else\s+if|for|while|case|catch|except|switch|match)\b|&&|\|\|"
)


def run_git(
    root: Path,
    args: Sequence[str],
    check: bool = True,
    nul_terminated: bool = False,
) -> List[str]:
    result = subprocess.run(
        ["git", "-C", str(root)] + list(args),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        detail = os.fsdecode(result.stderr).strip() or "git command failed"
        raise RuntimeError("git {}: {}".format(" ".join(args), detail))
    if result.returncode != 0:
        return []
    records = result.stdout.split(b"\0") if nul_terminated else result.stdout.splitlines()
    return [os.fsdecode(record) for record in records if record]


def choose_base(root: Path, requested: Optional[str]) -> Optional[str]:
    if requested:
        if (
            run_git(root, ["rev-parse", "--verify", requested], check=False)
            and run_git(root, ["merge-base", "HEAD", requested], check=False)
        ):
            return requested
        raise RuntimeError("base ref does not exist or shares no merge base with HEAD: {}".format(requested))
    remote_head = run_git(
        root,
        ["symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
        check=False,
    )
    candidates = ["origin/main"]
    candidates.extend(remote_head)
    candidates.extend(("main", "origin/master", "master"))
    for candidate in candidates:
        if (
            run_git(root, ["rev-parse", "--verify", candidate], check=False)
            and run_git(root, ["merge-base", "HEAD", candidate], check=False)
        ):
            return candidate
    return None


def diff_files(root: Path, base: Optional[str]) -> List[str]:
    paths = set()
    if base:
        merge_base = run_git(root, ["merge-base", "HEAD", base])
        if merge_base:
            paths.update(run_git(
                root,
                ["diff", "--name-only", "--diff-filter=ACMR", "-z", merge_base[0], "HEAD"],
                nul_terminated=True,
            ))
    paths.update(run_git(
        root,
        ["diff", "--name-only", "--diff-filter=ACMR", "-z"],
        nul_terminated=True,
    ))
    paths.update(run_git(
        root,
        ["diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"],
        nul_terminated=True,
    ))
    paths.update(run_git(
        root,
        ["ls-files", "--others", "--exclude-standard", "-z"],
        nul_terminated=True,
    ))
    return sorted(paths)


def all_files(root: Path) -> List[str]:
    paths = set(run_git(root, ["ls-files", "-z"], nul_terminated=True))
    paths.update(run_git(
        root,
        ["ls-files", "--others", "--exclude-standard", "-z"],
        nul_terminated=True,
    ))
    return sorted(paths)


def is_candidate(relative: str) -> bool:
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        return False
    if relative_path.suffix.lower() not in CODE_EXTENSIONS:
        return False
    if any(part in EXCLUDED_PARTS for part in relative_path.parts):
        return False
    if relative_path.name.endswith(EXCLUDED_SUFFIXES):
        return False
    return True


def source_lines(root: Path, relative: str) -> Optional[List[str]]:
    if not is_candidate(relative):
        return None

    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory = getattr(os, "O_DIRECTORY", 0)
    if not nofollow or os.open not in os.supports_dir_fd:
        return None

    descriptors = []
    try:
        current = os.open(root, os.O_RDONLY | directory)
        descriptors.append(current)
        parts = Path(relative).parts
        for part in parts[:-1]:
            current = os.open(
                part,
                os.O_RDONLY | directory | nofollow,
                dir_fd=current,
            )
            descriptors.append(current)

        file_descriptor = os.open(
            parts[-1],
            os.O_RDONLY | nofollow,
            dir_fd=current,
        )
        descriptors.append(file_descriptor)
        if not stat.S_ISREG(os.fstat(file_descriptor).st_mode):
            return None

        descriptors.pop()
        with os.fdopen(file_descriptor, "r", encoding="utf-8", errors="ignore") as source:
            return source.read().splitlines()
    except OSError:
        return None
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


def analyze_file(lines: List[str], relative: str, large_lines: int) -> Tuple[Dict[str, object], List[Dict[str, object]]]:
    nonblank = [line for line in lines if line.strip()]
    branch_count = sum(len(BRANCHES.findall(line)) for line in lines)
    max_indent = 0
    for line in nonblank:
        expanded = line.expandtabs(4)
        max_indent = max(max_indent, len(expanded) - len(expanded.lstrip(" ")))

    markers = []
    for number, line in enumerate(lines, start=1):
        for kind, pattern in MARKERS.items():
            if pattern.search(line):
                markers.append({
                    "kind": kind,
                    "path": relative,
                    "line": number,
                    "text": line.strip()[:180],
                })

    metric = {
        "path": relative,
        "lines": len(lines),
        "nonblank_lines": len(nonblank),
        "branch_tokens": branch_count,
        "max_indent_spaces": max_indent,
        "large": len(lines) >= large_lines,
        "complexity_lead": branch_count >= 35 or max_indent >= 20,
    }
    return metric, markers


def terminal_safe(value: str) -> str:
    escaped = []
    for character in value:
        if character.isprintable():
            escaped.append(character)
            continue
        codepoint = ord(character)
        escaped.append(
            "\\x{:02x}".format(codepoint)
            if codepoint <= 0xFF
            else "\\u{:04x}".format(codepoint)
        )
    return "".join(escaped)


def render_text(result: Dict[str, object], marker_limit: int) -> None:
    print("Junk-detection hotspot scan (leads, not findings)")
    print(
        "scope: {} | base: {} | code files: {}".format(
            result["scope"], terminal_safe(str(result["base"])), result["file_count"]
        )
    )

    metrics = result["metrics"]
    large = sorted((item for item in metrics if item["large"]), key=lambda item: item["lines"], reverse=True)
    complex_leads = sorted(
        (item for item in metrics if item["complexity_lead"]),
        key=lambda item: (item["branch_tokens"], item["max_indent_spaces"]),
        reverse=True,
    )

    print("\nLarge files")
    if not large:
        print("  none")
    for item in large:
        print("  {}: {} lines".format(terminal_safe(str(item["path"])), item["lines"]))

    print("\nComplexity leads")
    if not complex_leads:
        print("  none")
    for item in complex_leads[:30]:
        print(
            "  {}: branches={}, max-indent={}, lines={}".format(
                terminal_safe(str(item["path"])),
                item["branch_tokens"],
                item["max_indent_spaces"],
                item["lines"],
            )
        )

    grouped = result["markers"]
    for kind in sorted(grouped):
        items = grouped[kind]
        print("\n{} markers ({})".format(kind.capitalize(), len(items)))
        if not items:
            print("  none")
        for item in items[:marker_limit]:
            print(
                "  {}:{}: {}".format(
                    terminal_safe(str(item["path"])),
                    item["line"],
                    terminal_safe(str(item["text"])),
                )
            )
        if len(items) > marker_limit:
            print("  ... {} more".format(len(items) - marker_limit))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: current directory)")
    parser.add_argument("--scope", choices=("diff", "all"), default="diff")
    parser.add_argument("--base", help="trunk ref for diff scope (auto-detects origin/main/main)")
    parser.add_argument("--large-lines", type=int, default=500)
    parser.add_argument("--marker-limit", type=int, default=40)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not (root / ".git").exists():
        print("error: not a git repository root: {}".format(root), file=sys.stderr)
        return 2

    try:
        base = choose_base(root, args.base)
        relative_paths = diff_files(root, base) if args.scope == "diff" else all_files(root)
    except RuntimeError as error:
        print("error: {}".format(error), file=sys.stderr)
        return 2

    metrics = []
    grouped_markers = {kind: [] for kind in MARKERS}
    for relative in relative_paths:
        lines = source_lines(root, relative)
        if lines is None:
            continue
        metric, markers = analyze_file(lines, relative, args.large_lines)
        metrics.append(metric)
        for marker in markers:
            grouped_markers[marker["kind"]].append(marker)

    result = {
        "scope": args.scope,
        "base": base or "none",
        "file_count": len(metrics),
        "metrics": metrics,
        "markers": grouped_markers,
    }
    if args.json:
        json.dump(result, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        render_text(result, args.marker_limit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
