"""Music + SFX for the reel, synthesised with numpy only.

Usage: python3 sound.py out.wav            (music + SFX)
       python3 sound.py out.wav --sfx-only (SFX only, for adding a trending track in Instagram)
100 BPM, beat = 0.6 s; all cues follow the timeline in reel.html.
"""
import sys, wave
import numpy as np

SR = 48000
DUR = 24.6
N = int(DUR * SR)
BEAT = 0.6
rng = np.random.default_rng(11)
L = np.zeros(N); R = np.zeros(N)


def add(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N:
        return
    sig = sig[: N - i] * gain
    l = np.cos((pan + 1) * np.pi / 4); r = np.sin((pan + 1) * np.pi / 4)
    L[i:i + len(sig)] += sig * l * 1.414
    R[i:i + len(sig)] += sig * r * 1.414


def fft_filter(x, lo=None, hi=None):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    m = np.ones_like(f)
    if lo: m *= 1 / (1 + (lo / np.maximum(f, 1)) ** 4)
    if hi: m *= 1 / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * m, len(x))


def env(n, a=0.002, d=0.2):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)


def hz(note):  # 'D4' style
    names = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}
    n, o = note[:-1], int(note[-1])
    return 440 * 2 ** ((names[n] + 12 * (o + 1) - 69) / 12)


def pluck(f, dur=1.2, bright=0.5, decay=0.996):
    n = int(dur * SR); P = int(SR / f)
    y = np.zeros(n)
    y[:P] = fft_filter(rng.uniform(-1, 1, P + 64), hi=1500 + 6000 * bright)[:P]
    for i in range(P + 1, n):
        y[i] = decay * 0.5 * (y[i - P] + y[i - P - 1])
    y += 0.25 * y * np.sin(2 * np.pi * f * 2 * np.arange(n) / SR)  # komuz-like metallic edge
    return y * env(n, 0.001, dur * 0.5)


def kick(g=1.0):
    n = int(0.45 * SR); t = np.arange(n) / SR
    f = 45 + 80 * np.exp(-t * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9) * g


def noise_burst(dur, lo, hi, a=0.003, d=0.08):
    n = int(dur * SR)
    return fft_filter(rng.uniform(-1, 1, n), lo, hi) * env(n, a, d)


def pad(freqs, dur, cutoff=1800):
    n = int(dur * SR); t = np.arange(n) / SR; y = np.zeros(n)
    for f in freqs:
        for det in (-0.12, 0.0, 0.11):
            ff = f * 2 ** (det / 12)
            y += 2 * ((t * ff) % 1) - 1
    y = fft_filter(y / (len(freqs) * 3), hi=cutoff)
    a = np.minimum(1, t / 0.35) * np.minimum(1, (dur - t) / 0.35)
    return y * a


def bell(f, dur=2.2):
    n = int(dur * SR); t = np.arange(n) / SR; y = np.zeros(n)
    for r, g, d in ((1, 1, 1.4), (2.76, .5, .7), (5.4, .25, .35), (8.93, .12, .2)):
        y += g * np.sin(2 * np.pi * f * r * t) * np.exp(-t / d)
    return y * np.minimum(1, t / 0.002)


def whoosh(dur=0.7, rise=True):
    n = int(dur * SR); t = np.arange(n) / SR
    base = rng.uniform(-1, 1, n)
    lo_band = fft_filter(base, 200, 900); hi_band = fft_filter(base, 1500, 7000)
    x = t / dur if rise else 1 - t / dur
    y = lo_band * (1 - x) + hi_band * x
    return y * np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2


def ping(f, d=0.35):
    n = int(d * 2 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * np.exp(-t / d * 3) * np.minimum(1, t / 0.001)


def pop(f0=900, f1=280):
    n = int(0.12 * SR); t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 60)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 30)


def stamp():
    return kick(1.0) * 0.9 + np.pad(noise_burst(0.08, 100, 2500, 0.001, 0.02), (0, int(0.37 * SR)))


