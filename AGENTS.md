# Project guidance

## Project

This repository is an early NBA fantasy basketball analytics prototype. The current UI lives in `fantasy-ui/`; `fantasy-api/` contains an Express starter server.

## Working in this repository

- Keep changes focused on the user's current request and explain meaningful tradeoffs before making broad architectural changes.
- Preserve the existing React and TypeScript structure unless the task calls for a migration.
- Use the package manager and lockfile already present in the package being changed. The UI has its own `package.json` and `package-lock.json`; do not treat `fantasy-api/package-lock.json` as a complete package definition because that folder currently has no `package.json`.
- Do not push commits unless the user explicitly asks. Create local commits only when the user requests one.
- Do not add secrets, credentials, or personal data to the repository.
