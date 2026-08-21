# origin-watch

Watches the public docs and API spec of [Cursor Origin](https://cursor.com/docs/origin) and commits every change as a diff.

Origin opened in beta on August 17, 2026, and its REST API is alpha. Both move fast, and the official pages show the current state, not the history. This repo is the running changelog of what changed and when.

- [CHANGELOG.md](CHANGELOG.md) - one line per changed source per run, newest first
- `changes/` - created when the first change lands: one report per changed source, with the source, fetch time, and the diff of the changed hunks
- `snapshots/` - created by the first run: the current normalized copy of every watched source; git history is the full record

## What it watches

| id | source | why |
|---|---|---|
| `openapi` | [openapi.yaml](https://cursor.com/docs/api/origin/openapi.yaml) | OpenAPI 3.1 spec for the REST API (v1alpha1). Breaking changes land here. |
| `api-changelog` | [API changelog](https://cursor.com/docs/api/origin/changelog) | The official API changelog, grouped by day. |
| `api-index` | [API llms.txt](https://cursor.com/docs/api/origin/llms.txt) | Index of the API docs. New or removed endpoint pages show up here. |
| `api-reference` | [API llms-full.txt](https://cursor.com/docs/api/origin/llms-full.txt) | The complete API reference as one Markdown file. |
| `docs-index` | [cursor.com/llms.txt](https://cursor.com/llms.txt), `## origin` section | Index of the Origin product docs. New or removed pages show up here. |
| `docs-origin` | [origin.md](https://cursor.com/docs/origin.md) | Origin overview: beta status and who can access it. |
| `cli-commands` | [cli/reference/commands.md](https://cursor.com/docs/origin/cli/reference/commands.md) | Full command listing for the `origin` CLI. |
| `cli-pull-requests` | [cli/reference/pull-requests.md](https://cursor.com/docs/origin/cli/reference/pull-requests.md) | `origin pr` subcommands and their options. |

The list lives in [sources.yml](sources.yml). Sources use the Markdown endpoints Cursor publishes for its docs; the API changelog has no Markdown form, so its rendered page is watched instead. Only the Origin section of the site-wide index is watched, so changes to other Cursor products do not show up here.

## How it runs

[watch.yml](.github/workflows/watch.yml) runs `watch.py` on GitHub Actions once a day at 00:17 UTC, and on manual dispatch. Each run:

1. Fetches every source once, with a 30 s timeout and the User-Agent `origin-watch (+https://github.com/aiedwardyi/origin-watch)`. Redirects must end on `cursor.com`.
2. Validates the response: HTTP 200, non-empty, above a per-source length floor, and containing the source's `expect` string. A source that fails validation keeps its last committed snapshot, and the run is marked failed.
3. Normalizes the content: UTF-8, `\n` line endings, trailing whitespace stripped; HTML pages are reduced to the text of their main content. Only structure is normalized; the text itself, including dates, versions, and hashes, is kept as published.
4. Compares the result with the committed snapshot. Each changed source gets a report in `changes/` and a line at the top of `CHANGELOG.md`, and the run ends in one commit authored by `github-actions[bot]`.

No change, no commit.

## Reading a change report

Reports are named `changes/<run time UTC>-<id>.md`, for example `changes/2026-08-22T001715Z-openapi.md`. Each one lists the source URL, the fetch time, the line counts, and a unified diff trimmed to the changed hunks with three lines of context. The full before and after text is in the history of `snapshots/<id>`: the report's commit and the one before it.

## Adding a source

Add an entry to [sources.yml](sources.yml):

```yaml
  - id: docs-git            # lowercase slug, names the snapshot file
    url: https://cursor.com/docs/origin/git.md
    type: md                # md | yaml | txt | html
    expect: "# Git"         # must appear in the fetched text, guards against soft 404s
    note: Cloning, pushing, and authenticating over git.
```

Optional fields: `min_chars` (validation floor, default 200) and `section` (for `txt`/`md`, keep one heading block such as `"## origin"` and drop the rest). The next run seeds the new source's baseline with a `watch: seed snapshots` commit and watches it from then on. Sources are only ever added by hand; when a watched index lists a new page, that shows up as a diff, not as a new source.

## Running locally

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt        # Windows: .venv\Scripts\pip install -r requirements.txt
python -m unittest            # normalizer fixtures plus an end-to-end run in a temp repo
python watch.py --repo /path/to/clone --seed
```

`watch.py` commits into whatever repo `--repo` points at (default: the directory it lives in). `--seed` creates baselines for sources that have no committed snapshot yet; without it, a missing baseline counts as a failure. Exit code 0 is a clean run, 2 means at least one source failed validation (the others were still processed and committed).

## License

[MIT](LICENSE).
