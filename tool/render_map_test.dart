// まとめマップの背景を、画像（PNG）に書き出す道具（試作用）。アプリには入らない。
// 使い方: flutter test tool/yoridou_render_map_test.dart
// 出力:   honya-sanpo-spots/map_build/<エリア>_raw.png と <エリア>_bounds.json
//
// 地図の形（OpenStreetMapから作った線や面）は tool/yoridou_geo/ にあり、アプリには入れない。
// 入れるのは、ここで描いた「画像」だけ（ODbLでいう「作った絵（Produced Work）」）。
import 'dart:convert';
import 'dart:io';
import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:bookmap_v2/experiments/yoridou/demachiyanagi_data.dart';
import 'package:bookmap_v2/experiments/yoridou/onomichi_data.dart';
import 'package:bookmap_v2/experiments/yoridou/yoridou_data.dart';

import 'yoridou_geo/area_geo.dart';
import 'yoridou_geo/demachiyanagi_geo.dart';
import 'yoridou_geo/onomichi_geo.dart';

const _outDir = 'map_build';
const _unitM = 5000.0; // 地図の1ユニット = 5km
const _pxPerM = 0.45; // 画像の細かさ（1mあたり0.45px）
const _marginKm = 1.8; // スポットの範囲の外側に足す余白
// 線の太さ：もとの描画（画面のpx）に、この倍率をかける（中くらいの拡大で、もとと同じ太さに見える）
const _k = 3.5;

Future<void> _render(
  String key,
  List<YSpot> spots,
  double lat0,
  double lng0,
  AreaGeo geo,
) async {
  (double, double) pos(YSpot s) {
    final xKm =
        ((s.lng ?? lng0) - lng0) * 111.32 * math.cos(lat0 * math.pi / 180);
    final yKm = (lat0 - (s.lat ?? lat0)) * 111.32;
    return (0.5 + xKm / 5, 0.5 + yKm / 5);
  }

  var minX = 9.0, maxX = -9.0, minY = 9.0, maxY = -9.0;
  for (final s in spots) {
    final p = pos(s);
    minX = math.min(minX, p.$1);
    maxX = math.max(maxX, p.$1);
    minY = math.min(minY, p.$2);
    maxY = math.max(maxY, p.$2);
  }
  const m = _marginKm * 1000 / _unitM;
  final x0 = minX - m, x1 = maxX + m, y0 = minY - m, y1 = maxY + m;
  final pxPerUnit = _unitM * _pxPerM;
  final w = ((x1 - x0) * pxPerUnit).round(),
      h = ((y1 - y0) * pxPerUnit).round();

  Path poly(List<List<double>> lines, {required bool close}) {
    final p = Path();
    for (final l in lines) {
      for (var i = 0; i + 1 < l.length; i += 2) {
        i == 0 ? p.moveTo(l[i], l[i + 1]) : p.lineTo(l[i], l[i + 1]);
      }
      if (close) p.close();
    }
    return p;
  }

  final rec = ui.PictureRecorder();
  final canvas = Canvas(rec);
  final rect = Rect.fromLTWH(0, 0, w.toDouble(), h.toDouble());
  final sea = geo.sea;
  canvas.drawRect(
    rect,
    Paint()..color = sea ? const Color(0xFFCADDE4) : const Color(0xFFF6F1E7),
  );
  canvas.save();
  canvas.scale(pxPerUnit);
  canvas.translate(-x0, -y0);
  final scale = pxPerUnit; // 1ユニットあたりのpx
  Paint line(double wpx, Color c) => Paint()
    ..style = PaintingStyle.stroke
    ..strokeCap = StrokeCap.round
    ..strokeJoin = StrokeJoin.round
    ..strokeWidth = wpx * _k / scale
    ..color = c;
  if (sea) {
    canvas.drawPath(
      poly(geo.land, close: true),
      Paint()..color = const Color(0xFFF6F1E7),
    );
    canvas.drawPath(
      poly(geo.land, close: true),
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.2 * _k / scale
        ..strokeJoin = StrokeJoin.round
        ..color = const Color(0xFFAFC8D2),
    );
  } else {
    canvas.drawPath(
      poly(geo.parks, close: true),
      Paint()..color = const Color(0xFFE3EBD6),
    );
    canvas.drawPath(
      poly(geo.water, close: true),
      Paint()..color = const Color(0xFFCADDE4),
    );
    canvas.drawPath(
      poly(geo.waterLines, close: false),
      line(4.0, const Color(0xFFCADDE4)),
    );
  }
  canvas.drawPath(poly(geo.smallRoads, close: false), line(1.7, Colors.white));
  canvas.drawPath(
    poly(geo.mainRoads, close: false),
    line(5.0, const Color(0xFFE9DFD2)),
  );
  canvas.drawPath(poly(geo.mainRoads, close: false), line(3.2, Colors.white));
  canvas.drawPath(
    poly(geo.rails, close: false),
    line(1.3, const Color(0xFFC9C2B6)),
  );
  canvas.restore();

  final image = await rec.endRecording().toImage(w, h);
  final bytes = (await image.toByteData(format: ui.ImageByteFormat.png))!;
  Directory(_outDir).createSync(recursive: true);
  File('$_outDir/${key}_raw.png').writeAsBytesSync(bytes.buffer.asUint8List());
  File('$_outDir/${key}_bounds.json').writeAsStringSync(
    jsonEncode({
      'x0': x0,
      'y0': y0,
      'x1': x1,
      'y1': y1,
      'w': w,
      'h': h,
      'sea': sea,
    }),
  );
  // ignore: avoid_print
  print('$key: ${w}x$h px, 範囲 x $x0..$x1  y $y0..$y1');
}

void main() {
  testWidgets('地図の背景を画像に書き出す', (tester) async {
    await tester.runAsync(() async {
      await _render(
        'onomichi',
        kOnomichiSpots,
        34.4049,
        133.1999,
        const AreaGeo(
          sea: true,
          land: kGeoLand,
          mainRoads: kGeoMainRoads,
          smallRoads: kGeoSmallRoads,
          rails: kGeoRails,
        ),
      );
      await _render(
        'demachiyanagi',
        kDemachiyanagiSpots,
        35.0306702,
        135.7731889,
        kDemachiyanagiGeo,
      );
    });
  });
}
