"""Builds the sample reels in assets/videos from the scene lists below.

Requires ffmpeg, Pillow, edge-tts and the Inter font (FONT_DIR, static TTF files).
Usage: FONT_DIR=/path/to/inter/extras/ttf python3 tools/make_reels.py [name ...]
"""
import asyncio
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import edge_tts
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "videos"
LOGO = Path(__file__).resolve().parent / "medelit-logo.png"
FONT_DIR = Path(os.environ.get("FONT_DIR", "/tmp/fonts/inter/extras/ttf"))
VOICE = "ru-RU-SvetlanaNeural"
W, H, FPS = 1080, 1920, 30
X0, MAXW = 84, 912
LABEL = "Информация носит рекламный характер"

BG = (242, 250, 245)
MINT = (221, 244, 226)
PEACH = (252, 244, 230)
GREEN = (0, 129, 55)
ORANGE = (225, 119, 17)
INK = (22, 37, 29)
MUTED = (62, 77, 70)
WHITE = (255, 255, 255)

REELS = {
    "densitometriya": {
        "accent": GREEN,
        "scenes": [
            {"label": "20 октября · день остеопороза", "title": "Как проверить плотность костей?",
             "voice": ["Как проверить плотность костей?"]},
            {"label": "Что это", "title": "Ультразвуковая денситометрия",
             "sub": "Измеряет минеральную плотность костной ткани",
             "voice": ["С помощью ультразвуковой денситометрии. Она измеряет минеральную плотность костной ткани."]},
            {"label": "Как проходит", "title": "10–15 минут",
             "chips": ["Безболезненно", "Без лучевой нагрузки", "Быстрый результат"],
             "voice": ["Это десять–пятнадцать минут, без боли и без лучевой нагрузки."],
             "cap": ["Это 10–15 минут, без боли и без лучевой нагрузки."]},
            {"label": "Подготовка", "title": "Без особой подготовки",
             "items": ["За сутки не принимать препараты кальция", "Сказать врачу о возможной беременности"],
             "voice": ["Специальной подготовки не нужно. За сутки не принимайте препараты кальция и предупредите врача о возможной беременности."]},
            {"label": "Стоимость", "title": "15 BYN", "sub": "Результат обсудите с врачом",
             "voice": ["Стоимость — пятнадцать рублей. Результат обсудите с врачом."],
             "cap": ["Стоимость — 15 рублей. Результат обсудите с врачом."]},
            {"label": "Запись", "title": "+375 29 566 80 80", "one_line": True,
             "lines": ["Онлайн — на medelit.by", "Гродно, ул. Большая Троицкая, 40А"],
             "voice": ["Запись на сайте или по телефону. «Медэлит», Большая Троицкая, сорок А.", LABEL],
             "cap": ["Запись на сайте или по телефону. «Медэлит», Большая Троицкая, 40А.", LABEL],
             "final": True},
        ],
    },
    "mammolog-chast-1": {
        "accent": ORANGE,
        "scenes": [
            {"label": "Розовый октябрь", "title": "Идёте к маммологу?",
             "sub": "3 вопроса перед приёмом · часть 1",
             "voice": ["Собираетесь к маммологу? Три вопроса до приёма. Часть первая."]},
            {"label": "Вопрос 1", "title": "Что входит в консультацию?",
             "items": ["Расспрос о здоровье и наследственности", "Осмотр молочных желёз и лимфоузлов",
                       "При необходимости — направление на УЗИ или маммографию"],
             "voice": ["Что входит в консультацию? Расспрос о здоровье и наследственности, осмотр молочных желёз и лимфоузлов. Если нужно — направление на УЗИ или маммографию."]},
            {"label": "Вопрос 2", "title": "Что взять с собой?",
             "items": ["Результаты УЗИ и маммографии, если есть", "Медицинские документы и список лекарств",
                       "Свободную одежду — для осмотра"],
             "voice": ["Что взять с собой? Результаты прошлых УЗИ и маммографии, документы и список лекарств. И свободную одежду."]},
            {"label": "Вопрос 3", "title": "Когда делать УЗИ груди?",
             "items": ["На 5–11 день цикла", "В менопаузе — в любой удобный день"],
             "voice": ["Когда делать УЗИ груди? С пятого по одиннадцатый день цикла. В менопаузе — в любой удобный день."],
             "cap": ["Когда делать УЗИ груди? С 5 по 11 день цикла. В менопаузе — в любой удобный день."]},
            {"label": "Часть 2", "title": "Ваши вопросы — врачу",
             "sub": "Присылайте в директ, ответим в следующем ролике",
             "voice": ["Свои вопросы присылайте в директ — врач ответит во второй части."]},
            {"label": "Запись", "title": "+375 29 566 80 80", "one_line": True,
             "lines": ["Консультация онколога-маммолога — от 43 BYN", "Онлайн — на medelit.by",
                       "Гродно, ул. Большая Троицкая, 40А"],
             "voice": ["Консультация — от сорока трёх рублей. Запись на сайте или по телефону.", LABEL],
             "cap": ["Консультация — от 43 рублей. Запись на сайте или по телефону.", LABEL],
             "final": True},
        ],
    },
    "otkrytie-v-7": {
        "accent": GREEN,
        "scenes": [
            {"clock": True, "title": "6:55", "title_end": "7:00", "sub": "По будням открываемся в 7:00",
             "voice": ["Без пяти семь. По будням мы открываемся в семь утра."]},
            {"label": "Чтобы успеть до работы", "title": "Пн–Пт 7:00–21:00",
             "items": ["Сб 8:00–18:00", "Вс 8:00–16:00"],
             "voice": ["С понедельника по пятницу — с семи до девяти вечера. В субботу — с восьми до шести, в воскресенье — с восьми до четырёх."],
             "cap": ["Пн–Пт — с 7:00 до 21:00. В субботу — с 8:00 до 18:00, в воскресенье — с 8:00 до 16:00."]},
            {"label": "Онлайн-запись", "title": "medelit.by",
             "items": ["Выберите дату и время", "СМС с подтверждением", "Напоминание за сутки"],
             "voice": ["Записаться можно на сайте: выберите свободное время — придёт СМС с подтверждением, а за сутки — напоминание."]},
            {"label": "Или по телефону", "title": "+375 29 566 80 80", "one_line": True,
             "sub": "Администратор подскажет, что взять с собой и как подготовиться",
             "voice": ["Или по телефону — администратор подскажет, что взять с собой и как подготовиться."]},
            {"label": "Медицинский центр «Медэлит»", "title": "Большая Троицкая, 40А", "one_line": True,
             "lines": ["Гродно · medelit.by"],
             "voice": ["Медицинский центр «Медэлит», Большая Троицкая, сорок А.", LABEL],
             "cap": ["Медицинский центр «Медэлит», Большая Троицкая, 40А.", LABEL],
             "final": True},
        ],
    },
}


