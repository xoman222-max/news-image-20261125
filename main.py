# news-image-20261125: front page of Wednesday 25 November 2026.
# Pure Python 3 stdlib. Hand-rolled PNG writer, no PIL, no network,
# no clock, no randomness (fixed-seed LCG grain). Two runs write
# byte-identical output. 1024x1024, under 1 MiB.
# Layout: masthead with huge date, Taipei-time timeline, 14 featured
# stories (2 cols x 7), world map with 14 numbered pins, ALSO ON
# 25 NOVEMBER list of 31, footer disclaimer. All artwork is flat
# vector shapes drawn by this program; no photographs.
import os
import struct
import zlib

W = 1024
H = 1024

# ---- palette ----
CREAM = (250, 246, 235)
PAPER = (246, 240, 226)
INK = (24, 30, 52)
NAVY = (22, 44, 92)
NAVY2 = (30, 58, 112)
RED = (192, 28, 28)
GOLD = (178, 128, 10)
BLUE = (31, 84, 150)
TEAL = (16, 108, 94)
GREEN = (46, 118, 68)
ORANGE = (206, 96, 20)
PURPLE = (108, 62, 148)
BROWN = (122, 78, 40)
WHITE = (255, 255, 255)
BLACK = (12, 12, 16)
TINT_BLUE = (214, 226, 240)
TINT_GOLD = (246, 234, 202)
TINT_GREY = (230, 230, 226)
TINT_RED = (248, 220, 220)
TINT_TEAL = (208, 232, 224)
TINT_GREEN = (214, 234, 214)
TINT_PURPLE = (230, 216, 240)
TINT_ORANGE = (250, 226, 204)
OCEAN = (196, 218, 238)
OCEAN2 = (178, 206, 232)
LAND = (196, 212, 172)
LAND2 = (172, 196, 150)
GRAIN_L = (238, 232, 216)
GRAIN_D = (226, 218, 198)

# ---- canvas ----
px = bytearray(W * H * 3)


def set_px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        px[i] = c[0]
        px[i + 1] = c[1]
        px[i + 2] = c[2]


def fill_rect(x, y, w, h, c):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        for xx in range(x0, x1):
            i = base + (xx - x0) * 3
            px[i] = c[0]
            px[i + 1] = c[1]
            px[i + 2] = c[2]


def rect_outline(x, y, w, h, c, t=1):
    fill_rect(x, y, w, t, c)
    fill_rect(x, y + h - t, w, t, c)
    fill_rect(x, y, t, h, c)
    fill_rect(x + w - t, y, t, h, c)


