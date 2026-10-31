"""
Generátor krabičky pro krbový teploměr (ESP32 + MAX31856).

Remix modelu "ESP32-WROOM-32 (USB-C) Box with Lid" od autora PLAUK
(https://www.printables.com/model/711587-esp32-wroom-32-usb-c-box-with-lid),
licence CC BY 4.0. Originální STL jsou v adresáři original/.

Změny oproti originálu:
  * krabička prodloužena o oddíl pro modul LaskaKit MAX31856 (lícem dolů),
  * plné dno nahrazeno policí pod ESP + kabelovým prostorem pro dupont
    konektory, zadní strana otevřená s lepicím lemem (montáž na zeď),
  * výřez pro kabel termočlánku v boční stěně + jazýček ve víčku,
  * druhý pár zaklapávacích západek, přítlačné kolíky ve víčku.

Použití:
  pip install -r requirements.txt
  python build_enclosure.py      # vytvoří enclosure_box.stl a enclosure_lid.stl

Tento skript: MIT licence (viz LICENSE-CODE). Výsledné modely: CC BY-SA 4.0.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORIG_BOX = HERE / 'original' / 'Box.stl'
ORIG_LID = HERE / 'original' / 'Lid.stl'

import numpy as np, trimesh
import manifold3d as mf
from manifold3d import Manifold, Mesh

# ---------------- PARAMETRY ----------------
L        = 40.0   # o kolik se krabička prodlouží (strana proti USB, +Y)
DUPONT   = 20.0   # délka pinů + dupont konektorů pod deskou (od spodku DPS)
BEND     = 6.0    # volné místo pod konektory na ohyb drátů
SHELF_T  = 2.0    # tloušťka police pod ESP (místo původního plného dna)
FLANGE_W = 4.0    # šířka lepicího lemu na zadní straně
FLANGE_T = 1.5
SPINE_T  = 2.0    # podélné žebro pod policí ESP (podpora + lepicí plocha)
# modul LaskaKit MAX31856 (30 x 24 mm), osazený LÍCEM DOLŮ: svorkovnice KF301
# (uprostřed delší strany) a sdružený konektor (uprostřed kratší strany, 10 mm)
# visí dolů do kabelového prostoru, rubová strana DPS je nahoře
MAX_W    = 24.0   # šířka DPS (osa X)
MAX_L    = 30.0   # délka DPS (osa Y)
MAX_T    = 1.6    # tloušťka DPS
MAX_FACE_Z = 0.0  # výška lícové strany DPS = horní plocha polic (rub DPS musí být pod háčkem západky z=1.95)
TERM_H   = 10.0   # výška svorkovnice KF301 pod DPS
TERM_ENTRY = 4.5  # střed otvoru svorkovnice pod DPS
TERM_FREE = 7.0   # ± okolí svorkovnice na hraně DPS bez podpěry
MAX_Y0   = 27.2   # začátek DPS (za ESP deskou, která končí do y = 26.2)
MCLR     = 0.4    # vůle kolem DPS modulu
# výstup termočlánku – v boční stěně (+X) proti svorkovnici
NOTCH_W  = 5.5    # šířka výřezu pro kabel
OPEN_H   = 5.0    # výška otvoru, který zůstane po nasazení víčka
CLR      = 0.2    # vůle jazýčku víčka ve výřezu
SEG      = 64

# ---------------- pomocné funkce ----------------
def load(path):
    t = trimesh.load(str(path))
    return Manifold(Mesh(vert_properties=np.asarray(t.vertices, np.float32),
                         tri_verts=np.asarray(t.faces, np.uint32)))

def save(M, path):
    me = M.simplify(1e-3).to_mesh()   # sloučí mikro-hrany vzniklé zaokrouhlením
    t = trimesh.Trimesh(me.vert_properties[:, :3], me.tri_verts)
    t.merge_vertices()
    print('  watertight:', t.is_watertight, ' objem mm3:', round(t.volume, 1))
    t.export(path)

def stretch_z(M, pos, d, down=False):
    """vloží d mm konstantního průřezu v rovině z=pos"""
    eps = 0.0
    lo = M.trim_by_plane([0, 0, -1], -pos)
    hi = M.trim_by_plane([0, 0, 1], pos)
    mid = M.slice(pos).extrude(d + 2 * eps)
    if down:
        return Manifold.batch_boolean(
            [lo.translate([0, 0, -d]), mid.translate([0, 0, pos - d - eps]), hi], mf.OpType.Add)
    return Manifold.batch_boolean(
        [lo, mid.translate([0, 0, pos - eps]), hi.translate([0, 0, d])], mf.OpType.Add)

def stretch_y(M, pos, d):
    R = M.rotate([90, 0, 0])            # y -> z
    R = stretch_z(R, pos, d)
    return R.rotate([-90, 0, 0])

def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])

def rbox(x0, x1, y0, y1, z0, z1, r):
    """kvádr se zaoblenými svislými hranami"""
    cs = mf.CrossSection.square([x1 - x0 - 2 * r, y1 - y0 - 2 * r]).offset(
        r, mf.JoinType.Round, circular_segments=SEG)
    return cs.extrude(z1 - z0).translate([x0 + r, y0 + r, z0])

def slot_x(xc, w, y0, y1, zb, ztop):
    """svislý U-výřez (dole půlkruh) procházející stěnou ve směru Y"""
    r = w / 2
    c = Manifold.cylinder(y1 - y0, r, r, SEG).rotate([-90, 0, 0]).translate([xc, y0, zb + r])
    return c + box(xc - r, xc + r, y0, y1, zb + r, ztop)

def slot_y(yc, w, x0, x1, zb, ztop):
    """svislý U-výřez (dole půlkruh) procházející stěnou ve směru X"""
    r = w / 2
    c = Manifold.cylinder(x1 - x0, r, r, SEG).rotate([0, 90, 0]).translate([x0, yc, zb + r])
    return c + box(x0, x1, yc - r, yc + r, zb + r, ztop)

# ---------------- původní míry ----------------
f32 = lambda v: float(np.float32(v))     # STL je ve float32 – shodné hodnoty = čisté booleany
Y_SPLIT_BOX = 25.6    # rovina natažení krabičky (před vnitřní stěnou y=26.2)
Y_SPLIT_LID = 24.5    # rovina natažení víčka (před obvodovým límcem)
INNER_X     = f32(14.55)   # vnitřní stěny ±14.5
INNER_YEND  = f32(26.2)    # vnitřní čelní stěna (strana proti USB)
OUTER_YEND  = f32(28.6)
TOP_Z       = f32(4.95)
FLOOR_TOP   = f32(-0.2)
INNER_YSTART = f32(-26.2)  # vnitřní stěna na straně USB

MAX_Z    = MAX_FACE_Z                             # police podpírají líc DPS
SHELF_BOT = FLOOR_TOP - SHELF_T
BOTTOM_Z = FLOOR_TOP - DUPONT - BEND               # zadní (lepená) strana – určuje ji ESP
DZ       = f32(-8.7) - BOTTOM_Z
NOTCH_Z0 = MAX_Z - TERM_ENTRY - OPEN_H / 2         # otvor proti vstupu svorkovnice
assert MAX_Z + MAX_T + 1.5 < TOP_Z, 'rub DPS s pájkou by narážel do víčka'

# ================= KRABIČKA =================
B = load(ORIG_BOX)
B = stretch_z(B, -4.0, DZ, down=True)      # prohloubení (průřez v z=-4 je konstantní)

in_end  = INNER_YEND + L
out_end = OUTER_YEND + L
OUT_X, OUT_R, IN_X, IN_R, CHAMF = f32(16.55), 2.73, INNER_X, 1.0, 0.5
Y_SHELL, Y_CAV, Y_POCKET = 25.5, 25.45, 25.6   # za sloupky (končí na y=25.4)

def far_round(x, y0, y1, r):
    """obdélník ±x, y0..y1, zaoblený jen na vzdáleném konci"""
    rr = mf.CrossSection.square([2 * x - 2 * r, (y1 - y0) - 2 * r]).offset(
        r, mf.JoinType.Round, circular_segments=SEG).translate([-x + r, y0 + r])
    return rr + mf.CrossSection.square([2 * x, (y1 - y0) - r]).translate([-x, y0])

# nový plášť (vnější tvar shodný s originálem: ±16.55, R2.73, spodní sražení 0.5)
fp = far_round(OUT_X, Y_SHELL, out_end, OUT_R)
fp_in = far_round(OUT_X - CHAMF, Y_SHELL, out_end - CHAMF, OUT_R - CHAMF)
shell = Manifold.hull(fp_in.extrude(0.01).translate([0, 0, BOTTOM_Z]) +
                      fp.extrude(TOP_Z - (BOTTOM_Z + CHAMF)).translate([0, 0, BOTTOM_Z + CHAMF]))
B = B + shell

# vnitřní prostor nad policí (prodloužení původní dutiny)
cav = far_round(IN_X, Y_CAV, in_end, IN_R).extrude(TOP_Z + 1 - FLOOR_TOP).translate([0, 0, FLOOR_TOP])
# oddíl pro modul – průchozí až na zadní stranu
pocket = far_round(IN_X, Y_POCKET, in_end, IN_R).extrude(FLOOR_TOP + 0.5 - BOTTOM_Z + 1).translate([0, 0, BOTTOM_Z - 1])
# kabelový prostor pod policí ESP (z původního plného dna zůstane jen police)
chamber = box(-IN_X, IN_X, INNER_YSTART, Y_POCKET + 0.5, BOTTOM_Z - 1, SHELF_BOT)
# výřez pro kabel termočlánku v čelní stěně
# poloha modulu: k levé stěně (-X), svorkovnice míří k pravé stěně (+X)
x0 = -IN_X + MCLR                          # levá hrana DPS
x1 = x0 + MAX_W                            # pravá hrana DPS (strana se svorkovnicí)
y0 = MAX_Y0
y1 = y0 + MAX_L + MCLR
TERM_Y = (y0 + y1) / 2                     # střed svorkovnice
notch = slot_y(TERM_Y, NOTCH_W, IN_X - 1, OUT_X + 1, NOTCH_Z0, TOP_Z + 1)
B = B - cav - pocket - chamber - notch

# podélné žebro pod policí a lepicí lem po obvodu zadní strany
spine = box(-SPINE_T / 2, SPINE_T / 2, INNER_YSTART - 0.5, Y_POCKET, BOTTOM_Z, SHELF_BOT + 0.01)
flange = (box(-IN_X - 0.5, IN_X + 0.5, INNER_YSTART - 0.5, in_end + 0.5, BOTTOM_Z, BOTTOM_Z + FLANGE_T) -
          rbox(-IN_X + FLANGE_W, IN_X - FLANGE_W, INNER_YSTART + FLANGE_W, in_end - FLANGE_W,
               BOTTOM_Z - 1, BOTTOM_Z + FLANGE_T + 1, 2.0))
B = B + spine + flange

# lože modulu (lícem dolů): police se sražením 45° (tisk bez podpěr) + dorazy
LEDGE = 1.0                                # o kolik police podebírá DPS (jen okraj)
GUIDE_TOP = MAX_Z + MAX_T + 1.0
def wedge(xe, ya, yb, side):
    """police od stěny (side=-1 levá, +1 pravá) k hraně DPS xe, horní plocha MAX_Z"""
    xa, xb = sorted((xe, side * (IN_X + 0.3)))
    xw0, xw1 = sorted((side * (IN_X - 0.3), side * (IN_X + 0.3)))
    drop = abs(side * IN_X - xe) + 1.5
    top = box(xa, xb, ya, yb, MAX_Z - 1.5, MAX_Z)
    foot = box(xw0, xw1, ya, yb, MAX_Z - 1.5 - drop, MAX_Z - 1.5)
    return Manifold.hull(top + foot)
# levá strana: police po celé délce (stěna sama slouží jako vodítko)
B = B + wedge(x0 + LEDGE, y0 - 1.0, y1 + 1.0, -1)
# pravá strana: police mimo oblast svorkovnice
B = B + wedge(x1 - LEDGE, y0 - 1.0, TERM_Y - TERM_FREE, +1)
B = B + wedge(x1 - LEDGE, TERM_Y + TERM_FREE, y1 + 1.0, +1)
# pravá vodítka (jen u konců, mimo zářez západky ve stěně)
for ga, gb in ((y0 - 1.0, y0 + 6.0), (y1 - 6.0, y1 + 1.0)):
    B = B + box(x1, 12.9, ga, gb, MAX_Z - 0.01, GUIDE_TOP)
# dorazy na krátkých stranách (v rozích, mimo konektor uprostřed)
for ya, yb in ((y0 - 1.0, y0), (y1, y1 + 1.0)):
    for xa, xb in ((-IN_X - 0.3, x0 + 5.0), (x1 - 5.0, 12.9)):
        B = B + box(xa, xb, ya, yb, MAX_Z - 0.01, GUIDE_TOP)

print(f'zadní strana z={BOTTOM_Z:.2f}, výška {TOP_Z - BOTTOM_Z:.2f} mm, DPS x {x0:.2f}..{x1:.2f} y {y0:.2f}..{y1:.2f}, svorkovnice y={TERM_Y:.2f}, mezera ke stěně {IN_X - x1:.2f}')

# ================= VÍČKO =================
Lid = load(ORIG_LID)
Lid = stretch_y(Lid, Y_SPLIT_LID, L)
# mezera v límci nad výřezem (pravý bok)
Lid = Lid - box(IN_X - 1.0, OUT_X + 1, TERM_Y - NOTCH_W / 2 - 0.2, TERM_Y + NOTCH_W / 2 + 0.2, 1.0, TOP_Z - 0.01)
# jazýček, který výřez shora zavře a nechá otvor OPEN_H pro kabel
tw = NOTCH_W / 2 - CLR
tongue = box(IN_X + CLR, OUT_X - 0.3, TERM_Y - tw, TERM_Y + tw, NOTCH_Z0 + OPEN_H, TOP_Z + 0.5)
Lid = Lid + tongue
# přítlačné kolíky na rub DPS modulu (mimo pružná raménka západek)
for px in (x0 + 5.0, x1 - 2.0):
    for py in (y0 + 2.5, y1 - 2.5):
        Lid = Lid + Manifold.cylinder(TOP_Z + 0.5 - (MAX_Z + MAX_T + 0.2), 1.5, 1.5, 32).translate(
            [px, py, MAX_Z + MAX_T + 0.2])

# ================= DRUHÝ PÁR ZÁPADEK =================
# Oblasti s originálními západkami se zkopírují 1:1 a posunou o SNAP_DY do
# prodloužené části (tam je průřez krabičky i víčka hladký, takže hranice sedí).
SNAP_DY = 56.4            # původní háček je na y = -5..0 → nový na y = 51.4..56.4
B0, L0 = load(ORIG_BOX), load(ORIG_LID)
for sx in (-1, 1):
    xa, xb = sorted((sx * 17.0, sx * 13.0))
    rb = box(xa, xb, -6.0, 1.0, 0.5, 4.6)                 # zářez ve stěně krabičky
    B = (B - rb.translate([0, SNAP_DY, 0])) + (B0 ^ rb).translate([0, SNAP_DY, 0])
    xa, xb = sorted((sx * 17.0, sx * 11.8))
    rl = box(xa, xb, -10.8, 7.6, 1.0, 7.5)                # pružné raménko s háčkem
    Lid = (Lid - rl.translate([0, SNAP_DY, 0])) + (L0 ^ rl).translate([0, SNAP_DY, 0])

for name, M in (('enclosure_box', B), ('enclosure_lid', Lid)):
    print(name, M.status(), 'genus', M.genus(), 'bbox', np.round(M.bounding_box(), 2))
    save(M, HERE / f'{name}.stl')
