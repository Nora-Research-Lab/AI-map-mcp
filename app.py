"""
app.py
------
AI Map MCP server.

This is a from-scratch rewrite of the MCP transport/wiring layer.
The map/visualization engine itself lives in map.py and is unchanged
in behavior; every tool below has the same name, signature, and
capability as before.

ARCHITECTURE
============
Earlier versions of this file wrapped FastMCP's generated app inside
a *second*, separate FastAPI app via `outer_app.mount("/mcp", mcp_app)`.
That composition caused three real, verified bugs:

  1. FastMCP's own default internal route is ALSO "/mcp", so mounting
     it again at "/mcp" produced an actual working endpoint at
     "/mcp/mcp" instead of "/mcp".
  2. FastMCP's session manager is started by *its own* Starlette
     lifespan handler. That only fires when its app is run directly;
     when mounted as a sub-app, the outer app's lifespan doesn't
     trigger it, so every request failed with
     "RuntimeError: Task group is not initialized."
  3. The mounted route only declares GET/POST/DELETE. A bare OPTIONS
     request (no Origin header — the kind of capability probe some
     MCP clients send before doing anything else, including Claude's
     own connector setup flow) isn't a CORS preflight, so
     CORSMiddleware passes it straight through to the route, which
     has no OPTIONS handler and returns a bare 405.

This version avoids the first two bugs *by construction*, by never
creating a second outer app at all: `mcp.streamable_http_app()` is
used directly as the ASGI app that uvicorn runs, and the plain HTTP
endpoints (health check, map viewer, etc.) are registered on that
same app via `@mcp.custom_route(...)` instead of being routes on a
separate FastAPI instance. There is exactly one Starlette app, one
lifespan, and one "/mcp" path — no mount, no redirect, no wiring to
get wrong.

The third bug (OPTIONS/405) is still a real gap in what FastMCP
generates, so it's fixed explicitly below with a dedicated OPTIONS
route, the same way as before.

See AGENT.md for the full write-up of these gotchas, the MCP
transport conventions this server follows, and the verification
recipe used to confirm the server behaves correctly end to end.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response

from mcp.server.fastmcp import FastMCP

from map import MapEngine


# ============================================================
# CONFIGURATION
# ============================================================

APP_NAME = "AI Map MCP"
APP_VERSION = "1.0.0"

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Shared map engine. The engine maintains the current canvas/map state.
map_engine = MapEngine()


# ============================================================
# MCP SERVER
# ============================================================

mcp = FastMCP(
    name=APP_NAME,
    # This is the one and only path the MCP protocol is served on.
    # No outer app, no mount, so this is exactly the request path a
    # client uses — matching the "https://mcp.example.com/mcp" style
    # example Claude's own connector setup shows.
    streamable_http_path="/mcp",
)


# ============================================================
# MAP TOOLS
# ============================================================

@mcp.tool()
def create_map(
    width: int = 1200,
    height: int = 800,
    coordinate_system: str = "cartesian",
    xmin: float = 0,
    xmax: float = 100,
    ymin: float = 0,
    ymax: float = 100,
    grid: bool = True,
    grid_spacing: Optional[float] = 10,
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new drawable map/canvas.

    The canvas can represent:
    - a normal Cartesian graph
    - a geographic coordinate space
    - a scientific plotting surface
    - a geological map
    - any custom 2D coordinate system

    Coordinates supplied to other tools use the map's coordinate system.
    """

    return map_engine.create_map(
        width=width,
        height=height,
        coordinate_system=coordinate_system,
        xmin=xmin,
        xmax=xmax,
        ymin=ymin,
        ymax=ymax,
        grid=grid,
        grid_spacing=grid_spacing,
        title=title,
    )


@mcp.tool()
def add_points(
    points: List[Dict[str, Any]],
    layer: str = "points",
    radius: float = 5,
    color: Optional[str] = None,
    label_field: Optional[str] = None,
    show_labels: bool = False,
) -> Dict[str, Any]:
    """
    Add point features to the map.

    Each point should contain:
        {
            "x": 10,
            "y": 20,
            "label": "Sample A",
            "properties": {...}
        }

    Geographic maps may use:
        {
            "longitude": 4.91,
            "latitude": 7.63
        }

    Additional properties can be used for scientific or geological data.
    """

    return map_engine.add_points(
        points=points,
        layer=layer,
        radius=radius,
        color=color,
        label_field=label_field,
        show_labels=show_labels,
    )


