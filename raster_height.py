# raster_height.py
import numpy as np
import rasterio
from rasterio.windows import Window
from shapely.geometry import Polygon

def hae_korkeustiedot(tif_reitti, x, y, etaisyys_m=5):
    """
    Lukee rasterista korkeustiedot (mean, min, max) x,y -sijainnin ympäriltä.
    etaisyys_m = puskurisäde metreinä.
    """
    with rasterio.open(tif_reitti) as src:
        row, col = src.index(x, y)

        px_size = src.res[0]
        buffer_px = int(etaisyys_m / px_size)

        window = Window(
            col - buffer_px,
            row - buffer_px,
            buffer_px * 2 + 1,
            buffer_px * 2 + 1
        )

        data = src.read(1, window=window)
        valid = data[data != src.nodata]

        if valid.size == 0:
            return None, None, None

        mean = float(np.mean(valid))
        minv = float(np.min(valid))
        maxv = float(np.max(valid))

        return mean, minv, maxv

def luo_aarin_neliö(x, y, sade_m=5):
    """
    Luo 10x10 m neliön (aari) keskipisteen (x, y) ympärille.
    sade_m = 5 m keskipisteestä sivuille.
    """
    vasen = x - sade_m
    oikea = x + sade_m
    ala = y - sade_m
    yla = y + sade_m

    kulmat = [
        (vasen, yla),
        (oikea, yla),
        (oikea, ala),
        (vasen, ala),
        (vasen, yla)
    ]
    return Polygon(kulmat)

def kerää_korkeuspisteet(polygon, tif_tiedosto, ruutu=10, etaisyys_m=5.0):
    """
    Kerää pisteitä polygonin sisäpuolelta ruutu x ruutu -verkolla.
    Palauttaa listan (x, y, z_mean).
    """
    xmin, ymin, xmax, ymax = polygon.bounds

    import math
    xmin_r = math.floor(xmin / ruutu) * ruutu
    ymin_r = math.floor(ymin / ruutu) * ruutu
    xmax_r = math.ceil(xmax / ruutu) * ruutu
    ymax_r = math.ceil(ymax / ruutu) * ruutu

    print("Rounded bounds:")
    print("xmin:", xmin_r)
    print("ymin:", ymin_r)
    print("xmax:", xmax_r)
    print("ymax:", ymax_r)

    max_varianssi = 0.0
    pisteet = []

    i = xmin_r
    while i <= xmax_r:
        j = ymin_r
        while j <= ymax_r:
            aari = luo_aarin_neliö(i, j, sade_m=ruutu / 2)
            if aari.within(polygon):
                mean, minv, maxv = hae_korkeustiedot(tif_tiedosto, i, j, etaisyys_m=etaisyys_m)
                if mean is not None:
                    pisteet.append((i, j, mean))
                    if max_varianssi < (maxv - minv):
                        max_varianssi = maxv - minv
            j += ruutu
        i += ruutu

    print(f"Suurin korkeuden vaihtelu tarkastelluilla alueilla: {max_varianssi:.2f} m")
    if max_varianssi <= 0.5:
        print("  -> Alue on tasainen (vaihtelu <= 0.5 m).")

    return pisteet
