import unittest
from pathlib import Path

import watch

FIXTURES = Path(__file__).parent / "fixtures"


class TextNormalizeTest(unittest.TestCase):
    def test_crlf_and_cr_become_lf(self):
        self.assertEqual(watch.normalize_text(b"a\r\nb\rc\n"), "a\nb\nc\n")

    def test_trailing_whitespace_stripped(self):
        self.assertEqual(watch.normalize_text(b"a  \nb\t\n"), "a\nb\n")

    def test_trailing_blank_lines_collapse_to_one_newline(self):
        self.assertEqual(watch.normalize_text(b"a\n\n\n\n"), "a\n")
        self.assertEqual(watch.normalize_text(b"a"), "a\n")

    def test_bom_stripped(self):
        self.assertEqual(watch.normalize_text(b"\xef\xbb\xbfa\n"), "a\n")

    def test_content_untouched(self):
        raw = b"version: v1alpha1 2026-08-21 sha 9f2c1e\n\n\n  indented: x\n"
        self.assertEqual(watch.normalize_text(raw), raw.decode())

    def test_empty_stays_empty(self):
        self.assertEqual(watch.normalize_text(b""), "")
        self.assertEqual(watch.normalize_text(b"\n\n  \n"), "")

    def test_idempotent(self):
        once = watch.normalize_text(b"a \r\n\r\nb\r\n\r\n")
        self.assertEqual(watch.normalize_text(once.encode()), once)

    def test_golden_md_fixture(self):
        raw = (FIXTURES / "origin-pull-requests.md").read_bytes()
        expected = (FIXTURES / "origin-pull-requests.expected.md").read_bytes().decode()
        self.assertEqual(watch.normalize_text(raw), expected)


class HtmlNormalizeTest(unittest.TestCase):
    def test_main_preferred_over_body(self):
        html = b"<body><p>outside</p><main><p>inside</p></main></body>"
        self.assertEqual(watch.normalize_html(html), "inside\n")

    def test_article_when_no_main(self):
        html = b"<body><p>outside</p><article><p>inside</p></article></body>"
        self.assertEqual(watch.normalize_html(html), "inside\n")

    def test_body_when_no_main_or_article(self):
        self.assertEqual(watch.normalize_html(b"<body><p>x</p></body>"), "x\n")

    def test_noise_elements_dropped(self):
        html = (b"<main><nav>nav</nav><header>hdr</header><script>js()</script>"
                b"<style>.a{}</style><noscript>ns</noscript><template>tpl</template>"
                b"<svg><title>icon</title></svg><p>keep</p><footer>ftr</footer></main>")
        self.assertEqual(watch.normalize_html(html), "keep\n")

    def test_cookie_and_consent_elements_dropped(self):
        html = (b'<main><div class="cookie-banner">cookies</div><div id="consent-modal">ok</div>'
                b'<p>keep</p></main>')
        self.assertEqual(watch.normalize_html(html), "keep\n")

    def test_inline_elements_join_one_line(self):
        html = b"<main><p>Requires <code>repo:read</code>. Results are <b>paged</b>.</p></main>"
        self.assertEqual(watch.normalize_html(html), "Requires repo:read. Results are paged.\n")

    def test_block_elements_split_lines(self):
        html = b"<main><h2>Aug 19</h2><ul><li>one</li><li>two</li></ul><p>three</p></main>"
        self.assertEqual(watch.normalize_html(html), "Aug 19\none\ntwo\nthree\n")

    def test_br_splits_lines(self):
        self.assertEqual(watch.normalize_html(b"<main><p>a<br>b</p></main>"), "a\nb\n")

    def test_whitespace_collapsed_outside_pre(self):
        html = b"<main><p>\n   a   \n  b \n</p></main>"
        self.assertEqual(watch.normalize_html(html), "a b\n")

    def test_pre_preserved(self):
        html = b"<main><pre>{\n    \"a\": 1\n}</pre></main>"
        self.assertEqual(watch.normalize_html(html), '{\n    "a": 1\n}\n')

    def test_comments_dropped(self):
        self.assertEqual(watch.normalize_html(b"<main><!-- c --><p>x</p></main>"), "x\n")

    def test_entities_decoded(self):
        self.assertEqual(watch.normalize_html(b"<main><p>a &amp; b</p></main>"), "a & b\n")

    def test_golden_html_fixture(self):
        raw = (FIXTURES / "api-changelog.html").read_bytes()
        expected = (FIXTURES / "api-changelog.expected.txt").read_bytes().decode()
        self.assertEqual(watch.normalize_html(raw), expected)


class SectionTest(unittest.TestCase):
    TEXT = "# Docs\n\n## a\n\n- 1\n\n## b\n\n- 2\n\n### b.1\n\n- 3\n\n# Other\n\n- 4\n"

    def test_keeps_heading_through_next_same_or_higher_heading(self):
        self.assertEqual(watch.extract_section(self.TEXT, "## b"), "## b\n\n- 2\n\n### b.1\n\n- 3\n")

    def test_first_section(self):
        self.assertEqual(watch.extract_section(self.TEXT, "## a"), "## a\n\n- 1\n")

    def test_missing_heading_is_none(self):
        self.assertIsNone(watch.extract_section(self.TEXT, "## zzz"))


class NormalizeDispatchTest(unittest.TestCase):
    def test_html_type_extracts_text(self):
        self.assertEqual(watch.normalize(b"<main><p>x</p></main>", "html"), "x\n")

    def test_text_types_minimal(self):
        for type_ in ("md", "yaml", "txt"):
            self.assertEqual(watch.normalize(b"a \r\n", type_), "a\n")

    def test_section_applied_to_text(self):
        self.assertEqual(watch.normalize(b"## a\n- 1\n## b\n- 2\n", "txt", section="## b"), "## b\n- 2\n")

    def test_missing_section_raises(self):
        with self.assertRaises(watch.SectionNotFound):
            watch.normalize(b"## a\n", "txt", section="## b")


if __name__ == "__main__":
    unittest.main()