@mcp.tool()
def add_lines(
    lines: List[Dict[str, Any]],
    layer: str = "lines",
    color: Optional[str] = None,
    width: float = 2,
    show_labels: bool = False,
) -> Dict[str, Any]:
    """
    Add line features to the map.

    Example:

        {
            "id": "fault_01",
            "coordinates": [
                [10, 20],
                [20, 30],
                [40, 35]
            ],
            "label": "Fault 1"
        }

    Useful for:
    - geological faults
    - boundaries
    - roads
    - rivers
    - profiles
    - trajectories
    - connections between observations
    """

    return map_engine.add_lines(
        lines=lines,
        layer=layer,
        color=color,
        width=width,
        show_labels=show_labels,
    )


@mcp.tool()
def add_polygons(
    polygons: List[Dict[str, Any]],
    layer: str = "polygons",
    fill: Optional[str] = None,
    stroke: Optional[str] = None,
    stroke_width: float = 1,
    opacity: float = 0.5,
    show_labels: bool = False,
) -> Dict[str, Any]:
    """
    Add polygon features to the map.

    Useful for:
    - geological units
    - exploration blocks
    - mineralized zones
    - study areas
    - administrative boundaries
    - anomalous zones
    """

    return map_engine.add_polygons(
        polygons=polygons,
        layer=layer,
        fill=fill,
        stroke=stroke,
        stroke_width=stroke_width,
        opacity=opacity,
        show_labels=show_labels,
    )


@mcp.tool()
def add_grid(
    spacing_x: Optional[float] = None,
    spacing_y: Optional[float] = None,
    major_every: Optional[int] = None,
    labels: bool = True,
    layer: str = "grid",
) -> Dict[str, Any]:
    """
    Add or update a coordinate grid.

    Useful for creating a graph-sheet style drawing surface.
    """

    return map_engine.add_grid(
        spacing_x=spacing_x,
        spacing_y=spacing_y,
        major_every=major_every,
        labels=labels,
        layer=layer,
    )


@mcp.tool()
def add_annotation(
    text: str,
    x: float,
    y: float,
    layer: str = "annotations",
    size: float = 14,
    color: Optional[str] = None,
    anchor: str = "start",
) -> Dict[str, Any]:
    """
    Add text to the map.

    Can be used for:
    - labels
    - geological names
    - coordinates
    - observations
    - explanations
    - map titles
    """

    return map_engine.add_annotation(
        text=text,
        x=x,
        y=y,
        layer=layer,
        size=size,
        color=color,
        anchor=anchor,
    )


@mcp.tool()
def add_circle(
    x: float,
    y: float,
    radius: float,
    layer: str = "circles",
    fill: Optional[str] = None,
    stroke: Optional[str] = None,
    stroke_width: float = 2,
    opacity: float = 0.3,
) -> Dict[str, Any]:
    """
    Add a circle to the map.

    Useful for:
    - buffers
    - influence zones
    - search areas
    - uncertainty regions
    - distance-based analysis
    """

    return map_engine.add_circle(
        x=x,
        y=y,
        radius=radius,
        layer=layer,
        fill=fill,
        stroke=stroke,
        stroke_width=stroke_width,
        opacity=opacity,
    )


@mcp.tool()
def add_rectangle(
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
    layer: str = "rectangles",
    fill: Optional[str] = None,
    stroke: Optional[str] = None,
    stroke_width: float = 2,
    opacity: float = 0.3,
) -> Dict[str, Any]:
    """
    Add a rectangle to the map.

    Useful for:
    - study areas
    - exploration blocks
    - bounding boxes
    - selection regions
    """

    return map_engine.add_rectangle(
        xmin=xmin,
        ymin=ymin,
        xmax=xmax,
        ymax=ymax,
        layer=layer,
        fill=fill,
        stroke=stroke,
        stroke_width=stroke_width,
        opacity=opacity,
    )


@mcp.tool()
def add_heatmap(
    points: List[Dict[str, Any]],
    value_field: str,
    layer: str = "heatmap",
    radius: float = 10,
) -> Dict[str, Any]:
    """
    Create a heatmap from point data.

    Each point should contain x/y coordinates and the requested value field.

    Example:

        {
            "x": 20,
            "y": 40,
            "gold_grade": 4.7
        }

    The value field determines the intensity of the visualization.
    """

    return map_engine.add_heatmap(
        points=points,
        value_field=value_field,
        layer=layer,
        radius=radius,
    )


