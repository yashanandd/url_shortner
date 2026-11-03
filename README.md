# LinkFlow URL Shortener

LinkFlow is a URL-shortening project. Its product requirements and planned
architecture are documented in [PRD.md](./PRD.md).

## Repository layout

```text
backend/       Backend scaffold
frontend/      React application built with Vite
PRD.md         Product requirements and planned system design
```

The backend and frontend are currently scaffolds; URL-shortening features and
the API are not implemented yet.

## Frontend

Requirements: Node.js and npm.

From the repository root, run:

```powershell
cd frontend
npm ci
npm run dev
```

To check the frontend:

```powershell
npm run lint
npm run build
```

## Backend

`backend/main.py` is a placeholder. The backend dependencies and API entry
point will be documented here when the backend is implemented.
