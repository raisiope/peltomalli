# cli.py
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Peruslohko + kolmioverkko -ohjelma")

    parser.add_argument(
        "visualisointi",
        nargs="?",
        default="qgis",
        help="3D-visualisointi: '3d' näyttää matplotlib-pinnan, muuten vain data (oletus: qgis)"
    )

    parser.add_argument(
        "peruslohko",
        nargs="?",
        default="9750925303",
        help="Peruslohkon tunnus (oletus: 9750925303)"
    )

    parser.add_argument(
        "tiedosto",
        nargs="?",
        default="P3343B.tif",
        help="DEM/DTM TIF -tiedoston nimi (oletus: P3343B.tif)"
    )

    return parser.parse_args()
