# GitHub Publish Scratchpad

> Living memory for publishing this repo to GitHub.
> Keep entries short and scannable. Do not store secrets.

## Goal
- Publish `C:\Users\valen\Documents\Code\stocks` to `https://github.com/muhuuh/picker`.

## Current plan
- [x] Confirm local folder and GitHub CLI auth.
- [x] Check durable repo context before publishing.
- [x] Initialize Git safely and exclude secrets.
- [x] Push initial repository contents to GitHub.
- [x] Record final result and any follow-up work.

## Key decisions (and why)
- 2026-05-03: Treat this as a first publish because the folder is not currently a Git repository.
- 2026-05-03: Exclude `.env` before Git initialization because stock repo rules forbid storing secrets or credentials in tracked files.
- 2026-05-03: Use `main` as the initial branch because the target GitHub repository had no default branch or refs.

## What we learned
- GitHub CLI is installed and authenticated as `muhuuh`.
- `rg --files` failed with Access denied in this environment; PowerShell `Get-ChildItem` works.
- The folder has no `.git` directory at task start.
- `https://github.com/muhuuh/picker` existed but had no refs before the first push.
- Initial commit `d10255a` was pushed to `origin/main`.

## Open questions / unknowns
- None for the initial publish.

## Next steps
- Add root `README.md` and `SETUP.md` when the repo has runtime setup instructions to document.

## Risks / gotchas
- Do not commit `.env` or other private account/API data.
- If the remote already has commits, avoid overwriting history without explicit user approval.
- Check `git status --ignored` before future broad staging; `.env` should remain ignored.

## Commands / environment notes
- Repo path: `C:\Users\valen\Documents\Code\stocks`.
- Target remote: `https://github.com/muhuuh/picker`.
- Verification used: `gh auth status`, `git ls-remote`, staged secret scan excluding `.env`, `git status --ignored`, and `git push -u origin main`.