# ------------------------------------------------------------------ music
def music():
    # A: 0-12 s, D minor, muted plucks + soft pulse
    patA = ['D4', 'A4', 'F4', 'A4', 'G4', 'A4', 'F4', 'C5']
    for bar in range(4):
        t0 = bar * 4 * BEAT
        for k, nte in enumerate(patA):
            add(pluck(hz(nte), 0.9, 0.25), t0 + k * BEAT / 2, 0.16 + 0.03 * (k % 2 == 0), pan=-0.25 + 0.5 * (k % 2))
        for b in range(4):
            add(pluck(hz('D2') if bar % 2 == 0 or b < 2 else hz('C2'), 0.9, 0.15, 0.993), t0 + b * BEAT, 0.30)
            if b % 2 == 0:
                add(kick(0.6), t0 + b * BEAT, 0.38)
        if bar >= 2:
            for e in range(8):
                add(noise_burst(0.04, 6000, None, 0.001, 0.012), t0 + e * BEAT / 2 + BEAT / 4, 0.05, pan=0.3)
    add(pad([hz('D3'), hz('A3')], 9.6, 900), 0.0, 0.10)

    # B: 12-24 s, warm: F - C - Dm - Bb - F, brighter plucks, four-on-floor
    chords = [('F', ['F3', 'A3', 'C4'], ['C5', 'A4', 'F5', 'A4', 'G5', 'F5', 'C5', 'A4']),
              ('C', ['C3', 'G3', 'E4'], ['E5', 'C5', 'G5', 'C5', 'A5', 'G5', 'E5', 'D5']),
              ('Dm', ['D3', 'A3', 'F4'], ['F5', 'D5', 'A5', 'D5', 'C6', 'A5', 'F5', 'E5']),
              ('Bb', ['Bb2', 'F3', 'D4'], ['D5', 'Bb4', 'F5', 'Bb4', 'G5', 'F5', 'D5', 'C5']),
              ('F', ['F3', 'A3', 'C4'], ['C5', 'F5', 'A5', 'C6', 'A5', 'F5', 'G5', 'A5'])]
    for i, (_, ch, mel) in enumerate(chords):
        t0 = 9.6 + i * 4 * BEAT
        add(pad([hz(n) for n in ch], 4 * BEAT + 0.3, 2400), t0, 0.16)
        for k, nte in enumerate(mel):
            add(pluck(hz(nte), 1.0, 0.65), t0 + k * BEAT / 2, 0.17, pan=-0.3 + 0.6 * (k % 2))
        root = ch[0][:-1] + '2'
        for b in range(4):
            add(pluck(hz(root), 0.8, 0.2, 0.993), t0 + b * BEAT, 0.32)
            add(kick(0.8), t0 + b * BEAT, 0.40)
            if b % 2 == 1:
                add(noise_burst(0.18, 900, 5000, 0.001, 0.05), t0 + b * BEAT, 0.20)  # clap
            for s in range(4):
                add(noise_burst(0.05, 5000, None, 0.001, 0.015), t0 + b * BEAT + s * BEAT / 4, 0.05 + 0.03 * (s == 2), pan=0.35)

    # C: 21.6-24.6 s, back to the question, sparse, resolve
    for k, nte in enumerate(['D4', 'A4', 'F4', 'A4', 'G4', 'E4', 'F4', 'E4', 'D4']):
        add(pluck(hz(nte), 1.2, 0.3), 21.6 + k * BEAT / 2, 0.17)
    add(pad([hz('D3'), hz('F3'), hz('A3')], 3.0, 1200), 21.6, 0.13)
    add(kick(0.7), 21.6, 0.4); add(kick(0.7), 22.8, 0.35)



# ---- voice-sync warp: same monotone cubic as reel.html, inverted numerically
import json, os
_W = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'warp.json')))['anchors']
def _old_of_new(x):
    xs = [a[0] for a in _W]; ys = [a[1] for a in _W]; n = len(xs)
    d = [(ys[i+1]-ys[i])/(xs[i+1]-xs[i]) for i in range(n-1)]
    m = [d[0]] + [0 if d[i-1]*d[i] <= 0 else 3*(d[i-1]+d[i])/((2*d[i]+d[i-1])/d[i-1]+(d[i]+2*d[i-1])/d[i]) for i in range(1, n-1)] + [d[-1]]
    if x <= xs[0]: return ys[0]
    if x >= xs[-1]: return ys[-1]
    i = 0
    while x > xs[i+1]: i += 1
    h = xs[i+1]-xs[i]; u = (x-xs[i])/h
    return (2*u**3-3*u**2+1)*ys[i] + (u**3-2*u**2+u)*h*m[i] + (-2*u**3+3*u**2)*ys[i+1] + (u**3-u**2)*h*m[i+1]
_grid = np.arange(0, _W[-1][0] + 1e-9, 0.001)
_oldg = np.array([_old_of_new(x) for x in _grid])
def warp(t_old):
    return float(np.interp(t_old, _oldg, _grid))
def addw(sig, t_old, gain=1.0, pan=0.0):
    add(sig, warp(t_old), gain, pan)