def font(weight, size, display=False):
    family = "InterDisplay" if display else "Inter"
    return ImageFont.truetype(str(FONT_DIR / f"{family}-{weight}.ttf"), size)


PROBE = ImageDraw.Draw(Image.new("RGBA", (1, 1)))


def wrap(text, fnt, width):
    lines, cur = [], ""
    for word in text.split():
        test = f"{cur} {word}".strip()
        if PROBE.textlength(test, font=fnt) <= width or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def text_block(text, fnt, color, width=MAXW, spacing=1.12, tracking=0):
    lines = wrap(text, fnt, width)
    asc, desc = fnt.getmetrics()
    lh = int((asc + desc) * spacing)
    img = Image.new("RGBA", (width + 40, lh * len(lines) + desc), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        if tracking:
            x = 0
            for ch in line:
                d.text((x, i * lh), ch, font=fnt, fill=color)
                x += d.textlength(ch, font=fnt) + tracking
        else:
            d.text((0, i * lh), line, font=fnt, fill=color)
    return img


def card(text, fnt, accent, pad=(34, 24)):
    lines = wrap(text, fnt, MAXW - 2 * pad[0] - 28)
    asc, desc = fnt.getmetrics()
    lh = int((asc + desc) * 1.1)
    h = lh * len(lines) + 2 * pad[1]
    img = Image.new("RGBA", (MAXW, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, MAXW - 1, h - 1), radius=26, fill=WHITE + (255,), outline=(213, 232, 219, 255), width=2)
    d.rounded_rectangle((0, 18, 8, h - 18), radius=4, fill=accent + (255,))
    for i, line in enumerate(lines):
        d.text((pad[0] + 10, pad[1] + i * lh), line, font=fnt, fill=INK + (255,))
    return img


def chips(texts, fnt, accent):
    asc, desc = fnt.getmetrics()
    ch, gap, padx = asc + desc + 30, 16, 28
    rows, row, x = [], [], 0
    for t in texts:
        w = int(PROBE.textlength(t, font=fnt)) + 2 * padx
        if row and x + w > MAXW:
            rows.append(row)
            row, x = [], 0
        row.append((t, w))
        x += w + gap
    rows.append(row)
    img = Image.new("RGBA", (MAXW, len(rows) * (ch + gap)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    tint = tuple(int(255 - (255 - c) * 0.14) for c in accent)
    for r, items in enumerate(rows):
        x = 0
        for t, w in items:
            y = r * (ch + gap)
            d.rounded_rectangle((x, y, x + w, y + ch), radius=ch // 2, fill=tint + (255,), outline=accent + (90,), width=2)
            d.text((x + padx, y + 15), t, font=fnt, fill=accent + (255,))
            x += w + gap
    return img


def contact_card(scene, title_font):
    pad = 56
    inner = MAXW - 2 * pad
    parts = [text_block(scene["label"].upper(), font("SemiBold", 32), WHITE + (190,), width=inner, tracking=3),
             text_block(scene["title"], title_font, WHITE + (255,), width=inner, spacing=1.04)]
    parts += [text_block(line, font("Medium", 44), WHITE + (235,), width=inner) for line in scene.get("lines", [])]
    gaps = [14, 30] + [12] * len(scene.get("lines", []))
    h = 2 * pad + sum(p.height for p in parts) + sum(gaps[:len(parts) - 1])
    img = Image.new("RGBA", (MAXW, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, MAXW - 1, h - 1), radius=36, fill=GREEN + (255,))
    y = pad
    for part, gap in zip(parts, gaps):
        img.alpha_composite(part, (pad, y))
        y += part.height + gap
    return img


def clock(minute):
    size = 300
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = size / 2
    d.ellipse((6, 6, size - 6, size - 6), fill=WHITE + (255,), outline=GREEN + (255,), width=8)
    for i in range(12):
        a = math.radians(i * 30)
        r1, r2 = c - 30, c - 18
        d.line((c + r1 * math.sin(a), c - r1 * math.cos(a), c + r2 * math.sin(a), c - r2 * math.cos(a)),
               fill=MUTED + (160,), width=5)
    hour_a = math.radians((6 + minute / 60) * 30)
    min_a = math.radians(minute * 6)
    d.line((c, c, c + 72 * math.sin(hour_a), c - 72 * math.cos(hour_a)), fill=INK + (255,), width=12)
    d.line((c, c, c + 112 * math.sin(min_a), c - 112 * math.cos(min_a)), fill=ORANGE + (255,), width=7)
    d.ellipse((c - 12, c - 12, c + 12, c + 12), fill=INK + (255,))
    return img


def scene_elements(scene, accent):
    size = 104 if len(scene["title"]) < 18 else 92
    while scene.get("one_line") and PROBE.textlength(scene["title"], font=font("Bold", size, display=True)) > MAXW - 120:
        size -= 4
    title_font = font("Bold", size, display=True)
    if scene.get("final"):
        return [("img", contact_card(scene, title_font))]
    els = []
    if scene.get("clock"):
        els.append(("clock", None))
    if scene.get("label"):
        els.append(("img", text_block(scene["label"].upper(), font("SemiBold", 34), accent + (255,), tracking=3)))
    els.append(("title", text_block(scene["title"], title_font, INK + (255,), spacing=1.04)))
    if scene.get("title_end"):
        scene["_title_end"] = text_block(scene["title_end"], title_font, INK + (255,), spacing=1.04)
    if scene.get("sub"):
        els.append(("img", text_block(scene["sub"], font("Medium", 46), MUTED + (255,))))
    if scene.get("chips"):
        els.append(("img", chips(scene["chips"], font("SemiBold", 40), accent)))
    for item in scene.get("items", []):
        els.append(("img", card(item, font("Medium", 42), accent)))
    return els


def layout(els):
    gaps = {"clock": 44, "title": 30}
    heights = [300 if kind == "clock" else img.height for kind, img in els]
    total = sum(heights) + sum(gaps.get(k, 26) for k, _ in els[:-1])
    y = int(H * 0.47 - total / 2)
    ys = []
    for (kind, _), h in zip(els, heights):
        ys.append(y)
        y += h + gaps.get(kind, 26)
    return ys


def background(now):
    img = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(img)
    cx, cy = 1000 + 18 * math.sin(now / 5), 120 + 22 * math.cos(now / 6)
    d.ellipse((cx - 330, cy - 330, cx + 330, cy + 330), fill=MINT + (255,))
    cx, cy = 40 + 16 * math.cos(now / 7), 1700 + 20 * math.sin(now / 5)
    d.ellipse((cx - 300, cy - 300, cx + 300, cy + 300), fill=PEACH + (255,))
    return img


def header():
    logo = Image.open(LOGO).convert("RGBA")
    logo = logo.resize((int(logo.width * 1.3), int(logo.height * 1.3)), Image.LANCZOS)
    bar_w, bar_h = 230, 8
    img = Image.new("RGBA", (W, logo.height + 26 + bar_h), (0, 0, 0, 0))
    img.alpha_composite(logo, (X0 - 8, 0))
    bar = Image.new("RGBA", (bar_w, bar_h))
    for x in range(bar_w):
        t = x / (bar_w - 1)
        col = tuple(int(o + (g - o) * t) for o, g in zip((230, 136, 38), (8, 131, 53)))
        ImageDraw.Draw(bar).line((x, 0, x, bar_h), fill=col + (255,))
    mask = Image.new("L", (bar_w, bar_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, bar_w - 1, bar_h - 1), radius=4, fill=255)
    bar.putalpha(mask)
    img.alpha_composite(bar, (X0, logo.height + 26))
    return img


def footer():
    fnt = font("SemiBold", 32)
    w = int(PROBE.textlength(LABEL, font=fnt)) + 64
    img = Image.new("RGBA", (w, 70), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, 69), radius=35, fill=WHITE + (220,), outline=(213, 232, 219, 255), width=2)
    d.text((32, 15), LABEL, font=fnt, fill=MUTED + (255,))
    return img


def fade(img, op):
    if op >= 0.999:
        return img
    out = img.copy()
    out.putalpha(img.getchannel("A").point(lambda v: int(v * op)))
    return out


def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


async def tts(text, path):
    await edge_tts.Communicate(text, VOICE, rate="+8%").save(str(path))


def duration(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)])
    return float(json.loads(out)["format"]["duration"])


def vtt_time(t):
    m, s = divmod(t, 60)
    return f"{int(m):02d}:{s:06.3f}"


def build(name, spec, tmp):
    accent, scenes = spec["accent"], spec["scenes"]
    clips, cues, t = [], [], 0.0
    for si, scene in enumerate(scenes):
        start = t
        offset = 0.25 if si else 0.1
        for vi, text in enumerate(scene["voice"]):
            raw, path = tmp / f"{name}_{si}_{vi}.mp3", tmp / f"{name}_{si}_{vi}.wav"
            asyncio.run(tts(text, raw))
            trim = "silenceremove=start_periods=1:start_threshold=-50dB"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af",
                            f"{trim},areverse,{trim},areverse,apad=pad_dur=0.05", str(path)], check=True)
            d = duration(path)
            clips.append((path, start + offset))
            cap = scene.get("cap", scene["voice"])[vi]
            cues.append((start + offset, start + offset + d, cap))
            offset += d + 0.3
        scene["_start"], scene["_dur"] = start, max(offset + 0.35, 2.4)
        t += scene["_dur"]
    total = t + 0.6

    inputs, filters = [], []
    for i, (path, at) in enumerate(clips):
        inputs += ["-i", str(path)]
        filters.append(f"[{i}:a]aresample=48000,adelay={int(at * 1000)}:all=1[a{i}]")
    mix = "".join(f"[a{i}]" for i in range(len(clips)))
    filters.append(f"{mix}amix=inputs={len(clips)}:normalize=0,apad,atrim=0:{total:.3f}[aout]")
    audio = tmp / f"{name}.m4a"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filters),
                    "-map", "[aout]", "-c:a", "aac", "-b:a", "128k", str(audio)], check=True)

    head, foot = header(), footer()
    for scene in scenes:
        scene["_els"] = scene_elements(scene, accent)
        scene["_ys"] = layout(scene["_els"])

    video = OUT / f"{name}.mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-i", str(audio), "-map", "0:v", "-map", "1:a",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "24", "-pix_fmt", "yuv420p",
                            "-c:a", "copy", "-shortest", "-movflags", "+faststart", str(video)],
                           stdin=subprocess.PIPE)
    poster = None
    for f in range(int(total * FPS)):
        now = f / FPS
        frame = background(now)
        frame.alpha_composite(head, (0, 200))
        frame.alpha_composite(foot, ((W - foot.width) // 2, 1500))
        scene = next((s for s in reversed(scenes) if now >= s["_start"]), scenes[0])
        local = now - scene["_start"]
        out_op = 1.0 if scene.get("final") else ease((scene["_dur"] - local) / 0.25)
        for i, ((kind, img), y) in enumerate(zip(scene["_els"], scene["_ys"])):
            p = ease((local - 0.08 * i) / 0.45)
            op = p * out_op
            if op <= 0.01:
                continue
            dy = int((1 - p) * 40)
            if kind == "clock":
                img = clock(55 + 5 * ease((local - scene["_dur"] + 1.8) / 1.0))
            if kind == "title" and scene.get("_title_end") is not None and local > scene["_dur"] - 0.85:
                img = scene["_title_end"]
            frame.alpha_composite(fade(img, op), (X0, y + dy))
        if poster is None and scene is scenes[0] and local > 1.2:
            poster = frame.convert("RGB")
        enc.stdin.write(frame.convert("RGB").tobytes())
    enc.stdin.close()
    enc.wait()
    if enc.returncode:
        raise SystemExit(f"ffmpeg failed for {name}")

    poster.resize((540, 960), Image.LANCZOS).save(OUT / f"{name}.jpg", quality=84)
    lines = ["WEBVTT", ""]
    for a, b, text in cues:
        lines += [f"{vtt_time(a)} --> {vtt_time(b)}", text, ""]
    (OUT / f"{name}.vtt").write_text("\n".join(lines), encoding="utf-8")
    print(f"{name}: {total:.1f} s")


def main():
    names = sys.argv[1:] or list(REELS)
    with tempfile.TemporaryDirectory() as d:
        for name in names:
            build(name, REELS[name], Path(d))


if __name__ == "__main__":
    main()
