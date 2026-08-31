# Agent context: Splitser / WieBetaaltWat client + MCP

Unofficial Python monorepo for the Splitser / WieBetaaltWat web API: HTTP client (`splitser-api`) and MCP server (`splitser-mcp`). Not affiliated with Splitser BV. MIT licensed.

## Documentation: one source of truth (hard rule)

Write each fact once. Everywhere else, link. Do not copy env tables, tool lists, method tables, or install recipes between `AGENTS.md` and the READMEs.

| Kind of content | Source of truth | Elsewhere |
| --- | --- | --- |
| Install, env vars, auth setup, usage examples | [README.md](README.md), [api/README.md](api/README.md), [mcp/README.md](mcp/README.md) | Link only |
| Full MCP tool list | [mcp/README.md](mcp/README.md) | Link only |
| Client method list | [api/README.md](api/README.md) | Link only |
| Disclaimer / out of scope | [README.md](README.md) | Link only |
| Agent conventions, settled choices, git/PR rules | This file | Do not duplicate into READMEs |

If code and docs disagree, fix the owning doc in the same change. Do not keep a second copy here.

## Who you're helping

Senior engineer. Skip 101. Keep answers short. Metric units. English, or Dutch if he writes Dutch. Commit, push, or change repo visibility only when asked.

## Settled stack

Do not reopen these. Setup steps are in the READMEs.

| Layer | Choice |
| --- | --- |
| Layout | Monorepo: `api/` (`splitser-api`) + `mcp/` (`splitser-mcp`) |
| Python | 3.14+, [uv](https://docs.astral.sh/uv/) |
| HTTP | `httpx` async client |
| MCP | SDK 2.x `MCPServer` from `mcp.server.mcpserver` (not FastMCP) |
| Auth | Email/password → `_wbw_rails_session` cookie jar on disk |
| Amounts | Fractional cents (`1234` = EUR 12.34); MCP also accepts `amount_euros` |
| Payments | Out of scope: iDEAL, Bancontact, payment requests, bank linking |
| License | MIT |

## How to decide architecture

- Keep the settled stack above.
- Add behavior on `SplitserClient` first. MCP tools in `mcp/src/splitser_mcp/main.py` stay thin wrappers.
- Match the live web/app JSON shapes. Do not invent a cleaner local model.
- If Splitser changes headers or payloads, fix the client. Put the quirk in this file only when agents hit it often. User-facing detail goes in the READMEs.
- Mutating tools change real account data. Stay read-only unless he asked to write.

## Quick pointers (no duplicated facts)

| Need | Go to |
| --- | --- |
| Clone / MCP Cursor config / disclaimer | [README.md](README.md) |
| Env vars, client usage, method table | [api/README.md](api/README.md) |
| Tool list, `run_mcp.sh` | [mcp/README.md](mcp/README.md) |
| HTTP client | `api/src/splitser_api/client.py` |
| Env config | `api/src/splitser_api/config.py` |
| Cookie jar | `api/src/splitser_api/session.py` |
| Money helpers | `api/src/splitser_api/money.py` |
| MCP tools + `main()` | `mcp/src/splitser_mcp/main.py` |

## Repo layout

```
api/                         # splitser-api package
  src/splitser_api/          # client, config, session, money, errors
  tests/                     # unit + optional live integration
mcp/                         # splitser-mcp package
  src/splitser_mcp/          # MCPServer tools
  run_mcp.sh                 # Cursor / stdio entry
LICENSE
README.md
AGENTS.md                    # this file (agent conventions only)
```

## Commands

```bash
cd api && uv sync && uv run pytest -q && uv run ruff check src tests
cd mcp && uv sync && uv run ruff check src && ./run_mcp.sh
```

Live API test (needs credentials; see [api/README.md](api/README.md)):

```bash
cd api
SPLITSER_EMAIL=… SPLITSER_PASSWORD=… RUN_INTEGRATION_TESTS=1 uv run pytest -q -m integration
```

## Auth and API quirks

Easy to get wrong. Install and env detail: [api/README.md](api/README.md).

- Credentials come from env only (`SPLITSER_EMAIL`, `SPLITSER_PASSWORD`). Never commit secrets or cookie files.
- Session flow: load jar → `GET /api/users/current` → sign in if needed → persist jar after requests.
- Send `Accept-Version` (default `11`) and `X-App-React: true` on requests.
- WieBetaaltWat: `SPLITSER_BASE_URL=https://app.wiebetaaltwat.nl`, `SPLITSER_LANG=nl`.
- Create expense: client-generated UUID; POST body uses `shares_attributes`.
- Update expense: PUT body uses `shares` (not `shares_attributes`). MCP `shares` / `shares_json` may be a JSON string or a list.
- Share meta: `exact` (fixed amount, multiplier 0), `factor` (weight), `percent`. Specs use `exact_euros` / `exact_fractional`, `factor`, or `percent` per member. Exact rows first; remainder split by factor or percent.
- List expenses: `GET …/list_items`.
- Settled expenses usually cannot be updated or deleted.
- Nickname invite creates an anonymous member and an invite link. It does not send email by itself.
- Upstream can break when Splitser ships app updates.

## Conventions for agents

- One source of truth: follow [Documentation: one source of truth](#documentation-one-source-of-truth-hard-rule).
- Keep diffs small. Match existing code style.
- Do not commit, push, or open PRs unless asked.
- Do not reopen the [settled stack](#settled-stack).
- Do not add iDEAL, Bancontact, payment requests, or bank linking unless asked.
- MCP tools return JSON strings.
- Docs and PR prose stay plain and dry. No em dashes. No AI-tool credit in commits, PRs, code, or docs.

## Git: commits, branches, PRs

Commit titles and PR titles use the same Conventional Commits shape:

```text
<type>(optional-scope): <imperative summary>
```

- Lowercase after the colon. No trailing period.
- Imperative verb: add, fix, remove. Not added or adds.
- Scope when it helps: `api`, `mcp`, `docs`.
- Breaking change: `feat(api)!: …` or a `BREAKING CHANGE:` footer.
- One line. Say what changed. Skip sales language.
- Commit body only when it helps (why or caveats).

| Type | Use for | Commits | PRs |
| --- | --- | --- | --- |
| `feat` | New feature | yes | yes |
| `fix` | Bug fix | yes | yes |
| `docs` | Docs only | yes | yes |
| `style` | Formatting or whitespace only | yes | yes |
| `refactor` | Neither fix nor feature | yes | yes |
| `perf` | Performance | yes | yes |
| `test` | Tests | yes | yes |
| `ci` | CI config or scripts | yes | yes |
| `chore` | Tooling, deps, other non-src/test | yes | yes |
| `revert` | Revert a prior commit | yes | yes |
| `release` | Release or hotfix into `main` | no | yes |

Examples: `feat(api): add settlement preview helper`, `fix(mcp): accept shares_json as list`, `chore: add MIT license`.

### Branches

```text
<type>/<short-kebab-slug>
```

Optional scope in the slug: `feat/api-accept-version`, `fix/mcp-shares-json-list`, `docs/agents-conventions`.
Same type vocabulary as commits. No `build/`. One concern per branch.

### PR body

Skip a Test plan section unless asked. Default:

```markdown
## Description

This PR <one clear sentence starting with "This PR">.

### Changes

- <concrete change>
- <concrete change>
```

Add `### Notes` only when reviewers need extra context. Add `Closes #N` when it applies.

PR voice: plain and dry. Open with what the PR does. No em dashes. No hype words. Concrete bullets. Active voice.
