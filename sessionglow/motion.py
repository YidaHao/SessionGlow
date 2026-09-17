"""Continuous, interruptible animation parameters independent of Qt."""

import math


# RGB, waveform amplitude, flow speed, jitter, particles, liquid, brightness
TARGETS = {
    "unknown": (98, 126, 145, 0, 0, 0, 0, 0, 0.3),
    "running": (66, 170, 255, 0.48, 0.55, 0.04, 0.85, 0, 1),
    "failed": (255, 80, 103, 0, 0, 0.085, 0.65, 0, 0.85),
    "done": (53, 221, 160, 0, 0.24, 0, 0, 1, 0.85),
    "waiting": (255, 196, 66, 0.48, 0.65, 0.46, 0.95, 0, 1),
}


class Motion:
    def __init__(self, now=0, duration=0.8):
        self.state = "unknown"
        self.start = self.target = TARGETS["unknown"]
        self.since = now
        self.duration = duration
        self.phase = 0.0
        self.travel = 0.0
        self.last = now

    def values(self, now):
        t = min(1, max(0, (now - self.since) / self.duration))
        if t == 1:
            return self.target
        blend = t * t * t * (t * (t * 6 - 15) + 10)  # C2 continuous easing.
        return tuple(a + (b - a) * blend for a, b in zip(self.start, self.target))

    def change(self, state, now):
        if state == self.state:
            return
        self.start = self.values(now)
        self.target = TARGETS.get(state, TARGETS["unknown"])
        self.state = state
        self.since = now

    def advance(self, now):
        dt = max(0, min(0.1, now - self.last))
        self.last = now
        values = self.values(now)
        self.phase += dt * values[4] * 1.8
        self.travel += dt * values[4] * 0.085
        return values


def wave(x, phase, clock, amplitude, jitter):
    smooth = math.sin(x * math.tau * 1.6 - phase) * 0.73 + math.sin(x * math.tau * 3.3 + phase * 0.7) * 0.27
    # Deterministic continuous noise, not a new random path every frame.
    noise = math.sin(x * 57 + clock * 19) * 0.5 + math.sin(x * 109 - clock * 27) * 0.3 + math.sin(x * 31 + clock * 11) * 0.2
    envelope = math.sin(math.pi * x) ** 0.4
    return (smooth * amplitude + noise * jitter * 0.32) * envelope
