# cli-pull-requests changed

- url: https://cursor.com/docs/origin/cli/reference/pull-requests.md
- fetched: 2026-11-17T07:53:58Z
- lines: +47/-38
- note: origin pr subcommands and their options.

````diff
--- a/snapshots/cli-pull-requests.md
+++ b/snapshots/cli-pull-requests.md
@@ -62,9 +62,12 @@
 | `--status <status>`         | Initial status: `draft` or `open` (default: `open`)                                                                     |
 | `-d, --draft`               | Create as a draft. Alias for `--status draft`                                                                           |
 | `-f, --fill`                | Use commit information for the title and body                                                                           |
+| `--attach <path>`           | Attach a local image or video to the description. Repeatable, up to 50                                                  |
 | `--fill-first`              | Use the first commit's information for the title and body                                                               |
 
-A new pull request opens ready for review. When the author's **Never open PRs as drafts** setting is on, Origin opens it ready even with `--draft`, and the output says so.
+A new pull request opens ready for review unless you pass `--draft`.
+
+`--attach` uploads each file as a pull request attachment. `origin pr edit` and `origin pr comment` take it too. A Markdown link or image in the body that names the file points at the upload, and a file the body doesn't name is added at the end. Images can be GIF, JPEG, PNG, or WebP up to 10 MB, and videos MOV, MP4, or WebM up to 100 MB.
 
 `--stack-on` works best when you branch from the parent's head, so its commits are in your branch. Origin doesn't rebase your branch when the parent moves; run `origin stack restack`. See [Stack commands](https://cursor.com/docs/origin/cli/reference/stacks.md).
 
@@ -84,25 +87,25 @@
 
 ## View, diff, and checks
 
-| Command  | Option                      | Description                                                                    |
-| -------- | --------------------------- | ------------------------------------------------------------------------------ |
-| `view`   | `--diff`                    | Show the collected patch diff for the selected version                         |
-| `view`   | `--checks`                  | Include the mergeability and CI summary                                        |
-| `view`   | `-c, --comments`            | Show comments and reviews, with per-thread resolution state                    |
-| `view`   | `--agents`                  | Show the cloud agents attached to the pull request                             |
-| `view`   | `--name-only`               | With `--diff`, print only the changed file paths                               |
-| `view`   | `--exclude <glob>`          | Exclude paths matching a glob. Repeatable                                      |
-| `view`   | `-w, --web`                 | Open the pull request in your browser                                          |
-| `view`   | `--change-version <number>` | Version to display (default: latest)                                           |
-| `view`   | `--json <fields>`           | Output JSON with the fields you list. Bare `--json` lists the fields           |
-| `diff`   | `--patch`                   | Display the diff in patch format                                               |
-| `diff`   | `--name-only`               | Print only the changed file paths                                              |
-| `diff`   | `-e, --exclude <glob>`      | Exclude files matching a glob. Repeatable                                      |
-| `diff`   | `--change-version <number>` | Version to diff (default: latest)                                              |
-| `checks` | `--watch`                   | Watch the checks until they finish                                             |
-| `checks` | `--name <name>`             | Only checks with a matching name, exact or a glob with `*` and `?`. Repeatable |
-| `checks` | `--log <job>`               | Print the full log of a finished Origin CI job, named as in the checks list    |
-| `checks` | `--json <fields>`           | Output JSON with the fields you list                                           |
+| Command  | Option                      | Description                                                                                                        |
+| -------- | --------------------------- | ------------------------------------------------------------------------------------------------------------------ |
+| `view`   | `--diff`                    | Show the collected patch diff for the selected version                                                             |
+| `view`   | `--checks`                  | Include the mergeability and CI summary and, for an open or draft pull request, what it still needs from reviewers |
+| `view`   | `-c, --comments`            | Show comments and reviews, with per-thread resolution state                                                        |
+| `view`   | `--agents`                  | Show the cloud agents attached to the pull request                                                                 |
+| `view`   | `--name-only`               | With `--diff`, print only the changed file paths                                                                   |
+| `view`   | `--exclude <glob>`          | Exclude paths matching a glob. Repeatable                                                                          |
+| `view`   | `-w, --web`                 | Open the pull request in your browser                                                                              |
+| `view`   | `--change-version <number>` | Version to display (default: latest)                                                                               |
+| `view`   | `--json <fields>`           | Output JSON with the fields you list. Bare `--json` lists the fields                                               |
+| `diff`   | `--patch`                   | Display the diff in patch format                                                                                   |
+| `diff`   | `--name-only`               | Print only the changed file paths                                                                                  |
+| `diff`   | `-e, --exclude <glob>`      | Exclude files matching a glob. Repeatable                                                                          |
+| `diff`   | `--change-version <number>` | Version to diff (default: latest)                                                                                  |
+| `checks` | `--watch`                   | Watch the checks until they finish                                                                                 |
+| `checks` | `--name <name>`             | Only checks with a matching name, exact or a glob with `*` and `?`. Repeatable                                     |
+| `checks` | `--log <job>`               | Print the full log of a finished Origin CI job, named as in the checks list                                        |
+| `checks` | `--json <fields>`           | Output JSON with the fields you list                                                                               |
 
 `list`, `status`, `view`, `diff`, `checks`, `requirements`, and `watch` also take `--color <always|never|auto>` (default: `auto`).
 
@@ -114,11 +117,13 @@
 
 `origin pr checks` exits `0` when every check passed, `1` when a check failed or there are no checks, and `8` while checks are pending. `--watch` polls every 10 seconds until the checks finish.
 
-`--diff`, `--checks`, `--comments`, and `--agents` only shape the plain-text output of `origin pr view`. For JSON, request the fields you want instead, such as `files`, `mergeability`, `ciState`, `comments`, `threads`, or `agents`.
+`--diff`, `--checks`, `--comments`, and `--agents` only shape the plain-text output of `origin pr view`. For JSON, request the fields you want instead, such as `files`, `mergeability`, `ciState`, `reviewRequirements`, `comments`, `threads`, or `agents`.
 
 ## Requirements and watch
 
-`origin pr requirements` names what a pull request still needs before it can merge: required gates and their status at the head commit, approvals, each owner rule and where it stands, the Code Review Gate, and blockers in its stack. `--json <fields>` takes `headSha`, `mergeability`, `gates`, `codeReviewGates`, `approvals`, and `ownerRules`.
+`origin pr requirements` names what a pull request still needs before it can merge: required gates and their status at the head commit, approvals still needed and the reviews on record, each owner rule and where it stands, the Code Review Gate, and blockers in its stack. `--json <fields>` takes `headSha`, `mergeability`, `gates`, `codeReviewGates`, `approvals`, `ownerRules`, and `reviewsOnRecord`.
+
+`origin pr view --checks` prints the same requirements under `Review requirements:`, without the reviews on record. `--json reviewRequirements` returns them as JSON.
 
 `origin pr watch` follows a pull request over a live stream and exits when a condition is met:
 
@@ -130,6 +135,8 @@
 | `--json <fields>`     | Print one object describing how the watch ended: `outcome`, `exitCode`, `status`, `headSha`, `checks`, `comment`                   |
 
 With the default `--until checks`, `origin pr watch` exits `0` when the checks pass or the pull request merges, and `1` when a check fails or it closes. Other conditions exit `0` when met and `1` otherwise, for example on a timeout or when the pull request closes first.
+
+`origin pr watch` can show `Mergeable` and `Merge conflicts` as `not checked`, because it reads the pull request's CI state without running the merge conflict check.
 
 ## Checkout, edit, and lifecycle
 
@@ -143,6 +150,7 @@
 | `edit`     | `-t, --title <title>`       | Set a new title                                                                                                                                       |
 | `edit`     | `-b, --body <body>`         | Set a new body                                                                                                                                        |
 | `edit`     | `-F, --body-file <path>`    | Read the new body from a file. Use `-` for stdin                                                                                                      |
+| `edit`     | `--attach <path>`           | Attach a local image or video to the description. Repeatable, up to 50                                                                                |
 | `edit`     | `-B, --base <branch>`       | Change the base branch                                                                                                                                |
 | `edit`     | `--stack-on <target>`       | Stack this pull request on another one, by number or branch                                                                                           |
 | `edit`     | `--clear-stack`             | Remove this pull request's stack parent. Don't use it after a parent merges, because it splits the stack                                              |
@@ -192,22 +200,23 @@
 
 `reviewer request` and `reviewer remove` take `-r, --reviewer` (required): an email, an `org/team` slug, or an ID as `origin pr reviewer list` prints it (`user_…`, `grp_…`, `sa_…`). It's repeatable or comma-separated. Comment IDs come from `origin pr comment`, `origin pr view --comments`, or `origin pr thread list -c`.
 
-| Command          | Option                          | Description                                          |
-| ---------------- | ------------------------------- | ---------------------------------------------------- |
-| `review`         | `-a, --approve`                 | Approve the pull request                             |
-| `review`         | `-r, --request-changes`         | Request changes                                      |
-| `review`         | `-c, --comment`                 | File the review as a comment                         |
-| `review`         | `-b, --body <body>`             | Review body text                                     |
-| `review`         | `-F, --body-file <path>`        | Read the review body from a file. Use `-` for stdin  |
-| `review`         | `--change-version <number>`     | Version being reviewed (default: latest)             |
-| `comment`        | `-b, --body <body>`             | Comment body text                                    |
-| `comment`        | `-F, --body-file <path>`        | Read the comment body from a file. Use `-` for stdin |
-| `comment`        | `--edit-last`                   | Edit your newest discussion comment                  |
-| `comment`        | `--create-if-none`              | With `--edit-last`, add a comment when you have none |
-| `comment`        | `--delete-last`                 | Delete your newest discussion comment                |
-| `comment`        | `-y, --yes`                     | With `--delete-last`, skip the confirmation prompt   |
-| `comment edit`   | `-b, --body`, `-F, --body-file` | New comment body                                     |
-| `comment delete` | `-y, --yes`                     | Skip the confirmation prompt                         |
+| Command          | Option                          | Description                                                        |
+| ---------------- | ------------------------------- | ------------------------------------------------------------------ |
+| `review`         | `-a, --approve`                 | Approve the pull request                                           |
+| `review`         | `-r, --request-changes`         | Request changes                                                    |
+| `review`         | `-c, --comment`                 | File the review as a comment                                       |
+| `review`         | `-b, --body <body>`             | Review body text                                                   |
+| `review`         | `-F, --body-file <path>`        | Read the review body from a file. Use `-` for stdin                |
+| `review`         | `--change-version <number>`     | Version being reviewed (default: latest)                           |
+| `comment`        | `-b, --body <body>`             | Comment body text                                                  |
+| `comment`        | `-F, --body-file <path>`        | Read the comment body from a file. Use `-` for stdin               |
+| `comment`        | `--attach <path>`               | Attach a local image or video to the comment. Repeatable, up to 50 |
+| `comment`        | `--edit-last`                   | Edit your newest discussion comment                                |
+| `comment`        | `--create-if-none`              | With `--edit-last`, add a comment when you have none               |
+| `comment`        | `--delete-last`                 | Delete your newest discussion comment                              |
+| `comment`        | `-y, --yes`                     | With `--delete-last`, skip the confirmation prompt                 |
+| `comment edit`   | `-b, --body`, `-F, --body-file` | New comment body                                                   |
+| `comment delete` | `-y, --yes`                     | Skip the confirmation prompt                                       |
 
 `reviewer list` takes `--json <fields>`: `kind`, `id`, `name`, `slug`, and `requestedAt`.
 
````