# ------------------------------------------------------------------ SFX
def sfx():
    # 1: cards falling (paper swishes), hook punch
    r = np.random.default_rng(5)
    for t in np.arange(0.0, 3.3, 0.22):
        addw(noise_burst(0.25, 1800, 9000, 0.02, 0.06), t + r.uniform(0, 0.08), 0.10, pan=r.uniform(-.7, .7))
    addw(kick(1.0), 2.1, 0.7); addw(noise_burst(0.5, 60, 400, 0.002, 0.2), 2.1, 0.25)
    # 2: transition, card flip, price stamp
    addw(whoosh(0.6), 3.3, 0.30)
    addw(noise_burst(0.12, 2500, 9000, 0.001, 0.03), 4.25, 0.25, pan=0.2)
    addw(stamp(), 4.8, 0.55)
    # 3: grid counter ticks, red stamp
    addw(whoosh(0.5), 5.8, 0.22)
    for t in np.arange(6.3, 7.7, 0.07):
        addw(ping(2400 + 400 * ((t * 10) % 2), 0.03), t, 0.05, pan=r.uniform(-.5, .5))
    addw(stamp(), 7.8, 0.75)
    # 4: houses pop, bundle hops
    for i in range(5):
        addw(pop(700 + 60 * i, 260), 8.7 + i * 0.12, 0.18, pan=-0.5 + 0.25 * i)
    def draw_at(t):
        x = np.clip((t - 8.7) / 2.9, 0, 1)
        return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
    ts = np.arange(8.7, 11.6, 0.005)
    for f in (0.2, 0.38, 0.55, 0.72, 0.92):
        t = ts[np.argmin(np.abs([draw_at(x) - f for x in ts]))]
        addw(noise_burst(0.07, 300, 2500, 0.001, 0.02), t, 0.22)
        addw(ping(hz('A5'), 0.08), t, 0.06)
    # 5: thread + phone + 2 500 chime
    addw(whoosh(0.9, rise=False), 11.6, 0.25)
    addw(bell(hz('A5')), 12.6, 0.22); addw(bell(hz('E6'), 1.6), 12.62, 0.10)
    # 6: link chip, 300 pings
    addw(whoosh(0.5), 14.4, 0.35)
    pent = [hz(n) for n in ('F5', 'G5', 'A5', 'C6', 'D6', 'F6', 'G6', 'A6')]
    for k in range(70):
        t = 15.2 + 1.7 * (k / 70) ** 0.8
        addw(ping(pent[r.integers(len(pent))], 0.12), t, 0.035 + 0.02 * r.random(), pan=r.uniform(-.8, .8))
    # 7: bars, difference hit, shimmer
    addw(noise_burst(0.3, 80, 600, 0.002, 0.1), 17.45, 0.35); addw(noise_burst(0.3, 80, 600, 0.002, 0.1), 17.65, 0.3)
    addw(kick(1.0), 18.4, 0.7); addw(bell(hz('F5'), 1.2), 18.4, 0.10)
    for k in range(12):
        addw(ping(hz('C6') * 2 ** (k / 12 * 1.0), 0.15), 19.4 + k * 0.05, 0.05, pan=-.5 + k / 12)
    # 8: letters pop, bubble, typing
    for i in range(5):
        addw(pop(1100 - 80 * i, 320), 21.2 + i * 0.13, 0.22)
    addw(pop(600, 200), 22.0, 0.2)
    for t in (22.45, 22.6, 22.75):
        addw(noise_burst(0.025, 3000, None, 0.0005, 0.006), t, 0.3)
    # 9: back to the question
    addw(whoosh(0.6), 23.7, 0.3)
    for t in np.arange(24.0, 26.0, 0.25):
        addw(noise_burst(0.25, 1800, 9000, 0.02, 0.06), t + r.uniform(0, 0.08), 0.08, pan=r.uniform(-.7, .7))
    addw(kick(1.0), 24.6, 0.6)


sfx_only = '--sfx-only' in sys.argv
if not sfx_only:
    music()
sfx()
mix = np.stack([L, R], 1)
mix = fft_filter(mix[:, 0], 30, 16000)[:, None] * [1, 0] + fft_filter(mix[:, 1], 30, 16000)[:, None] * [0, 1]
fade = np.ones(N); nf = int(0.25 * SR); fade[-nf:] = np.linspace(1, 0, nf)
mix *= fade[:, None]
mix = np.tanh(mix * 1.1) / np.tanh(1.1)  # gentle soft clip
mix *= 0.89 / np.max(np.abs(mix))
out = sys.argv[1]
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
print('wrote', out, 'peak', np.max(np.abs(mix)), 'rms dBFS', 20 * np.log10(np.sqrt(np.mean(mix ** 2))))
