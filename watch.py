#!/usr/bin/env python3
"""Watch Cursor Origin's public docs, snapshot what changed, commit it."""
import argparse
import datetime as dt
import difflib
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import requests
import yaml
from bs4 import BeautifulSoup, Comment, NavigableString, Tag

USER_AGENT = "origin-watch (+https://github.com/aiedwardyi/origin-watch)"
TIMEOUT = 30
DEFAULT_MIN_CHARS = 200
ALLOWED_HOST = "cursor.com"
EXT = {"md": "md", "yaml": "yaml", "txt": "txt", "html": "txt"}

# HTML elements that never carry page content.
DROP_TAGS = ["script", "style", "noscript", "template", "svg", "iframe", "nav", "header", "footer"]
DROP_SELECTOR = "[class*=cookie],[id*=cookie],[class*=consent],[id*=consent]"
BLOCK_TAGS = {
    "address", "article", "aside", "blockquote", "caption", "dd", "details", "div", "dl", "dt",
    "fieldset", "figcaption", "figure", "form", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "li",
    "main", "ol", "p", "pre", "section", "summary", "table", "tbody", "td", "tfoot", "th",
    "thead", "tr", "ul",
}


class SectionNotFound(Exception):
    pass


# --- normalize -----------------------------------------------------------------

def normalize_text(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="replace").lstrip("\ufeff")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines) + "\n" if lines else ""


def _flush(out: list, buf: list) -> None:
    text = " ".join("".join(buf).split())
    if text:
        out.append(text)
    buf.clear()


def _html_lines(node: Tag, out: list, buf: list) -> None:
    """Block elements start new lines, inline text joins; <pre> is kept verbatim."""
    for child in node.children:
        if isinstance(child, Comment):
            continue
        if isinstance(child, NavigableString):
            buf.append(str(child))
        elif not isinstance(child, Tag):
            continue
        elif child.name == "pre":
            _flush(out, buf)
            out.extend(child.get_text().split("\n"))
        elif child.name == "br":
            _flush(out, buf)
        elif child.name in BLOCK_TAGS:
            _flush(out, buf)
            _html_lines(child, out, buf)
            _flush(out, buf)
        else:
            _html_lines(child, out, buf)


def normalize_html(raw: bytes) -> str:
    soup = BeautifulSoup(raw, "html.parser")
    root = soup.find("main") or soup.find("article") or soup.body or soup
    for tag in root.find_all(DROP_TAGS):
        tag.decompose()
    for tag in root.select(DROP_SELECTOR):
        tag.decompose()
    lines, buf = [], []
    _html_lines(root, lines, buf)
    _flush(lines, buf)
    return normalize_text("\n".join(lines).encode("utf-8"))


def extract_section(text: str, heading: str):
    """Lines from `heading` up to the next heading of the same or higher level, or None."""
    level = len(heading) - len(heading.lstrip("#"))
    lines = text.split("\n")
    start = next((i for i, line in enumerate(lines) if line.rstrip() == heading), None)
    if start is None:
        return None
    end = len(lines)
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if line.startswith("#") and 0 < len(line) - len(line.lstrip("#")) <= level:
            end = i
            break
    return normalize_text("\n".join(lines[start:end]).encode("utf-8"))


def normalize(raw: bytes, type_: str, section: str = None) -> str:
    text = normalize_html(raw) if type_ == "html" else normalize_text(raw)
    if section:
        text = extract_section(text, section)
        if text is None:
            raise SectionNotFound(section)
    return text


# --- fetch + validate ----------------------------------------------------------

class SourceFailure(Exception):
    pass


def http_fetch(url: str):
    r = requests.get(url, timeout=TIMEOUT, allow_redirects=True, headers={"User-Agent": USER_AGENT})
    return r.status_code, r.url, r.content


def host_allowed(url: str) -> bool:
    host = urlparse(url).hostname or ""
    return host == ALLOWED_HOST or host.endswith("." + ALLOWED_HOST)


def looks_like_html(body: bytes) -> bool:
    return body.lstrip()[:32].lower().startswith((b"<!doctype html", b"<html"))


def fetch_source(src: dict, fetch) -> str:
    """Normalized text for one source, or SourceFailure. Never touches disk."""
    try:
        status, final_url, body = fetch(src["url"])
    except Exception as e:
        raise SourceFailure(f"fetch error: {e}")
    if not host_allowed(final_url):
        raise SourceFailure(f"final host not allowed: {final_url}")
    if status != 200:
        raise SourceFailure(f"HTTP {status}")
    if src["type"] != "html" and looks_like_html(body):
        raise SourceFailure("HTML document at a text endpoint")
    try:
        text = normalize(body, src["type"], src.get("section"))
    except SectionNotFound as e:
        raise SourceFailure(f"section not found: {e}")
    if not text:
        raise SourceFailure("empty after normalization")
    floor = src.get("min_chars", DEFAULT_MIN_CHARS)
    if len(text) < floor:
        raise SourceFailure(f"too short: {len(text)} < {floor} chars")
    if src["expect"] not in text:
        raise SourceFailure(f"expect string not found: {src['expect']!r}")
    return text


def load_sources(path: Path) -> list:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    sources = data.get("sources") or []
    seen = set()
    for src in sources:
        missing = {"id", "url", "type", "expect"} - set(src)
        if missing:
            raise ValueError(f"source missing {sorted(missing)}: {src}")
        sid = src["id"]
        if not sid.replace("-", "").isalnum() or sid != sid.lower() or sid in seen:
            raise ValueError(f"source id must be a unique lowercase slug: {sid!r}")
        if src["type"] not in EXT:
            raise ValueError(f"source {sid}: type must be one of {sorted(EXT)}")
        seen.add(sid)
    if not sources:
        raise ValueError(f"no sources in {path}")
    return sources


