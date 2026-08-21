import contextlib
import datetime as dt
import io
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import watch

NOW = dt.datetime(2026, 8, 21, 5, 0, 0, tzinfo=dt.timezone.utc)
STAMP = "2026-08-21T050000Z"
DATE = "2026-08-21"
URL = "https://cursor.com/docs/origin/page.md"
V1 = b"# Origin page\n\nline one\nline two\nline three\nline four\nline five\nline six\nline seven\nline eight\n"
V2 = V1.replace(b"line eight", b"line eight changed")

SOURCES = """sources:
  - id: page
    url: https://cursor.com/docs/origin/page.md
    type: md
    expect: "Origin"
    min_chars: 10
    note: test page
"""


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout


def fake(pages):
    """pages: url -> (status, final_url, body), or an Exception to raise."""
    def fetch(url):
        hit = pages[url]
        if isinstance(hit, Exception):
            raise hit
        return hit
    return fetch


def ok(body, url=URL):
    return {url: (200, url, body)}


class WatchTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name) / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.name", "test")
        git(self.repo, "config", "user.email", "test@example.com")
        git(self.repo, "config", "commit.gpgsign", "false")
        (self.repo / ".gitattributes").write_text("* text=auto eol=lf\n", newline="\n")
        self.write_sources(SOURCES)
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-q", "-m", "init")

    def tearDown(self):
        self._tmp.cleanup()

    def write_sources(self, text):
        (self.repo / "sources.yml").write_text(text, newline="\n")

    def run_watch(self, pages, *flags):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = watch.main(["--repo", str(self.repo), *flags], fetch=fake(pages), now=NOW)
        return rc, out.getvalue()

    def subjects(self):
        return git(self.repo, "log", "--format=%s").split("\n")[:-1]

    def head_files(self):
        return sorted(git(self.repo, "show", "--name-only", "--format=", "HEAD").split())

    def status(self):
        return git(self.repo, "status", "--porcelain")

    def snapshot(self, name="page.md"):
        return (self.repo / "snapshots" / name).read_bytes()

    def changelog_entries(self):
        text = (self.repo / "CHANGELOG.md").read_text(encoding="utf-8")
        return [line for line in text.split("\n") if line.startswith("## ")]


class SeedTest(WatchTestBase):
    def test_seed_writes_snapshot_and_seed_commit(self):
        rc, _ = self.run_watch(ok(V1), "--seed")
        self.assertEqual(rc, 0)
        self.assertEqual(self.snapshot(), V1)
        self.assertEqual(self.subjects()[0], f"watch: seed snapshots {DATE}")
        self.assertEqual(self.head_files(), ["snapshots/page.md"])
        self.assertFalse((self.repo / "changes").exists())
        self.assertFalse((self.repo / "CHANGELOG.md").exists())
        self.assertEqual(self.status(), "")

    def test_missing_baseline_without_seed_fails_loud(self):
        rc, out = self.run_watch(ok(V1))
        self.assertEqual(rc, 2)
        self.assertIn("no committed baseline", out)
        self.assertFalse((self.repo / "snapshots").exists())
        self.assertEqual(self.subjects(), ["init"])

    def test_seed_does_not_reseed_existing_baseline(self):
        self.run_watch(ok(V1), "--seed")
        rc, _ = self.run_watch(ok(V1), "--seed")
        self.assertEqual(rc, 0)
        self.assertEqual(len(self.subjects()), 2)


