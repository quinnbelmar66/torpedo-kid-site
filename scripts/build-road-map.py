"""Builds src/components/torpedo/roadMap.ts: the map for "The road to Sweden".

Coastlines and borders come from Natural Earth 1:50m (public domain):
  https://github.com/nvkelso/natural-earth-vector/tree/master/geojson
    ne_50m_land.geojson, ne_50m_admin_0_boundary_lines_land.geojson

Usage:
  python scripts/build-road-map.py <ne_50m_land.geojson> <ne_50m_admin_0_boundary_lines_land.geojson>

The route is a list of towns along the motorways (lon, lat), smoothed. It is
stylised, not a planned itinerary.
"""
import json, math, os, sys

LON0, LON1, LAT0, LAT1 = 3.0, 15.0, 50.9, 58.0      # visible area
PAD = 0.6                                            # clip a little outside it
S = 100                                              # px per degree of latitude
KX = math.cos(math.radians(55))                      # shrink longitude at ~55°N
W = round((LON1 - LON0) * KX * S)
H = round((LAT1 - LAT0) * S)

def proj(lon, lat):
    return ((lon - LON0) * KX * S, (LAT1 - lat) * S)

def clip_polygon(pts, x0, y0, x1, y1):
    """Sutherland-Hodgman against an axis-aligned box (lon/lat)."""
    def clip(points, inside, cut):
        out = []
        for i, cur in enumerate(points):
            prev = points[i - 1]
            if inside(cur):
                if not inside(prev):
                    out.append(cut(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(cut(prev, cur))
        return out
    def at_x(x):
        return lambda a, b: (x, a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]))
    def at_y(y):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]), y)
    for inside, cut in ((lambda p: p[0] >= x0, at_x(x0)), (lambda p: p[0] <= x1, at_x(x1)),
                        (lambda p: p[1] >= y0, at_y(y0)), (lambda p: p[1] <= y1, at_y(y1))):
        pts = clip(pts, inside, cut)
        if not pts:
            return []
    return pts

def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    (ax, ay), (bx, by) = pts[0], pts[-1]
    dx, dy = bx - ax, by - ay
    norm = math.hypot(dx, dy) or 1e-9
    idx, dmax = 0, -1.0
    for i in range(1, len(pts) - 1):
        px, py = pts[i]
        d = abs(dy * px - dx * py + bx * ay - by * ax) / norm
        if d > dmax:
            idx, dmax = i, d
    if dmax > eps:
        return rdp(pts[: idx + 1], eps)[:-1] + rdp(pts[idx:], eps)
    return [pts[0], pts[-1]]

def fmt(p):
    return f'{p[0]:.1f} {p[1]:.1f}'

def path(pts, closed):
    return 'M' + ' L'.join(fmt(p) for p in pts) + ('Z' if closed else '')

box = (LON0 - PAD, LAT0 - PAD, LON1 + PAD, LAT1 + PAD)

land = []
for f in json.load(open(sys.argv[1], encoding='utf-8'))['features']:
    g = f['geometry']
    polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    for poly in polys:
        ring = [tuple(p[:2]) for p in poly[0]]
        clipped = clip_polygon(ring, *box)
        if len(clipped) < 3:
            continue
        ring_px = [proj(*p) for p in clipped]
        # A closed ring starts and ends on the same point, which RDP can't measure from;
        # split it at the point farthest from the start and simplify each half.
        far = max(range(len(ring_px)), key=lambda i: math.dist(ring_px[0], ring_px[i]))
        pts = rdp(ring_px[: far + 1], 0.45)[:-1] + rdp(ring_px[far:] + [ring_px[0]], 0.45)[:-1]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        if len(pts) >= 3 and (max(xs) - min(xs)) * (max(ys) - min(ys)) > 40:   # drop specks
            land.append(path(pts, True))

borders = []
for f in json.load(open(sys.argv[2], encoding='utf-8'))['features']:
    g = f['geometry']
    lines = g['coordinates'] if g['type'] == 'MultiLineString' else [g['coordinates']]
    for line in lines:
        run = []
        for lon, lat in (p[:2] for p in line):
            if box[0] <= lon <= box[2] and box[1] <= lat <= box[3]:
                run.append(proj(lon, lat))
            elif run:
                if len(run) > 1:
                    borders.append(path(rdp(run, 0.45), False))
                run = []
        if len(run) > 1:
            borders.append(path(rdp(run, 0.45), False))

# Towns along the motorways, Eindhoven to Malmö (lon, lat)
TOWNS = [(5.478, 51.441), (6.17, 51.37), (7.63, 51.96), (8.05, 52.28), (8.80, 53.08), (9.99, 53.55),
         (9.98, 54.07), (9.43, 54.78), (9.47, 55.49), (9.73, 55.50), (10.39, 55.40), (10.80, 55.31),
         (11.14, 55.33), (12.57, 55.68), (13.00, 55.60)]

def chaikin(pts, n):
    for _ in range(n):
        out = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            out += [(0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]),
                    (0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1])]
        out.append(pts[-1])
        pts = out
    return pts

route = chaikin([proj(*t) for t in TOWNS], 3)

LABELS = [('Eindhoven', 5.7, 51.25, 'start'), ('Netherlands', 5.2, 52.55, 'middle'), ('Germany', 10.4, 52.35, 'middle'),
          ('Denmark', 9.2, 56.45, 'middle'), ('Sweden', 13.75, 56.75, 'middle')]

out = f'''// Generated by scripts/build-road-map.py from Natural Earth 1:50m (public domain). Do not edit by hand.
export const VIEW = {{ width: {W}, height: {H} }};
export const LAND = {json.dumps(land)};
export const BORDERS = {json.dumps(borders)};
export const ROUTE: [number, number][] = {json.dumps([[round(x, 1), round(y, 1)] for x, y in route])};
export const LABELS: {{ text: string; x: number; y: number; anchor: 'start' | 'middle' | 'end' }}[] = {json.dumps([dict(text=t, x=round(proj(lo, la)[0], 1), y=round(proj(lo, la)[1], 1), anchor=a) for t, lo, la, a in LABELS])};
'''
dest = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'components', 'torpedo', 'roadMap.ts')
open(dest, 'w', encoding='utf-8').write(out)
print(f'{W}x{H}, {len(land)} land shapes, {len(borders)} border lines, {len(route)} route points, {len(out) // 1024} KB')
