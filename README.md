# 🌾 Peltomalli – Peruslohkon korkeusmalli, kolmioverkko ja virtauslaskenta

Peltomalli on Python‑pohjainen työkalu, joka rakentaa peruslohkon sisäisen **korkeusmallin**, muodostaa siitä **kolmioverkon**, laskee **virtaussuunnat, virtauspolut ja kertyminen‑arvot**, ja tuottaa tulokset **GeoJSON‑tiedostoina** QGIS‑visualisointia varten.

### Ohjelma hyödyntää:

- Ruokaviraston **INSPIRE WFS** ‑rajapintaa peruslohkon geometrian hakemiseen

- Maanmittauslaitoksen tai muun lähteen **DTM/DEM‑rasteria** korkeustietojen lukemiseen

- **Delaunay‑triangulaatiota** kolmioverkon muodostamiseen

- Hydrologista logiikkaa virtausreittien ja kertymän laskentaan

- **GeoJSON‑tiedostoja**, jotka avautuvat suoraan QGIS:iin (EPSG:3067)

Kaikki tulokset tallennetaan automaattisesti **peruslohkon omaan hakemistoon**, esim:

```bash
9750925303/
    peltomalli_kolmio.json
    peltomalli_verkko.json
    peltomalli_viivat.geojson
    peltomalli_virtaus.geojson
    peltomalli_kertyminen.geojson
```

# 📐 Toimintaperiaate
Peltomallin laskenta etenee seuraavien vaiheiden kautta:

## 1. Peruslohkon geometrian haku (WFS)
Ohjelma hakee Ruokaviraston INSPIRE‑rajapinnasta peruslohkon polygonin:

- EPSG:3067

- Tarkka lohkon rajaus

- Käytetään CQL‑suodatinta: ``` PERUSLOHKOTUNNUS='...' ```

## 2. Korkeuspisteiden keruu rasterista
Peruslohkon sisälle muodostetaan **10 m x 10 m ruudukko:**

- Jokaisen ruudun keskelle luodaan 10×10 m neliö (aari)

- Jos neliö on kokonaan lohkon sisällä → se hyväksytään

- Rasterista luetaan korkeusarvot 5 m säteellä

- Tallennetaan pisteet muodossa:
**(x, y, z_mean)**

## 3. Kolmioverkon muodostus
Pisteistä muodostetaan Delaunay‑triangulaatio, jonka jälkeen:

- Liian pitkät sivut (yli 15 m) suodatetaan pois

- Jokaiselle kolmiolle lasketaan **keskikorkeus**

- Kolmioille etsitään **naapurit** (2 yhteistä pistettä)

Tuloksena syntyy **Kolmioverkko JSON**, jota käytetään jatkolaskennassa.

## 4. Virtauslogiikka
Jokaiselle kolmiolle:

- Lasketaan centroidi

- Etsitään naapurikolmiot, joiden korkeus ≤ oma korkeus

- Valitaan matalin → **virtaussuunta**

- Jos ei löydy alempaa → kolmio on **notko**

- Jos kolmio on reunassa → **ulosvirtaus**

## 5. Virtauspolut
Virtauspolku rakennetaan seuraavasti:

- Aloita kolmiosta tX

- Kulje aina matalimpaan naapuriin

- Pysähdy, jos:

    - saavut reunaan → ulosvirtaus

    - ei ole alempia naapureita → notko

## 6. Kertyminen (flow accumulation)
Hydrologinen kertymä lasketaan:

- Jokainen kolmio aloittaa arvolla 1

- Virta jaetaan tasan kaikkiin alempiin naapureihin

- Käsittelyjärjestys: korkeimmasta matalimpaan

Tuloksena syntyy **acc‑arvo**, joka kertoo veden kertymisen määrän.

## 7. GeoJSON‑tiedostot
Ohjelma tuottaa kolme karttatasoa:

### 🔹 peltomalli_viivat.geojson
Centroidista seuraavaan alempaan kolmioon kulkevat virtausviivat.

### 🔹 peltomalli_virtaus.geojson

Sisältää:

- Kolmiot (Polygon)

- Virtauspolut

- Notkot

- Ensimmäisen askeleen virtausviivat

