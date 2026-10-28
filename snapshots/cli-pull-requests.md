# Pull request commands

Origin is currently released in early beta. You can create repos, push and pull with git, mirror from GitHub, browse and search code, open and merge pull requests, and share with your Cursor team.

Every `origin pr` subcommand with its options. For the rest of the CLI, see [Commands](https://cursor.com/docs/origin/cli/reference/commands.md). For how pull requests work in Origin, see [Pull requests](https://cursor.com/docs/origin/pull-requests.md).

## Targeting a pull request

Pull request commands infer the repository from `ORIGIN_REPO`, then the `origin` git remote in your current checkout. Override it with `-R, --repo` in `org/name` format.

Most subcommands take an optional `[target]`: a number (`13` or `#13`), an Origin pull request URL, or a branch name. Omit it and the CLI uses the open or draft pull request for your current branch:

```bash
origin pr view 13        # pull request 13
origin pr view my-branch # pull request for my-branch
origin pr view           # pull request for the current branch
```

## Subcommands

| Subcommand              | Description                                                                          | Usage                           |
| ----------------------- | ------------------------------------------------------------------------------------ | ------------------------------- |
| `create` \| `new`       | Open a pull request against an Origin repo                                           | `origin pr create -t "Fix CI"`  |
| `list` \| `ls`          | List pull requests in a repository                                                   | `origin pr list`                |
| `status`                | Show the pull requests relevant to you in a repository                               | `origin pr status`              |
| `view [target]`         | Display a pull request, and optionally its diff, checks, comments, or agents         | `origin pr view 13`             |
| `diff [target]`         | View the diff for a pull request                                                     | `origin pr diff`                |
| `checks [target]`       | Show CI status for a pull request                                                    | `origin pr checks`              |
| `requirements [target]` | Show what a pull request still needs before it can merge                             | `origin pr requirements`        |
| `watch [target]`        | Wait until CI settles, the pull request merges, its head moves, or a comment matches | `origin pr watch`               |
| `checkout [target]`     | Fetch and check out the pull request branch                                          | `origin pr checkout 13`         |
| `edit [target]`         | Edit the title, body, base branch, labels, or reviewers                              | `origin pr edit -t "New title"` |
| `ready [target]`        | Mark a draft as ready for review                                                     | `origin pr ready`               |
| `reviewer`              | List, request, and remove requested reviewers                                        | `origin pr reviewer list`       |
| `review [target]`       | Add a review                                                                         | `origin pr review --approve`    |
| `comment [target]`      | Add, edit, or delete a discussion comment                                            | `origin pr comment -b "LGTM"`   |
| `thread`                | List, view, resolve, reopen, and reply to review threads                             | `origin pr thread list`         |
| `merge [target]`        | Merge a pull request, or a stack up to and including it                              | `origin pr merge`               |
| `close [target]`        | Close a pull request                                                                 | `origin pr close`               |
| `reopen [target]`       | Reopen a closed pull request                                                         | `origin pr reopen`              |
| `refresh [target]`      | Snapshot a new version from the current refs                                         | `origin pr refresh`             |

Pushing to the head branch snapshots a new version on its own. Run `origin pr refresh` only when `origin pr view` or `origin pr checks` still report the previous head commit. It does nothing when the resolved commits already match the latest version.

`origin pr review` files a formal review. `origin pr comment` adds a discussion comment. `origin pr view --comments` lists both.

## Create

| Option                      | Description                                                                                                             |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `-t, --title <title>`       | Title of the pull request                                                                                               |
| `-b, --body <body>`         | Body of the pull request                                                                                                |
| `--description <text>`      | Description of the pull request                                                                                         |
| `-F, --body-file <path>`    | Read the body from a file. Use `-` for stdin                                                                            |
| `-H, --head <branch>`       | Branch that holds your commits (default: current branch)                                                                |
| `-B, --base <branch>`       | Branch you want your code merged into (default: the `--stack-on` parent's head branch, else the repo default branch)    |
| `--stack-on <target>`       | Stack the new pull request on an existing one, by number or branch                                                      |
| `-l, --label <name>`        | Add a label by name. Repeatable or comma-separated                                                                      |
| `-r, --reviewer <reviewer>` | Request a review by email, `org/team` slug, or ID as `origin pr reviewer list` prints it. Repeatable or comma-separated |
| `--push`                    | Push the head branch without prompting when it isn't on the remote yet                                                  |
| `--remote <remote>`         | Remote to push to when the head branch isn't on the remote (default: `origin`)                                          |
| `--status <status>`         | Initial status: `draft` or `open` (default: `open`)                                                                     |
| `-d, --draft`               | Create as a draft. Alias for `--status draft`                                                                           |
| `-f, --fill`                | Use commit information for the title and body                                                                           |
| `--fill-first`              | Use the first commit's information for the title and body                                                               |

A new pull request opens ready for review. When the author's **Never open PRs as drafts** setting is on, Origin opens it ready even with `--draft`, and the output says so.

`--stack-on` works best when you branch from the parent's head, so its commits are in your branch. Origin doesn't rebase your branch when the parent moves; run `origin stack restack`. See [Stack commands](https://cursor.com/docs/origin/cli/reference/stacks.md).

## List and status

| Command  | Option                  | Description                                                                                                                                                |
| -------- | ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `list`   | `-s, --state <state>`   | Filter by state: `open`, `closed`, `merged`, `draft`, or `all` (default: `open`)                                                                           |
| `list`   | `--mine`                | Only show pull requests you authored                                                                                                                       |
| `list`   | `-B, --base <branch>`   | Filter by base branch                                                                                                                                      |
| `list`   | `-H, --head <branch>`   | Filter by head branch                                                                                                                                      |
| `list`   | `--file <path>`         | Filter by a changed path. Repeatable; a trailing `/` matches a folder prefix                                                                               |
| `list`   | `--commit <sha>`        | Find the pull requests for one full commit SHA: the branch tip, a pushed version, or a merge commit. Can't be combined with the other filters or `--limit` |
| `list`   | `-L, --limit <number>`  | Maximum number of items to fetch (default: `30`)                                                                                                           |
| `list`   | `--json <fields>`       | Output JSON with the fields you list, for example `number,title,status`                                                                                    |
| `status` | `-c, --conflict-status` | Show the merge conflict status of each pull request                                                                                                        |

## View, diff, and checks

| Command  | Option                      | Description                                                                    |
| -------- | --------------------------- | ------------------------------------------------------------------------------ |
| `view`   | `--diff`                    | Show the collected patch diff for the selected version                         |
| `view`   | `--checks`                  | Include the mergeability and CI summary                                        |
| `view`   | `-c, --comments`            | Show comments and reviews, with per-thread resolution state                    |
| `view`   | `--agents`                  | Show the cloud agents attached to the pull request                             |
| `view`   | `--name-only`               | With `--diff`, print only the changed file paths                               |
| `view`   | `--exclude <glob>`          | Exclude paths matching a glob. Repeatable                                      |
| `view`   | `-w, --web`                 | Open the pull request in your browser                                          |
| `view`   | `--change-version <number>` | Version to display (default: latest)                                           |
| `view`   | `--json <fields>`           | Output JSON with the fields you list. Bare `--json` lists the fields           |
| `diff`   | `--patch`                   | Display the diff in patch format                                               |
| `diff`   | `--name-only`               | Print only the changed file paths                                              |
| `diff`   | `-e, --exclude <glob>`      | Exclude files matching a glob. Repeatable                                      |
| `diff`   | `--change-version <number>` | Version to diff (default: latest)                                              |
| `checks` | `--watch`                   | Watch the checks until they finish                                             |
| `checks` | `--name <name>`             | Only checks with a matching name, exact or a glob with `*` and `?`. Repeatable |
| `checks` | `--log <job>`               | Print the full log of a finished Origin CI job, named as in the checks list    |
| `checks` | `--json <fields>`           | Output JSON with the fields you list                                           |

`list`, `status`, `view`, `diff`, `checks`, `requirements`, and `watch` also take `--color <always|never|auto>` (default: `auto`).

To limit `origin pr diff` to some paths, list them after `--`. Each is a file, a directory, or a glob relative to the repository root:

```bash
origin pr diff 123 -- src/ '*.md'
```

`origin pr checks` exits `0` when every check passed, `1` when a check failed or there are no checks, and `8` while checks are pending. `--watch` polls every 10 seconds until the checks finish.

`--diff`, `--checks`, `--comments`, and `--agents` only shape the plain-text output of `origin pr view`. For JSON, request the fields you want instead, such as `files`, `mergeability`, `ciState`, `comments`, `threads`, or `agents`.

## Requirements and watch

`origin pr requirements` names what a pull request still needs before it can merge: required gates and their status at the head commit, approvals, each owner rule and where it stands, the Code Review Gate, and blockers in its stack. `--json <fields>` takes `headSha`, `mergeability`, `gates`, `codeReviewGates`, `approvals`, and `ownerRules`.

`origin pr watch` follows a pull request over a live stream and exits when a condition is met:

| Option                | Description                                                                                                                        |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `--until <condition>` | `checks` (default), `merged`, `head:<sha>`, or `comment:<regex>`. `comment:` also matches comments posted before the watch started |
| `--timeout <seconds>` | Give up after this many seconds                                                                                                    |
| `-f, --follow`        | Keep streaming until you press Ctrl-C instead of exiting when CI settles or the pull request merges or closes                      |
| `--json <fields>`     | Print one object describing how the watch ended: `outcome`, `exitCode`, `status`, `headSha`, `checks`, `comment`                   |

With the default `--until checks`, `origin pr watch` exits `0` when the checks pass or the pull request merges, and `1` when a check fails or it closes. Other conditions exit `0` when met and `1` otherwise, for example on a timeout or when the pull request closes first.

## Checkout, edit, and lifecycle

| Command    | Option                      | Description                                                                                                                                           |
| ---------- | --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `checkout` | `-b, --branch <name>`       | Local branch name to use (default: the pull request's head ref)                                                                                       |
| `checkout` | `--detach`                  | Check out with a detached HEAD                                                                                                                        |
| `checkout` | `-f, --force`               | Reset the existing local branch to the latest state                                                                                                   |
| `checkout` | `--remote <remote>`         | Remote to fetch from (default: `origin`)                                                                                                              |
| `checkout` | `--stack`                   | Fetch and fast-forward every branch in the pull request's stack, then check out this one. Never merges or rebases locally. Same as `origin stack get` |
| `edit`     | `-t, --title <title>`       | Set a new title                                                                                                                                       |
| `edit`     | `-b, --body <body>`         | Set a new body                                                                                                                                        |
| `edit`     | `-F, --body-file <path>`    | Read the new body from a file. Use `-` for stdin                                                                                                      |
| `edit`     | `-B, --base <branch>`       | Change the base branch                                                                                                                                |
| `edit`     | `--stack-on <target>`       | Stack this pull request on another one, by number or branch                                                                                           |
| `edit`     | `--clear-stack`             | Remove this pull request's stack parent. Don't use it after a parent merges, because it splits the stack                                              |
| `edit`     | `--add-label <name>`        | Add a label by name. Repeatable                                                                                                                       |
| `edit`     | `--remove-label <name>`     | Remove a label by name. Repeatable                                                                                                                    |
| `edit`     | `--add-reviewer <reviewer>` | Request a review from a user by email or a team by `org/team` slug. Repeatable or comma-separated                                                     |
| `ready`    | `--undo`                    | Convert the pull request back to a draft                                                                                                              |
| `close`    | `-c, --comment <body>`      | Leave a closing comment                                                                                                                               |
| `reopen`   | `-c, --comment <body>`      | Add a reopening comment                                                                                                                               |
| `reopen`   | `--reset-base`              | Reset the base branch to before this pull request's commits when they're already on it, then reopen                                                   |
| `reopen`   | `-y, --yes`                 | Skip the `--reset-base` confirmation                                                                                                                  |

Labels must already exist on the repository. List them with [`origin label list`](https://cursor.com/docs/origin/cli/reference/commands.md#labels).

## Merge

| Option                         | Description                                                                                                                               |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `-s, --squash`                 | Squash the commits into one commit on the base branch. The default when the repository disallows merge commits                            |
| `-m, --merge`                  | Create a merge commit. The default when the repository allows merge commits                                                               |
| `-t, --subject <text>`         | Subject of the merge commit, used verbatim. Single pull request merges only                                                               |
| `-b, --body <text>`            | Body of the merge commit, used verbatim. Single pull request merges only                                                                  |
| `-F, --body-file <path>`       | Read the merge commit body from a file. Use `-` for stdin                                                                                 |
| `--auto`                       | Merge once the requirements are met, then return. Turns on merge-when-ready                                                               |
| `--disable-auto`               | Turn off merge-when-ready for this pull request                                                                                           |
| `--downstack`                  | With `--auto`, also turn on merge-when-ready for every open pull request below this one in its stack                                      |
| `--expect-head <number>=<sha>` | Refuse the merge unless pull request `<number>` is still at `<sha>`. Repeatable, and covers every stack member the merge lands            |
| `--match-head-commit <sha>`    | Refuse the merge unless this pull request's head is still `<sha>`. The `gh` spelling of `--expect-head` for the target                    |
| `--base-ok`                    | Merge even when the base is the head branch of another pull request: an open one the two aren't stacked on, or one closed without merging |
| `--bypass-rules`               | Merge even when rules on the base branch fail, through your ruleset bypass. Never gets you past a rule you can't bypass                   |

Without `--auto`, the merge happens now. `origin pr view`, `origin pr status`, and `origin pr requirements` print a `Merge-when-ready:` line for an open or draft pull request.

On a stacked pull request, merging `#N` lands every open pull request from the stack root through `#N` together, in one commit. Origin checks every member first and lands nothing if any member is blocked. To land them one at a time, merge the lowest open pull request each time, then run `origin stack sync` and `origin stack push --all` to move the rest onto trunk. `--auto` arms one pull request, and Origin lands it once it's the lowest open member of its stack. `--auto --downstack` also arms every open pull request below it. See [Stack commands](https://cursor.com/docs/origin/cli/reference/stacks.md).

Where the repository requires it, a merge that would rely on your ruleset bypass is refused until you pass `--bypass-rules`.

## Reviewers, reviews, and comments

| Subcommand                    | Description                                                                            | Usage                                            |
| ----------------------------- | -------------------------------------------------------------------------------------- | ------------------------------------------------ |
| `reviewer list [target]`      | List the reviewers requested on a pull request                                         | `origin pr reviewer list`                        |
| `reviewer request [target]`   | Request reviews from users, teams, or service accounts. Re-requests existing reviewers | `origin pr reviewer request -r dana@acme.com`    |
| `reviewer remove [target]`    | Remove requested reviewers                                                             | `origin pr reviewer remove -r acme/platform`     |
| `comment edit <comment-id>`   | Replace the body of a comment you wrote                                                | `origin pr comment edit <comment-id> -b "Fixed"` |
| `comment delete <comment-id>` | Delete a comment                                                                       | `origin pr comment delete <comment-id>`          |

`reviewer request` and `reviewer remove` take `-r, --reviewer` (required): an email, an `org/team` slug, or an ID as `origin pr reviewer list` prints it (`user_…`, `grp_…`, `sa_…`). It's repeatable or comma-separated. Comment IDs come from `origin pr comment`, `origin pr view --comments`, or `origin pr thread list -c`.

| Command          | Option                          | Description                                          |
| ---------------- | ------------------------------- | ---------------------------------------------------- |
| `review`         | `-a, --approve`                 | Approve the pull request                             |
| `review`         | `-r, --request-changes`         | Request changes                                      |
| `review`         | `-c, --comment`                 | File the review as a comment                         |
| `review`         | `-b, --body <body>`             | Review body text                                     |
| `review`         | `-F, --body-file <path>`        | Read the review body from a file. Use `-` for stdin  |
| `review`         | `--change-version <number>`     | Version being reviewed (default: latest)             |
| `comment`        | `-b, --body <body>`             | Comment body text                                    |
| `comment`        | `-F, --body-file <path>`        | Read the comment body from a file. Use `-` for stdin |
| `comment`        | `--edit-last`                   | Edit your newest discussion comment                  |
| `comment`        | `--create-if-none`              | With `--edit-last`, add a comment when you have none |
| `comment`        | `--delete-last`                 | Delete your newest discussion comment                |
| `comment`        | `-y, --yes`                     | With `--delete-last`, skip the confirmation prompt   |
| `comment edit`   | `-b, --body`, `-F, --body-file` | New comment body                                     |
| `comment delete` | `-y, --yes`                     | Skip the confirmation prompt                         |

`reviewer list` takes `--json <fields>`: `kind`, `id`, `name`, `slug`, and `requestedAt`.

## Review threads

Every review comment belongs to a thread with its own resolution state. Thread IDs start with `cth_`.

| Subcommand                            | Description                             | Usage                                       |
| ------------------------------------- | --------------------------------------- | ------------------------------------------- |
| `thread list [target]`                | List threads and their resolution state | `origin pr thread list --unresolved`        |
| `thread view <thread-id> [target]`    | Show one thread with every comment      | `origin pr thread view cth_123`             |
| `thread resolve <thread-id> [target]` | Resolve a thread                        | `origin pr thread resolve cth_123`          |
| `thread reopen <thread-id> [target]`  | Reopen a resolved thread                | `origin pr thread reopen cth_123`           |
| `thread reply <thread-id> [target]`   | Add a comment to a thread               | `origin pr thread reply cth_123 -b "Fixed"` |

| Command        | Option                      | Description                                                          |
| -------------- | --------------------------- | -------------------------------------------------------------------- |
| `list`         | `--unresolved`              | Only show unresolved threads                                         |
| `list`         | `-c, --comments`            | Print every comment body instead of the opening excerpt              |
| `list`         | `--change-version <number>` | Only threads filed against this version (default: every version)     |
| `list`, `view` | `--json <fields>`           | Output JSON with the fields you list, for example `id,resolved,path` |
| `reply`        | `-b, --body <body>`         | Reply body text                                                      |
| `reply`        | `-F, --body-file <path>`    | Read the reply body from a file. Use `-` for stdin                   |

Scripts that gate on "all threads resolved" can use `origin pr thread list --unresolved --json id | jq length`.

## Getting help

Every subcommand takes `--help`:

```bash
origin pr --help
origin pr create --help
origin pr thread --help
```

## Next steps

- [Commands](https://cursor.com/docs/origin/cli/reference/commands.md)
- [Stack commands](https://cursor.com/docs/origin/cli/reference/stacks.md)
- [Pull requests](https://cursor.com/docs/origin/pull-requests.md)
- [Clone, Push & Pull](https://cursor.com/docs/origin/git.md)


---

## Sitemap

[Overview of all docs pages](/llms.txt)
