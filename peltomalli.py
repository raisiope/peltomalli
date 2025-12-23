# main.py
import os
import json
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (import käytössä sivuvaikutuksena)

from cli import parse_args
from wfs_peruslohko import hae_peruslohko_polygon
from raster_height import kerää_korkeuspisteet
from mesh import luo_suodatettu_mcp_json, enrich_mesh
from geojson_outputs import (
    kirjoita_flow_viivat,
    kirjoita_virtausverkko,
    kirjoita_kertyminen,
)

def nayta_3d_pinta(mcp_data):
    pts = np.array(mcp_data["pisteet"])
    triangles = np.array(mcp_data["kolmiot"])

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")

    ax.plot_trisurf(
        pts[:, 0],
        pts[:, 1],
        pts[:, 2],
        triangles=triangles,
        cmap="terrain",
        edgecolor="gray",
        alpha=0.8,
    )
    ax.set_box_aspect((1, 1, 0.2))
    plt.title("Peltolohkon tasoitettu kolmioverkko")
    plt.show()

def main():
    args = parse_args()

    PL = args.peruslohko
    tif_tiedosto = "MML/" + args.tiedosto
    visual_3d = (args.visualisointi == "3d")

    # Luo peruslohkon hakemisto, jos sitä ei ole
    if not os.path.exists("PL"):
        os.makedirs("PL")
    if not os.path.exists("PL/"+PL):
        os.makedirs("PL/"+PL)

    print("Peruslohko:", PL)
    print("Tiedosto:", tif_tiedosto)
    mcp_polku = f"PL/{PL}/peltomalli_mcp.json"

    # Jos MCP-data on jo olemassa, lue se ja ohita raskas laskenta
    if os.path.exists(mcp_polku):
        print("peltomalli_mcp.json löytyi — ohitetaan MCP-datan rakentaminen.")
        with open(mcp_polku, "r", encoding="utf-8") as f:
            mcp_data = json.load(f)

    else:
        print("peltomalli_mcp.json ei löytynyt — rakennetaan MCP-data...")

        # 1) Hae peruslohkon polygon
        polygon = hae_peruslohko_polygon(PL)

        # 2) Kerää korkeuspisteet rasterista
        pisteet = kerää_korkeuspisteet(polygon, tif_tiedosto, ruutu=10, etaisyys_m=5.0)

        # 3) Kolmioverkko (MCP-tyylinen JSON)
        mcp_data = luo_suodatettu_mcp_json(pisteet, max_sivu=15.0)

        # 4) Tallenna MCP-data
        with open(mcp_polku, "w", encoding="utf-8") as f:
            json.dump(mcp_data, f, indent=2)

        print(f"Valmis! {mcp_polku}")

    # 5) Rikastettu verkko (pisteet + kolmiot + naapurit + korkeudet)
    verkko_polku = f"PL/{PL}/peltomalli_verkko.json"

    # Jos verkko on jo olemassa, lue se suoraan
    if os.path.exists(verkko_polku):
        print("peltomalli_verkko.json löytyi — ei lasketa uudelleen.")
        with open(verkko_polku, "r", encoding="utf-8") as f:
            enriched = json.load(f)

    else:
        print("peltomalli_verkko.json ei löytynyt — lasketaan verkko...")
        enriched = enrich_mesh(mcp_data)

        with open(verkko_polku, "w", encoding="utf-8") as f:
            json.dump(enriched, f, indent=2)
        print(f"Valmis! {verkko_polku}")

    # 6) GeoJSON-tasot
    OUTPUT_VIIVAT_GEOJSON = f"PL/{PL}/peltomalli_viivat.geojson"
    OUTPUT_VIRTAUS_GEOJSON = f"PL/{PL}/peltomalli_virtaus.geojson"
    OUTPUT_KERTYMINEN_GEOJSON = f"PL/{PL}/peltomalli_kertyminen.geojson"

    kirjoita_flow_viivat(enriched, OUTPUT_VIIVAT_GEOJSON)
    kirjoita_virtausverkko(enriched, OUTPUT_VIRTAUS_GEOJSON)
    kirjoita_kertyminen(enriched, OUTPUT_KERTYMINEN_GEOJSON)

    # 7) 3D-visuaali tarvittaessa
    if visual_3d:
        nayta_3d_pinta(mcp_data)

if __name__ == "__main__":
    main()
