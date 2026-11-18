#!/usr/bin/env python3
"""
OpenStreetMap（Overpass API）から、地図の背景に使う道・線路・川・池・公園・森を取って data/osm/ に保存する（Googleには接続しない）。
データ: © OpenStreetMap contributors（ODbL）。
使い方: python3 fetch_osm_area.py demachiyanagi
"""
import os, subprocess, sys, time, urllib.parse

AREAS = {
    # 名前: (南, 西, 北, 東)
    "demachiyanagi": (35.000, 135.740, 35.060, 135.805),
}
QUERIES = {
    "roads": '(way["highway"~"^(primary|secondary|tertiary|unclassified|residential|living_street|pedestrian|service|footway|path)$"]({b});way["railway"~"^(rail|light_rail|subway|tram|narrow_gauge)$"]({b}););',
    "water": '(way["waterway"~"^(river|stream|canal)$"]({b});way["natural"="water"]({b});way["waterway"="riverbank"]({b});relation["natural"="water"]({b});relation["waterway"="riverbank"]({b}););',
    "green": '(way["leisure"~"^(park|garden)$"]({b});way["landuse"~"^(forest|grass|meadow)$"]({b});way["natural"="wood"]({b}););',
}

def main():
    area = sys.argv[1]
    s, w, n, e = AREAS[area]
    b = f"{s},{w},{n},{e}"
    for name, q in QUERIES.items():
        ql = f"[out:json][timeout:90];{q.format(b=b)}out geom;"
        url = "https://overpass-api.de/api/interpreter?data=" + urllib.parse.quote(ql)
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "osm", f"{area}_{name}.json")
        # このMacの標準Pythonは、Overpassとの暗号通信に失敗するため、curlで取る
        subprocess.run(["curl", "-s", "--max-time", "150", "-A", "honya-sanpo-osm/1.0 (https://github.com/mina-7890/honya-sanpo-osm)", "-o", path, url], check=True)
        import os
        data = open(path, "rb").read()
        print(name, len(data) // 1024, "KB ->", path)
        time.sleep(3)

if __name__ == "__main__":
    main()
