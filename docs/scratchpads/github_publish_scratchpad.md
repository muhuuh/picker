# GitHub Publish Scratchpad

> Living memory for publishing this repo to GitHub.
> Keep entries short and scannable. Do not store secrets.

## Goal
- Publish `C:\Users\valen\Documents\Code\stocks` to `https://github.com/muhuuh/picker`.

## Current plan
- [x] Confirm local folder and GitHub CLI auth.
- [x] Check durable repo context before publishing.
- [ ] Initialize Git safely and exclude secrets.
- [ ] Push initial repository contents to GitHub.
- [ ] Record final result and any follow-up work.

## Key decisions (and why)
- 2026-05-03: Treat this as a first publish because the folder is not currently a Git repository.
- 2026-05-03: Exclude `.env` before Git initialization because stock repo rules forbid storing secrets or credentials in tracked files.

## What we learned
- GitHub CLI is installed and authenticated as `muhuuh`.
- `rg --files` failed with Access denied in this environment; PowerShell `Get-ChildItem` works.
- The folder has no `.git` directory at task start.

## Open questions / unknowns
- Whether the target GitHub repository is empty or already has commits.

## Next steps
- Check target repo state.
- Add `.gitignore`, initialize Git, create an initial commit, and push.

## Risks / gotchas
- Do not commit `.env` or other private account/API data.
- If the remote already has commits, avoid overwriting history without explicit user approval.

## Commands / environment notes
- Repo path: `C:\Users\valen\Documents\Code\stocks`.
- Target remote: `https://github.com/muhuuh/picker`.
