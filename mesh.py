# mesh.py
import numpy as np
from scipy.spatial import Delaunay
from collections import defaultdict

# ---------- Kolmioverkon luonti ----------

def laske_sivun_pituus(p1, p2):
    return float(np.sqrt(np.sum((p1 - p2) ** 2)))

def luo_suodatettu_kolmio_json(pisteet_xyz, max_sivu=15.0):
    """
    Luo Delaunay-kolmioverkon, suodattaa liian pitkät sivut,
    palauttaa kolmio-tyylisen dictin: metadata + pisteet + kolmiot.
    """
    pisteet_np = np.array(pisteet_xyz)
    if len(pisteet_np) < 3:
        return {"error": "Liian vähän pisteitä kolmiointiin"}

    tri = Delaunay(pisteet_np[:, :2])

    hyvaksytyt_kolmiot = []
    for simplex in tri.simplices:
        p1 = pisteet_np[simplex[0], :2]
        p2 = pisteet_np[simplex[1], :2]
        p3 = pisteet_np[simplex[2], :2]

        sivut = [
            laske_sivun_pituus(p1, p2),
            laske_sivun_pituus(p2, p3),
            laske_sivun_pituus(p3, p1),
        ]

        if max(sivut) <= max_sivu:
            hyvaksytyt_kolmiot.append(simplex.tolist())

    kolmio_data = {
        "metadata": {
            "pisteiden_maara": len(pisteet_np),
            "alkuperaiset_kolmiot": len(tri.simplices),
            "suodatetut_kolmiot": len(hyvaksytyt_kolmiot),
            "max_sallittu_sivu_m": max_sivu,
            "koordinaattijarjestelma": "EPSG:3067",
            "suositeltu_pystyskaala": 0.2,
        },
        "pisteet": pisteet_np.tolist(),
        "kolmiot": hyvaksytyt_kolmiot,
    }
    return kolmio_data

# ---------- Rikastus: korkeudet, naapurit ----------

def compute_triangle_height(points, triangle):
    z_values = [points[i][2] for i in triangle]
    return sum(z_values) / len(z_values)

def find_neighbors(triangles):
    """
    triangle_index -> [neighbor_indices], jos on 2 yhteistä verteksiä.
    """
    neighbors = defaultdict(list)
    tri_sets = {i: set(tri) for i, tri in enumerate(triangles)}

    for i in tri_sets:
        for j in tri_sets:
            if i == j:
                continue
            if len(tri_sets[i].intersection(tri_sets[j])) == 2:
                neighbors[i].append(j)

    return neighbors

def enrich_mesh(data):
    points = data["pisteet"]
    triangles = data["kolmiot"]

    enriched = {
        "metadata": data.get("metadata", {}),
        "points": {},
        "triangles": {}
    }

    for idx, p in enumerate(points):
        enriched["points"][f"p{idx}"] = p

    for idx, tri in enumerate(triangles):
        height = compute_triangle_height(points, tri)
        enriched["triangles"][f"t{idx}"] = {
            "vertices": [f"p{tri[0]}", f"p{tri[1]}", f"p{tri[2]}"],
            "height": height,
            "neighbors": []
        }

    neighbor_map = find_neighbors(triangles)
    for idx, neighs in neighbor_map.items():
        enriched["triangles"][f"t{idx}"]["neighbors"] = [f"t{n}" for n in neighs]

    return enriched

# ---------- Virtauslogiikka ----------

def centroid_of_triangle(vertices, points):
    xs = []
    ys = []
    for pid in vertices:
        x, y, _z = points[pid]
        xs.append(x)
        ys.append(y)
    return sum(xs) / 3.0, sum(ys) / 3.0

def find_next_downhill_neighbor(triangle_id, triangles):
    current_h = triangles[triangle_id]["height"]
    neighs = triangles[triangle_id].get("neighbors", [])

    downhill = [n for n in neighs if triangles[n]["height"] <= current_h]
    if not downhill:
        return None

    return min(downhill, key=lambda n: triangles[n]["height"])

def find_flow_path(triangle_id, triangles):
    visited = set()
    stack = [(triangle_id, [triangle_id])]

    while stack:
        current, path = stack.pop()
        if current in visited:
            continue
        visited.add(current)

        neighs = triangles[current].get("neighbors", [])
        height = triangles[current]["height"]

        if len(neighs) < 3:
            return path

        downhill = [n for n in neighs if triangles[n]["height"] <= height]
        if not downhill:
            return None

        next_tid = min(downhill, key=lambda n: triangles[n]["height"])
        stack.append((next_tid, path + [next_tid]))

    return None

# ---------- Kertyminen ----------

def compute_flow_accumulation(triangles):
    heights = {tid: tdata["height"] for tid, tdata in triangles.items()}
    sorted_tids = sorted(triangles.keys(), key=lambda t: heights[t], reverse=True)

    acc = {tid: 1.0 for tid in triangles.keys()}

    for tid in sorted_tids:
        h = heights[tid]
        neighs = triangles[tid].get("neighbors", [])

        downhill = [n for n in neighs if heights[n] <= h]
        if not downhill:
            continue

        share = acc[tid] / len(downhill)
        for n in downhill:
            acc[n] += share

    return acc
