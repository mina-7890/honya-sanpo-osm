#!/usr/bin/env python3
"""
data/osm/<駅名>_*.json（fetch_osm_area.py で取得）から、内陸の駅（海のない街）の地図の背景（Dart）を作る。
データ: © OpenStreetMap contributors（ODbL）。Googleのデータは使わない。
使い方: python3 build_geo_area.py demachiyanagi
出力:   geo/<駅名>_geo.dart
"""
import json, math, os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
HERE = os.path.join(ROOT, "data", "osm")
APP = os.path.join(ROOT, "geo")
AREAS = {
    # 名前: (原点の緯度, 原点の経度, 残す範囲(南,西,北,東), Dartの定数名)
    "demachiyanagi": (35.0306702, 135.7731889, (35.008, 135.748, 35.052, 135.798), "kDemachiyanagiGeo"),
    "kitahama": (34.6915050, 135.5065821, (34.673, 135.485, 34.707, 135.528), "kKitahamaGeo"),
    "kichijoji": (35.7031389, 139.5802187, (35.679, 139.541, 35.724, 139.617), "kKichijojiGeo"),
}



def expand_relations(elements):
    """multipolygon の外周（outer）をつなぎ合わせ、閉じた形の way として追加する（内側の穴は無視）。"""
    out = []
    for e in elements:
        if e["type"] != "relation":
            out.append(e)
            continue
        segs = [[(p["lat"], p["lon"]) for p in m["geometry"]]
                for m in e.get("members", []) if m.get("role") == "outer" and m.get("geometry")]
        while segs:
            ring = segs.pop(0)
            grew = True
            while grew and ring[0] != ring[-1]:
                grew = False
                for i, sg in enumerate(segs):
                    if sg[0] == ring[-1]:
                        ring += sg[1:]
                    elif sg[-1] == ring[-1]:
                        ring += sg[::-1][1:]
                    elif sg[-1] == ring[0]:
                        ring = sg[:-1] + ring
                    elif sg[0] == ring[0]:
                        ring = sg[::-1][:-1] + ring
                    else:
                        continue
                    segs.pop(i)
                    grew = True
                    break
            if ring[0] == ring[-1] and len(ring) > 3:
                out.append({"type": "way", "tags": e.get("tags", {}),
                            "geometry": [{"lat": a, "lon": b} for a, b in ring]})
    return out

def make(area):
    lat0, lng0, BOX, CONST = AREAS[area]

    def xy(lat, lng):
        return (0.5 + (lng - lng0) * 111.32 * math.cos(lat0 * math.pi / 180) / 5, 0.5 + (lat0 - lat) * 111.32 / 5)

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

    def inbox(g):
        return any(BOX[0] <= a <= BOX[2] and BOX[1] <= b <= BOX[3] for a, b in g)

    def flat(pts):
        return ",".join(f"{x:.4f},{y:.4f}" for x, y in pts)

    def emit(name, lines):
        s = f"  {name}: [\n"
        for pts in lines:
            s += "    [" + flat(pts) + "],\n"
        return s + "  ],\n"

    main_roads, small_roads, rails, water, water_lines, parks = [], [], [], [], [], []
    for e in json.load(open(f"{HERE}/{area}_roads.json"))["elements"]:
        if e["type"] != "way" or "geometry" not in e:
            continue
        g = [(p["lat"], p["lon"]) for p in e["geometry"]]
        if not inbox(g):
            continue
        t = e.get("tags", {})
        pts = dp([xy(a, b) for a, b in g], 0.0008)
        if t.get("railway"):
            rails.append(pts)
        elif t.get("highway") in ("primary", "secondary", "tertiary"):
            main_roads.append(pts)
        elif t.get("highway") in ("footway", "path", "service"):
            continue  # 細すぎる道は省く（容量のため）
        else:
            small_roads.append(pts)
    for e in expand_relations(json.load(open(f"{HERE}/{area}_water.json"))["elements"]):
        if e["type"] != "way" or "geometry" not in e:
            continue
        g = [(p["lat"], p["lon"]) for p in e["geometry"]]
        if not inbox(g):
            continue
        t = e.get("tags", {})
        closed = g[0] == g[-1] and len(g) > 3
        if closed and (t.get("natural") == "water" or t.get("waterway") == "riverbank"):
            pts = dp([xy(a, b) for a, b in g[:-1]], 0.0006)  # 閉じた形は、最後の点（始点と同じ）を除いて簡略化する
            if len(pts) >= 3:
                water.append(pts)
        elif t.get("waterway") in ("river", "canal", "stream"):
            water_lines.append(dp([xy(a, b) for a, b in g], 0.0006))
    green_els = json.load(open(f"{HERE}/{area}_green.json"))["elements"]
    if os.path.exists(f"{HERE}/{area}_green2.json"):  # 複数の線をまとめた形の公園・森（取れた駅だけ）
        green_els += json.load(open(f"{HERE}/{area}_green2.json"))["elements"]
    for e in expand_relations(green_els):
        if e["type"] != "way" or "geometry" not in e:
            continue
        g = [(p["lat"], p["lon"]) for p in e["geometry"]]
        if not inbox(g) or g[0] != g[-1] or len(g) < 4:
            continue
        pts = dp([xy(a, b) for a, b in g[:-1]], 0.001)
        if len(pts) < 3:
            continue
        # 小さすぎる緑地は省く
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        if (max(xs) - min(xs)) * (max(ys) - min(ys)) < 0.00002:
            continue
        parks.append(pts)
    # 手で囲んだ緑地（OSMにない公園まわりの緑。OSMのデータとは別ファイルに分けて持つ）
    if os.path.exists(f"{HERE}/{area}_green_hand.json"):
        for poly in json.load(open(f"{HERE}/{area}_green_hand.json"))["polygons"]:
            parks.append(dp([xy(a, b) for a, b in poly], 0.001))

    out = f"// 自動生成（scripts/build_geo_area.py）。手で直さない。\n"
    out += "// 地図データ: © OpenStreetMap contributors（Open Database License 1.0）。https://www.openstreetmap.org/copyright\n"
    if os.path.exists(f"{HERE}/{area}_green_hand.json"):
        out += "// 緑地の一部は、OSMにない範囲を、国土地理院の地図を見て目で追って足したもの（OSMのデータではない）。\n"
    out += "// 座標は、yoridou_data.dart の mapPosOf と同じ投影（原点は駅）。\n"
    out += "import 'area_geo.dart';\n\n"
    out += f"const AreaGeo {CONST} = AreaGeo(\n  sea: false,\n"
    out += emit("water", water) + emit("waterLines", water_lines) + emit("parks", parks)
    out += emit("mainRoads", main_roads) + emit("smallRoads", small_roads) + emit("rails", rails)
    out += ");\n"
    path = f"{APP}/{area}_geo.dart"
    open(path, "w", encoding="utf-8").write(out)
    print(len(water), len(water_lines), len(parks), len(main_roads), len(small_roads), len(rails), len(out) // 1024, "KB ->", path)


if __name__ == "__main__":
    make(sys.argv[1])
