# AGENT.md — AI Map MCP

This file is for whoever (human or AI) touches this repo next. It
covers three things: what this server *is*, the MCP-transport
conventions it depends on, and the exact bugs that were hit getting
it working — so they don't come back.

Read this before changing `app.py`. `map.py` (the rendering engine)
is much lower-risk to edit; `app.py` (the MCP transport layer) is
where every bug so far has actually lived.

---

## 1. What this server does

**AI Map MCP** is an MCP server that gives an AI system tools to
build and export 2D maps and scientific visualizations: points,
lines, polygons, grids, annotations, circles, rectangles, heatmaps,
scatter plots, contours, scale bars, north arrows — on either a
plain Cartesian canvas or a geographic coordinate space. State is
kept in a single in-memory `MapEngine` instance per server process
(`map_engine` in `app.py`) and rendered to SVG on demand.

Two files:

- **`map.py`** — `MapEngine`: pure Python state + SVG rendering.
  No MCP/HTTP concerns at all. Safe to extend.
- **`app.py`** — the MCP server: wraps every `MapEngine` method as an
  `@mcp.tool()`, plus a handful of plain HTTP endpoints, all served
  over Streamable HTTP. This is the file with the historically
  fragile parts — see §3.

### Full tool inventory (23 tools)

| Tool | Purpose |
|---|---|
| `create_map` | Start a new canvas: size, coordinate system, bounds, optional grid |
| `add_points` | Point features (x/y or longitude/latitude) |
| `add_lines` | Polylines — faults, roads, rivers, trajectories |
| `add_polygons` | Filled regions — geological units, blocks, boundaries |
| `add_grid` | Coordinate grid lines |
| `add_annotation` | Free text at a coordinate |
| `add_circle` | Circle — buffers, uncertainty regions |
| `add_rectangle` | Rectangle — study areas, bounding boxes |
| `add_heatmap` | Intensity surface from point data + a value field |
| `add_scatter` | Plot arbitrary tabular data as x/y points |
| `add_contour` | Isolines from spatial point measurements |
| `add_scale_bar` | Map scale bar |
| `add_north_arrow` | North arrow (geographic maps) |
| `list_layers` | List all layers on the map |
| `set_layer_visibility` | Show/hide a layer |
| `remove_layer` | Delete a layer |
| `clear_map` | Reset to an empty canvas |
| `set_view` | Change the visible coordinate extent |
| `fit_to_data` | Auto-fit the view to current features |
| `get_map_state` | Full structured map state (for the AI to inspect/continue editing) |
| `get_map_summary` | Concise summary (cheaper than full state) |
| `export_map` | Export as svg/json/geojson |
| `render_map` | Render current map to SVG |

If you add a new capability, add it to **both** `MapEngine` (in
`map.py`) and as an `@mcp.tool()` in `app.py`, and add a row here.
Keeping this table in sync is the whole point of it — it's the one
place capability drift gets caught.

---

## 2. MCP transport conventions this server follows

- **Transport:** Streamable HTTP (not stdio, not SSE-only). One
  endpoint, `/mcp`, handles `GET`/`POST`/`DELETE` per the MCP spec
  (`POST` for JSON-RPC calls, `GET` to open a server-push stream,
  `DELETE` to end a session).
- **Auth: none.** This server has no OAuth, no API key, nothing.
  That's a deliberate, fully supported MCP configuration — Claude's
  own connector docs list "None: no sign-in" as a first-class
  option. When adding this connector in Claude, the Authentication
  setting must be explicitly set to **None** (Claude doesn't always
  auto-detect this correctly — see §3.2).
- **One canonical path, no trailing-slash ambiguity.** The MCP
  endpoint is exactly `/mcp` — the same shape Claude's own "Add
  custom connector" dialog shows as its example
  (`https://mcp.example.com/mcp`). `/mcp/` redirects *to* `/mcp`
  (harmless), not away from it.
- **CORS is wide open** (`allow_origins=["*"]`) since this is a
  public, unauthenticated tool server. Tighten this if that ever
  changes.
- **`mcp<2` is required.** `mcp` 2.x renamed `FastMCP` to
  `MCPServer` and changed its API. A bare `pip install mcp` installs
  2.x today and will break `from mcp.server.fastmcp import FastMCP`
  outright. `requirements.txt` pins `mcp<2` — don't remove that pin
  without porting the whole file to the 2.x API.

---

## 3. Bugs already hit here, and why they won't come back

Every one of these was found by actually running the server and
making real requests against it — not just reading the code. If you
change how `app.py` is structured, re-run the verification recipe in
§4 before shipping.

### 3.1 Don't wrap `mcp.streamable_http_app()` in a second outer app

**What went wrong (twice, in different ways):**

The first version mounted FastMCP's app inside a *separate* FastAPI
app: `outer_app.mount("/mcp", mcp_app)`. That composition caused two
real bugs:

- FastMCP's own default internal route is *also* `/mcp`
  (`streamable_http_path` defaults to `/mcp`). Mounting it again at
  `/mcp` produced a real working endpoint at `/mcp/mcp`, not `/mcp`.