### 🔹 peltomalli_kertyminen.geojson

Kolmiot, joissa attribuuttina:

- height

- acc (kertyminen)

- neighbor_count

Kaikki tiedostot sisältävät CRS‑tiedon:

```json
"crs": {
  "type": "name",
  "properties": { "name": "EPSG:3067" }
}
```
# 🚀 Käyttöohje
## 1. Asenna riippuvuudet

```bash
pip install requests numpy scipy rasterio geopandas shapely matplotlib
```

## 2. Aja ohjelma
### Peruskäyttö:
```bash
python peltomalli.py
```

### Käyttää oletuksia:

- peruslohko: 9750925303

- maastomalli: P3343B.tif

- visualisointi: qgis

### Määritä peruslohko ja rasteri:
```bash
python peltomalli.py qgis 9750088877 P3343B.tif
```
### Näytä 3D‑pinta:
```bash
python peltomalli.py 3d 9750088877 P3343B.tif
```
# ⚡ Optimoinnit
Ohjelma ei laske raskaita vaiheita uudelleen, jos tulokset löytyvät hakemistosta:

## ✔ Kolmio‑data (peltomalli_kolmio.json)
Jos tiedosto on olemassa:

- Ei WFS‑hakua

- Ei rasterin läpikäyntiä

- Ei triangulaatiota

## ✔ Kolmioverkko (peltomalli_verkko.json)
Jos tiedosto on olemassa:

- Ei naapureiden laskentaa

- Ei korkeuksien laskentaa

- Ei virtauspolkujen laskentaa

## ✔ GeoJSON‑tiedostot tehdään aina uudelleen
Koska ne ovat kevyitä ja riippuvat vain verkon rakenteesta.

# 📂 Hakemistorakenne
```bash
peltomalli/
│
├── peltomalli.py
├── cli.py
├── wfs_peruslohko.py
├── raster_height.py
├── mesh.py
├── geojson_outputs.py
├── kuvat/
│   ├── 3d.png
│   ├── virtaus.png
│   └── kertyminen.png
├── MML/
│   └── P3343B.tif
└── PL/
    └── 9750925303/
        ├── peltomalli_kolmio.json
        ├── peltomalli_verkko.json
        ├── peltomalli_viivat.geojson
        ├── peltomalli_virtaus.geojson
        ├── peltomalli_kertyminen.geojson
```

# 🧭 QGIS‑käyttö
1. Avaa QGIS

2. Vedä GeoJSON‑tiedostot hakemistosta PL/

3. Aseta symbologia:

    - **Virtausviivat** → sininen viiva

    - **Kolmiot** → läpinäkyvä täyttö + musta reunaviiva

    - **Kertyminen** → graduated color (viridis)

4. Voit yhdistää tasot overlay‑työkaluilla

# 🧩 Yhteenveto
### Peltomalli tarjoaa:

- Tarkan peruslohkon sisäisen korkeusmallin

- Hydrologisesti järkevän kolmioverkon

- Virtausreittien ja notkojen tunnistuksen

- Kertymäanalyysin

- QGIS‑yhteensopivat karttatasot

- Automaattisen optimoinnin ja välimuistin

### Se on suunniteltu erityisesti:

- peltotöiden suunnitteluun

- kuivatusanalyysiin

- notkojen tunnistamiseen

- maanmuokkauksen optimointiin

- hydrologiseen mallinnukseen


# 🖼️ Esimerkki kuvat
### 🧊 Esimerkki: Peltomallin 3D

![Esimerkki: Peltomallin 3D](https://github.com/raisiope/peltomalli/blob/main/kuvat/3d.png "Peltomallin 3D")

### 📐 Esimerkki: Peltomallin pintavalunta


![Esimerkki: Peltomallin pintavalunta](https://github.com/raisiope/peltomalli/blob/main/kuvat/virtaus.png "Peltomallin pintavalunta")

### 🌧️ Esimerkki: Peltomallin veden kertyminen pintavalunnasta

![Esimerkki: Peltomallin veden kertyminen pintavalunnasta ](https://github.com/raisiope/peltomalli/blob/main/kuvat/kertyminen.png "Peltomallin veden kertyminen pintavalunnasta")