class ChangeTest(WatchTestBase):
    def setUp(self):
        super().setUp()
        self.run_watch(ok(V1), "--seed")

    def test_change_writes_report_changelog_and_one_commit(self):
        rc, _ = self.run_watch(ok(V2))
        self.assertEqual(rc, 0)
        self.assertEqual(self.snapshot(), V2)
        self.assertEqual(self.subjects()[0], f"watch: page changed {DATE}")
        self.assertEqual(len(self.subjects()), 3)
        report = f"changes/{STAMP}-page.md"
        self.assertEqual(self.head_files(), ["CHANGELOG.md", report, "snapshots/page.md"])
        self.assertEqual(self.status(), "")
        text = (self.repo / report).read_text(encoding="utf-8")
        self.assertIn(URL, text)
        self.assertIn("2026-08-21T05:00:00Z", text)
        self.assertIn("-line eight\n", text)
        self.assertIn("+line eight changed\n", text)
        self.assertIn("line five", text)  # context
        self.assertNotIn("line one", text)  # hunks only, never the whole file
        self.assertEqual(self.changelog_entries(),
                         [f"## {DATE} - page changed (+1/-1 lines) - [report]({report})"])

    def test_unchanged_rerun_is_silent(self):
        self.run_watch(ok(V2))
        before = self.subjects()
        rc, _ = self.run_watch(ok(V2))
        self.assertEqual(rc, 0)
        self.assertEqual(self.subjects(), before)
        self.assertEqual(len(list((self.repo / "changes").iterdir())), 1)
        self.assertEqual(self.status(), "")

    def test_no_timestamp_in_snapshot(self):
        self.run_watch(ok(V2))
        self.assertNotIn(b"2026-08-21", self.snapshot())

    def test_only_owned_paths_committed(self):
        (self.repo / "stray.txt").write_text("x")
        self.write_sources(SOURCES + "# edited\n")
        self.run_watch(ok(V2))
        self.assertEqual(self.head_files(), ["CHANGELOG.md", f"changes/{STAMP}-page.md", "snapshots/page.md"])
        self.assertIn("?? stray.txt", self.status())
        self.assertIn(" M sources.yml", self.status())

    def test_new_changelog_entries_go_on_top(self):
        self.run_watch(ok(V2))
        rc, _ = self.run_watch(ok(V2.replace(b"line one", b"line 1")))
        self.assertEqual(rc, 0)
        entries = self.changelog_entries()
        self.assertEqual(len(entries), 2)
        self.assertTrue(entries[0].startswith(f"## {DATE} - page changed (+1/-1 lines)"))


class FailureTest(WatchTestBase):
    def setUp(self):
        super().setUp()
        self.run_watch(ok(V1), "--seed")

    def assert_failed(self, pages, reason):
        with self.subTest(reason=reason):
            rc, out = self.run_watch(pages)
            self.assertEqual(rc, 2)
            self.assertIn(reason, out)
            self.assertEqual(self.snapshot(), V1)
            self.assertEqual(len(self.subjects()), 2)
            self.assertFalse((self.repo / "changes").exists())
            self.assertEqual(self.status(), "")

    def test_validation_failures_keep_snapshot_and_exit_2(self):
        self.assert_failed({URL: (500, URL, V2)}, "HTTP 500")
        self.assert_failed({URL: (404, URL, b'{"error":"File not found"}')}, "HTTP 404")
        self.assert_failed({URL: (200, "https://evil.example/x.md", V2)}, "host")
        self.assert_failed({URL: (200, URL, b"# Other product\n" + b"x" * 300)}, "expect")
        self.assert_failed({URL: (200, URL, b"# Origin\n")}, "too short")
        self.assert_failed({URL: (200, URL, b"\n\n")}, "empty")
        self.assert_failed({URL: (200, URL, b"<!DOCTYPE html><html><body>Origin " + b"x" * 300)}, "HTML document")
        self.assert_failed({URL: ConnectionError("boom")}, "boom")

    def test_subdomain_host_allowed(self):
        rc, _ = self.run_watch({URL: (200, "https://www.cursor.com/docs/origin/page.md", V2)})
        self.assertEqual(rc, 0)
        self.assertEqual(self.snapshot(), V2)

    def test_step_summary_lists_failure(self):
        summary = self.repo.parent / "summary.md"
        os.environ["GITHUB_STEP_SUMMARY"] = str(summary)
        try:
            self.run_watch({URL: (500, URL, V2)})
        finally:
            del os.environ["GITHUB_STEP_SUMMARY"]
        self.assertIn("HTTP 500", summary.read_text(encoding="utf-8"))


TWO = """sources:
  - id: b-page
    url: https://cursor.com/b.md
    type: md
    expect: "Origin"
    min_chars: 10
  - id: a-page
    url: https://cursor.com/a.md
    type: md
    expect: "Origin"
    min_chars: 10
"""
A, B, C = "https://cursor.com/a.md", "https://cursor.com/b.md", "https://cursor.com/c.md"


