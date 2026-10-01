"""Filters (§9): SAO's one-euro filter for the per-frame solve, and the zero-phase Butterworth low-pass of the
post-bake smoothing.

One-euro (js/one_euro_filter.js, after Casiez et al.) is a low-pass whose cutoff rises with the signal's speed:

    alpha(fc) = 1 / (1 + fs / (2π fc))
    dx        = (x - x_prev) · fs, low-passed at d_cutoff
    fc        = min_cutoff + beta · |dx|
    y         = y_prev + alpha(fc) · (x - y_prev)

with x_prev the previous input and fs the sample rate. The first sample passes unchanged. Quaternions slerp, and
their derivative is the rotation vector per second (SAO slerps an extrapolated quaternion; the two agree for the
small steps between frames). SAO runs its filters at its video's frame rate, the bake at the scene's, so their
cutoffs mean the same in seconds. One difference from SAO's JavaScript: there a scalar sample of exactly 0
restarts the filter (it tests `!value`), so a fingertip shift released to 0 snaps; here 0 is an ordinary sample.

The solve iterates within a frame, so a frame's passes all filter from the state the previous frame left
(`FilterBank.apply`), and `FilterBank.commit` keeps the state of the last pass once the frame is solved.

SAO's parameters ([fs, min_cutoff, beta, d_cutoff, type] in min.js), as (min_cutoff, beta, d_cutoff):
- fingertip shift, magnets with fingertips (Tt, fingertip_filter [30, .5, .5, 1, 1]): (0.5, 0.5, 1);
- magnet pull, reference_point_filter (Tt, [30, .5, .5, 1, 3]): (0.5, 0.5, 1);
- rotation-based reference_point_filter (Tt, [30, .25, .25, .5, 1]): (0.25, 0.25, 0.5), on an angle;
- fretting wrist rotation (It, hand_rot_filter [30, 1, 1, 1, 4]): (1, 1, 1);
- arm IK target (jt, armIK [30, 1, 1/5, 1, 3]): (1, 0.2, 1); SAO runs it only in its hand-camera mode.
Lengths are filtered in SAO's arm space (MMD units of an avatar with SAO's reference arm), so beta keeps its
meaning on every character; the solver converts.
"""

import math
from dataclasses import dataclass

import numpy as np
from mathutils import Quaternion, Vector

SAO_FINGERTIP = (0.5, 0.5, 1.0)
SAO_PULL = (0.5, 0.5, 1.0)
SAO_ROTATION = (0.25, 0.25, 0.5)
SAO_WRIST = (1.0, 1.0, 1.0)
SAO_TARGET = (1.0, 0.2, 1.0)
KINDS = ('SCALAR', 'VECTOR', 'QUATERNION')


def alpha(cutoff, fs):
    """Smoothing factor of a first-order low-pass at `cutoff` Hz sampled at `fs` Hz."""
    tau = 1.0 / (2.0 * math.pi * max(cutoff, 1e-9))
    return 1.0 / (1.0 + tau * fs)


@dataclass(frozen=True)
class State:
    raw: object         # the last input
    value: object       # the last output
    speed: object       # the low-passed derivative (a number or a Vector)


def _zero(kind):
    return 0.0 if kind == 'SCALAR' else Vector((0.0, 0.0, 0.0))


def _derivative(kind, x, previous, fs):
    if kind == 'QUATERNION':
        step = (x @ previous.inverted()).normalized()
        if step.w < 0.0:
            step.negate()
        axis, angle = step.to_axis_angle()
        return axis * (angle * fs)
    return (x - previous) * fs


def _magnitude(kind, value):
    return abs(value) if kind == 'SCALAR' else value.length


class OneEuro:
    """A one-euro filter over one signal: 'SCALAR' (float), 'VECTOR' (Vector) or 'QUATERNION'."""

    def __init__(self, kind, params, fs):
        if kind not in KINDS:
            raise ValueError(f"unknown filter kind {kind!r}")
        self.kind = kind
        self.min_cutoff, self.beta, self.d_cutoff = (float(v) for v in params)
        self.fs = float(fs)
        self.state = None

    def peek(self, x):
        """(output, new state) for input `x`, without keeping the state."""
        kind = self.kind
        if kind == 'QUATERNION':
            x = Quaternion(x).normalized()
        elif kind == 'VECTOR':
            x = Vector(x)
        else:
            x = float(x)
        state = self.state
        if state is None:
            return (x.copy() if kind != 'SCALAR' else x), State(x, x, _zero(kind))
        dx = _derivative(kind, x, state.raw, self.fs)
        speed = state.speed + (dx - state.speed) * alpha(self.d_cutoff, self.fs)
        a = alpha(self.min_cutoff + self.beta * _magnitude(kind, speed), self.fs)
        if kind == 'QUATERNION':
            target = x.copy()
            if target.dot(state.value) < 0.0:
                target.negate()
            y = state.value.slerp(target, a).normalized()
        else:
            y = state.value + (x - state.value) * a
        return y, State(x, y, speed)

    def __call__(self, x):
        y, self.state = self.peek(x)
        return y


