"""
map.py
------
Core 2D mapping and scientific visualization engine for AI Map MCP.

The engine maintains a structured map state and renders it to SVG.
It supports Cartesian and geographic coordinate spaces, layers,
points, lines, polygons, grids, annotations, circles, rectangles,
scatter plots, heatmaps, contours, scale bars, north arrows,
view management, state inspection, and export.
"""

from __future__ import annotations

import json
import math
import uuid
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple


class MapEngine:
    """
    Stateful 2D map/drawing engine.

    The AI interacts with this class indirectly through the MCP
    tools exposed by app.py.
    """

    def __init__(self) -> None:
        self.state: Dict[str, Any] = {}
        self.reset()

    # ============================================================
    # STATE
    # ============================================================

    def reset(self) -> None:
        self.state = {
            "map": {
                "id": self._id("map"),
                "width": 1200,
                "height": 800,
                "coordinate_system": "cartesian",
                "title": None,
                "bounds": {
                    "xmin": 0.0,
                    "xmax": 100.0,
                    "ymin": 0.0,
                    "ymax": 100.0,
                },
            },
            "layers": [],
            "metadata": {},
        }

    def _id(self, prefix: str = "feature") -> str:
        return f"{prefix}_{uuid.uuid4().hex[:10]}"

    def _ensure_map(self) -> None:
        if not self.state or "map" not in self.state:
            self.reset()

    def _find_layer(self, name: str) -> Optional[Dict[str, Any]]:
        for layer in self.state["layers"]:
            if layer["name"] == name:
                return layer
        return None

    def _get_or_create_layer(
        self,
        name: str,
        layer_type: str = "features",
    ) -> Dict[str, Any]:

        layer = self._find_layer(name)

        if layer is None:
            layer = {
                "id": self._id("layer"),
                "name": name,
                "type": layer_type,
                "visible": True,
                "features": [],
            }

            self.state["layers"].append(layer)

        return layer

    # ============================================================
    # MAP CREATION
    # ============================================================

    def create_map(
        self,
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

        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be positive.")

        if xmin >= xmax or ymin >= ymax:
            raise ValueError("Invalid coordinate bounds.")

        self.reset()

        self.state["map"] = {
            "id": self._id("map"),
            "width": int(width),
            "height": int(height),
            "coordinate_system": coordinate_system,
            "title": title,
            "bounds": {
                "xmin": float(xmin),
                "xmax": float(xmax),
                "ymin": float(ymin),
                "ymax": float(ymax),
            },
        }

        if grid:
            self.add_grid(
                spacing_x=grid_spacing,
                spacing_y=grid_spacing,
            )

        return {
            "success": True,
            "map_id": self.state["map"]["id"],
            "coordinate_system": coordinate_system,
            "bounds": self.state["map"]["bounds"],
            "width": width,
            "height": height,
        }

    # ============================================================
    # COORDINATE TRANSFORMATION
    # ============================================================

    def world_to_screen(
        self,
        x: float,
        y: float,
        margin: float = 50,
    ) -> Tuple[float, float]:

        bounds = self.state["map"]["bounds"]

        xmin = bounds["xmin"]
        xmax = bounds["xmax"]
        ymin = bounds["ymin"]
        ymax = bounds["ymax"]

        width = self.state["map"]["width"]
        height = self.state["map"]["height"]

        drawable_width = max(width - 2 * margin, 1)
        drawable_height = max(height - 2 * margin, 1)

        sx = (
            margin
            + ((x - xmin) / (xmax - xmin)) * drawable_width
        )

        sy = (
            height
            - margin
            - ((y - ymin) / (ymax - ymin)) * drawable_height
        )

        return sx, sy

    def screen_to_world(
        self,
        sx: float,
        sy: float,
        margin: float = 50,
    ) -> Tuple[float, float]:

        bounds = self.state["map"]["bounds"]

        width = self.state["map"]["width"]
        height = self.state["map"]["height"]

        drawable_width = max(width - 2 * margin, 1)
        drawable_height = max(height - 2 * margin, 1)

        x = (
            bounds["xmin"]
            + ((sx - margin) / drawable_width)
            * (bounds["xmax"] - bounds["xmin"])
        )

        y = (
            bounds["ymin"]
            + ((height - margin - sy) / drawable_height)
            * (bounds["ymax"] - bounds["ymin"])
        )

        return x, y

    # ============================================================
    # POINTS
    # ============================================================

    def add_points(
        self,
        points: List[Dict[str, Any]],
        layer: str = "points",
        radius: float = 5,
        color: Optional[str] = None,
        label_field: Optional[str] = None,
        show_labels: bool = False,
    ) -> Dict[str, Any]:

        target = self._get_or_create_layer(layer, "points")

        created = []

        for point in points:

            if "longitude" in point and "latitude" in point:
                x = float(point["longitude"])
                y = float(point["latitude"])
            else:
                if "x" not in point or "y" not in point:
                    raise ValueError(
                        "Every point requires x/y or longitude/latitude."
                    )

                x = float(point["x"])
                y = float(point["y"])

            properties = deepcopy(
                point.get("properties", {})
            )

            for key, value in point.items():
                if key not in {
                    "x",
                    "y",
                    "longitude",
                    "latitude",
                    "label",
                    "properties",
                }:
                    properties[key] = value

            label = point.get("label")

            if label_field:
                label = point.get(label_field)

                if label is None:
                    label = properties.get(label_field)

            feature = {
                "id": point.get("id", self._id("point")),
                "type": "Point",
                "geometry": {
                    "x": x,
                    "y": y,
                },
                "properties": properties,
                "label": label,
                "style": {
                    "radius": float(radius),
                    "color": color or "#2563eb",
                    "show_label": bool(show_labels),
                },
            }

            target["features"].append(feature)
            created.append(feature["id"])

        return {
            "success": True,
            "layer": layer,
            "features_added": len(created),
            "feature_ids": created,
        }

    # ============================================================
    # LINES
    # ============================================================

    def add_lines(
        self,
        lines: List[Dict[str, Any]],
        layer: str = "lines",
        color: Optional[str] = None,
        width: float = 2,
        show_labels: bool = False,
    ) -> Dict[str, Any]:

        target = self._get_or_create_layer(layer, "lines")

        created = []

        for line in lines:

            coordinates = line.get("coordinates")

            if not coordinates or len(coordinates) < 2:
                raise ValueError(
                    "Every line requires at least two coordinates."
                )

            normalized = [
                [float(p[0]), float(p[1])]
                for p in coordinates
            ]

            feature = {
                "id": line.get("id", self._id("line")),
                "type": "LineString",
                "geometry": {
                    "coordinates": normalized,
                },
                "properties": deepcopy(
                    line.get("properties", {})
                ),
                "label": line.get("label"),
                "style": {
                    "color": color or "#dc2626",
                    "width": float(width),
                    "show_label": bool(show_labels),
                },
            }

            target["features"].append(feature)
            created.append(feature["id"])

        return {
            "success": True,
            "layer": layer,
            "features_added": len(created),
            "feature_ids": created,
        }

    # ============================================================
    # POLYGONS
    # ============================================================

    def add_polygons(
        self,
        polygons: List[Dict[str, Any]],
        layer: str = "polygons",
        fill: Optional[str] = None,
        stroke: Optional[str] = None,
        stroke_width: float = 1,
        opacity: float = 0.5,
        show_labels: bool = False,
    ) -> Dict[str, Any]:

        target = self._get_or_create_layer(layer, "polygons")

        created = []

        for polygon in polygons:

            coordinates = polygon.get("coordinates")

            if not coordinates or len(coordinates) < 3:
                raise ValueError(
                    "Every polygon requires at least three coordinates."
                )

            normalized = [
                [float(p[0]), float(p[1])]
                for p in coordinates
            ]

            feature = {
                "id": polygon.get("id", self._id("polygon")),
                "type": "Polygon",
                "geometry": {
                    "coordinates": normalized,
                },
                "properties": deepcopy(
                    polygon.get("properties", {})
                ),
                "label": polygon.get("label"),
                "style": {
                    "fill": fill or "#94a3b8",
                    "stroke": stroke or "#334155",
                    "stroke_width": float(stroke_width),
                    "opacity": max(
                        0.0,
                        min(1.0, float(opacity)),
                    ),
                    "show_label": bool(show_labels),
                },
            }

            target["features"].append(feature)
            created.append(feature["id"])

        return {
            "success": True,
            "layer": layer,
            "features_added": len(created),
            "feature_ids": created,
        }

    # ============================================================
    # GRID
    # ============================================================

    def add_grid(
        self,
        spacing_x: Optional[float] = None,
        spacing_y: Optional[float] = None,
        major_every: Optional[int] = None,
        labels: bool = True,
        layer: str = "grid",
    ) -> Dict[str, Any]:

        bounds = self.state["map"]["bounds"]

        sx = spacing_x or (
            bounds["xmax"] - bounds["xmin"]
        ) / 10

        sy = spacing_y or (
            bounds["ymax"] - bounds["ymin"]
        ) / 10

        if sx <= 0 or sy <= 0:
            raise ValueError("Grid spacing must be positive.")

        target = self._get_or_create_layer(layer, "grid")

        target["features"] = []

        # Vertical lines.
        x = bounds["xmin"]
        index = 0

        while x <= bounds["xmax"] + sx * 0.000001:

            major = (
                major_every is not None
                and index % max(int(major_every), 1) == 0
            )

            target["features"].append({
                "id": self._id("grid"),
                "type": "GridLine",
                "axis": "x",
                "value": x,
                "major": major,
                "label": str(self._format_number(x))
                if labels else None,
            })

            x += sx
            index += 1

        # Horizontal lines.
        y = bounds["ymin"]
        index = 0

        while y <= bounds["ymax"] + sy * 0.000001:

            major = (
                major_every is not None
                and index % max(int(major_every), 1) == 0
            )

            target["features"].append({
                "id": self._id("grid"),
                "type": "GridLine",
                "axis": "y",
                "value": y,
                "major": major,
                "label": str(self._format_number(y))
                if labels else None,
            })

            y += sy
            index += 1

        return {
            "success": True,
            "layer": layer,
            "spacing_x": sx,
            "spacing_y": sy,
            "features": len(target["features"]),
        }

    # ============================================================
    # ANNOTATIONS
    # ============================================================

    def add_annotation(
        self,
        text: str,
        x: float,
        y: float,
        layer: str = "annotations",
        size: float = 14,
        color: Optional[str] = None,
        anchor: str = "start",
    ) -> Dict[str, Any]:

        target = self._get_or_create_layer(
            layer,
            "annotations",
        )

        feature = {
            "id": self._id("text"),
            "type": "Text",
            "geometry": {
                "x": float(x),
                "y": float(y),
            },
            "text": str(text),
            "style": {
                "size": float(size),
                "color": color or "#111827",
                "anchor": anchor,
            },
        }

        target["features"].append(feature)

        return {
            "success": True,
            "layer": layer,
            "feature_id": feature["id"],
        }

    # ============================================================
    # CIRCLES
    # ============================================================

    def add_circle(
        self,
        x: float,
        y: float,
        radius: float,
        layer: str = "circles",
        fill: Optional[str] = None,
        stroke: Optional[str] = None,
        stroke_width: float = 2,
        opacity: float = 0.3,
    ) -> Dict[str, Any]:

        if radius <= 0:
            raise ValueError("Circle radius must be positive.")

        target = self._get_or_create_layer(
            layer,
            "circles",
        )

        feature = {
            "id": self._id("circle"),
            "type": "Circle",
            "geometry": {
                "x": float(x),
                "y": float(y),
                "radius": float(radius),
            },
            "style": {
                "fill": fill or "#3b82f6",
                "stroke": stroke or "#1d4ed8",
                "stroke_width": float(stroke_width),
                "opacity": max(
                    0,
                    min(1, float(opacity)),
                ),
            },
        }

        target["features"].append(feature)

        return {
            "success": True,
            "layer": layer,
            "feature_id": feature["id"],
        }

    # ============================================================
    # RECTANGLES
    # ============================================================

    def add_rectangle(
        self,
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

        if xmin >= xmax or ymin >= ymax:
            raise ValueError("Invalid rectangle coordinates.")

        target = self._get_or_create_layer(
            layer,
            "rectangles",
        )

        feature = {
            "id": self._id("rectangle"),
            "type": "Rectangle",
            "geometry": {
                "xmin": float(xmin),
                "ymin": float(ymin),
                "xmax": float(xmax),
                "ymax": float(ymax),
            },
            "style": {
                "fill": fill or "#64748b",
                "stroke": stroke or "#334155",
                "stroke_width": float(stroke_width),
                "opacity": max(
                    0,
                    min(1, float(opacity)),
                ),
            },
        }

        target["features"].append(feature)

        return {
            "success": True,
            "layer": layer,
            "feature_id": feature["id"],
        }

    # ============================================================
    # SCATTER
    # ============================================================

    def add_scatter(
        self,
        data: List[Dict[str, Any]],
        x_field: str,
        y_field: str,
        layer: str = "scatter",
        radius: float = 5,
        color: Optional[str] = None,
        show_labels: bool = False,
    ) -> Dict[str, Any]:

        points = []

        for row in data:

            if x_field not in row or y_field not in row:
                continue

            points.append({
                "x": float(row[x_field]),
                "y": float(row[y_field]),
                "properties": deepcopy(row),
                "label": str(row.get("label", "")),
            })

        return self.add_points(
            points=points,
            layer=layer,
            radius=radius,
            color=color,
            show_labels=show_labels,
        )

    # ============================================================
    # HEATMAP
    # ============================================================

    def add_heatmap(
        self,
        points: List[Dict[str, Any]],
        value_field: str,
        layer: str = "heatmap",
        radius: float = 10,
    ) -> Dict[str, Any]:

        values = []

        for point in points:
            if value_field in point:
                try:
                    values.append(float(point[value_field]))
                except (ValueError, TypeError):
                    pass

            elif value_field in point.get("properties", {}):
                try:
                    values.append(
                        float(
                            point["properties"][value_field]
                        )
                    )
                except (ValueError, TypeError):
                    pass

        if not values:
            raise ValueError(
                f"No numeric values found for '{value_field}'."
            )

        minimum = min(values)
        maximum = max(values)

        target = self._get_or_create_layer(
            layer,
            "heatmap",
        )

        target["features"] = []

        for point in points:

            if "longitude" in point:
                x = float(point["longitude"])
                y = float(point["latitude"])
            else:
                x = float(point["x"])
                y = float(point["y"])

            raw = point.get(value_field)

            if raw is None:
                raw = point.get(
                    "properties",
                    {},
                ).get(value_field)

            try:
                value = float(raw)
            except (ValueError, TypeError):
                continue

            if maximum == minimum:
                normalized = 1.0
            else:
                normalized = (
                    value - minimum
                ) / (
                    maximum - minimum
                )

            feature = {
                "id": self._id("heat"),
                "type": "HeatPoint",
                "geometry": {
                    "x": x,
                    "y": y,
                },
                "value": value,
                "normalized": normalized,
                "radius": float(radius),
                "properties": deepcopy(
                    point.get("properties", {})
                ),
            }

            target["features"].append(feature)

        return {
            "success": True,
            "layer": layer,
            "value_field": value_field,
            "minimum": minimum,
            "maximum": maximum,
            "features_added": len(target["features"]),
        }

    # ============================================================
    # CONTOURS
    # ============================================================

    def add_contour(
        self,
        points: List[Dict[str, Any]],
        value_field: str,
        levels: Optional[List[float]] = None,
        layer: str = "contours",
    ) -> Dict[str, Any]:

        """
        Generate contour-style isolines using a lightweight
        inverse-distance weighting interpolation.

        This is deliberately implemented without external
        geospatial dependencies so the MCP remains portable.
        """

        observations = []

        for point in points:

            try:
                if "longitude" in point:
                    x = float(point["longitude"])
                    y = float(point["latitude"])
                else:
                    x = float(point["x"])
                    y = float(point["y"])

                raw = point.get(value_field)

                if raw is None:
                    raw = point.get(
                        "properties",
                        {},
                    ).get(value_field)

                value = float(raw)

                observations.append(
                    (x, y, value)
                )

            except (
                ValueError,
                TypeError,
                KeyError,
            ):
                continue

        if len(observations) < 3:
            raise ValueError(
                "At least three numeric observations are required "
                "for contour generation."
            )

        values = [
            p[2]
            for p in observations
        ]

        minimum = min(values)
        maximum = max(values)

        if levels is None:
            count = 8

            step = (
                maximum - minimum
            ) / count

            if step == 0:
                levels = [minimum]
            else:
                levels = [
                    minimum + step * i
                    for i in range(1, count)
                ]

        target = self._get_or_create_layer(
            layer,
            "contours",
        )

        target["features"] = []

        # Create a regular interpolation grid.
        bounds = self._data_bounds(
            [
                {
                    "x": p[0],
                    "y": p[1]
                }
                for p in observations
            ]
        )

        grid_size = 40

        xs = self._linspace(
            bounds["xmin"],
            bounds["xmax"],
            grid_size,
        )

        ys = self._linspace(
            bounds["ymin"],
            bounds["ymax"],
            grid_size,
        )

        values_grid = []

        for y in ys:
            row = []

            for x in xs:

                weighted_sum = 0.0
                weight_sum = 0.0

                for ox, oy, value in observations:

                    distance = math.hypot(
                        x - ox,
                        y - oy,
                    )

                    if distance < 1e-12:
                        weighted_sum = value
                        weight_sum = 1.0
                        break

                    weight = 1 / (
                        distance * distance
                    )

                    weighted_sum += (
                        value * weight
                    )

                    weight_sum += weight

                row.append(
                    weighted_sum / weight_sum
                )

            values_grid.append(row)

        # A lightweight marching-squares implementation.
        for level in levels:

            segments = self._marching_squares(
                xs,
                ys,
                values_grid,
                float(level),
            )

            for segment in segments:

                target["features"].append({
                    "id": self._id("contour"),
                    "type": "Contour",
                    "level": float(level),
                    "geometry": {
                        "coordinates": segment,
                    },
                    "style": {
                        "color": "#7c3aed",
                        "width": 1.5,
                    },
                })

        return {
            "success": True,
            "layer": layer,
            "levels": levels,
            "features_generated": len(
                target["features"]
            ),
        }

    # ============================================================
    # SCALE BAR
    # ============================================================

    def add_scale_bar(
        self,
        length: Optional[float] = None,
        x: Optional[float] = None,
        y: Optional[float] = None,
        units: str = "map units",
    ) -> Dict[str, Any]:

        bounds = self.state["map"]["bounds"]

        if length is None:
            length = (
                bounds["xmax"]
                - bounds["xmin"]
            ) / 5

        if x is None:
            x = bounds["xmin"] + (
                bounds["xmax"]
                - bounds["xmin"]
            ) * 0.05

        if y is None:
            y = bounds["ymin"] + (
                bounds["ymax"]
                - bounds["ymin"]
            ) * 0.05

        target = self._get_or_create_layer(
            "map_decorations",
            "decorations",
        )

        feature = {
            "id": self._id("scale"),
            "type": "ScaleBar",
            "geometry": {
                "x": float(x),
                "y": float(y),
                "length": float(length),
            },
            "units": units,
        }

        target["features"].append(feature)

        return {
            "success": True,
            "feature_id": feature["id"],
            "length": length,
            "units": units,
        }

    # ============================================================
    # NORTH ARROW
    # ============================================================

    def add_north_arrow(
        self,
        x: Optional[float] = None,
        y: Optional[float] = None,
        size: float = 30,
    ) -> Dict[str, Any]:

        bounds = self.state["map"]["bounds"]

        if x is None:
            x = (
                bounds["xmin"]
                + (
                    bounds["xmax"]
                    - bounds["xmin"]
                ) * 0.92
            )

        if y is None:
            y = (
                bounds["ymin"]
                + (
                    bounds["ymax"]
                    - bounds["ymin"]
                ) * 0.90
            )

        target = self._get_or_create_layer(
            "map_decorations",
            "decorations",
        )

        feature = {
            "id": self._id("north"),
            "type": "NorthArrow",
            "geometry": {
                "x": float(x),
                "y": float(y),
                "size": float(size),
            },
        }

        target["features"].append(feature)

        return {
            "success": True,
            "feature_id": feature["id"],
        }

    # ============================================================
    # LAYER MANAGEMENT
    # ============================================================

    def list_layers(self) -> Dict[str, Any]:

        return {
            "success": True,
            "layers": [
                {
                    "id": layer["id"],
                    "name": layer["name"],
                    "type": layer["type"],
                    "visible": layer["visible"],
                    "feature_count": len(
                        layer["features"]
                    ),
                }
                for layer in self.state["layers"]
            ],
        }

    def set_layer_visibility(
        self,
        layer: str,
        visible: bool,
    ) -> Dict[str, Any]:

        target = self._find_layer(layer)

        if target is None:
            raise ValueError(
                f"Layer '{layer}' does not exist."
            )

        target["visible"] = bool(visible)

        return {
            "success": True,
            "layer": layer,
            "visible": visible,
        }

    def remove_layer(
        self,
        layer: str,
    ) -> Dict[str, Any]:

        original_count = len(
            self.state["layers"]
        )

        self.state["layers"] = [
            item
            for item in self.state["layers"]
            if item["name"] != layer
        ]

        if len(self.state["layers"]) == original_count:
            raise ValueError(
                f"Layer '{layer}' does not exist."
            )

        return {
            "success": True,
            "layer_removed": layer,
        }

    def clear(self) -> Dict[str, Any]:

        self.state["layers"] = []

        return {
            "success": True,
            "message": "Map cleared.",
        }

    # ============================================================
    # VIEW
    # ============================================================

    def set_view(
        self,
        xmin: float,
        xmax: float,
        ymin: float,
        ymax: float,
    ) -> Dict[str, Any]:

        if xmin >= xmax or ymin >= ymax:
            raise ValueError("Invalid view bounds.")

        self.state["map"]["bounds"] = {
            "xmin": float(xmin),
            "xmax": float(xmax),
            "ymin": float(ymin),
            "ymax": float(ymax),
        }

        return {
            "success": True,
            "bounds": self.state["map"]["bounds"],
        }

    def fit_to_data(
        self,
        padding: float = 5,
    ) -> Dict[str, Any]:

        coordinates = []

        for layer in self.state["layers"]:

            for feature in layer["features"]:

                geometry = feature.get(
                    "geometry",
                    {},
                )

                feature_type = feature.get(
                    "type"
                )

                if feature_type == "Point":
                    coordinates.append(
                        (
                            geometry["x"],
                            geometry["y"],
                        )
                    )

                elif feature_type == "LineString":
                    coordinates.extend(
                        [
                            (p[0], p[1])
                            for p in geometry[
                                "coordinates"
                            ]
                        ]
                    )

                elif feature_type == "Polygon":
                    coordinates.extend(
                        [
                            (p[0], p[1])
                            for p in geometry[
                                "coordinates"
                            ]
                        ]
                    )

                elif feature_type == "Circle":
                    x = geometry["x"]
                    y = geometry["y"]
                    r = geometry["radius"]

                    coordinates.extend([
                        (x - r, y - r),
                        (x + r, y + r),
                    ])

                elif feature_type == "Rectangle":
                    coordinates.extend([
                        (
                            geometry["xmin"],
                            geometry["ymin"],
                        ),
                        (
                            geometry["xmax"],
                            geometry["ymax"],
                        ),
                    ])

                elif feature_type == "Text":
                    coordinates.append(
                        (
                            geometry["x"],
                            geometry["y"],
                        )
                    )

        if not coordinates:
            return {
                "success": False,
                "message": "No spatial data available.",
            }

        xs = [p[0] for p in coordinates]
        ys = [p[1] for p in coordinates]

        xmin = min(xs)
        xmax = max(xs)
        ymin = min(ys)
        ymax = max(ys)

        xspan = xmax - xmin
        yspan = ymax - ymin

        if xspan == 0:
            xspan = 1

        if yspan == 0:
            yspan = 1

        xpad = xspan * (
            float(padding) / 100
        )

        ypad = yspan * (
            float(padding) / 100
        )

        return self.set_view(
            xmin=xmin - xpad,
            xmax=xmax + xpad,
            ymin=ymin - ypad,
            ymax=ymax + ypad,
        )

    # ============================================================
    # STATE INSPECTION
    # ============================================================

    def get_state(self) -> Dict[str, Any]:
        return deepcopy(self.state)

    def get_summary(self) -> Dict[str, Any]:

        layers = []

        total_features = 0

        for layer in self.state["layers"]:

            count = len(layer["features"])

            total_features += count

            layers.append({
                "name": layer["name"],
                "type": layer["type"],
                "visible": layer["visible"],
                "feature_count": count,
            })

        return {
            "map": deepcopy(
                self.state["map"]
            ),
            "layer_count": len(layers),
            "total_features": total_features,
            "layers": layers,
        }

    # ============================================================
    # EXPORT
    # ============================================================

    def export(
        self,
        format: str = "svg",
    ) -> Dict[str, Any]:

        format = format.lower().strip()

        if format == "svg":
            return {
                "success": True,
                "format": "svg",
                "svg": self._render_svg(),
            }

        if format == "json":
            return {
                "success": True,
                "format": "json",
                "data": deepcopy(
                    self.state
                ),
            }

        if format == "geojson":
            return {
                "success": True,
                "format": "geojson",
                "data": self._to_geojson(),
            }

        raise ValueError(
            f"Unsupported export format: {format}"
        )

    def render(self) -> Dict[str, Any]:

        svg = self._render_svg()

        return {
            "success": True,
            "format": "svg",
            "svg": svg,
            "map": deepcopy(
                self.state["map"]
            ),
            "layers": self.list_layers()[
                "layers"
            ],
        }

    # ============================================================
    # SVG RENDERER
    # ============================================================

    def _render_svg(self) -> str:

        width = self.state["map"]["width"]
        height = self.state["map"]["height"]

        title = self.state["map"].get(
            "title"
        )

        parts = [
            (
                f'<svg xmlns="http://www.w3.org/2000/svg" '
                f'width="{width}" height="{height}" '
                f'viewBox="0 0 {width} {height}">'
            )
        ]

        parts.append(
            '<rect width="100%" height="100%" '
            'fill="white"/>'
        )

        if title:
            parts.append(
                self._svg_text(
                    width / 2,
                    28,
                    title,
                    size=20,
                    anchor="middle",
                )
            )

        for layer in self.state["layers"]:

            if not layer["visible"]:
                continue

            parts.append(
                f'<g id="{self._escape(layer["name"])}">'
            )

            for feature in layer["features"]:

                rendered = (
                    self._render_feature(
                        feature
                    )
                )

                if rendered:
                    parts.append(rendered)

            parts.append("</g>")

        parts.append("</svg>")

        return "\n".join(parts)

    def _render_feature(
        self,
        feature: Dict[str, Any],
    ) -> str:

        feature_type = feature.get(
            "type"
        )

        geometry = feature.get(
            "geometry",
            {},
        )

        style = feature.get(
            "style",
            {},
        )

        if feature_type == "GridLine":

            value = geometry.get(
                "value"
            )

            if feature.get("axis") == "x":
                x1, y1 = self.world_to_screen(
                    value,
                    self.state["map"][
                        "bounds"
                    ]["ymin"],
                )

                x2, y2 = self.world_to_screen(
                    value,
                    self.state["map"][
                        "bounds"
                    ]["ymax"],
                )

                line = (
                    f'<line x1="{x1:.2f}" '
                    f'y1="{y1:.2f}" '
                    f'x2="{x2:.2f}" '
                    f'y2="{y2:.2f}" '
                    f'stroke="#e5e7eb" '
                    f'stroke-width="1"/>'
                )

                label = feature.get("label")

                if label:
                    line += self._svg_text(
                        x1,
                        self.state["map"]["height"]
                        - 10,
                        label,
                        size=10,
                        anchor="middle",
                        color="#6b7280",
                    )

                return line

            y = value

            x1, y1 = self.world_to_screen(
                self.state["map"][
                    "bounds"
                ]["xmin"],
                y,
            )

            x2, y2 = self.world_to_screen(
                self.state["map"][
                    "bounds"
                ]["xmax"],
                y,
            )

            line = (
                f'<line x1="{x1:.2f}" '
                f'y1="{y1:.2f}" '
                f'x2="{x2:.2f}" '
                f'y2="{y2:.2f}" '
                f'stroke="#e5e7eb" '
                f'stroke-width="1"/>'
            )

            label = feature.get("label")

            if label:
                line += self._svg_text(
                    8,
                    y1 + 4,
                    label,
                    size=10,
                    anchor="start",
                    color="#6b7280",
                )

            return line

        if feature_type == "Point":

            x, y = self.world_to_screen(
                geometry["x"],
                geometry["y"],
            )

            radius = style.get(
                "radius",
                5,
            )

            color = style.get(
                "color",
                "#2563eb",
            )

            output = (
                f'<circle cx="{x:.2f}" '
                f'cy="{y:.2f}" '
                f'r="{radius}" '
                f'fill="{self._escape(color)}"/>'
            )

            if style.get(
                "show_label"
            ) and feature.get("label"):

                output += self._svg_text(
                    x + radius + 4,
                    y - radius - 2,
                    str(feature["label"]),
                    size=11,
                    anchor="start",
                    color="#111827",
                )

            return output

        if feature_type == "LineString":

            coordinates = geometry[
                "coordinates"
            ]

            points = []

            for point in coordinates:
                sx, sy = self.world_to_screen(
                    point[0],
                    point[1],
                )

                points.append(
                    f"{sx:.2f},{sy:.2f}"
                )

            output = (
                f'<polyline points="{" ".join(points)}" '
                f'fill="none" '
                f'stroke="{self._escape(style.get("color", "#dc2626"))}" '
                f'stroke-width="{style.get("width", 2)}" '
                f'stroke-linejoin="round" '
                f'stroke-linecap="round"/>'
            )

            if (
                style.get("show_label")
                and feature.get("label")
            ):
                midpoint = coordinates[
                    len(coordinates) // 2
                ]

                sx, sy = self.world_to_screen(
                    midpoint[0],
                    midpoint[1],
                )

                output += self._svg_text(
                    sx,
                    sy,
                    str(feature["label"]),
                    size=11,
                    anchor="middle",
                )

            return output

        if feature_type == "Polygon":

            coordinates = geometry[
                "coordinates"
            ]

            points = []

            for point in coordinates:
                sx, sy = self.world_to_screen(
                    point[0],
                    point[1],
                )

                points.append(
                    f"{sx:.2f},{sy:.2f}"
                )

            output = (
                f'<polygon points="{" ".join(points)}" '
                f'fill="{self._escape(style.get("fill", "#94a3b8"))}" '
                f'fill-opacity="{style.get("opacity", 0.5)}" '
                f'stroke="{self._escape(style.get("stroke", "#334155"))}" '
                f'stroke-width="{style.get("stroke_width", 1)}"/>'
            )

            if (
                style.get("show_label")
                and feature.get("label")
            ):
                cx = sum(
                    p[0]
                    for p in coordinates
                ) / len(coordinates)

                cy = sum(
                    p[1]
                    for p in coordinates
                ) / len(coordinates)

                sx, sy = self.world_to_screen(
                    cx,
                    cy,
                )

                output += self._svg_text(
                    sx,
                    sy,
                    str(feature["label"]),
                    size=11,
                    anchor="middle",
                )

            return output

        if feature_type == "Circle":

            x, y = self.world_to_screen(
                geometry["x"],
                geometry["y"],
            )

            radius_world = geometry[
                "radius"
            ]

            # Convert world radius to screen radius.
            sx2, _ = self.world_to_screen(
                geometry["x"] + radius_world,
                geometry["y"],
            )

            screen_radius = abs(
                sx2 - x
            )

            return (
                f'<circle cx="{x:.2f}" '
                f'cy="{y:.2f}" '
                f'r="{screen_radius:.2f}" '
                f'fill="{self._escape(style.get("fill", "#3b82f6"))}" '
                f'fill-opacity="{style.get("opacity", 0.3)}" '
                f'stroke="{self._escape(style.get("stroke", "#1d4ed8"))}" '
                f'stroke-width="{style.get("stroke_width", 2)}"/>'
            )

        if feature_type == "Rectangle":

            x1, y1 = self.world_to_screen(
                geometry["xmin"],
                geometry["ymax"],
            )

            x2, y2 = self.world_to_screen(
                geometry["xmax"],
                geometry["ymin"],
            )

            width = abs(x2 - x1)
            height = abs(y2 - y1)

            return (
                f'<rect x="{x1:.2f}" '
                f'y="{y1:.2f}" '
                f'width="{width:.2f}" '
                f'height="{height:.2f}" '
                f'fill="{self._escape(style.get("fill", "#64748b"))}" '
                f'fill-opacity="{style.get("opacity", 0.3)}" '
                f'stroke="{self._escape(style.get("stroke", "#334155"))}" '
                f'stroke-width="{style.get("stroke_width", 2)}"/>'
            )

        if feature_type == "Text":

            x, y = self.world_to_screen(
                geometry["x"],
                geometry["y"],
            )

            return self._svg_text(
                x,
                y,
                feature.get("text", ""),
                size=style.get(
                    "size",
                    14,
                ),
                anchor=style.get(
                    "anchor",
                    "start",
                ),
                color=style.get(
                    "color",
                    "#111827",
                ),
            )

        if feature_type == "HeatPoint":

            x, y = self.world_to_screen(
                geometry["x"],
                geometry["y"],
            )

            normalized = float(
                feature.get(
                    "normalized",
                    0,
                )
            )

            radius = float(
                feature.get(
                    "radius",
                    10,
                )
            )

            opacity = (
                0.15
                + normalized * 0.55
            )

            # Heatmap is represented as overlapping
            # translucent circles. The browser handles
            # the visual blending.

            return (
                f'<circle cx="{x:.2f}" '
                f'cy="{y:.2f}" '
                f'r="{radius}" '
                f'fill="#ef4444" '
                f'fill-opacity="{opacity:.3f}"/>'
            )

        if feature_type == "Contour":

            coordinates = geometry[
                "coordinates"
            ]

            if len(coordinates) < 2:
                return ""

            points = []

            for point in coordinates:

                sx, sy = self.world_to_screen(
                    point[0],
                    point[1],
                )

                points.append(
                    f"{sx:.2f},{sy:.2f}"
                )

            return (
                f'<polyline points="{" ".join(points)}" '
                f'fill="none" '
                f'stroke="{self._escape(style.get("color", "#7c3aed"))}" '
                f'stroke-width="{style.get("width", 1.5)}"/>'
            )

        if feature_type == "ScaleBar":

            x, y = self.world_to_screen(
                geometry["x"],
                geometry["y"],
            )

            x2, _ = self.world_to_screen(
                geometry["x"]
                + geometry["length"],
                geometry["y"],
            )

            units = feature.get(
                "units",
                "map units",
            )

            output = (
                f'<line x1="{x:.2f}" '
                f'y1="{y:.2f}" '
                f'x2="{x2:.2f}" '
                f'y2="{y:.2f}" '
                f'stroke="#111827" '
                f'stroke-width="4"/>'
            )

            output += self._svg_text(
                (x + x2) / 2,
                y - 8,
                f'{self._format_number(geometry["length"])} {units}',
                size=11,
                anchor="middle",
            )

            return output

        if feature_type == "NorthArrow":

            x, y = self.world_to_screen(
                geometry["x"],
                geometry["y"],
            )

            size = geometry["size"]

            points = [
                (x, y - size),
                (x - size * 0.35, y + size * 0.35),
                (x, y + size * 0.10),
                (x + size * 0.35, y + size * 0.35),
            ]

            polygon = " ".join(
                f"{px:.2f},{py:.2f}"
                for px, py in points
            )

            return (
                f'<polygon points="{polygon}" '
                f'fill="#111827"/>'
                + self._svg_text(
                    x,
                    y + size + 15,
                    "N",
                    size=14,
                    anchor="middle",
                )
            )

        return ""

    # ============================================================
    # GEOJSON
    # ============================================================

    def _to_geojson(self) -> Dict[str, Any]:

        features = []

        for layer in self.state["layers"]:

            for feature in layer["features"]:

                geometry = feature.get(
                    "geometry",
                    {},
                )

                feature_type = feature.get(
                    "type"
                )

                if feature_type == "Point":

                    geometry_out = {
                        "type": "Point",
                        "coordinates": [
                            geometry["x"],
                            geometry["y"],
                        ],
                    }

                elif feature_type == "LineString":

                    geometry_out = {
                        "type": "LineString",
                        "coordinates": geometry[
                            "coordinates"
                        ],
                    }

                elif feature_type == "Polygon":

                    coordinates = geometry[
                        "coordinates"
                    ]

                    ring = coordinates[:]

                    if ring[0] != ring[-1]:
                        ring.append(ring[0])

                    geometry_out = {
                        "type": "Polygon",
                        "coordinates": [ring],
                    }

                else:
                    continue

                properties = deepcopy(
                    feature.get(
                        "properties",
                        {},
                    )
                )

                properties[
                    "_map_layer"
                ] = layer["name"]

                features.append({
                    "type": "Feature",
                    "id": feature.get(
                        "id"
                    ),
                    "geometry": geometry_out,
                    "properties": properties,
                })

        return {
            "type": "FeatureCollection",
            "features": features,
        }

    # ============================================================
    # CONTOUR HELPERS
    # ============================================================

    def _marching_squares(
        self,
        xs: List[float],
        ys: List[float],
        grid: List[List[float]],
        level: float,
    ) -> List[List[List[float]]]:

        segments = []

        for j in range(len(ys) - 1):

            for i in range(len(xs) - 1):

                v00 = grid[j][i]
                v10 = grid[j][i + 1]
                v11 = grid[j + 1][i + 1]
                v01 = grid[j + 1][i]

                x0 = xs[i]
                x1 = xs[i + 1]

                y0 = ys[j]
                y1 = ys[j + 1]

                crossings = []

                if (
                    (v00 < level) !=
                    (v10 < level)
                ):
                    crossings.append(
                        self._interpolate_edge(
                            x0,
                            y0,
                            v00,
                            x1,
                            y0,
                            v10,
                            level,
                        )
                    )

                if (
                    (v10 < level) !=
                    (v11 < level)
                ):
                    crossings.append(
                        self._interpolate_edge(
                            x1,
                            y0,
                            v10,
                            x1,
                            y1,
                            v11,
                            level,
                        )
                    )

                if (
                    (v11 < level) !=
                    (v01 < level)
                ):
                    crossings.append(
                        self._interpolate_edge(
                            x1,
                            y1,
                            v11,
                            x0,
                            y1,
                            v01,
                            level,
                        )
                    )

                if (
                    (v01 < level) !=
                    (v00 < level)
                ):
                    crossings.append(
                        self._interpolate_edge(
                            x0,
                            y1,
                            v01,
                            x0,
                            y0,
                            v00,
                            level,
                        )
                    )

                if len(crossings) == 2:
                    segments.append(
                        crossings
                    )

                elif len(crossings) == 4:
                    segments.append(
                        [
                            crossings[0],
                            crossings[1],
                        ]
                    )

                    segments.append(
                        [
                            crossings[2],
                            crossings[3],
                        ]
                    )

        return segments

    def _interpolate_edge(
        self,
        x1: float,
        y1: float,
        v1: float,
        x2: float,
        y2: float,
        v2: float,
        level: float,
    ) -> List[float]:

        if abs(v2 - v1) < 1e-12:
            ratio = 0.5
        else:
            ratio = (
                level - v1
            ) / (
                v2 - v1
            )

        ratio = max(
            0.0,
            min(1.0, ratio),
        )

        return [
            x1 + ratio * (x2 - x1),
            y1 + ratio * (y2 - y1),
        ]

    # ============================================================
    # GENERAL HELPERS
    # ============================================================

    def _data_bounds(
        self,
        points: List[Dict[str, float]],
    ) -> Dict[str, float]:

        xs = [
            float(p["x"])
            for p in points
        ]

        ys = [
            float(p["y"])
            for p in points
        ]

        return {
            "xmin": min(xs),
            "xmax": max(xs),
            "ymin": min(ys),
            "ymax": max(ys),
        }

    def _linspace(
        self,
        start: float,
        stop: float,
        count: int,
    ) -> List[float]:

        if count <= 1:
            return [start]

        step = (
            stop - start
        ) / (
            count - 1
        )

        return [
            start + i * step
            for i in range(count)
        ]

    @staticmethod
    def _format_number(
        value: float,
    ) -> str:

        if abs(value - round(value)) < 1e-9:
            return str(int(round(value)))

        return f"{value:.4f}".rstrip(
            "0"
        ).rstrip(".")

    @staticmethod
    def _escape(
        value: Any,
    ) -> str:

        text = str(value)

        return (
            text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )

    def _svg_text(
        self,
        x: float,
        y: float,
        text: str,
        size: float = 14,
        anchor: str = "start",
        color: str = "#111827",
    ) -> str:

        return (
            f'<text x="{x:.2f}" '
            f'y="{y:.2f}" '
            f'font-family="Arial, sans-serif" '
            f'font-size="{size}" '
            f'fill="{self._escape(color)}" '
            f'text-anchor="{self._escape(anchor)}">'
            f'{self._escape(text)}'
            f'</text>'
        )
