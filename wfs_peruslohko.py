# wfs_peruslohko.py
import requests
import geopandas as gpd
from io import BytesIO

WFS_URL = "https://inspire.ruokavirasto-awsa.com/geoserver/wfs"
LAYER_NAME = "inspire:LC.LandCoverSurfaces.LPIS.2024"

def hae_peruslohko_polygon(peruslohkotunnus: str):
    """
    Hakee peruslohkon polygonin Ruokaviraston INSPIRE WFS-rajapinnasta.
    Palauttaa Shapelyn Polygon-olion.
    """
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeName": LAYER_NAME,
        "outputFormat": "application/json",
        "CQL_FILTER": f"PERUSLOHKOTUNNUS='{peruslohkotunnus}'"
    }

    response = requests.get(WFS_URL, params=params)
    response.raise_for_status()

    gdf = gpd.read_file(BytesIO(response.content))

    if gdf.empty:
        raise ValueError(f"Peruslohkoa {peruslohkotunnus} ei löytynyt WFS-rajapinnasta.")

    geom = gdf.geometry.iloc[0]
    print(f"Hakutulos: {len(gdf)} kohdetta, CRS: {gdf.crs}")
    return geom
