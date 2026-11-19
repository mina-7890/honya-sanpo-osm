# honya-sanpo-osm

iOSアプリ「本屋さんぽ」の「妄想さんぽ」で使う、**地図の背景の形のデータ**と、それを作るスクリプトの公開リポジトリです。
This repository publishes the map-shape data (derived from OpenStreetMap) used by the "Mōsō Sanpo" feature of the iOS app *Honya Sanpo*, and the scripts that produce it.

## データについて / About the data

- 地図の形（道・線路・川・池・公園・森）は、**© OpenStreetMap contributors** のデータから作っています。
- Map shapes (roads, railways, rivers, ponds, parks, forests) are derived from data © OpenStreetMap contributors.
- ライセンス / License: **Open Database License (ODbL) 1.0** — <https://opendatacommons.org/licenses/odbl/1-0/>
  帰属表示 / Attribution: <https://www.openstreetmap.org/copyright>
- `data/osm/` … OpenStreetMap（Overpass API）から取得した、元のデータの抜き出し。
- `geo/` … そこから作った、地図の形のデータ（派生データベース）。ODbL 1.0 で提供します。
- アプリには、この形のデータそのものは入れていません。形から描いた**地図の画像（Produced Work）**だけを入れ、画面に「© OpenStreetMap contributors」を表示しています。

## スクリプト / Scripts

| ファイル | 内容 |
|---|---|
| `scripts/fetch_osm_area.py` | Overpass API から、範囲内の道・川・緑を取って `data/osm/` に保存する（混んでいて止まったら、同じコマンドで続きから再開する） |
| `scripts/build_geo_data.py` | 尾道の形のデータ（`geo/onomichi_geo.dart`）を作る |
| `scripts/build_geo_area.py` | 内陸の駅（出町柳・吉祥寺）の形のデータ（`geo/<駅名>_geo.dart`）を作る |
| `tool/render_map_test.dart` | 形のデータから、地図の画像を描く（アプリ本体のプロジェクトの中で動かす参考用） |

```bash
python3 scripts/fetch_osm_area.py demachiyanagi
python3 scripts/build_geo_area.py demachiyanagi
```

## 手で足した緑地 / Hand-drawn green areas

- `data/osm/kichijoji_green_hand.json` は、OpenStreetMap のデータではありません。吉祥寺の井の頭恩賜公園まわりで、OSMに入っていない公園の緑が狭かったため、**国土地理院の地図（標準地図）を見て、おおよその範囲を目で追って足した**ものです。`geo/kichijoji_geo.dart` は、OSM由来のデータと、この手で足した範囲を合わせて作っています。
- `data/osm/kichijoji_green_hand.json` is not OpenStreetMap data. It is a hand-traced approximation (using the GSI Japan standard map as a visual reference) of park greenery missing from OSM around Inokashira Park. `geo/kichijoji_geo.dart` combines OSM-derived data with this hand-drawn area.
- 出典 / Source for reference: 国土地理院（Geospatial Information Authority of Japan） <https://maps.gsi.go.jp/>

スクリプトのライセンス / Scripts license: MIT（下の `LICENSE-scripts` を参照）。

## 連絡先 / Contact

本屋さんぽ（App Store のアプリ情報にある問い合わせ先）。
