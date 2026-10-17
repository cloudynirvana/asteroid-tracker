"""Synthesize the soundtrack (104.5 s, stereo) and mix the voiceover over it.

All of the music is generated here from sines and filtered noise: no samples,
so there is nothing to license. The voiceover lines are vo/line_N.wav, made by
voiceover.py, and the music ducks under them.
"""
import wave
from pathlib import Path

import numpy as np

SR, DUR = 44100, 104.5
t = np.arange(int(SR * DUR)) / SR
L, R = np.zeros_like(t), np.zeros_like(t)
rng = np.random.default_rng(7)
note = lambda m: 440 * 2 ** ((m - 69) / 12)

# One line per scene; keep in step with SCENES in src/Film.jsx.
VO_START = [1.2, 10.2, 21.7, 35.2, 47.2, 62.2, 79.2, 95.2]
SCENE_EDGE = [9, 20.5, 34, 46, 61, 78, 94]


def env(start, attack, decay):
    x = np.clip(t - start, 0, None)
    return np.where(t < start, 0, np.where(x < attack, x / max(attack, 1e-6), np.exp(-(x - attack) / decay)))


def lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same")


def band(x, lo, hi):
    return lowpass(x, lo) - lowpass(x, hi)


# A slow minor pad: Am - F - C - Em, two bars each, repeating.
chords = [[45, 57, 60, 64], [41, 53, 57, 60], [48, 55, 60, 64], [40, 52, 55, 59]]
for i in range(9):
    s, e = i * 12.0, i * 12.0 + 13.0
    w = np.clip((t - s) / 2.8, 0, 1) * np.clip((e - t) / 2.8, 0, 1)
    for m in chords[i % 4]:
        f = note(m)
        L += 0.05 * w * np.sin(2 * np.pi * f * t)
        R += 0.05 * w * np.sin(2 * np.pi * f * 1.004 * t + 0.9)
        L += 0.014 * w * np.sin(2 * np.pi * f * 2 * t)

# A tracking tick, all the way through: this is a thing that is watching.
noise = rng.standard_normal(len(t))
tick_src = band(noise, 4, 22)
for b in np.arange(0.6, DUR - 1, 0.75):
    e = env(b, 0.002, 0.045)
    L += 0.5 * e * tick_src
    R += 0.5 * e * np.roll(tick_src, 700)
    ping = 0.05 * env(b, 0.002, 0.18) * np.sin(2 * np.pi * note(84) * t)
    L += ping
    R += ping

# The year of approaches counting up: the ticks crowd together under scene two.
for b in np.arange(11.5, 19.8, 0.14):
    e = env(b, 0.001, 0.02)
    L += 0.22 * e * tick_src
    R += 0.22 * e * np.roll(tick_src, 400)

# A low pulse from the data scenes onward.
for b in np.arange(34.0, 94.0, 0.75):
    x = np.clip(t - b, 0, None)
    hit = 0.26 * env(b, 0.004, 0.1) * np.sin(2 * np.pi * (46 + 52 * np.exp(-x * 28)) * x)
    L += hit
    R += hit

# A whoosh into each new scene.
air = lowpass(noise, 40)
for s in SCENE_EDGE:
    w = np.exp(-((t - s + 0.35) / 0.3) ** 2)
    L += 0.4 * w * air
    R += 0.4 * w * np.roll(air, 520)

# The closest approach arrives as one long, close pass: a rising then falling sweep.
x = np.clip(t - 22.4, 0, 5.0)
freq = 70 + 210 * np.sin(np.pi * np.clip(x / 5.0, 0, 1))
sweep = 0.16 * ((t > 22.4) & (t < 27.4)) * np.sin(2 * np.pi * np.cumsum(freq) / SR)
L += sweep
R += np.roll(sweep, 420)

# The hazardous flag: a cluster of warning pings, deliberately not alarming.
for i, b in enumerate([63.0, 63.9, 64.8]):
    ping = 0.13 * env(b, 0.004, 0.8) * np.sin(2 * np.pi * note(76 + 4 * i) * t)
    L += ping
    R += ping

# The honest ending: a deep open fifth under the last two scenes.
w = np.clip((t - 79) / 3, 0, 1) * np.clip((103 - t) / 4, 0, 1)
for m in (33, 40, 52):
    L += 0.045 * w * np.sin(2 * np.pi * note(m) * t)
    R += 0.045 * w * np.sin(2 * np.pi * note(m) * 1.003 * t)

# Voiceover, with the music ducked underneath it.
vo = np.zeros_like(t)
for i, start in enumerate(VO_START, 1):
    f = Path(f"vo/line_{i}.wav")
    if not f.exists():
        continue
    with wave.open(str(f)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), "<i2") / 32768
        x = np.interp(np.arange(0, len(x), w.getframerate() / SR), np.arange(len(x)), x)
    a = int(start * SR)
    vo[a:a + len(x)] += x[:len(vo) - a]
speaking = lowpass((np.abs(vo) > 0.01).astype(float), int(0.4 * SR))
duck = 1 - 0.68 * np.clip(speaking * 3, 0, 1)
peak = max(np.abs(L).max(), np.abs(R).max())
L = L / peak * 0.6 * duck + 0.92 * vo
R = R / peak * 0.6 * duck + 0.92 * vo

fade = np.clip(t / 1.2, 0, 1) * np.clip((DUR - t) / 2.5, 0, 1)
st = np.stack([L, R], 1) * fade[:, None]
st = st / np.abs(st).max() * 0.86
Path("public").mkdir(exist_ok=True)
with wave.open("public/soundtrack.wav", "wb") as f:
    f.setnchannels(2)
    f.setsampwidth(2)
    f.setframerate(SR)
    f.writeframes((st * 32767).astype("<i2").tobytes())
print("public/soundtrack.wav")
