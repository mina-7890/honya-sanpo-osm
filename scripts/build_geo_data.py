#!/usr/bin/env python3
"""
OpenStreetMap の海岸線・道・線路から、試作の地図の背景（Dart）を作る。
データ: © OpenStreetMap contributors（ODbL）。data/osm/ に保存した取得結果を使う（Googleには接続しない）。

使い方:  python3 build_geo_data.py
出力:    geo/onomichi_geo.dart
"""
import json, math

import os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
HERE = os.path.join(ROOT, "data", "osm")
OUT = os.path.join(ROOT, "geo", "onomichi_geo.dart")
LAT0, LNG0 = 34.4049, 133.1999
BOX = (34.390, 133.175, 34.420, 133.228)  # 道を残す範囲 (lat0, lng0, lat1, lng1)


def xy(lat, lng):
    """mapPosOf と同じ投影（km/5）"""
    return (0.5 + (lng - LNG0) * 111.32 * math.cos(LAT0 * math.pi / 180) / 5, 0.5 + (LAT0 - lat) * 111.32 / 5)


def dp(pts, eps):
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dmax, idx = 0, 0
    for i in range(1, len(pts) - 1):
        x0, y0 = pts[i]
        num = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1)
        den = math.hypot(y2 - y1, x2 - x1) or 1e-12
        d = num / den
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        return dp(pts[: idx + 1], eps)[:-1] + dp(pts[idx:], eps)
    return [pts[0], pts[-1]]


def flat(pts):
    return ",".join(f"{x:.4f},{y:.4f}" for x, y in pts)


chains = json.load(open(f"{HERE}/coast_chains.json"))
# 本土の海岸線（北側が陸）と、向島の海岸線（南側が陸）
main = next(c for c in chains if len(c) > 400)
island = next(c for c in chains if len(c) == 333)
MIN_LAT, MAX_LAT, MIN_LNG, MAX_LNG = 34.36, 34.44, 133.14, 133.26
main_poly = main + [(MAX_LAT, main[-1][1] + 0.02), (MAX_LAT, MIN_LNG), (main[0][0], MIN_LNG)]
island_poly = island + [(MIN_LAT, island[-1][1]), (MIN_LAT, island[0][1])]  # 始点と同じ点は足さない（簡略化で多角形がつぶれるため）
land = [dp([xy(*p) for p in main_poly], 0.0004), dp([xy(*p) for p in island_poly], 0.0004)]

roads_json = json.load(open(f"{HERE}/osm_roads.json"))
main_roads, small_roads, rails = [], [], []
for e in roads_json["elements"]:
    g = [(p["lat"], p["lon"]) for p in e["geometry"]]
    if not any(BOX[0] <= a <= BOX[2] and BOX[1] <= b <= BOX[3] for a, b in g):
        continue
    pts = dp([xy(a, b) for a, b in g], 0.0006)
    t = e.get("tags", {})
    if t.get("railway"):
        rails.append(pts)
    elif t.get("highway") in ("primary", "secondary", "tertiary"):
        main_roads.append(pts)
    else:
        small_roads.append(pts)

def emit(name, lines):
    s = f"const List<List<double>> {name} = [\n"
    for pts in lines:
        s += "  [" + flat(pts) + "],\n"
    return s + "];\n"

out = "// 自動生成（honya-sanpo-spots/build_geo_data.py）。手で直さない。\n"
out += "// 地図データ: © OpenStreetMap contributors（ODbL）。試作用。本番での使い方は、規約を確認してから決める。\n"
out += "// 座標は、yoridou_data.dart の mapPosOf と同じ投影（x,y を並べたもの）。\n\n"
out += emit("kGeoLand", land) + emit("kGeoMainRoads", main_roads) + emit("kGeoSmallRoads", small_roads) + emit("kGeoRails", rails)
open(OUT, "w", encoding="utf-8").write(out)
print(len(land), len(main_roads), len(small_roads), len(rails), len(out) // 1024, "KB")