@mcp.tool()
def add_scatter(
    data: List[Dict[str, Any]],
    x_field: str,
    y_field: str,
    layer: str = "scatter",
    radius: float = 5,
    color: Optional[str] = None,
    show_labels: bool = False,
) -> Dict[str, Any]:
    """
    Plot tabular data as an x/y scatter visualization.

    Example:

        data = [
            {"depth": 10, "grade": 1.2},
            {"depth": 20, "grade": 3.4}
        ]

        x_field = "depth"
        y_field = "grade"
    """

    return map_engine.add_scatter(
        data=data,
        x_field=x_field,
        y_field=y_field,
        layer=layer,
        radius=radius,
        color=color,
        show_labels=show_labels,
    )


@mcp.tool()
def add_contour(
    points: List[Dict[str, Any]],
    value_field: str,
    levels: Optional[List[float]] = None,
    layer: str = "contours",
) -> Dict[str, Any]:
    """
    Generate contour-style isolines from spatial point measurements.

    Intended for scientific and geological data such as:
    - elevation
    - magnetic intensity
    - gravity
    - geochemical concentration
    - temperature
    - other continuous spatial variables
    """

    return map_engine.add_contour(
        points=points,
        value_field=value_field,
        levels=levels,
        layer=layer,
    )


@mcp.tool()
def add_scale_bar(
    length: Optional[float] = None,
    x: Optional[float] = None,
    y: Optional[float] = None,
    units: str = "map units",
) -> Dict[str, Any]:
    """
    Add a scale bar to the map.
    """

    return map_engine.add_scale_bar(
        length=length,
        x=x,
        y=y,
        units=units,
    )


@mcp.tool()
def add_north_arrow(
    x: Optional[float] = None,
    y: Optional[float] = None,
    size: float = 30,
) -> Dict[str, Any]:
    """
    Add a north arrow to geographic maps.
    """

    return map_engine.add_north_arrow(
        x=x,
        y=y,
        size=size,
    )


# ============================================================
# LAYER MANAGEMENT
# ============================================================

@mcp.tool()
def list_layers() -> Dict[str, Any]:
    """
    Return all layers currently present on the map.
    """

    return map_engine.list_layers()


@mcp.tool()
def set_layer_visibility(
    layer: str,
    visible: bool,
) -> Dict[str, Any]:
    """
    Show or hide a map layer.
    """

    return map_engine.set_layer_visibility(
        layer=layer,
        visible=visible,
    )


@mcp.tool()
def remove_layer(
    layer: str,
) -> Dict[str, Any]:
    """
    Remove an entire map layer.
    """

    return map_engine.remove_layer(layer)


@mcp.tool()
def clear_map() -> Dict[str, Any]:
    """
    Clear all map features and return to an empty canvas.
    """

    return map_engine.clear()


# ============================================================
# VIEW / MAP CONTROL
# ============================================================

@mcp.tool()
def set_view(
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
) -> Dict[str, Any]:
    """
    Change the visible coordinate extent of the map.
    """

    return map_engine.set_view(
        xmin=xmin,
        xmax=xmax,
        ymin=ymin,
        ymax=ymax,
    )


@mcp.tool()
def fit_to_data(
    padding: float = 5,
) -> Dict[str, Any]:
    """
    Automatically adjust the map view to contain all current features.
    """

    return map_engine.fit_to_data(padding=padding)


# ============================================================
# DATA / STATE
# ============================================================

@mcp.tool()
def get_map_state() -> Dict[str, Any]:
    """
    Return the complete structured representation of the current map.

    This allows the AI to inspect what has already been drawn and
    continue editing it.
    """

    return map_engine.get_state()


@mcp.tool()
def get_map_summary() -> Dict[str, Any]:
    """
    Return a concise description of the current map.

    Useful for AI agents that need to understand the current canvas
    without retrieving every coordinate.
    """

    return map_engine.get_summary()


# ============================================================
# EXPORT
# ============================================================

@mcp.tool()
def export_map(
    format: str = "svg",
) -> Dict[str, Any]:
    """
    Export the current map.

    Supported formats depend on the map engine.

    Typical formats:
    - svg
    - json
    - geojson
    """

    return map_engine.export(format=format)


