#!/usr/bin/env python3
"""The World in One Day - 24 November 2026.

Draws one deterministic 1024x1024 PNG summing up the world's news of
Tuesday 24 November 2026, reading the story data from stories.json next
to this file.

No network, no clock, no randomness: identical inputs always give
identical bytes. Run:  python3 main.py   (writes /output/entry.png)
or set OUTPUT_PATH to pick another destination.
"""

import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("OUTPUT_PATH", "/output/entry.png")

W, H = 1024, 1024
PAPER = (247, 241, 222)
INK = (25, 25, 25)
RED = (163, 22, 33)
NAVY = (31, 58, 95)
GREEN = (46, 107, 52)
AMBER = (150, 104, 0)
MUTED = (107, 99, 83)
LIGHT = (233, 226, 203)
SKY = (178, 205, 219)
LAND = (216, 196, 150)
RULE = (25, 25, 25)

TAG_FILL = {
    "CONFIRMED": NAVY,
    "OFFICIAL": GREEN,
    "REPORTED": AMBER,
    "FORECAST": MUTED,
}

SERIF = "DejaVuSerif.ttf"
SERIF_B = "DejaVuSerif-Bold.ttf"
SANS = "DejaVuSans.ttf"
SANS_B = "DejaVuSans-Bold.ttf"


def font(name, size):
    return ImageFont.truetype(os.path.join(HERE, "fonts", name), size)


