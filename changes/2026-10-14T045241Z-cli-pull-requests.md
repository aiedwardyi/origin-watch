# cli-pull-requests changed

- url: https://cursor.com/docs/origin/cli/reference/pull-requests.md
- fetched: 2026-10-14T04:52:41Z
- lines: +1/-5
- note: origin pr subcommands and their options.

````diff
--- a/snapshots/cli-pull-requests.md
+++ b/snapshots/cli-pull-requests.md
@@ -69,7 +69,6 @@
 | `list`   | `--file <path>`         | Filter by a changed path. Repeatable; a trailing `/` matches a folder prefix     |
 | `list`   | `-L, --limit <number>`  | Maximum number of items to fetch (default: `30`)                                 |
 | `list`   | `--json <fields>`       | Output JSON with the fields you list, for example `number,title,status`          |
-| `list`   | `-q, --jq <expression>` | Filter the JSON output with a jq expression. Requires `--json`                   |
 | `status` | `-c, --conflict-status` | Show the merge conflict status of each pull request                              |
 
 ## View, diff, and checks
@@ -84,13 +83,11 @@
 | `view`   | `-w, --web`                 | Open the pull request in your browser                                |
 | `view`   | `--change-version <number>` | Version to display (default: latest)                                 |
 | `view`   | `--json <fields>`           | Output JSON with the fields you list. Bare `--json` lists the fields |
-| `view`   | `-q, --jq <expression>`     | Filter the JSON output with a jq expression. Requires `--json`       |
 | `diff`   | `--patch`                   | Display the diff in patch format                                     |
 | `diff`   | `--name-only`               | Print only the changed file paths                                    |
 | `diff`   | `-e, --exclude <glob>`      | Exclude files matching a glob. Repeatable                            |
 | `checks` | `--watch`                   | Watch the checks until they finish                                   |
 | `checks` | `--json <fields>`           | Output JSON with the fields you list                                 |
-| `checks` | `-q, --jq <expression>`     | Filter the JSON output with a jq expression. Requires `--json`       |
 
 `list`, `status`, `view`, `diff`, and `checks` also take `--color <always|never|auto>` (default: `auto`).
 
@@ -144,11 +141,10 @@
 | `list`  | `-c, --comments`            | Print every comment body instead of the opening excerpt              |
 | `list`  | `--change-version <number>` | Only threads filed against this version (default: every version)     |
 | `list`  | `--json <fields>`           | Output JSON with the fields you list, for example `id,resolved,path` |
-| `list`  | `-q, --jq <expression>`     | Filter the JSON output with a jq expression. Requires `--json`       |
 | `reply` | `-b, --body <body>`         | Reply body text                                                      |
 | `reply` | `-F, --body-file <path>`    | Read the reply body from a file. Use `-` for stdin                   |
 
-Scripts that gate on "all threads resolved" can use `origin pr thread list --unresolved --json id --jq length`.
+Scripts that gate on "all threads resolved" can use `origin pr thread list --unresolved --json id | jq length`.
 
 ## Getting help
 
````
