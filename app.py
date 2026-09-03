from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from mcp.server.fastmcp import FastMCP

from map import MapEngine


# ============================================================
# Configuration
# ============================================================

APP_NAME = "AI Map MCP"
APP_VERSION = "1.0.0"

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Shared map engine.
# The engine maintains the current canvas/map state.
map_engine = MapEngine()


# ============================================================
# MCP SERVER
# ============================================================

mcp = FastMCP(
    name=APP_NAME,
    # We mount this server under "/mcp" on the FastAPI app below.
    # FastMCP's own default internal route is ALSO "/mcp", so leaving
    # this unset produces a real endpoint at /mcp/mcp instead of /mcp.
    # Setting it to "/" here means the mount prefix ("/mcp") becomes
    # the actual, correct endpoint path.
    streamable_http_path="/",
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

    result = map_engine.create_map(
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

    return result


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
# FASTAPI APPLICATION
# ============================================================

# Build the MCP ASGI sub-app *before* the FastAPI app so we can wire
# its session manager into our lifespan (see note below).
mcp_app = mcp.streamable_http_app()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # FastMCP's streamable_http_app() normally starts its session
    # manager's task group via its own Starlette lifespan handler.
    # That only fires when the app is run directly with uvicorn.
    # When it's *mounted* inside another app (as we do below),
    # the parent app's lifespan does not automatically trigger it,
    # so every request fails with:
    #   RuntimeError: Task group is not initialized. Make sure to use run().
    # Running mcp.session_manager.run() inside our own lifespan fixes
    # that: it starts before the app accepts requests and stops on
    # shutdown, matching what FastMCP would do if it were standalone.
    async with mcp.session_manager.run():
        yield


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "An MCP server that gives AI systems the ability to create, "
        "edit, analyze and export 2D maps and scientific visualizations."
    ),
    lifespan=lifespan,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# BASIC HTTP ENDPOINTS
# ============================================================

@app.get("/")
async def root() -> Dict[str, Any]:
    """
    Basic service information.
    """

    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "description": (
            "AI-native mapping and visualization MCP server."
        ),
        "mcp_endpoint": "/mcp",
        "status": "online",
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    """
    Health-check endpoint for deployment platforms.
    """

    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION,
    }


@app.get("/state")
async def state() -> Dict[str, Any]:
    """
    HTTP endpoint for retrieving the current map state.
    """

    return map_engine.get_state()


@app.get("/map")
async def map_view() -> HTMLResponse:
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


@app.get("/map/json")
async def map_json() -> JSONResponse:
    """
    Return the complete map as JSON.
    """

    return JSONResponse(
        content=map_engine.get_state()
    )


# ============================================================
# MCP MOUNT
# ============================================================

# Explicit OPTIONS handlers for the MCP endpoint. FastMCP's mounted
# streamable-http route only declares GET, POST, DELETE, so a bare
# OPTIONS request (the kind of capability probe some MCP clients,
# including Claude's own connector setup flow, send before doing
# anything else) hits the mount and gets a bare 405 back with no
# CORS headers, since CORSMiddleware only handles OPTIONS requests
# that carry an Origin header (real browser preflight) and otherwise
# passes them straight through to the route. Registering these here,
# before the mount, means they're matched first for OPTIONS
# specifically, while GET/POST/DELETE continue through to the mount
# exactly as before.
@app.options("/mcp")
@app.options("/mcp/")
async def mcp_options() -> Response:
    return Response(status_code=204, headers={"Allow": "OPTIONS, GET, POST, DELETE"})


# mcp_app was already built above (before the FastAPI app existed)
# so its lifespan could be wired in. Mount it here, after all the
# plain HTTP routes are registered.
app.mount(
    "/mcp",
    mcp_app,
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
