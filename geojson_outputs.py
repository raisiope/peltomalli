# geojson_outputs.py
import json
from mesh import centroid_of_triangle, find_next_downhill_neighbor, find_flow_path, compute_flow_accumulation

def _base_fc(crs_epsg="EPSG:3067"):
    return {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {
                "name": crs_epsg
            }
        },
        "features": []
    }

def kirjoita_flow_viivat(enriched, output_path, crs_epsg="EPSG:3067"):
    points = enriched["points"]
    triangles = enriched["triangles"]

    fc = _base_fc(crs_epsg)

    for tid, tdata in triangles.items():
        next_tid = find_next_downhill_neighbor(tid, triangles)
        if next_tid is None:
            continue

        cx1, cy1 = centroid_of_triangle(tdata["vertices"], points)
        cx2, cy2 = centroid_of_triangle(triangles[next_tid]["vertices"], points)

        feature = {
            "type": "Feature",
            "properties": {
                "from": tid,
                "to": next_tid,
                "height_from": tdata["height"],
                "height_to": triangles[next_tid]["height"]
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [cx1, cy1],
                    [cx2, cy2]
                ]
            }
        }
        fc["features"].append(feature)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(fc, f, indent=2)

    print(f"Valmis! Virtausviivat: {output_path}")

def kirjoita_virtausverkko(enriched, output_path, crs_epsg="EPSG:3067"):
    points = enriched["points"]
    triangles = enriched["triangles"]

    fc = _base_fc(crs_epsg)

    # Kolmiot + sink / flow_path
    for tid, tdata in triangles.items():
        coords = []
        for pid in tdata["vertices"]:
            x, y, _z = points[pid]
            coords.append([x, y])
        coords.append(coords[0])

        path = find_flow_path(tid, triangles)
        sink = 1 if path is None else 0
        flow_path_str = "" if path is None else "->".join(path)

        feature = {
            "type": "Feature",
            "properties": {
                "layer": "triangles",
                "id": tid,
                "height": tdata["height"],
                "sink": sink,
                "flow_path": flow_path_str,
                "neighbor_count": len(tdata.get("neighbors", []))
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [coords]
            }
        }
        fc["features"].append(feature)

    # Flow-lines (ensimmäinen askel)
    for tid, tdata in triangles.items():
        path = find_flow_path(tid, triangles)
        if path is None or len(path) < 2:
            continue

        next_tid = path[1]

        cx1, cy1 = centroid_of_triangle(tdata["vertices"], points)
        cx2, cy2 = centroid_of_triangle(triangles[next_tid]["vertices"], points)

        feature = {
            "type": "Feature",
            "properties": {
                "layer": "flow_lines",
                "from": tid,
                "to": next_tid,
                "full_path": "->".join(path),
                "height_from": tdata["height"],
                "height_to": triangles[next_tid]["height"]
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [cx1, cy1],
                    [cx2, cy2]
                ]
            }
        }
        fc["features"].append(feature)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(fc, f, indent=2)

    print(f"Valmis! Virtausverkko: {output_path}")

def kirjoita_kertyminen(enriched, output_path, crs_epsg="EPSG:3067"):
    points = enriched["points"]
    triangles = enriched["triangles"]

    acc = compute_flow_accumulation(triangles)

    fc = _base_fc(crs_epsg)

    for tid, tdata in triangles.items():
        coords = []
        for pid in tdata["vertices"]:
            x, y, _z = points[pid]
            coords.append([x, y])
        coords.append(coords[0])

        feature = {
            "type": "Feature",
            "properties": {
                "id": tid,
                "height": tdata["height"],
                "acc": acc[tid],
                "neighbor_count": len(tdata.get("neighbors", []))
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [coords]
            }
        }
        fc["features"].append(feature)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(fc, f, indent=2)

    print(f"Valmis! Kertyminen: {output_path}")
