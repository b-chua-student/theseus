# Theseus frontend

The Svelte frontend provides the project dashboard, manuscript editor, source library, and writing assistant. Use Node.js 24 and follow the [repository setup](../README.md#local-setup) to install frontend and backend dependencies.

Start both services from the repository root with the backend Python environment active.

```sh
npm run dev
```

Open the URL printed by Vite. It proxies `/api` to Flask at `http://localhost:5000`.

From this directory, use the following commands.

| Command | Purpose |
| --- | --- |
| `npm run dev` | Start Vite when Flask is already running. |
| `npm run lint` | Run ESLint. |
| `npm test` | Run Node tests in `*.test.js`. |
| `npm run test:components` | Run Vitest tests in `*.spec.js`. |
| `npm run build` | Build the production assets in `dist/`. |

The [Dockerfile](../Dockerfile) builds the frontend and packages it with Flask for same-origin API requests. See the [API reference](../docs/api.md) for the backend contract.