def wrap(text, fnt, max_w, draw):
    """Greedy word wrap to lines no wider than max_w pixels."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit_lines(text, fnt, max_w, max_lines, draw):
    """Wrap text and clip to max_lines with an ellipsis if needed.

    The ellipsis always follows a whole word, never a chopped one.
    """
    lines = wrap(text, fnt, max_w, draw)
    if len(lines) <= max_lines:
        return lines
    lines = lines[:max_lines]
    while lines and draw.textlength(lines[-1] + "...", font=fnt) > max_w:
        words = lines[-1].split()
        if len(words) > 1:
            lines[-1] = " ".join(words[:-1])
        else:
            lines[-1] = lines[-1][:-1]
    lines[-1] = lines[-1].rstrip() + "..."
    return lines


def one_line(text, fnt, max_w, draw):
    """Clip text to a single fitting line with an ellipsis if needed.

    Truncation always ends at a word boundary, never mid-word.
    """
    if draw.textlength(text, font=fnt) <= max_w:
        return text
    while text and draw.textlength(text + "...", font=fnt) > max_w:
        text = text[:-1]
    text = text.rstrip()
    if " " in text:
        text = text.rsplit(" ", 1)[0]
    return text + "..."


def chip(draw, x, y, tag):
    """Draw a verification-tag chip; return its pixel width."""
    fnt = font(SANS_B, 9)
    tw = draw.textlength(tag, font=fnt)
    w = int(tw) + 10
    h = 15
    draw.rounded_rectangle([x, y, x + w, y + h], radius=3,
                           fill=TAG_FILL.get(tag, MUTED))
    draw.text((x + 5, y + 2), tag, font=fnt, fill=(255, 255, 255))
    return w


def source_line(draw, x, y, source, max_w, size=9, prefix="Source: "):
    fnt = font(SANS, size)
    draw.text((x, y), one_line(prefix + source, fnt, max_w, draw),
              font=fnt, fill=MUTED)


def draw_art(draw, kind, box, accent):
    """Small flat vector drawing inside box (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = box
    cx = (x0 + x1) // 2
    cy = (y0 + y1) // 2
    w = x1 - x0
    if kind == "tanker":
        draw.rectangle([x0 + 4, cy + 2, x1 - 4, cy + 16], fill=INK)
        draw.rectangle([x0 + 14, cy - 12, x0 + 34, cy + 2], fill=accent)
        draw.rectangle([x0 + 40, cy - 6, x0 + 52, cy + 2], fill=accent)
        draw.line([x0 + 44, cy - 18, x0 + 44, cy - 6], fill=INK, width=2)
        for bx in (x0 + 2, x0 + 30, x0 + 58):
            draw.arc([bx, cy + 16, bx + 24, cy + 26], 0, 180, fill=SKY, width=2)
    elif kind == "flag":
        draw.line([x0 + 8, y0 + 4, x0 + 8, y1 - 4], fill=INK, width=3)
        draw.polygon([(x0 + 8, y0 + 4), (x1 - 6, y0 + 12),
                      (x0 + 8, y0 + 22)], fill=accent)
        draw.line([x0 + 4, y1 - 4, x0 + w - 4, y1 - 4], fill=INK, width=2)
    elif kind == "chart":
        draw.line([x0 + 8, y1 - 8, x1 - 4, y1 - 8], fill=INK, width=2)
        draw.line([x0 + 8, y1 - 8, x0 + 8, y0 + 6], fill=INK, width=2)
        bw = (w - 24) // 4
        heights = [10, 18, 14, 26]
        for i, hh in enumerate(heights):
            bx = x0 + 12 + i * (bw + 2)
            draw.rectangle([bx, y1 - 8 - hh, bx + bw, y1 - 8],
                           fill=accent if i == 3 else NAVY)
    elif kind == "building":
        draw.rectangle([x0 + 10, y0 + 10, x1 - 10, y1 - 6], fill=NAVY)
        for r in range(3):
            for c in range(3):
                # Keep every window inside the art box: the old 14 px
                # spacing pushed the right column past x1 (and the card border).
                wx = x0 + 13 + c * 11
                wy = y0 + 15 + r * 9
                draw.rectangle([wx, wy, wx + 6, wy + 6], fill=PAPER)
        draw.rectangle([x0 + 4, y1 - 6, x1 - 4, y1 - 2], fill=INK)
    elif kind == "satellite":
        draw.rectangle([cx - 12, cy - 8, cx + 12, cy + 8], fill=NAVY)
        draw.rectangle([x0 + 2, cy - 12, cx - 14, cy + 12], fill=accent)
        draw.rectangle([cx + 14, cy - 12, x1 - 2, cy + 12], fill=accent)
        draw.line([cx, cy + 8, cx + 10, cy + 18], fill=INK, width=2)
        draw.ellipse([cx + 6, cy + 14, cx + 16, cy + 24], outline=INK, width=2)
    elif kind == "ship":
        # All coordinates stay inside the art box (x0..x1, y0..y1):
        # the old second container ended 12 px past x1, crossing the card border.
        draw.polygon([(x0 + 6, cy + 4), (x1 - 6, cy + 4),
                      (x1 - 16, cy + 16), (x0 + 16, cy + 16)], fill=INK)
        draw.rectangle([x0 + 12, cy - 12, x0 + 26, cy + 4], fill=accent)
        draw.rectangle([x0 + 28, cy - 8, x0 + 40, cy + 4], fill=NAVY)
        for bx in (x0 + 2, x0 + 20):
            draw.arc([bx, cy + 16, bx + 18, cy + 26], 0, 180, fill=SKY, width=2)
    elif kind == "globe":
        draw.ellipse([x0 + 6, y0 + 4, x1 - 6, y1 - 4], outline=NAVY, width=2)
        draw.ellipse([cx - 12, y0 + 4, cx + 12, y1 - 4], outline=NAVY, width=1)
        draw.line([x0 + 6, cy, x1 - 6, cy], fill=NAVY, width=1)
        draw.arc([x0 + 6, y0 + 4, x1 - 6, y1 - 4], 200, 340, fill=accent, width=3)
    elif kind == "ball":
        draw.ellipse([x0 + 8, y0 + 4, x1 - 8, y1 - 4], outline=INK, width=2)
        draw.polygon([(cx, cy - 8), (cx + 8, cy - 2), (cx + 5, cy + 8),
                      (cx - 5, cy + 8), (cx - 8, cy - 2)], fill=accent)
        draw.line([cx, y0 + 4, cx, cy - 8], fill=INK, width=1)
        draw.line([x0 + 8, cy - 2, cx - 8, cy - 2], fill=INK, width=1)
        draw.line([x1 - 8, cy - 2, cx + 8, cy - 2], fill=INK, width=1)
    elif kind == "coin":
        draw.ellipse([x0 + 8, y0 + 4, x1 - 8, y1 - 4], outline=AMBER, width=3)
        draw.ellipse([x0 + 14, y0 + 10, x1 - 14, y1 - 10],
                     outline=AMBER, width=1)
        draw.text((cx - 6, cy - 11), "$", font=font(SANS_B, 18), fill=AMBER)
    else:
        draw.ellipse([x0 + 8, y0 + 6, x1 - 8, y1 - 6], outline=accent, width=3)


def draw_map(draw, box, regions):
    """Schematic world map with a numbered pin per region."""
    regions = {k.upper(): v for k, v in regions.items()}
    x0, y0, x1, y1 = box
    draw.rounded_rectangle([x0, y0, x1, y1], radius=6, fill=SKY)
    mw, mh = x1 - x0, y1 - y0

    def blob(cx, cy, rx, ry):
        draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=LAND)

    # Rough continents, schematic only (labelled as such on the image).
    blob(x0 + mw * 0.16, y0 + mh * 0.42, mw * 0.09, mh * 0.24)  # N America
    blob(x0 + mw * 0.30, y0 + mh * 0.72, mw * 0.06, mh * 0.16)  # S America
    blob(x0 + mw * 0.50, y0 + mh * 0.34, mw * 0.06, mh * 0.16)  # Europe
    blob(x0 + mw * 0.53, y0 + mh * 0.62, mw * 0.09, mh * 0.22)  # Africa
    blob(x0 + mw * 0.66, y0 + mh * 0.44, mw * 0.05, mh * 0.14)  # Mid East
    blob(x0 + mw * 0.80, y0 + mh * 0.42, mw * 0.12, mh * 0.26)  # Asia
    blob(x0 + mw * 0.88, y0 + mh * 0.78, mw * 0.05, mh * 0.10)  # Oceania
    pins = [
        ("N. AMERICA", 0.16, 0.42), ("S. AMERICA", 0.30, 0.72),
        ("EUROPE", 0.50, 0.34), ("AFRICA", 0.53, 0.62),
        ("MIDDLE EAST", 0.66, 0.44), ("ASIA", 0.80, 0.42),
        ("OCEANIA", 0.88, 0.78),
    ]
    fnt = font(SANS_B, 9)
    for name, fx, fy in pins:
        px = int(x0 + mw * fx)
        py = int(y0 + mh * fy)
        label = str(regions.get(name, 0))
        draw.ellipse([px - 8, py - 8, px + 8, py + 8], fill=RED)
        tw = draw.textlength(label, font=fnt)
        draw.text((px - tw / 2, py - 5), label, font=fnt, fill=(255, 255, 255))
    draw.text((x0 + 8, y1 - 14), "SCHEMATIC MAP — NOT TO SCALE",
              font=font(SANS, 8), fill=MUTED)