class FilterBank:
    """The one-euro filters of a bake, keyed by what they filter.

    `apply` filters from the committed state and keeps the new state pending; `commit` keeps the pending states,
    so the passes of one frame all start from the previous frame.
    """

    def __init__(self, fs):
        self.fs = float(fs)
        self.filters = {}
        self.pending = {}

    def apply(self, key, kind, params, value):
        filt = self.filters.get(key)
        if filt is None:
            filt = self.filters[key] = OneEuro(kind, params, self.fs)
        y, self.pending[key] = filt.peek(value)
        return y

    def commit(self):
        for key, state in self.pending.items():
            self.filters[key].state = state
        self.pending.clear()

    def discard(self):
        self.pending.clear()


# Post-bake smoothing -------------------------------------------------------------------------------------------

def butterworth(cutoff, fs):
    """(b, a) of a second-order Butterworth low-pass at `cutoff` Hz for `fs` samples per second (bilinear transform
    with pre-warping). The DC gain is 1."""
    k = math.tan(math.pi * cutoff / fs)
    root2 = math.sqrt(2.0)
    norm = 1.0 / (1.0 + root2 * k + k * k)
    b0 = k * k * norm
    return (b0, 2.0 * b0, b0), (1.0, 2.0 * (k * k - 1.0) * norm, (1.0 - root2 * k + k * k) * norm)


def _lfilter(b, a, x, zi):
    """Direct form II transposed over axis 0 of x (n, channels), from the delay state zi (2, channels)."""
    b0, b1, b2 = b
    _, a1, a2 = a
    z0, z1 = zi[0].copy(), zi[1].copy()
    y = np.empty_like(x)
    for i in range(len(x)):
        xi = x[i]
        yi = b0 * xi + z0
        z0 = b1 * xi - a1 * yi + z1
        z1 = b2 * xi - a2 * yi
        y[i] = yi
    return y


def can_filter(cutoff, fs):
    """Whether `cutoff` is below the Nyquist frequency of `fs` (with a margin), so that filtering changes anything."""
    return 0.0 < cutoff < 0.45 * fs


def filtfilt(x, cutoff, fs):
    """`x` (n,) or (n, channels) low-passed forward and backward: zero phase, and the Butterworth magnitude
    squared (-6 dB at the cutoff). The ends are extended by odd reflection, three cutoff periods where the signal
    is that long, and each pass starts in the steady state of its first sample: a constant signal comes back
    unchanged, and a linear one once the start-up has died away in the extension."""
    x = np.asarray(x, dtype=np.float64)
    flat = x.ndim == 1
    data = x[:, None] if flat else x
    n = len(data)
    if n < 3 or not can_filter(cutoff, fs):
        return x.copy()
    b, a = butterworth(cutoff, fs)
    pad = min(n - 1, max(9, int(round(3.0 * fs / cutoff))))
    ext = np.concatenate((2.0 * data[0] - data[pad:0:-1], data, 2.0 * data[-1] - data[-2:-pad - 2:-1]))
    zi = np.array((b[1] + b[2] - a[1] - a[2], b[2] - a[2]))[:, None]
    y = _lfilter(b, a, ext, zi * ext[0])
    y = _lfilter(b, a, y[::-1], zi * y[-1])[::-1]
    y = y[pad:pad + n]
    return y[:, 0] if flat else y


def continuous_quaternions(q):
    """Quaternions (n, 4) with signs flipped so that neighbours have a positive dot product."""
    q = np.array(q, dtype=np.float64)
    for i in range(1, len(q)):
        if np.dot(q[i], q[i - 1]) < 0.0:
            q[i] = -q[i]
    return q


def smooth_quaternions(q, cutoff, fs):
    """Quaternions (n, 4) low-passed component-wise after sign continuity, then normalised."""
    q = filtfilt(continuous_quaternions(q), cutoff, fs)
    return q / np.linalg.norm(q, axis=1)[:, None]