@mcp.tool()
def render_map() -> Dict[str, Any]:
    """
    Render the current map and return the generated visualization.

    The rendering engine produces an SVG representation that can be
    displayed by a compatible frontend.
    """

    return map_engine.render()


# ============================================================
# PLAIN HTTP ENDPOINTS
# ============================================================
# Registered directly on the MCP app via @mcp.custom_route, so they
# live on the exact same Starlette app/lifespan as the MCP endpoint
# itself — no second app, no mount.

@mcp.custom_route("/", methods=["GET"])
async def root(request: Request) -> JSONResponse:
    """Basic service information."""

    return JSONResponse(
        {
            "name": APP_NAME,
            "version": APP_VERSION,
            "description": "AI-native mapping and visualization MCP server.",
            "mcp_endpoint": "/mcp",
            "status": "online",
        }
    )


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    """Health-check endpoint for deployment platforms."""

    return JSONResponse(
        {
            "status": "healthy",
            "service": APP_NAME,
            "version": APP_VERSION,
        }
    )


@mcp.custom_route("/state", methods=["GET"])
async def state(request: Request) -> JSONResponse:
    """HTTP endpoint for retrieving the current map state."""

    return JSONResponse(map_engine.get_state())


@mcp.custom_route("/map", methods=["GET"])
async def map_view(request: Request) -> HTMLResponse:
    """
    Return a simple browser visualization of the current SVG map.

    This provides a direct way to inspect the map without requiring
    an MCP client.
    """

    result = map_engine.render()
    svg = result.get("svg", "")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{APP_NAME}</title>
        <style>
            html, body {{
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                overflow: hidden;
                background: #ffffff;
            }}

            body {{
                display: flex;
                align-items: center;
                justify-content: center;
            }}

            svg {{
                max-width: 100%;
                max-height: 100%;
                width: 100%;
                height: 100%;
            }}
        </style>
    </head>
    <body>
        {svg}
    </body>
    </html>
    """

    return HTMLResponse(content=html)


@mcp.custom_route("/map/json", methods=["GET"])
async def map_json(request: Request) -> JSONResponse:
    """Return the complete map as JSON."""

    return JSONResponse(map_engine.get_state())


class MCPOptionsBypassMiddleware:
    """
    Answers bare OPTIONS requests to the MCP endpoint directly, before
    they ever reach FastMCP's routing.

    This can't be done as a normal Starlette route (even one
    registered specifically for OPTIONS on this path): FastMCP's own
    route for `streamable_http_path` is built with no `methods`
    filter at all, so at the Starlette routing layer it matches
    *every* HTTP method as a full match, including OPTIONS. Since
    that route is always added to the app first, it always wins the
    match before any later route — including one aimed only at
    OPTIONS — is ever considered. Only once the request reaches
    FastMCP's own ASGI handler does *it* decide OPTIONS isn't
    supported, and return a bare error.

    Middleware runs before routing, so intercepting here sidesteps
    that ordering entirely, regardless of how FastMCP orders its
    internal route list internally (now or in a future version).

    Only requests with *no* Origin header are intercepted. A real
    browser CORS preflight always includes one, and those are left
    to pass through untouched so CORSMiddleware (below) keeps
    handling that case exactly as it already does.
    """

    def __init__(self, app: Any, mcp_path: str) -> None:
        self.app = app
        self.mcp_path = mcp_path

    async def __call__(self, scope: Dict[str, Any], receive: Any, send: Any) -> None:
        if (
            scope.get("type") == "http"
            and scope.get("method") == "OPTIONS"
            and scope.get("path") == self.mcp_path
        ):
            header_names = {name for name, _ in scope.get("headers", [])}

            if b"origin" not in header_names:
                response = Response(
                    status_code=204,
                    headers={"Allow": "OPTIONS, GET, POST, DELETE"},
                )
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)


# ============================================================
# ASGI APPLICATION
# ============================================================
# This *is* the app uvicorn runs — mcp.streamable_http_app() already
# includes /mcp and every custom_route registered above, all as
# routes on one Starlette instance, with the correct lifespan already
# wired in by FastMCP itself. There is nothing left to compose.

app = mcp.streamable_http_app()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    MCPOptionsBypassMiddleware,
    mcp_path="/mcp",
)


# ============================================================
# LOCAL DEVELOPMENT
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
    )
