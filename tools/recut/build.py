"""Re-cut the clinic's own TikTok videos into short Reels.

Sources: yt-dlp --impersonate chrome -o "%(id)s.%(ext)s" https://www.tiktok.com/@medelit_grodno/video/<id>
into $TIKTOK_DIR. Cut points come from faster-whisper word timestamps.
Usage: python3 tools/recut/build.py preview|full [key ...]
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TT = os.environ.get("TIKTOK_DIR", "/tmp/tt")
OUT = os.path.join(HERE, "..", "..", "assets", "videos")
W = "/tmp/recut/work"
OVERLAY = os.path.join(HERE, "overlay.js")

REELS = {
    "statiny-chast-1": {
        "src": "7668231376663088404",
        "segs": [(16.66, 22.98, 1.0), (23.52, 25.45, 1.10), (39.10, 51.60, 1.0)],
        "end": 3.6,
        "tag": "Кардиолог отвечает · часть 1",
        "title": "Надо ли принимать статины?",
        "name": {"role": "Врач-кардиолог", "who": "Митягина Елена Николаевна", "at": 8.5, "len": 3.6, "top": 1450},
        "endcard": {"eye": "Часть 2", "title": "«У статинов же куча побочек?»",
                    "sub": "Кардиолог разбирает возражения, которые слышит на приёме."},
        "cues": [(16.66, 19.4, "Доктор, а мне уже надо принимать статины?"),
                 (19.4, 22.98, "Доктор, я так боюсь начинать принимать статины."),
                 (23.52, 25.45, "Хочу сказать вам самое главное."),
                 (39.10, 44.1, "Для того чтобы понять, принимать статины либо не принимать,"),
                 (44.1, 49.0, "надо прежде всего рассчитать ваш индивидуальный сердечно-сосудистый риск."),
                 (49.0, 51.60, "И в этом вам поможет врач-кардиолог.")],
    },
    "nevrolog-37-let": {
        "src": "7691609025615498517",
        "segs": [(18.70, 24.55, 1.0), (0.0, 9.98, 1.10), (35.05, 39.30, 1.0)],
        "end": 3.8,
        "tag": "Знакомьтесь: наш невролог",
        "big": "37 лет",
        "title": "заведовала отделением для пациентов с нарушением мозгового кровообращения",
        "name": {"role": "Врач-невролог", "who": "Филина Нина Александровна", "at": 6.1, "len": 0, "top": 1450},
        "endcard": {"eye": "29 октября — День борьбы с инсультом", "title": "Какой вопрос задать неврологу?",
                    "sub": "Пишите в комментариях — врач ответит в следующем ролике."},
        "cues": [(18.70, 24.55, "…в течение 37 лет заведовала отделением для больных с нарушением мозгового кровообращения."),
                 (0.0, 4.4, "Я Филина Нина Александровна, врач-невролог,"),
                 (4.4, 9.98, "работаю в настоящее время неврологом в медицинском центре «Медэлит»."),
                 (35.05, 39.30, "Я жду вас на приём в наш медицинский центр.")],
    },
    "endokrinolog-yod": {
        "src": "7669709656515759381",
        "segs": [(12.78, 16.45, 1.0), (37.55, 40.45, 1.10, 0.0), (60.70, 71.38, 1.0), (71.45, 82.35, 1.10)],
        "end": 3.6,
        "tag": "Эндокринолог отвечает",
        "title": "Йод нужен всем?",
        "name": {"role": "Врач-эндокринолог", "who": "Елисеева Людмила Леонидовна", "at": 0.5, "len": 3.0, "top": 430},
        "endcard": {"eye": "Вопросы эндокринологу", "title": "Что ещё разобрать про щитовидную железу?",
                    "sub": "Пишите в комментариях — врач ответит в следующем ролике."},
        "cues": [(12.78, 16.45, "Йод — это строительный материал для щитовидной железы."),
                 (37.55, 40.45, "Меньше йода — меньше гормонов."),
                 (60.70, 64.3, "А при аутоиммунных заболеваниях, при аутоиммунном тиреоидите,"),
                 (64.3, 67.55, "он может активизировать аутоиммунные процессы,"),
                 (67.55, 71.38, "может привести к увеличению и росту узловых образований."),
                 (71.45, 76.1, "Если у вас появились вопросы по поводу приёма препаратов йода,"),
                 (76.1, 78.0, "а также нужна консультация врача-эндокринолога,"),
                 (78.0, 82.35, "мы рады вас видеть в нашем медицинском центре «Медэлит».")],
    },
}

ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p", "-r", "30",
       "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]


def run(cmd):
    subprocess.run(cmd, check=True)


def vf(z, y=0.3):
    w, h = round(1080 * z / 2) * 2, round(1920 * z / 2) * 2
    return "scale=%d:%d:flags=lanczos,crop=1080:1920:(iw-1080)/2:(ih-1920)*%s,setsar=1,fps=30" % (w, h, y)


def fmt(t):
    return "%02d:%06.3f" % (int(t // 60), t % 60)


def build(key, stage):
    r = REELS[key]
    src = "%s/%s.mp4" % (TT, r["src"])
    wd = "%s/%s" % (W, key)
    os.makedirs(wd, exist_ok=True)
    starts, t = [], 0.0
    for seg in r["segs"]:
        a, b = seg[0], seg[1]
        starts.append(t)
        t += b - a
    end_at = round(t, 3)
    duration = round(t + r["end"], 3)
    n = r["name"]
    cfg = {"key": key, "duration": duration, "endAt": end_at, "tag": r["tag"], "title": r["title"], "big": r.get("big"),
           "name": {"role": n["role"], "who": n["who"], "a": n["at"], "b": n["at"] + n["len"], "top": n["top"]},
           "endcard": r["endcard"]}
    json.dump(cfg, open(wd + "/cfg.json", "w"), ensure_ascii=False)
    if stage == "preview":
        times = ",".join(str(x) for x in [0.5, n["at"] + 1.0] + [s + 0.6 for s in starts] + [end_at + 1.2])
        run(["node", OVERLAY, wd + "/cfg.json", times])
    parts = []
    for i, seg in enumerate(r["segs"]):
        a, b, z = seg[:3]
        p = "%s/seg%d.mp4" % (wd, i)
        d = b - a
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(a), "-t", "%.3f" % d, "-i", src, "-vf", vf(z, *seg[3:]),
             "-af", "aresample=48000,afade=t=in:d=0.03,afade=t=out:st=%.3f:d=0.06" % (d - 0.06), *ENC, "-t", "%.3f" % d, p])
        parts.append(p)
    a, b, z = r["segs"][-1][:3]
    still = wd + "/still.png"
    run(["ffmpeg", "-v", "error", "-y", "-ss", "%.3f" % (b - 0.05), "-i", src, "-frames:v", "1", "-vf", vf(z), still])
    endp = wd + "/end.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", str(r["end"]), "-i", still, "-f", "lavfi", "-t", str(r["end"]),
         "-i", "anullsrc=r=48000:cl=stereo", "-vf", "boxblur=18:2,eq=brightness=-0.06:saturation=0.9,fps=30,format=yuv420p",
         *ENC, "-shortest", endp])
    parts.append(endp)
    lst = wd + "/list.txt"
    open(lst, "w").write("".join("file '%s'\n" % p for p in parts))
    base = wd + "/base.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", base])
    if stage == "preview":
        for x in [0.5, n["at"] + 1.0] + [s + 0.6 for s in starts] + [end_at + 1.2]:
            run(["ffmpeg", "-v", "error", "-y", "-ss", str(x), "-i", base, "-i", "/tmp/recut/pv/%s/%.2f.png" % (key, x),
                 "-filter_complex", "[0:v][1:v]overlay=0:0,scale=540:960", "-frames:v", "1", "%s/pv-%05.2f.jpg" % (wd, x)])
        return
    run(["node", OVERLAY, wd + "/cfg.json", "full"])
    out = "%s/%s.mp4" % (OUT, key)
    run(["ffmpeg", "-v", "error", "-y", "-i", base, "-framerate", "30", "-i", "/tmp/recut/ov/%s/%%04d.png" % key,
         "-filter_complex", "[0:v][1:v]overlay=0:0:eof_action=pass,format=yuv420p[v];[0:a]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]",
         "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-profile:v", "high", "-preset", "slow", "-crf", "23", "-maxrate", "1800k", "-bufsize", "3600k",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-movflags", "+faststart", "-t", str(duration), out])
    run(["ffmpeg", "-v", "error", "-y", "-ss", "0.6", "-i", out, "-frames:v", "1", "-vf", "scale=540:960", "-q:v", "3",
         "%s/%s.jpg" % (OUT, key)])
    lines = ["WEBVTT", ""]
    for ca, cb, text in r["cues"]:
        for seg, s in zip(r["segs"], starts):
            a, b = seg[0], seg[1]
            if a - 0.01 <= ca and cb <= b + 0.01:
                lines += ["%s --> %s" % (fmt(s + ca - a), fmt(s + cb - a)), text, ""]
                break
        else:
            raise SystemExit("cue outside segments: " + text)
    lines += ["%s --> %s" % (fmt(end_at), fmt(duration)), r["endcard"]["title"] + " Информация носит рекламный характер.", ""]
    open("%s/%s.vtt" % (OUT, key), "w").write("\n".join(lines))
    print("built", key, duration)


if __name__ == "__main__":
    stage = sys.argv[1]
    for k in (sys.argv[2:] or REELS):
        build(k, stage)
