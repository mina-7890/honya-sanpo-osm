// 地図の背景の形（OpenStreetMapから作った線や面）を入れる入れ物。アプリには入れない（絵に描いてから、絵だけ入れる）。
/// 座標は mapPosOf と同じ投影で並べたもの（x,y,x,y,…）。
class AreaGeo {
  const AreaGeo({
    this.sea = false, // true: 海辺の街（背景が海で、陸を塗る）／false: 内陸（背景が陸で、川や池を塗る）
    this.land = const [],
    this.water = const [],
    this.waterLines = const [],
    this.parks = const [],
    required this.mainRoads,
    required this.smallRoads,
    required this.rails,
  });
  final bool sea;
  final List<List<double>> land, water, waterLines, parks;
  final List<List<double>> mainRoads, smallRoads, rails;
}
