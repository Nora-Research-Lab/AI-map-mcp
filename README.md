---
pretty_name: AI Map MCP — AI-Native Mapping & Visualization Server
tags:
  - mcp
  - ai
  - mapping
  - geospatial
  - gis
  - data-visualization
  - scientific-visualization
  - geoparquet
  - geojson
  - csv
  - earth-science
  - geology
task_categories:
  - other
---

<p align="center">
  <img src="https://i.ibb.co/Z3620QZ/file-00000000c2a481f485814b770bb35399.png" width="100%" alt="NORA AI Map MCP banner">
</p>

<p align="center">
  <a href="https://github.com/Nora-Research-Lab"><img src="https://img.shields.io/badge/GitHub-Nora--Research--Lab-181717?logo=github" alt="GitHub"></a>
  <a href="https://huggingface.co/NoraResearchLab"><img src="https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-NoraResearchLab-yellow" alt="Hugging Face"></a>
  <a href="https://www.linkedin.com/company/nora-research-lab"><img src="https://img.shields.io/badge/LinkedIn-NORA%20Research%20Lab-0A66C2?logo=linkedin" alt="LinkedIn"></a>
  <a href="https://x.com/noraresearchlab"><img src="https://img.shields.io/badge/X-@noraresearchlab-000000?logo=x" alt="X"></a>
</p>

## Quick Links