# --- git + files ---------------------------------------------------------------

def git(repo: Path, *args, check=True):
    return subprocess.run(["git", "-C", str(repo), *args], check=check, capture_output=True)


def committed(repo: Path, rel: str):
    """Content of `rel` at HEAD, or None when there is no such committed file."""
    if git(repo, "rev-parse", "--verify", "-q", "HEAD", check=False).returncode != 0:
        return None
    if git(repo, "cat-file", "-e", f"HEAD:{rel}", check=False).returncode != 0:
        return None
    return git(repo, "show", f"HEAD:{rel}").stdout.decode("utf-8")


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    with os.fdopen(fd, "wb") as f:
        f.write(text.encode("utf-8"))
    os.replace(tmp, path)


def unified(old: str, new: str, rel: str):
    lines = list(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
                                      fromfile=f"a/{rel}", tofile=f"b/{rel}", n=3))
    plus = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
    minus = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))
    return "".join(lines), plus, minus


def report_text(src: dict, fetched: str, diff: str, plus: int, minus: int) -> str:
    head = [f"# {src['id']} changed", "", f"- url: {src['url']}", f"- fetched: {fetched}",
            f"- lines: +{plus}/-{minus}"]
    if src.get("note"):
        head.append(f"- note: {src['note']}")
    # Four backticks: diffs of Markdown pages contain ``` fences of their own.
    return "\n".join(head) + "\n\n````diff\n" + diff + "````\n"


def prepend_changelog(path: Path, entries: list) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else "# Changelog\n"
    lines = text.split("\n")
    first = next((i for i, line in enumerate(lines) if line.startswith("## ")), None)
    if first is None:
        text = text.rstrip("\n") + "\n\n" + "\n".join(entries) + "\n"
    else:
        lines[first:first] = entries
        text = "\n".join(lines)
    write_atomic(path, text)


def commit(repo: Path, paths: list, changed: list, seeded: list, date: str) -> str:
    if len(changed) == 1:
        subject = f"watch: {changed[0]} changed {date}"
    elif changed:
        subject = f"watch: {len(changed)} sources changed {date}"
    else:
        subject = f"watch: seed snapshots {date}"
    body = []
    if len(changed) > 1:
        body.append("changed: " + ", ".join(changed))
    if seeded:
        body.append("seeded: " + ", ".join(seeded))
    git(repo, "add", "--", *paths)
    git(repo, "commit", "-q", "-m", subject, *[arg for b in body for arg in ("-m", b)])
    return subject


def step_summary(rows: list, outcome: str) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as f:
        f.write("| source | result |\n|---|---|\n")
        for sid, result in rows:
            f.write(f"| {sid} | {result} |\n")
        f.write(f"\n{outcome}\n")


# --- run -----------------------------------------------------------------------

def run(repo: Path, sources: list, seed: bool, fetch, now: dt.datetime) -> int:
    stamp = now.strftime("%Y-%m-%dT%H%M%SZ")
    date = now.strftime("%Y-%m-%d")
    fetched = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    changed, seeded, failed, paths, entries, rows = [], [], [], [], [], []
    for src in sources:
        sid = src["id"]
        rel = f"snapshots/{sid}.{EXT[src['type']]}"
        try:
            text = fetch_source(src, fetch)
            old = committed(repo, rel)
            if old is None and not seed:
                raise SourceFailure("no committed baseline (run with --seed)")
        except SourceFailure as e:
            failed.append(sid)
            rows.append((sid, f"FAILED: {e}"))
        except Exception as e:  # one broken source never takes down the run
            failed.append(sid)
            rows.append((sid, f"FAILED: {type(e).__name__}: {e}"))
        else:
            if old is None:
                write_atomic(repo / rel, text)
                paths.append(rel)
                seeded.append(sid)
                rows.append((sid, "seeded"))
            elif old == text:
                rows.append((sid, "unchanged"))
            else:
                diff, plus, minus = unified(old, text, rel)
                report = f"changes/{stamp}-{sid}.md"
                write_atomic(repo / report, report_text(src, fetched, diff, plus, minus))
                write_atomic(repo / rel, text)
                paths += [rel, report]
                entries.append((sid, f"## {date} - {sid} changed (+{plus}/-{minus} lines) - [report]({report})"))
                changed.append(sid)
                rows.append((sid, f"changed +{plus}/-{minus}"))
        print(f"{sid}: {rows[-1][1]}")
    if entries:
        prepend_changelog(repo / "CHANGELOG.md", [line for _, line in sorted(entries)])
        paths.append("CHANGELOG.md")
    outcome = commit(repo, paths, sorted(changed), sorted(seeded), date) if paths else "no changes"
    if failed:
        outcome += f"; {len(failed)} source(s) FAILED: {', '.join(failed)}"
    print(outcome)
    step_summary(rows, outcome)
    return 2 if failed else 0


def main(argv=None, fetch=http_fetch, now=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument("--sources", type=Path, help="default: <repo>/sources.yml")
    ap.add_argument("--seed", action="store_true", help="create baselines for sources with no committed snapshot")
    args = ap.parse_args(argv)
    sources = load_sources(args.sources or args.repo / "sources.yml")
    return run(args.repo, sources, args.seed, fetch, now or dt.datetime.now(dt.timezone.utc))


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors="replace")
    sys.exit(main())
