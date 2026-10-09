# cli-pull-requests changed

- url: https://cursor.com/docs/origin/cli/reference/pull-requests.md
- fetched: 2026-10-09T06:07:54Z
- lines: +16/-15
- note: origin pr subcommands and their options.

````diff
--- a/snapshots/cli-pull-requests.md
+++ b/snapshots/cli-pull-requests.md
@@ -98,21 +98,22 @@
 
 ## Checkout, edit, and lifecycle
 
-| Command    | Option                   | Description                                                     |
-| ---------- | ------------------------ | --------------------------------------------------------------- |
-| `checkout` | `-b, --branch <name>`    | Local branch name to use (default: the pull request's head ref) |
-| `checkout` | `--detach`               | Check out with a detached HEAD                                  |
-| `checkout` | `-f, --force`            | Reset the existing local branch to the latest state             |
-| `checkout` | `--remote <remote>`      | Remote to fetch from (default: `origin`)                        |
-| `edit`     | `-t, --title <title>`    | Set a new title                                                 |
-| `edit`     | `-b, --body <body>`      | Set a new body                                                  |
-| `edit`     | `-F, --body-file <path>` | Read the new body from a file. Use `-` for stdin                |
-| `edit`     | `-B, --base <branch>`    | Change the base branch                                          |
-| `ready`    | `--undo`                 | Convert the pull request back to a draft                        |
-| `merge`    | `--auto`                 | Merge once the requirements are met, then return                |
-| `merge`    | `--disable-auto`         | Turn off merge-when-ready for this pull request                 |
-| `close`    | `-c, --comment <body>`   | Leave a closing comment                                         |
-| `reopen`   | `-c, --comment <body>`   | Add a reopening comment                                         |
+| Command    | Option                   | Description                                                                                        |
+| ---------- | ------------------------ | -------------------------------------------------------------------------------------------------- |
+| `checkout` | `-b, --branch <name>`    | Local branch name to use (default: the pull request's head ref)                                    |
+| `checkout` | `--detach`               | Check out with a detached HEAD                                                                     |
+| `checkout` | `-f, --force`            | Reset the existing local branch to the latest state                                                |
+| `checkout` | `--remote <remote>`      | Remote to fetch from (default: `origin`)                                                           |
+| `edit`     | `-t, --title <title>`    | Set a new title                                                                                    |
+| `edit`     | `-b, --body <body>`      | Set a new body                                                                                     |
+| `edit`     | `-F, --body-file <path>` | Read the new body from a file. Use `-` for stdin                                                   |
+| `edit`     | `-B, --base <branch>`    | Change the base branch                                                                             |
+| `ready`    | `--undo`                 | Convert the pull request back to a draft                                                           |
+| `merge`    | `--auto`                 | Merge once the requirements are met, then return                                                   |
+| `merge`    | `--disable-auto`         | Turn off merge-when-ready for this pull request                                                    |
+| `merge`    | `--base-ok`              | Merge even when the base is the head branch of another open pull request this one isn't stacked on |
+| `close`    | `-c, --comment <body>`   | Leave a closing comment                                                                            |
+| `reopen`   | `-c, --comment <body>`   | Add a reopening comment                                                                            |
 
 ## Review and comment
 
````