- [GitHub](https://github.com/Nora-Research-Lab)
- [Hugging Face](https://huggingface.co/NoraResearchLab)
- [LinkedIn](https://www.linkedin.com/company/nora-research-lab)
- [X](https://x.com/noraresearchlab)
- [MCP Server](https://ai-map-mcp.onrender.com/mcp)

# AI Map MCP

An AI-native mapping and scientific visualization MCP server that gives
AI systems the ability to create, modify, and export maps using natural
language and structured data.

AI Map MCP provides an interactive computational canvas for AI systems,
allowing models to transform datasets and spatial instructions into
structured maps and visualizations.

Instead of an AI only describing a map, AI Map MCP gives it tools to
actually construct one.

## What It Does

AI Map MCP allows compatible AI systems to work with maps as a
programmable visual environment.

An AI can:

- Create coordinate-based maps
- Plot datasets as points
- Draw lines and paths
- Create polygons
- Generate Cartesian grids
- Add annotations and labels
- Create heatmaps
- Generate contour visualizations
- Add scale bars
- Add north arrows
- Change map views
- Fit maps automatically to available data
- Manage map layers
- Export maps as SVG
- Export spatial data as GeoJSON
- Export complete map state as JSON

This makes the server useful for scientific computing, GIS workflows,
geology, geophysics, environmental science, data analysis, and
general-purpose AI visualization.

## MCP Endpoint

The remote MCP server is available at:

```
https://ai-map-mcp.onrender.com/mcp
```

Compatible MCP clients can connect to this endpoint and allow their AI
models to discover and use the mapping tools.

For example, an AI could receive a dataset containing:

```text
latitude,longitude,gold_grade
7.52,4.61,2.4
7.55,4.67,5.8
7.61,4.72,12.3
7.68,4.81,1.7
```

and be instructed:

> Plot the gold occurrences and create a heatmap based on gold grade.

The AI can then use the available mapping tools to construct the visualization.

## Data Visualization

AI Map MCP is designed to work with structured scientific data.

Typical data fields include:

| Data | Example |
|---|---|
| Latitude | 7.6123 |
| Longitude | 4.7211 |
| X | 4500 |
| Y | 7200 |
| Elevation | 312.5 |
| Gold grade | 8.42 |
| Magnetic anomaly | 125.6 |
| Gravity anomaly | -34.2 |
| Category | Prospect |
| Location | Site A |

The AI can determine how these variables should be represented depending on the requested visualization.

## Map Layers

Maps are organized into independent layers.

Example:

```
AI Map
│
├── Grid
├── Gold Occurrences
├── Faults
├── Geological Units
├── Elevation Contours
├── Gold Grade Heatmap
└── Annotations
```

Each layer can be independently managed, displayed, hidden, or removed.

This allows AI systems to progressively construct complex scientific maps rather than generating a single static image.

## Coordinate Systems

The mapping engine supports coordinate-based visualization using:

- Cartesian coordinates
- Longitude / latitude coordinates
- WGS84-style geographic coordinates

The map maintains explicit spatial bounds and provides transformations between world coordinates and the rendered map canvas.

## Visualization Types

### Points

Useful for:

- Mineral occurrences
- Sample locations
- Earthquake epicenters
- Boreholes
- Monitoring stations
- Exploration targets

### Lines

Useful for:

- Faults
- Roads
- Rivers
- Geological contacts
- Transects
- Survey lines

### Polygons

Useful for:

- Geological units
- Mineral concessions
- Study areas
- Environmental zones
- Exploration blocks

### Heatmaps

Numeric attributes can be visualized spatially to reveal concentration or intensity patterns.

Examples include:

- Gold grade
- Temperature
- Magnetic intensity
- Gravity anomaly
- Pollution concentration

### Contours

The engine can generate contour-style isolines from scattered numeric observations.

Examples include:

- Elevation
- Gravity
- Magnetic intensity
- Geochemical concentration
- Other continuous spatial variables

## AI-Native Mapping

The main purpose of AI Map MCP is to make mapping an action an AI system can perform.

Instead of:

```
User → AI → "Here is how you could make the map..."
```

the workflow becomes:

```
User
  ↓
AI
  ↓
MCP tools
  ↓
AI Map
  ↓
Structured map
  ↓
SVG / GeoJSON / JSON
```

For example:

> Create a 100 × 100 map, add a grid every 10 units, plot these observations, make the points larger according to their values, and add a scale bar.

The AI can translate the instruction into a sequence of mapping operations.

## CSV Workflows

AI Map can be used together with a frontend interface to allow users to upload CSV datasets and visualize them.

A typical workflow is:

```
CSV
 ↓
Column detection
 ↓
Coordinate identification
 ↓
Value / category identification
 ↓
Map layer creation
 ↓
Visualization
 ↓
Export
```

A CSV containing:

```text
latitude,longitude,elevation
7.51,4.60,312
7.55,4.64,421
7.61,4.70,385
7.67,4.78,512
```

can be transformed into a spatial visualization using the detected coordinate and value fields.

## Scientific Applications

AI Map MCP can support workflows in:

- Geology
- Mineral exploration
- Geophysics
- Environmental geology
- Remote sensing
- Hydrology
- Earthquake analysis
- Geochemistry
- Spatial data science
- Scientific research
- Education

For example, geological data can be represented as:

```
Geological Units
       +
Faults
       +
Mineral Occurrences
       +
Geophysical Anomalies
       +
Geochemical Values
       ↓
Integrated Map
```

## Export Formats

### SVG

Vector map representation suitable for:

- Reports
- Presentations
- Web applications
- Scientific figures

### GeoJSON

Suitable for interoperability with:

- GIS software
- Web mapping applications
- Spatial analysis pipelines
- APIs

### JSON

Contains the complete structured map state, including:

- Map configuration
- Bounds
- Layers
- Features
- Properties
- Styling

## Architecture

```
AI Client
   │
   │ MCP
   ▼
AI Map MCP Server
   │
   ▼
app.py
   │
   ▼
Map Engine
   │
   ├── Points
   ├── Lines
   ├── Polygons
   ├── Grid
   ├── Heatmaps
   ├── Contours
   ├── Annotations
   └── Map Decorations
   │
   ▼
SVG / GeoJSON / JSON
```

The MCP interface is responsible for exposing mapping capabilities to AI systems, while the mapping engine handles the underlying spatial operations and rendering.

## Example AI Instructions

Once connected to an MCP-compatible AI client, users can issue instructions such as:

- Create a map with a 10-unit grid and plot these coordinates.
- Plot all sampling locations and label them using the sample_id field.
- Create a heatmap using the gold_grade column.
- Create contours from the elevation values.
- Draw the fault as a red line and place it above the geological units.
- Fit the map to all available data and add a north arrow and scale bar.
- Export the resulting map as GeoJSON.

## Project Structure

```
AI-Map-MCP/
│
├── app.py
├── map.py
├── requirements.txt
└── README.md
```

`app.py` provides the MCP server and exposes mapping capabilities to AI clients.

`map.py` contains the mapping and visualization engine.

`requirements.txt` contains the Python dependencies required to run the server.

## Deployment

The MCP server can be deployed as a web service.

Example start command:

```
uvicorn app:app --host 0.0.0.0 --port $PORT
```

The current remote MCP endpoint is:

```
https://ai-map-mcp.onrender.com/mcp
```

## Project Status

AI Map MCP is an active NORA Research Lab project focused on building an AI-native interface for spatial visualization and scientific mapping.

The long-term objective is to make maps a first-class tool for AI systems, allowing models to reason about spatial data and directly construct visual representations from datasets and natural-language instructions.

---

Developed by NORA Research Lab.

AI Map MCP is part of NORA Research Lab's broader work on AI, geological data infrastructure, scientific computing, and intelligent research systems.
