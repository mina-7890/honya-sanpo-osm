#!/usr/bin/env python3
"""
OpenStreetMap（Overpass API）から、地図の背景に使う道・線路・川・池・公園・森を取って data/osm/ に保存する（Googleのデータは使わない）。
データ: © OpenStreetMap contributors（ODbL）。
使い方: python3 fetch_osm_area.py demachiyanagi
"""
import os, subprocess, sys, time, urllib.parse

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "osm")
AREAS = {
    # 名前: (南, 西, 北, 東)
    "demachiyanagi": (35.000, 135.740, 35.060, 135.805),
    "kichijoji": (35.675, 139.535, 35.728, 139.622),
    "kitahama": (34.668, 135.480, 34.712, 135.533),
}
QUERIES = {
    "roads": '(way["highway"~"^(primary|secondary|tertiary|unclassified|residential|living_street|pedestrian|service|footway|path)$"]({b});way["railway"~"^(rail|light_rail|subway|tram|narrow_gauge)$"]({b}););',
    "water": '(way["waterway"~"^(river|stream|canal)$"]({b});way["natural"="water"]({b});way["waterway"="riverbank"]({b});relation["natural"="water"]({b});relation["waterway"="riverbank"]({b}););',
    "green": '(way["leisure"~"^(park|garden)$"]({b});way["landuse"~"^(forest|grass|meadow)$"]({b});way["natural"="wood"]({b}););',
    # 大きな公園・森は、複数の線をまとめた形（relation）で登録されていることが多い。green では拾えないぶんを足す
    "green2": '(relation["leisure"~"^(park|garden|nature_reserve)$"]({b});relation["landuse"~"^(forest|grass|meadow|recreation_ground)$"]({b});relation["natural"="wood"]({b});way["leisure"="nature_reserve"]({b});way["landuse"="recreation_ground"]({b}););',
}

GRID = {"kichijoji": (3, 4), "kitahama": (3, 3)}  # 密集した街は、範囲を(行, 列)に分けて取り、あとで合わせる
ENDPOINTS = ["https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter"]


def fetch(ql, path):
    """タイルごとに保存し、取れていればそれを使う（やり直しに強くする）。混んでいたら、待って再試行（倍々で長く）"""
    import json
    if os.path.exists(path):
        try:
            return json.load(open(path))["elements"]
        except Exception:
            pass
    wait = 20
    for k in range(8):
        base = ENDPOINTS[k % len(ENDPOINTS)]
        url = base + "?data=" + urllib.parse.quote(ql)
        # このMacの標準Pythonは、Overpassとの暗号通信に失敗するため、curlで取る
        subprocess.run(["curl", "-s", "--max-time", "170", "-A", "honya-sanpo-research/0.1", "-o", path + ".tmp", url])
        try:
            els = json.load(open(path + ".tmp"))["elements"]
            os.replace(path + ".tmp", path)
            return els
        except Exception:
            time.sleep(wait)
            wait = min(wait * 2, 240)
    raise SystemExit(f"取得に失敗: {path}")


def main():
    import json
    area = sys.argv[1]
    s, w, n, e = AREAS[area]
    rows, cols = GRID.get(area, (1, 1))
    only = sys.argv[2:]
    for name, q in QUERIES.items():
        if only and name not in only:
            continue
        els = {}
        for i in range(rows):
            for j in range(cols):
                bs = s + (n - s) * i / rows
                bn = s + (n - s) * (i + 1) / rows
                bw = w + (e - w) * j / cols
                be = w + (e - w) * (j + 1) / cols
                b = f"{bs},{bw},{bn},{be}"
                ql = f"[out:json][timeout:150];{q.format(b=b)}out geom;"
                path = f"{OUT}/{area}_{name}_p{i}{j}.json"
                for el in fetch(ql, path):
                    els[(el["type"], el["id"])] = el
                print(name, i, j, len(els), flush=True)
                time.sleep(2)
        out = f"{OUT}/{area}_{name}.json"
        json.dump({"elements": list(els.values())}, open(out, "w"))
        print(name, len(els), "件 ->", out, flush=True)


if __name__ == "__main__":
    main()