def main():
    with open(os.path.join(HERE, "stories.json"), encoding="utf-8") as fh:
        data = json.load(fh)

    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)
    mx = 28  # side margin
    cw = W - 2 * mx  # content width
    y = 22

    # ---- Masthead ----
    tf = font(SERIF_B, 52)
    tw = draw.textlength(data["title"], font=tf)
    draw.text(((W - tw) / 2, y), data["title"], font=tf, fill=INK)
    y += 58
    sub = "%s  •  %d STORIES  •  8 REGIONS  •  ONE DAY" % (
        data["date"], data["total_stories"])
    sf = font(SANS_B, 14)
    tw = draw.textlength(sub, font=sf)
    draw.text(((W - tw) / 2, y), sub, font=sf, fill=RED)
    y += 18
    draw.line([mx, y, W - mx, y], fill=RULE, width=2)
    y += 4
    draw.line([mx, y, W - mx, y], fill=RULE, width=1)
    y += 8

    # ---- THE DAY IN UTC ----
    draw.text((mx, y), "THE DAY IN UTC",
              font=font(SANS_B, 13), fill=NAVY)
    draw.text((W - mx - 210, y), "ALL TIMES UTC, 24 NOV 2026",
              font=font(SANS, 10), fill=MUTED)
    y += 18
    col_w = cw / 7
    for i, ev in enumerate(data["utc_events"]):
        x = mx + i * col_w
        draw.text((x + 2, y), ev["time"], font=font(SANS_B, 13), fill=RED)
        lines = fit_lines(ev["text"], font(SANS, 9), col_w - 8, 2, draw)
        ly = y + 16
        for ln in lines:
            draw.text((x + 2, ly), ln, font=font(SANS, 9), fill=INK)
            ly += 11
        if i:
            draw.line([x, y, x, y + 42], fill=MUTED, width=1)
    y += 46
    draw.line([mx, y, W - mx, y], fill=RULE, width=1)
    y += 6

    # ---- THE DAY IN NUMBERS ----
    draw.text((mx, y), "THE DAY IN NUMBERS",
              font=font(SANS_B, 13), fill=NAVY)
    y += 18
    col_w = cw / 6
    for i, num in enumerate(data["numbers"]):
        x = mx + i * col_w
        draw.text((x + 4, y), num["value"], font=font(SERIF_B, 22), fill=RED)
        lines = fit_lines(num["label"], font(SANS, 9), col_w - 10, 2, draw)
        ly = y + 26
        for ln in lines:
            draw.text((x + 4, ly), ln, font=font(SANS, 9), fill=INK)
            ly += 11
        if i:
            draw.line([x, y, x, y + 48], fill=MUTED, width=1)
    y += 50
    draw.line([mx, y, W - mx, y], fill=RULE, width=2)
    y += 6

    # ---- Lead card ----
    lead = data["lead"]
    art_w = 170
    draw.rectangle([mx, y, mx + art_w, y + 122], fill=LIGHT)
    draw_art(draw, lead["art"], (mx + 10, y + 14, mx + art_w - 10, y + 114), RED)
    tx = mx + art_w + 14
    twd = (W - mx) - tx
    draw.text((tx, y + 2), "LEAD  •  " + lead["region"],
              font=font(SANS_B, 11), fill=RED)
    hl = fit_lines(lead["headline"], font(SERIF_B, 27), twd, 2, draw)
    hy = y + 18
    for ln in hl:
        draw.text((tx, hy), ln, font=font(SERIF_B, 27), fill=INK)
        hy += 30
    sm = fit_lines(lead["summary"], font(SANS, 13), twd, 2, draw)
    sy = hy + 2
    for ln in sm:
        draw.text((tx, sy), ln, font=font(SANS, 13), fill=INK)
        sy += 16
    fy = sy + 2
    draw.text((tx, fy), one_line(lead["fact"], font(SANS, 10), twd, draw),
              font=font(SANS, 10), fill=MUTED)
    cw_chip = chip(draw, tx, fy + 15, lead["tag"])
    source_line(draw, tx + cw_chip + 8, fy + 17, lead["source"],
                twd - cw_chip - 8)
    draw.rectangle([mx, y, W - mx, y + 122], outline=RULE, width=1)
    y += 124

    # ---- Two big cards ----
    card_w = (cw - 12) // 2
    for i, card in enumerate(data["big"]):
        x = mx + i * (card_w + 12)
        draw.rectangle([x, y, x + card_w, y + 128], outline=RULE, width=1)
        aw = 84
        draw_art(draw, card["art"], (x + card_w - aw - 6, y + 8,
                                      x + card_w - 6, y + 62), NAVY)
        txw = card_w - aw - 18
        draw.text((x + 10, y + 6), card["region"],
                  font=font(SANS_B, 11), fill=RED)
        hl = fit_lines(card["headline"], font(SERIF_B, 19), txw, 2, draw)
        hy = y + 22
        for ln in hl:
            draw.text((x + 10, hy), ln, font=font(SERIF_B, 19), fill=INK)
            hy += 21
        sm = fit_lines(card["summary"], font(SANS, 11), card_w - 20, 2, draw)
        sy = hy + 2
        for ln in sm:
            draw.text((x + 10, sy), ln, font=font(SANS, 11), fill=INK)
            sy += 14
        draw.text((x + 10, y + 96),
                  one_line(card["fact"], font(SANS, 10), card_w - 20, draw),
                  font=font(SANS, 10), fill=MUTED)
        cw_chip = chip(draw, x + 10, y + 110, card["tag"])
        source_line(draw, x + 10 + cw_chip + 8, y + 112, card["source"],
                    card_w - cw_chip - 28)
    y += 130

    # ---- Ten small cards, 5 across x 2 rows ----
    cols, rows = 5, 2
    scw = (cw - 4 * 10) // cols
    sch = 108
    for idx, card in enumerate(data["small"]):
        r, c = divmod(idx, cols)
        x = mx + c * (scw + 10)
        yy = y + r * (sch + 8)
        draw.rectangle([x, yy, x + scw, yy + sch], outline=RULE, width=1)
        draw_art(draw, card["art"], (x + scw - 46, yy + 4, x + scw - 4, yy + 40),
                 NAVY)
        draw.text((x + 7, yy + 5), card["region"],
                  font=font(SANS_B, 9), fill=RED)
        hl = fit_lines(card["headline"], font(SANS_B, 11), scw - 52, 4, draw)
        hy = yy + 18
        for ln in hl:
            draw.text((x + 7, hy), ln, font=font(SANS_B, 11), fill=INK)
            hy += 13
        sm = fit_lines(card["summary"], font(SANS, 9), scw - 14, 2, draw)
        sy = yy + 62
        for ln in sm:
            draw.text((x + 7, sy), ln, font=font(SANS, 9), fill=MUTED)
            sy += 11
        cw_chip = chip(draw, x + 7, yy + sch - 19, card["tag"])
        source_line(draw, x + 7 + cw_chip + 6, yy + sch - 17, card["source"],
                    scw - cw_chip - 22, size=8, prefix="")
    y += rows * (sch + 8) + 4

    # ---- Map + region counts ----
    draw.text((mx, y), "WHERE IT HAPPENED",
              font=font(SANS_B, 13), fill=NAVY)
    y += 16
    map_h = 76
    map_w = int(cw * 0.62)
    draw_map(draw, (mx, y, mx + map_w, y + map_h), data["regions"])
    rx = mx + map_w + 14
    order = ["EUROPE", "ASIA", "MIDDLE EAST", "AFRICA",
             "N. AMERICA", "S. AMERICA", "OCEANIA", "WORLD"]
    rnorm = {k.upper(): v for k, v in data["regions"].items()}
    ry = y + 2
    for j in range(0, 8, 2):
        for k in (0, 1):
            name = order[j + k]
            xx = rx + k * 168
            draw.text((xx, ry), "%s %d" % (name, rnorm.get(name, 0)),
                      font=font(SANS_B, 11), fill=INK)
        ry += 18
    draw.text((rx, ry + 2), "Counts = stories per region.",
              font=font(SANS, 9), fill=MUTED)
    draw.text((rx, ry + 15), "Total 38 stories, numbered 1-38.",
              font=font(SANS, 9), fill=MUTED)
    y += map_h + 8

    # ---- ALSO ON ... list, 3 columns, items 14-38 ----
    draw.text((mx, y), "ALSO ON TUESDAY 24 NOVEMBER",
              font=font(SANS_B, 13), fill=NAVY)
    y += 16
    items = data["also"]
    per_col = 9
    col_w = cw // 3
    fnt = font(SANS, 10)
    tag_fnt = font(SANS_B, 8)
    for ci in range(3):
        chunk = items[ci * per_col:(ci + 1) * per_col]
        x = mx + ci * col_w
        ly = y
        for k, it in enumerate(chunk):
            num = 14 + ci * per_col + k
            prefix = "%d. " % num
            pw = draw.textlength(prefix, font=fnt)
            draw.text((x, ly), prefix, font=fnt, fill=RED)
            tag = it["tag"]
            tw = draw.textlength(tag, font=tag_fnt)
            avail = col_w - pw - tw - 14
            txt = one_line(it["text"], fnt, avail, draw)
            draw.text((x + pw, ly), txt, font=fnt, fill=INK)
            draw.text((x + col_w - tw - 4, ly + 1), tag,
                      font=tag_fnt, fill=TAG_FILL.get(tag, MUTED))
            ly += 12
    y += per_col * 12 + 2

    # ---- DATE CHECK + footer ----
    draw.line([mx, y, W - mx, y], fill=RULE, width=1)
    y += 4
    dc = ("DATE CHECK: Tuesday 24 November 2026. Every story here happened, or was "
          "first reported, on 24 Nov 2026 in some time zone. Monday's US market "
          "closes are not counted as Tuesday news.")
    lines = fit_lines(dc, font(SANS_B, 10), cw, 2, draw)
    for ln in lines:
        draw.text((mx, y), ln, font=font(SANS_B, 10), fill=RED)
        y += 12
    y += 2
    foot = ("CONFIRMED = reported as fact  •  OFFICIAL = stated by a government or the UN  •  "
            "REPORTED = a claim carried by outlets, not independently verified. "
            "Original drawings. Sources named on every story.")
    lines = fit_lines(foot, font(SANS, 9), cw, 2, draw)
    for ln in lines:
        draw.text((mx, y), ln, font=font(SANS, 9), fill=MUTED)
        y += 11

    if y > H - 8:
        print("WARNING: content overflows by %d px" % (y - (H - 8)),
              file=sys.stderr)

    out_dir = os.path.dirname(OUT)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    img.save(OUT, "PNG")
    print("wrote %s (%dx%d)" % (OUT, W, H))


if __name__ == "__main__":
    main()