class MultiSourceTest(WatchTestBase):
    def setUp(self):
        super().setUp()
        self.write_sources(TWO)
        self.run_watch({A: (200, A, V1), B: (200, B, V1)}, "--seed")

    def test_one_commit_for_several_changes_sorted_by_id(self):
        rc, _ = self.run_watch({A: (200, A, V2), B: (200, B, V2)})
        self.assertEqual(rc, 0)
        self.assertEqual(self.subjects()[0], f"watch: 2 sources changed {DATE}")
        self.assertEqual(len(self.subjects()), 3)
        body = git(self.repo, "log", "-1", "--format=%b")
        self.assertIn("a-page", body)
        self.assertIn("b-page", body)
        self.assertEqual([e.split(" - ")[1] for e in self.changelog_entries()],
                         ["a-page changed (+1/-1 lines)", "b-page changed (+1/-1 lines)"])

    def test_one_bad_source_does_not_block_the_rest(self):
        rc, out = self.run_watch({A: (200, A, V2), B: (500, B, V2)})
        self.assertEqual(rc, 2)
        self.assertEqual(self.subjects()[0], f"watch: a-page changed {DATE}")
        self.assertEqual(self.snapshot("a-page.md"), V2)
        self.assertEqual(self.snapshot("b-page.md"), V1)
        self.assertIn("b-page", out)

    def test_seed_and_change_in_one_run_is_one_commit(self):
        self.write_sources(TWO + "  - id: c-page\n    url: https://cursor.com/c.md\n    type: md\n    expect: Origin\n    min_chars: 10\n")
        rc, _ = self.run_watch({A: (200, A, V2), B: (200, B, V1), C: (200, C, V1)}, "--seed")
        self.assertEqual(rc, 0)
        self.assertEqual(len(self.subjects()), 3)
        self.assertEqual(self.subjects()[0], f"watch: a-page changed {DATE}")
        self.assertIn("seeded: c-page", git(self.repo, "log", "-1", "--format=%b"))
        self.assertEqual(self.head_files(),
                         ["CHANGELOG.md", f"changes/{STAMP}-a-page.md", "snapshots/a-page.md", "snapshots/c-page.md"])


class SourceTypesTest(WatchTestBase):
    def test_html_source_snapshots_extracted_text(self):
        url = "https://cursor.com/docs/api/origin/changelog"
        self.write_sources(f"sources:\n  - id: cl\n    url: {url}\n    type: html\n    expect: Changelog\n    min_chars: 10\n")
        html = b"<html><body><nav>menu</nav><main><h1>Origin API Changelog</h1><p>Added. <code>x</code> thing.</p></main></body></html>"
        rc, _ = self.run_watch({url: (200, url, html)}, "--seed")
        self.assertEqual(rc, 0)
        self.assertEqual(self.snapshot("cl.txt"), b"Origin API Changelog\nAdded. x thing.\n")

    def test_section_source_snapshots_only_that_section(self):
        url = "https://cursor.com/llms.txt"
        self.write_sources(f'sources:\n  - id: idx\n    url: {url}\n    type: txt\n    expect: origin\n    min_chars: 10\n    section: "## origin"\n')
        body = b"# Docs\n\n## agent\n\n- https://cursor.com/docs/agent.md\n\n## origin\n\n- https://cursor.com/docs/origin.md\n\n## sdk\n\n- https://cursor.com/docs/sdk.md\n"
        rc, _ = self.run_watch({url: (200, url, body)}, "--seed")
        self.assertEqual(rc, 0)
        self.assertEqual(self.snapshot("idx.txt"), b"## origin\n\n- https://cursor.com/docs/origin.md\n")

    def test_bad_source_id_is_a_config_error(self):
        self.write_sources("sources:\n  - id: Bad Id\n    url: https://cursor.com/x.md\n    type: md\n    expect: x\n")
        with self.assertRaises(ValueError):
            self.run_watch({})


if __name__ == "__main__":
    unittest.main()