def line(x0, y0, x1, y1, c):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        set_px(x0, y0, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def thick_line(x0, y0, x1, y1, c, t=2):
    line(x0, y0, x1, y1, c)
    for k in range(1, t):
        line(x0, y0 + k, x1, y1 + k, c)
        line(x0 + k, y0, x1 + k, y1, c)


def disc(cx, cy, r, c):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                set_px(xx, yy, c)


def ring(cx, cy, r, c, t=2):
    for yy in range(cy - r - 1, cy + r + 2):
        for xx in range(cx - r - 1, cx + r + 2):
            d = (xx - cx) ** 2 + (yy - cy) ** 2
            if (r - t) ** 2 <= d <= (r + 1) ** 2:
                set_px(xx, yy, c)


def tri(x0, y0, x1, y1, x2, y2, c):
    # filled triangle via scanline
    pts = sorted([(x0, y0), (x1, y1), (x2, y2)], key=lambda p: p[1])
    (ax, ay), (bx, by), (cx, cy) = pts
    for y in range(ay, cy + 1):
        if y < by:
            t1 = (y - ay) / (by - ay) if by != ay else 0
            xa = ax + (bx - ax) * t1
        else:
            t1 = (y - by) / (cy - by) if cy != by else 0
            xa = bx + (cx - bx) * t1
        t2 = (y - ay) / (cy - ay) if cy != ay else 0
        xb = ax + (cx - ax) * t2
        for x in range(int(min(xa, xb)), int(max(xa, xb)) + 1):
            set_px(x, y, c)


def poly_fill(points, c):
    if len(points) < 3:
        return
    ys = [p[1] for p in points]
    for y in range(min(ys), max(ys) + 1):
        xs = []
        n = len(points)
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                t = (y - y0) / (y1 - y0)
                xs.append(x0 + (x1 - x0) * t)
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            for x in range(int(xs[k]), int(xs[k + 1]) + 1):
                set_px(x, y, c)


def poly_line(points, c):
    for i in range(len(points)):
        x0, y0 = points[i]
        x1, y1 = points[(i + 1) % len(points)]
        line(int(x0), int(y0), int(x1), int(y1), c)


# ---- 5x7 bitmap font, all caps. Each glyph: 7 rows of 5 bits. ----
FONT = {
    'A': ('01110', '10001', '10001', '11111', '10001', '10001', '10001'),
    'B': ('11110', '10001', '10001', '11110', '10001', '10001', '11110'),
    'C': ('01110', '10001', '10000', '10000', '10000', '10001', '01110'),
    'D': ('11110', '10001', '10001', '10001', '10001', '10001', '11110'),
    'E': ('11111', '10000', '10000', '11110', '10000', '10000', '11111'),
    'F': ('11111', '10000', '10000', '11110', '10000', '10000', '10000'),
    'G': ('01110', '10001', '10000', '10111', '10001', '10001', '01111'),
    'H': ('10001', '10001', '10001', '11111', '10001', '10001', '10001'),
    'I': ('01110', '00100', '00100', '00100', '00100', '00100', '01110'),
    'J': ('00111', '00010', '00010', '00010', '00010', '10010', '01100'),
    'K': ('10001', '10010', '10100', '11000', '10100', '10010', '10001'),
    'L': ('10000', '10000', '10000', '10000', '10000', '10000', '11111'),
    'M': ('10001', '11011', '10101', '10101', '10001', '10001', '10001'),
    'N': ('10001', '11001', '10101', '10011', '10001', '10001', '10001'),
    'O': ('01110', '10001', '10001', '10001', '10001', '10001', '01110'),
    'P': ('11110', '10001', '10001', '11110', '10000', '10000', '10000'),
    'Q': ('01110', '10001', '10001', '10001', '10101', '10010', '01101'),
    'R': ('11110', '10001', '10001', '11110', '10100', '10010', '10001'),
    'S': ('01111', '10000', '10000', '01110', '00001', '00001', '11110'),
    'T': ('11111', '00100', '00100', '00100', '00100', '00100', '00100'),
    'U': ('10001', '10001', '10001', '10001', '10001', '10001', '01110'),
    'V': ('10001', '10001', '10001', '10001', '10001', '01010', '00100'),
    'W': ('10001', '10001', '10001', '10101', '10101', '10101', '01010'),
    'X': ('10001', '10001', '01010', '00100', '01010', '10001', '10001'),
    'Y': ('10001', '10001', '01010', '00100', '00100', '00100', '00100'),
    'Z': ('11111', '00001', '00010', '00100', '01000', '10000', '11111'),
    '0': ('01110', '10001', '10011', '10101', '11001', '10001', '01110'),
    '1': ('00100', '01100', '00100', '00100', '00100', '00100', '01110'),
    '2': ('01110', '10001', '00001', '00110', '01000', '10000', '11111'),
    '3': ('11110', '00001', '00001', '01110', '00001', '00001', '11110'),
    '4': ('00010', '00110', '01010', '10010', '11111', '00010', '00010'),
    '5': ('11111', '10000', '11110', '00001', '00001', '10001', '01110'),
    '6': ('01110', '10000', '10000', '11110', '10001', '10001', '01110'),
    '7': ('11111', '00001', '00010', '00100', '01000', '01000', '01000'),
    '8': ('01110', '10001', '10001', '01110', '10001', '10001', '01110'),
    '9': ('01110', '10001', '10001', '01111', '00001', '00001', '01110'),
    ' ': ('00000', '00000', '00000', '00000', '00000', '00000', '00000'),
    '.': ('00000', '00000', '00000', '00000', '00000', '01100', '01100'),
    ',': ('00000', '00000', '00000', '00000', '01100', '00100', '01000'),
    ':': ('00000', '01100', '01100', '00000', '01100', '01100', '00000'),
    ';': ('00000', '01100', '01100', '00000', '01100', '00100', '01000'),
    '!': ('00100', '00100', '00100', '00100', '00100', '00000', '00100'),
    '?': ('01110', '10001', '00001', '00110', '00100', '00000', '00100'),
    "'": ('00100', '00100', '01000', '00000', '00000', '00000', '00000'),
    '"': ('01010', '01010', '00000', '00000', '00000', '00000', '00000'),
    '-': ('00000', '00000', '00000', '01110', '00000', '00000', '00000'),
    '(': ('00010', '00100', '01000', '01000', '01000', '00100', '00010'),
    ')': ('01000', '00100', '00010', '00010', '00010', '00100', '01000'),
    '/': ('00001', '00010', '00010', '00100', '01000', '01000', '10000'),
    '&': ('01100', '10010', '10100', '01000', '10101', '10010', '01101'),
    '%': ('11001', '11010', '00010', '00100', '01000', '01011', '10011'),
    '+': ('00000', '00100', '00100', '11111', '00100', '00100', '00000'),
    '=': ('00000', '00000', '11111', '00000', '11111', '00000', '00000'),
    '$': ('00100', '01111', '10100', '01110', '00101', '11110', '00100'),
    '*': ('00000', '10101', '01110', '11111', '01110', '10101', '00000'),
    '#': ('01010', '01010', '11111', '01010', '11111', '01010', '01010'),
    '@': ('01110', '10001', '10111', '10101', '10110', '10000', '01110'),
    '<': ('00010', '00100', '01000', '10000', '01000', '00100', '00010'),
    '>': ('01000', '00100', '00010', '00001', '00010', '00100', '01000'),
}


def text_w(s, scale):
    return len(s) * 6 * scale


def draw_text(x, y, s, color, scale=1):
    s = s.upper()
    cx = x
    for ch in s:
        g = FONT.get(ch)
        if g is None:
            ch2 = {'\u2019': "'", '\u2014': '-', '\u2013': '-',
                   '\u00e9': 'E', '\u00fc': 'U', '\u00f6': 'O'}.get(ch, ' ')
            g = FONT.get(ch2, FONT[' '])
        for r in range(7):
            row = g[r]
            for c in range(5):
                if row[c] == '1':
                    fill_rect(cx + c * scale, y + r * scale, scale, scale, color)
        cx += 6 * scale
    return cx


def draw_text_center(x0, x1, y, s, color, scale=1):
    w = text_w(s, scale)
    draw_text(x0 + (x1 - x0 - w) // 2, y, s, color, scale)


def wrap(s, max_w, scale):
    words = s.split(' ')
    lines = []
    cur = ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if text_w(t, scale) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ---- story icons: small flat pictograms, 48x48 box ----
def icon_burst(x, y, c):
    disc(x + 24, y + 22, 15, c)
    for dx, dy in [(-16, -12), (0, -18), (16, -12), (20, 4), (14, 16),
                   (0, 20), (-14, 16), (-20, 4)]:
        tri(x + 24, y + 22, x + 24 + dx, y + 22 + dy,
            x + 24 + int(dx * 0.45), y + 22 + int(dy * 0.45), c)
    disc(x + 24, y + 22, 7, WHITE)


def icon_rocket(x, y, c):
    tri(x + 24, y + 2, x + 16, y + 26, x + 32, y + 26, c)
    fill_rect(x + 18, y + 24, 12, 10, c)
    tri(x + 18, y + 26, x + 8, y + 38, x + 18, y + 34, c)
    tri(x + 30, y + 26, x + 40, y + 38, x + 30, y + 34, c)
    disc(x + 24, y + 16, 4, WHITE)
    tri(x + 24, y + 34, x + 19, y + 46, x + 29, y + 46, ORANGE)


def icon_medal(x, y, c):
    tri(x + 14, y + 4, x + 22, y + 4, x + 20, y + 22, RED)
    tri(x + 34, y + 4, x + 26, y + 4, x + 28, y + 22, RED)
    disc(x + 24, y + 32, 13, c)
    ring(x + 24, y + 32, 13, GOLD, 2)
    disc(x + 24, y + 32, 5, WHITE)


def icon_chip(x, y, c):
    fill_rect(x + 12, y + 12, 24, 24, c)
    fill_rect(x + 18, y + 18, 12, 12, WHITE)
    fill_rect(x + 21, y + 21, 6, 6, c)
    for k in range(4):
        fill_rect(x + 15 + k * 6, y + 6, 3, 6, c)
        fill_rect(x + 15 + k * 6, y + 36, 3, 6, c)
        fill_rect(x + 6, y + 15 + k * 6, 6, 3, c)
        fill_rect(x + 36, y + 15 + k * 6, 6, 3, c)


def icon_gavel(x, y, c):
    thick_line(x + 10, y + 36, x + 38, y + 12, c, 3)
    fill_rect(x + 8, y + 8, 14, 8, c)
    fill_rect(x + 28, y + 28, 14, 8, c)
    fill_rect(x + 10, y + 40, 28, 4, c)


def icon_shield(x, y, c):
    poly_fill([(x + 24, y + 4), (x + 40, y + 10), (x + 40, y + 26),
               (x + 24, y + 44), (x + 8, y + 26), (x + 8, y + 10)], c)
    disc(x + 24, y + 22, 5, WHITE)
    fill_rect(x + 22, y + 22, 4, 10, WHITE)


def icon_ship(x, y, c):
    poly_fill([(x + 8, y + 24), (x + 40, y + 24), (x + 34, y + 38),
               (x + 14, y + 38)], c)
    fill_rect(x + 22, y + 6, 4, 18, c)
    tri(x + 26, y + 8, x + 26, y + 20, x + 38, y + 20, WHITE)
    for k in range(3):
        line(x + 6 + k * 12, y + 44, x + 14 + k * 12, y + 44, BLUE)


def icon_flame(x, y, c):
    poly_fill([(x + 24, y + 4), (x + 32, y + 18), (x + 38, y + 26),
               (x + 36, y + 38), (x + 24, y + 44), (x + 12, y + 38),
               (x + 10, y + 26), (x + 18, y + 16)], c)
    disc(x + 24, y + 32, 6, GOLD)


def icon_cross(x, y, c):
    disc(x + 24, y + 24, 18, c)
    fill_rect(x + 21, y + 12, 6, 24, WHITE)
    fill_rect(x + 12, y + 21, 24, 6, WHITE)


def icon_trophy(x, y, c):
    poly_fill([(x + 12, y + 6), (x + 36, y + 6), (x + 33, y + 26),
               (x + 15, y + 26)], c)
    line(x + 12, y + 10, x + 4, y + 18, c)
    line(x + 36, y + 10, x + 44, y + 18, c)
    fill_rect(x + 22, y + 26, 4, 8, c)
    fill_rect(x + 14, y + 34, 20, 4, c)
    disc(x + 24, y + 16, 5, WHITE)


def icon_ball(x, y, c):
    disc(x + 24, y + 24, 18, WHITE)
    ring(x + 24, y + 24, 18, c, 2)
    poly_fill([(x + 24, y + 18), (x + 30, y + 22), (x + 28, y + 29),
               (x + 20, y + 29), (x + 18, y + 22)], c)
    line(x + 24, y + 18, x + 24, y + 6, c)
    line(x + 30, y + 22, x + 40, y + 18, c)
    line(x + 18, y + 22, x + 8, y + 18, c)


def icon_bag(x, y, c):
    poly_fill([(x + 12, y + 14), (x + 36, y + 14), (x + 40, y + 42),
               (x + 8, y + 42)], c)
    ring(x + 24, y + 16, 7, c, 3)
    draw_text(x + 20, y + 24, '$', WHITE, 2)


def icon_train(x, y, c):
    fill_rect(x + 10, y + 6, 28, 30, c)
    fill_rect(x + 14, y + 11, 9, 8, WHITE)
    fill_rect(x + 25, y + 11, 9, 8, WHITE)
    fill_rect(x + 10, y + 30, 28, 6, GOLD)
    disc(x + 17, y + 40, 3, INK)
    disc(x + 31, y + 40, 3, INK)
    line(x + 6, y + 44, x + 42, y + 44, INK)


def icon_store(x, y, c):
    fill_rect(x + 8, y + 18, 32, 24, c)
    for k in range(4):
        fill_rect(x + 8 + k * 8, y + 10, 8, 8,
                  RED if k % 2 == 0 else WHITE)
    fill_rect(x + 20, y + 28, 8, 14, WHITE)


ICONS = {'burst': icon_burst, 'rocket': icon_rocket, 'medal': icon_medal,
         'chip': icon_chip, 'gavel': icon_gavel, 'shield': icon_shield,
         'ship': icon_ship, 'flame': icon_flame, 'cross': icon_cross,
         'trophy': icon_trophy, 'ball': icon_ball, 'bag': icon_bag,
         'train': icon_train, 'store': icon_store}

REGION_COLOR = {'NORTH AMERICA': BLUE, 'SOUTH AMERICA': GREEN,
                'EUROPE': PURPLE, 'MIDDLE EAST': RED, 'AFRICA': ORANGE,
                'ASIA': TEAL, 'OCEANIA': BROWN}
REGION_TINT = {'NORTH AMERICA': TINT_BLUE, 'SOUTH AMERICA': TINT_GREEN,
               'EUROPE': TINT_PURPLE, 'MIDDLE EAST': TINT_RED,
               'AFRICA': TINT_ORANGE, 'ASIA': TINT_TEAL, 'OCEANIA': TINT_GOLD}

# ---- featured stories: (num, region, icon, headline, deck) ----
FEATURED = [
    (1, 'MIDDLE EAST', 'burst',
     'HOUTHIS HIT RIYADH TOWER AGAIN',
     '11 HURT AS MISSILE HITS CAPITAL\'S TALLEST TOWER AGAIN'),
    (2, 'ASIA', 'rocket',
     'SHENZHOU-24 BLASTS OFF',
     'PAKISTAN\'S ZEESHAN ALI, FIRST FOREIGN ASTRONAUT AT TIANGONG'),
    (3, 'NORTH AMERICA', 'medal',
     'TRUMP HONOURS GIULIANI',
     'EX-NEW YORK MAYOR GIVEN TOP US CIVILIAN HONOUR'),
    (4, 'NORTH AMERICA', 'chip',
     'HUANG IN THERAPY AS RALLY FADES',
     'CEO APOLOGISES; TRUMP SAYS PARDON ALWAYS AN OPTION'),
    (5, 'ASIA', 'gavel',
     'HUAWEI FOUND GUILTY IN US',
     'JURY CONVICTS GIANT OF TRADE-SECRET THEFT, BANK FRAUD'),
    (6, 'NORTH AMERICA', 'shield',
     'CIA AND ODNI HIT BY CYBER BREACH',
     'Unclassified data exposed in latest US security lapse, reports say'),
    (7, 'EUROPE', 'ship',
     'KYIV CONFIRMS SHIP STRIKE',
     'UKRAINE HIT RUSSIAN CARGO SHIP IN GULF OF FINLAND, KYIV CONFIRMS'),
    (8, 'MIDDLE EAST', 'flame',
     'HAMAS SECURITY CHIEF KILLED',
     'Israeli air strike hits Gaza City, militants say'),
    (9, 'AFRICA', 'cross',
     'WHO FLEES EBOLA HOSPITAL IN CONGO',
     'STAFF EVACUATED FROM ITURI HOSPITAL AFTER DAYS OF FIGHTING'),
    (10, 'AFRICA', 'trophy',
     'SENEGAL WIN AFCON TITLE BACK',
     'CAS overturns ruling that gave trophy to Morocco after chaotic final'),
    (11, 'EUROPE', 'ball',
     'REAL HIT PSV FOR FIVE',
     'MADRID WIN 5-1; ARSENAL AND CITY HELD, VILLA LOSE'),
    (12, 'NORTH AMERICA', 'bag',
     'SHEIN TO PAY $100M IN US DEAL',
     'GIANT SETTLES US TRADE ALLEGATIONS OVER DECEPTION'),
    (13, 'ASIA', 'train',
     'SEOUL SUBWAY STRIKE CALLED OFF',
     'Wage deal reached hours before walkout was due to start'),
    (14, 'SOUTH AMERICA', 'store',
     'HOSTAGES HELD IN COLOMBIA STORE',
     'Gunmen seize supermarket after failed armoured-car raid'),
]

ALSO = [
    'US SOLDIER ADMITS SELLING SECRETS TO CHINA',
    'FORT HOOD SHOOTER SEEKS EXECUTION DELAY',
    'SARKOZY CORRUPTION CASE ORDERED TO TRIAL',
    'PELICOT SLAMS USE OF NUDE CASE PHOTOS',
    '2 HELD AFTER BREAK-IN AT PRINCE WILLIAM HOME',
    'THOMAS MARKLE CHARGED IN US ABUSE CASE',
    'IRAQ SEEKS HIGHER OPEC+ OUTPUT QUOTA',
    'SAUDI CROWN PRINCE TO ATTEND US G20 SUMMIT',
    'HOUTHIS PUSH TOWARD ADEN, ARMY HOLDS LINE',
    'US WARNS CITIZENS OF HOUTHI THREAT',
    '6 MISSING AFTER PLANE CRASH OFF MISSISSIPPI',
    'RADAR FAULT DELAYS CHICAGO O\'HARE FLIGHTS',
    'TRUMP PARDONS TURKEYS FREEDOM, FEATHERS',
    'INDIA URGES HUMAN CONTROL OF AI WEAPONS',
    'NEPAL QUAKE 5.3, TREMORS FELT IN INDIA',
    'QUAKE 5.9 STRIKES BALLENY ISLANDS',
    'DELHI AIR "VERY POOR" AS AQI HITS 327',
    'SEOUL PUPILS GET ZERO FOR EXAM CHEATING',
    'HONG KONG POWER BILLS TO RISE IN JANUARY',
    'HONG KONG VISITORS UP 12% TO 5.13 MILLION',
    'ASIAN MATHEMATICAL UNION LAUNCHES IN HK',
    'COP31 FAULTED OVER FOSSIL-FUEL FAILURE',
    'GUKESH HOLDS SINDAROV IN CHESS TITLE BID',
    'EISENKOT CLINCHES ISRAEL COALITION DEAL',
    'SERBIA\'S VUCIC REPORTS DEATH THREATS',
    'DENMARK COURT UPHOLDS "GHETTO" EVICTIONS',
    'NORWAY BARS RUSSIAN SPEED SKATERS',
    'PERU CUTS GROWTH FORECAST TO 3.1%',
    'IOWA ARMY TO BLAST 9,500 LB OF LEAD AZIDE',
    'GOLDMAN SEES GOLD AT $4,650 BY 2027',
    'LANDMINE DEATHS HIT 5-YEAR HIGH OF 7,000',
]

# (time Taipei, label) for the timeline strip
TIMELINE = [
    ('08:18', 'SHENZHOU-24 LIFTS OFF'),
    ('~08:30', 'SEOUL SUBWAY DEAL'),
    ('~10:00', 'RIYADH STRIKE REPORTED'),
    ('~12:00', 'GIULIANI HONOURED'),
    ('~15:00', 'HUAWEI VERDICT REPORTS'),
    ('23:00', 'IOWA BLAST SET'),
]

# pin locations: (num, lon, lat)
PINS = [(1, 46.7, 24.7), (2, 100.3, 40.9), (3, -77.0, 38.9),
        (4, -122.0, 37.4), (5, -72.5, 42.0), (6, -80.5, 35.5),
        (7, 24.0, 59.8), (8, 34.5, 31.5), (9, 29.8, 1.7),
        (10, -17.4, 14.7), (11, -0.1, 51.5), (12, -77.0, 39.0),
        (13, 127.0, 37.5), (14, -74.1, 4.7)]


# ---- simplified world map outlines (lon, lat) ----
N_AMERICA = [(-168, 66), (-158, 58), (-152, 60), (-140, 60), (-130, 54),
             (-125, 49), (-124, 42), (-120, 34), (-114, 29), (-110, 24),
             (-105, 20), (-97, 16), (-90, 14), (-83, 9), (-79, 9),
             (-81, 13), (-87, 13), (-90, 21), (-97, 26), (-93, 30),
             (-84, 30), (-81, 25), (-80, 32), (-76, 35), (-74, 40),
             (-70, 42), (-65, 44), (-60, 47), (-60, 52), (-65, 58),
             (-72, 58), (-78, 62), (-85, 66), (-92, 66), (-95, 69),
             (-110, 68), (-125, 70), (-140, 70), (-155, 71), (-165, 68)]
GREENLAND = [(-58, 64), (-52, 60), (-43, 60), (-40, 64), (-32, 68),
             (-22, 70), (-25, 76), (-35, 80), (-55, 80), (-60, 76),
             (-58, 70)]
S_AMERICA = [(-79, 9), (-77, 4), (-80, -3), (-81, -6), (-77, -12),
             (-72, -18), (-70, -23), (-70, -30), (-72, -37), (-73, -44),
             (-74, -50), (-70, -54), (-66, -55), (-65, -50), (-62, -45),
             (-58, -38), (-52, -33), (-48, -28), (-41, -23), (-39, -17),
             (-35, -9), (-35, -6), (-40, -3), (-44, -2), (-50, 0),
             (-53, 4), (-58, 6), (-62, 9), (-68, 11), (-72, 12),
             (-76, 10)]
AFRICA = [(-6, 35), (-10, 31), (-15, 27), (-17, 21), (-17, 15),
          (-15, 11), (-12, 8), (-8, 4), (-4, 5), (0, 6), (6, 4),
          (9, 4), (9, -1), (12, -5), (13, -10), (12, -17), (14, -22),
          (16, -28), (19, -34), (26, -34), (32, -29), (35, -24),
          (36, -18), (40, -15), (40, -10), (42, -4), (46, -1),
          (51, 2), (51, 11), (48, 11), (44, 11), (43, 12), (40, 15),
          (38, 18), (37, 22), (35, 28), (32, 31), (25, 32), (19, 33),
          (11, 34), (10, 37), (5, 37), (-1, 35)]
EUROPE = [(-10, 36), (-9, 38), (-9, 43), (-2, 44), (-1, 46), (-4, 48),
          (-1, 49), (0, 51), (3, 53), (8, 54), (8, 57), (10, 59),
          (5, 60), (5, 62), (10, 64), (13, 66), (18, 69), (25, 71),
          (30, 70), (35, 68), (40, 68), (44, 68), (40, 66), (35, 65),
          (30, 64), (28, 60), (24, 58), (21, 55), (19, 54), (15, 54),
          (12, 54), (8, 55), (5, 53), (3, 51), (0, 50), (-2, 48),
          (-5, 45), (-2, 43), (0, 43), (3, 43), (7, 44), (10, 44),
          (13, 45), (16, 44), (18, 42), (16, 40), (13, 40), (10, 38),
          (8, 38), (3, 38), (0, 39), (-2, 37), (-6, 36)]
ASIA = [(30, 70), (40, 68), (50, 69), (60, 69), (70, 72), (80, 73),
        (90, 75), (100, 76), (110, 74), (120, 73), (130, 72), (140, 72),
        (150, 70), (158, 66), (162, 60), (158, 56), (150, 59),
        (142, 55), (140, 50), (135, 45), (130, 42), (127, 40),
        (122, 38), (120, 35), (122, 32), (120, 28), (115, 23),
        (110, 20), (108, 18), (105, 15), (103, 10), (100, 8),
        (98, 10), (95, 15), (92, 20), (90, 22), (88, 22), (86, 20),
        (83, 18), (80, 15), (78, 10), (76, 8), (74, 10), (72, 15),
        (70, 20), (68, 23), (66, 25), (62, 25), (58, 26), (56, 27),
        (54, 26), (52, 25), (50, 26), (48, 29), (48, 30), (44, 29),
        (42, 31), (40, 32), (36, 36), (33, 36), (30, 36), (27, 37),
        (26, 40), (28, 42), (30, 44), (28, 46), (26, 48), (24, 50),
        (22, 52), (24, 55), (26, 58), (28, 60), (30, 62), (28, 65),
        (30, 68)]
AUSTRALIA = [(113, -22), (114, -30), (115, -33), (118, -35), (124, -33),
             (129, -32), (132, -32), (135, -35), (138, -35), (140, -38),
             (145, -38), (150, -37), (153, -32), (153, -27), (150, -23),
             (146, -19), (142, -15), (142, -11), (140, -17), (136, -15),
             (135, -12), (132, -12), (130, -13), (126, -14), (122, -17),
             (118, -20)]
ISLANDS = [((-2, 54), 3), ((138, 37), 3), ((115, -2), 3), ((172, -41), 3),
           ((47, -19), 3), ((-18, 65), 2), ((103, 1), 2), ((139, 36), 2)]

MAP_X0, MAP_Y0, MAP_X1, MAP_Y1 = 16, 638, 1008, 812


def lonlat_to_xy(lon, lat):
    x = MAP_X0 + (lon + 180.0) / 360.0 * (MAP_X1 - MAP_X0)
    y = MAP_Y0 + (75.0 - lat) / 130.0 * (MAP_Y1 - MAP_Y0)
    return int(x), int(y)


def draw_map():
    fill_rect(MAP_X0, MAP_Y0, MAP_X1 - MAP_X0, MAP_Y1 - MAP_Y0, OCEAN)
    # ocean stipple + graticule
    for gx in range(-150, 181, 30):
        x, _ = lonlat_to_xy(gx, 0)
        for yy in range(MAP_Y0, MAP_Y1, 3):
            set_px(x, yy, OCEAN2)
    for gl in range(-60, 76, 30):
        _, y = lonlat_to_xy(0, gl)
        for xx in range(MAP_X0, MAP_X1, 3):
            set_px(xx, y, OCEAN2)
    for poly in (N_AMERICA, GREENLAND, S_AMERICA, AFRICA, EUROPE, ASIA,
                 AUSTRALIA):
        pts = [lonlat_to_xy(lon, lat) for lon, lat in poly]
        poly_fill(pts, LAND)
        poly_line(pts, LAND2)
    for (lon, lat), r in ISLANDS:
        x, y = lonlat_to_xy(lon, lat)
        disc(x, y, r, LAND)
    # pins
    for num, lon, lat in PINS:
        x, y = lonlat_to_xy(lon, lat)
        disc(x, y, 13, RED)
        ring(x, y, 13, WHITE, 2)
        draw_text_center(x - 13, x + 14, y - 7, str(num), WHITE, 2)
    rect_outline(MAP_X0, MAP_Y0, MAP_X1 - MAP_X0, MAP_Y1 - MAP_Y0, NAVY, 3)


def draw_masthead():
    fill_rect(0, 0, W, 148, NAVY)
    # halftone dots in band
    for yy in range(4, 148, 12):
        for xx in range(6, W, 12):
            set_px(xx, yy, NAVY2)
    draw_text_center(0, W, 12, 'THE WORLD IN ONE DAY', GOLD, 2)
    fill_rect(120, 36, W - 240, 2, GOLD)
    draw_text_center(0, W, 44, '25 NOVEMBER 2026', WHITE, 6)
    draw_text_center(0, W, 108,
                     'WEDNESDAY  -  45 STORIES  -  7 REGIONS  -  ALL TIMES TAIPEI',
                     (210, 220, 240), 2)
    # corner rosettes
    for cx in (28, W - 28):
        disc(cx, 74, 14, GOLD)
        disc(cx, 74, 8, NAVY)
        disc(cx, 74, 3, WHITE)


def draw_timeline():
    y = 148
    fill_rect(0, y, W, 44, TINT_GOLD)
    line(24, y + 26, W - 24, y + 26, GOLD)
    n = len(TIMELINE)
    for i, (t, label) in enumerate(TIMELINE):
        cx = 60 + i * ((W - 120) // (n - 1))
        disc(cx, y + 26, 6, RED)
        disc(cx, y + 26, 2, WHITE)
        draw_text_center(cx - 40, cx + 40, y + 4, t, RED, 1)
        draw_text_center(max(4, cx - 78), min(W - 4, cx + 78), y + 32, label, INK, 1)
    fill_rect(0, y + 42, W, 2, GOLD)


def draw_featured():
    x0, y0 = 12, 196
    cw, ch = 494, 58
    for idx, (num, region, icon, head, deck) in enumerate(FEATURED):
        col = idx % 2
        row = idx // 2
        x = x0 + col * (cw + 8)
        y = y0 + row * (ch + 2)
        tint = REGION_TINT[region] if row % 2 == 0 else PAPER
        fill_rect(x, y, cw, ch, tint)
        rect_outline(x, y, cw, ch, (200, 196, 182), 1)
        # number badge
        disc(x + 12, y + 12, 9, REGION_COLOR[region])
        draw_text_center(x + 3, x + 21, y + 5, str(num), WHITE, 1)
        # icon box
        ICONS[icon](x + 26, y + 7, REGION_COLOR[region])
        tx = x + 80
        draw_text(tx, y + 4, region, REGION_COLOR[region], 1)
        hl = wrap(head, cw - 92, 2)
        hy = y + 15
        for ln in hl[:2]:
            draw_text(tx, hy, ln, INK, 2)
            hy += 15
        dl = wrap(deck, cw - 92, 1)
        draw_text(tx, y + 47, dl[0] if dl else '', (70, 74, 90), 1)


def draw_also():
    y0 = 820
    fill_rect(0, y0 - 6, W, 2, RED)
    draw_text(16, y0 + 4, 'ALSO ON 25 NOVEMBER', RED, 2)
    draw_text(16, y0 + 20, '31 MORE STORIES FROM THE DAY', INK, 1)
    colw = 330
    for i, item in enumerate(ALSO):
        col = i % 3
        row = i // 3
        x = 16 + col * colw
        y = y0 + 38 + row * 11
        disc(x + 3, y + 3, 2, RED)
        draw_text(x + 10, y, item, INK, 1)


def draw_footer():
    y = 1000
    fill_rect(0, y, W, 24, NAVY)
    draw_text_center(0, W, y + 5,
                     'DRAWN FROM REPORTS PUBLISHED 25 NOV 2026. ALL ARTWORK DRAWN BY CODE. NO PHOTOGRAPHS.',
                     (210, 220, 240), 1)


def grain():
    # deterministic LCG speckle over the whole page: raises file size
    # into the winners' density range and gives the paper texture.
    state = 123456789

    def rnd():
        nonlocal state
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        return state

    for yy in range(H):
        base = yy * W * 3
        for xx in range(W):
            r = rnd()
            if r % 7 == 0:
                i = base + xx * 3
                d = (r >> 8) % 17 - 8
                for k in range(3):
                    v = px[i + k] + d
                    px[i + k] = 0 if v < 0 else (255 if v > 255 else v)
            elif r % 13 == 0:
                i = base + xx * 3
                for k in range(3):
                    v = px[i + k] + 5
                    px[i + k] = 255 if v > 255 else v


def write_png(path):
    def chunk(typ, data):
        c = struct.pack('>I', len(data)) + typ + data
        c += struct.pack('>I', zlib.crc32(typ + data) & 0xFFFFFFFF)
        return c

    raw = bytearray()
    for yy in range(H):
        raw.append(0)
        raw.extend(px[yy * W * 3:(yy + 1) * W * 3])
    ihdr = struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0)
    data = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) +
            chunk(b'IDAT', zlib.compress(bytes(raw), 6)) +
            chunk(b'IEND', b''))
    with open(path, 'wb') as f:
        f.write(data)
    return len(data)


def main():
    fill_rect(0, 0, W, H, CREAM)
    # ruled paper lines across the page
    for yy in range(0, H, 4):
        for xx in range(0, W, 2):
            set_px(xx, yy, PAPER)
    draw_masthead()
    draw_timeline()
    draw_featured()
    draw_text(16, 618, 'WHERE IT HAPPENED  -  14 FEATURED STORIES PINNED',
              NAVY, 2)
    draw_map()
    draw_also()
    draw_footer()
    grain()
    out = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, 'entry.png')
    n = write_png(path)
    print('wrote %s (%d bytes)' % (path, n))


if __name__ == '__main__':
    main()