- FastMCP starts its session manager via *its own* Starlette
  lifespan handler. That only fires when its app is run directly.
  When mounted as a sub-app, the outer app's lifespan never triggers
  it, so every request failed with `RuntimeError: Task group is not
  initialized. Make sure to use run().`

**The fix, and why it's structural rather than a patch:** this
version never creates a second app at all. `mcp.streamable_http_app()`
*is* the ASGI app uvicorn runs. Plain HTTP endpoints (`/health`,
`/map`, etc.) are registered directly on it via `@mcp.custom_route(...)`
instead of living on a separate FastAPI instance that then needs
mounting. One app, one lifespan, one `/mcp` path — there's no
composition step left to get wrong.

If a future change reintroduces an outer app (e.g. to get some
FastAPI-only feature), re-wire the lifespan explicitly:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        yield
```
and build `mcp_app = mcp.streamable_http_app()` **before** constructing
the outer app, so its lifespan can be passed in.

### 3.2 `OPTIONS /mcp` needs explicit handling — and a plain route doesn't work

**What went wrong:** Claude's connector setup (and some other MCP
clients) send a bare `OPTIONS /mcp` request — no `Origin` header, so
it's a server-to-server capability probe, not a browser CORS
preflight — before doing anything else. FastMCP's generated route
for `/mcp` only handles `GET`/`POST`/`DELETE` internally, so this
came back as a bare `405`, which killed connector setup at step 1
before it ever reached MCP's own handshake.

**Why a normal route fix doesn't work:** the instinct is to add
`@mcp.custom_route("/mcp", methods=["OPTIONS"])`. That does *not*
work here specifically, because FastMCP's own `/mcp` route is built
with **no method filter at all** at the Starlette routing layer — it
forwards straight into the raw ASGI handler regardless of HTTP
method, so it always produces a full route match for *any* method,
including `OPTIONS`. Since that route is always added first, it
always wins before a later, OPTIONS-specific route is ever
considered. This isn't about registration order in your own code —
`streamable_http_app()` always puts its own route before your custom
ones internally.

**The fix:** a small ASGI middleware (`MCPOptionsBypassMiddleware` in
`app.py`) that intercepts `OPTIONS /mcp` requests **before routing
happens at all**, but only when there's no `Origin` header — real
browser preflights (which always carry one) are left alone so
`CORSMiddleware` keeps handling those correctly. If you ever remove
or rewrite this middleware, re-run check 1 and 2 in §4 — both must
pass, not just one.

### 3.3 `GridLine` render crash — a `map.py` bug, not a transport bug

Separately from the transport issues: `add_grid()` stored each grid
line's coordinate as a top-level `"value"` key on the feature dict,
but `_render_feature()` was reading it from a `"geometry"` sub-dict
that grid lines don't have — so it silently got `None` and crashed
with `TypeError: unsupported operand type(s) for -: 'NoneType' and
'float'`. Since `create_map()` adds a grid by default, this broke
almost every `render_map` call. Fixed by reading `feature.get("value")`
directly. Covered by check 7 in §4.

---

## 4. Verification recipe

Run this after any change to `app.py`. All of these should be true;
if any aren't, don't ship.

```bash
pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8000 &
sleep 2

# 1. Bare OPTIONS probe (no Origin) — must be 204, not 405
curl -s -o /dev/null -w "%{http_code}\n" -X OPTIONS http://127.0.0.1:8000/mcp

# 2. Real browser CORS preflight — must still be a normal 200 with CORS headers
curl -s -o /dev/null -w "%{http_code}\n" -X OPTIONS http://127.0.0.1:8000/mcp \
  -H "Origin: https://claude.ai" -H "Access-Control-Request-Method: POST"

# 3. No ghost double-mount path
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8000/mcp/mcp \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -d '{}'
# expect 404

# 4. Full MCP handshake — initialize, then tools/call
curl -s -D /tmp/h.txt -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}'
SID=$(grep -i mcp-session-id /tmp/h.txt | tr -d '\r' | awk '{print $2}')

# 5. A tool call that exercises the grid path (the one real map.py bug so far)
curl -s -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"create_map","arguments":{}}}'
curl -s -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SID" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"render_map","arguments":{}}}'
# response must NOT contain "isError":true
```

If you only test with a browser-based MCP client, you will not catch
§3.2 — that bug is specifically about requests with no `Origin`
header, which browsers never send. Check 1 above has to be run with
a raw HTTP client (curl, not `fetch`) to be meaningful.

---

## 5. Deploying

- `requirements.txt` pins `mcp<2`. Keep it pinned.
- `HOST`/`PORT` are read from env vars (defaults `0.0.0.0`/`8000`),
  matching typical PaaS conventions (Render, Railway, etc.).
- After deploying, re-run §4 against the live URL, not just
  localhost — CORS and the OPTIONS bypass both depend on real
  request headers a deploy platform's proxy might rewrite.
- In Claude, when (re-)adding this as a custom connector: remove any
  existing broken connector first (auth type can't be changed after
  the fact), then add it fresh and explicitly select **Authentication:
  None**.
