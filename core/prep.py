"""Mocap prep (mocap_prep_plan §5): touch-ups that give back some of the expressiveness capture and filtering
took out of the mocap, before the bake. NumPy only; prepjob.py samples the pose and writes the keys.

Quaternions are (w, x, y, z) arrays of shape (n, 4), made sign-continuous (filters.continuous_quaternions) before
they are filtered; `qlog` and `qexp` map unit quaternions to rotation vectors (radians) and back. Range and Snap
commute with a fixed change of frame (a conjugation), so they work on any bone's rotations as they are: basis
rotations, or a hand's turn relative to its forearm.

Base and detail (§5.2): base = q low-passed at `cutoff` (zero phase), detail = log(base⁻¹ q), q = base exp(detail).

Range (§5.3): q' = base exp(g · detail). Motion above the cutoff grows by g; the posture (the base) stays, and a
held pose settles back to its level within about 1/cutoff.

Snap (§5.4): a driver signal x is cut into moves between its turning points (a zig-zag: a turn counts once x has
come back h from it), and each move of at least h is retimed: with p(t) the move's progress from 0 to 1, the
frame t shows the original at t' = p⁻¹(S(p(t))), S(p) = pᵃ / (pᵃ + (1 - p)ᵃ). Held poses and the moment each move
crosses 50 % stay where they were; the move between them gets steeper (a = 1 changes nothing). Every bone
driven by one signal (the three joints of a finger) is replayed at the same t', slerped between frames.

Swing (§5.5): the arm swing a strum makes, synthesised from the stroke the hand already makes: the pick point's
motion above the cutoff, along its main direction u, moves the wrist target, and a few damped least-squares
passes turn the upper arm (a ball joint at the shoulder) and the elbow (a hinge) to put the wrist there.

Roll (§5.6): the swing-twist split of the hand's turn relative to the forearm about the forearm axis a. The twist
t = normalise(w, (v · a) a) moves onto the twist bone (MMD 手捩), and the hand keeps its pose exactly.
"""

import numpy as np

from . import filters

IDENTITY = np.array((1.0, 0.0, 0.0, 0.0))


# Quaternions ---------------------------------------------------------------------------------------------------

def qmul(a, b):
    aw, ax, ay, az = np.moveaxis(np.asarray(a, dtype=np.float64), -1, 0)
    bw, bx, by, bz = np.moveaxis(np.asarray(b, dtype=np.float64), -1, 0)
    return np.stack((aw * bw - ax * bx - ay * by - az * bz, aw * bx + ax * bw + ay * bz - az * by,
                     aw * by - ax * bz + ay * bw + az * bx, aw * bz + ax * by - ay * bx + az * bw), axis=-1)


def qinv(q):
    """The inverse of unit quaternions (their conjugate)."""
    return np.asarray(q, dtype=np.float64) * np.array((1.0, -1.0, -1.0, -1.0))


def qlog(q):
    """Rotation vectors (radians, at most π long) of unit quaternions."""
    q = np.asarray(q, dtype=np.float64)
    q = np.where(q[..., :1] < 0.0, -q, q)
    v = q[..., 1:]
    s = np.linalg.norm(v, axis=-1)
    angle = 2.0 * np.arctan2(s, q[..., 0])
    scale = np.where(s > 1e-12, angle / np.maximum(s, 1e-12), 2.0)
    return v * scale[..., None]


def qexp(r):
    """Unit quaternions of rotation vectors."""
    r = np.asarray(r, dtype=np.float64)
    angle = np.linalg.norm(r, axis=-1)
    scale = np.where(angle > 1e-12, np.sin(angle / 2.0) / np.maximum(angle, 1e-12), 0.5)
    return np.concatenate((np.cos(angle / 2.0)[..., None], r * scale[..., None]), axis=-1)


def qrot(q, v):
    """Vectors v (..., 3) turned by unit quaternions q (..., 4)."""
    q = np.asarray(q, dtype=np.float64)
    w, u = q[..., :1], q[..., 1:]
    t = 2.0 * np.cross(u, v)
    return v + w * t + np.cross(u, t)


def angles(q):
    """Rotation angles (radians) of unit quaternions."""
    return np.linalg.norm(qlog(q), axis=-1)


def normalize(v):
    v = np.asarray(v, dtype=np.float64)
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-12)


def continuous(q):
    return filters.continuous_quaternions(q)


def from_matrices(m):
    """Unit quaternions (..., 4) of rotation matrices (..., 3, 3) or the rotation part of (..., 4, 4) matrices
    without scale."""
    m = np.asarray(m, dtype=np.float64)[..., :3, :3]
    m00, m01, m02 = m[..., 0, 0], m[..., 0, 1], m[..., 0, 2]
    m10, m11, m12 = m[..., 1, 0], m[..., 1, 1], m[..., 1, 2]
    m20, m21, m22 = m[..., 2, 0], m[..., 2, 1], m[..., 2, 2]
    cases = np.stack((m00 + m11 + m22, m00, m11, m22), axis=-1)
    case = np.argmax(cases, axis=-1)
    with np.errstate(invalid='ignore', divide='ignore'):
        r0 = np.sqrt(np.maximum(1.0 + m00 + m11 + m22, 0.0))
        r1 = np.sqrt(np.maximum(1.0 + m00 - m11 - m22, 0.0))
        r2 = np.sqrt(np.maximum(1.0 - m00 + m11 - m22, 0.0))
        r3 = np.sqrt(np.maximum(1.0 - m00 - m11 + m22, 0.0))
        forms = (
            np.stack((0.5 * r0, (m21 - m12) / (2 * r0), (m02 - m20) / (2 * r0), (m10 - m01) / (2 * r0)), -1),
            np.stack(((m21 - m12) / (2 * r1), 0.5 * r1, (m01 + m10) / (2 * r1), (m02 + m20) / (2 * r1)), -1),
            np.stack(((m02 - m20) / (2 * r2), (m01 + m10) / (2 * r2), 0.5 * r2, (m12 + m21) / (2 * r2)), -1),
            np.stack(((m10 - m01) / (2 * r3), (m02 + m20) / (2 * r3), (m12 + m21) / (2 * r3), 0.5 * r3), -1),
        )
    q = np.choose(case[..., None], forms)
    q = np.where(q[..., :1] < 0.0, -q, q)
    return normalize(q)


def to_matrices(q):
    """Rotation matrices (..., 3, 3) of unit quaternions (..., 4)."""
    w, x, y, z = np.moveaxis(normalize(q), -1, 0)
    return np.stack((
        np.stack((1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)), -1),
        np.stack((2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)), -1),
        np.stack((2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)), -1)), -2)


def slerp(a, b, f):
    """Quaternions between a and b (..., 4), at fractions f (...,), the shorter way."""
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    f = np.asarray(f, dtype=np.float64)[..., None]
    dot = np.sum(a * b, axis=-1, keepdims=True)
    b = np.where(dot < 0.0, -b, b)
    dot = np.minimum(np.abs(dot), 1.0)
    theta = np.arccos(dot)
    sin = np.sin(theta)
    small = sin < 1e-6
    wa = np.where(small, 1.0 - f, np.sin((1.0 - f) * theta) / np.where(small, 1.0, sin))
    wb = np.where(small, f, np.sin(f * theta) / np.where(small, 1.0, sin))
    return normalize(wa * a + wb * b)


# Signals -------------------------------------------------------------------------------------------------------

def lowpass(x, cutoff, fs):
    """`x` (n, ...) low-passed at `cutoff` Hz, zero phase (filters.filtfilt)."""
    x = np.asarray(x, dtype=np.float64)
    shape = x.shape
    return filters.filtfilt(x.reshape(len(x), -1), cutoff, fs).reshape(shape)


def split(q, cutoff, fs):
    """(base, detail) of quaternions q (§5.2): base low-passed and normalised, detail as rotation vectors."""
    q = continuous(q)
    base = filters.smooth_quaternions(q, cutoff, fs)
    return base, qlog(qmul(qinv(base), q))


def join(base, detail):
    return continuous(qmul(base, qexp(detail)))


def principal(vectors):
    """(unit direction, share of the variance) of the main axis of `vectors` (n, k) about their mean."""
    v = np.asarray(vectors, dtype=np.float64)
    if len(v) < 2 or not np.isfinite(v).all():
        return np.eye(v.shape[1])[0], 0.0
    values, axes = np.linalg.eigh(np.cov(v.T))
    total = values.sum()
    return axes[:, -1], float(values[-1] / total) if total > 1e-30 else 0.0


def scale_detail(q, gain, cutoff, fs):
    """Range (§5.3): q' = base exp(gain · detail)."""
    if gain == 1.0:
        return continuous(q)
    base, detail = split(q, cutoff, fs)
    return join(base, detail * gain)


def retime_quaternions(q, times):
    """q (n, 4) shown at fractional frame indices `times` (n,), slerped between frames."""
    q = continuous(q)
    t = np.clip(np.asarray(times, dtype=np.float64), 0.0, len(q) - 1)
    i0 = np.minimum(np.floor(t).astype(int), len(q) - 1)
    i1 = np.minimum(i0 + 1, len(q) - 1)
    return continuous(slerp(q[i0], q[i1], t - i0))


def retime_vectors(v, times):
    v = np.asarray(v, dtype=np.float64)
    index = np.arange(len(v), dtype=np.float64)
    return np.stack([np.interp(times, index, v[:, k]) for k in range(v.shape[1])], axis=1)


# Snap ----------------------------------------------------------------------------------------------------------

def moves(x, h):
    """[(start, end)] frame indices of the moves of x between its turning points (zig-zag: a turn counts once x
    has come back `h` from it), keeping the moves of at least `h`."""
    x = np.asarray(x, dtype=np.float64)
    if len(x) < 2:
        return []
    turns, direction, hi, lo, ext = [0], 0, 0, 0, 0
    for i in range(1, len(x)):
        if direction == 0:
            hi = i if x[i] > x[hi] else hi
            lo = i if x[i] < x[lo] else lo
            if x[hi] - x[lo] >= h:
                first = lo if hi > lo else hi
                if first != 0:
                    turns.append(first)
                direction, ext = (1, hi) if hi > lo else (-1, lo)
        elif direction == 1:
            if x[i] > x[ext]:
                ext = i
            elif x[ext] - x[i] >= h:
                turns.append(ext)
                direction, ext = -1, i
        else:
            if x[i] < x[ext]:
                ext = i
            elif x[i] - x[ext] >= h:
                turns.append(ext)
                direction, ext = 1, i
    if direction != 0 and ext != turns[-1]:
        turns.append(ext)
    if turns[-1] != len(x) - 1:
        turns.append(len(x) - 1)
    return [(a, b) for a, b in zip(turns[:-1], turns[1:]) if abs(x[b] - x[a]) >= h]


def contrast(p, a):
    """The S-curve S(p) = pᵃ / (pᵃ + (1 - p)ᵃ) on [0, 1]; a = 1 is the identity."""
    p = np.clip(np.asarray(p, dtype=np.float64), 0.0, 1.0)
    return p ** a / (p ** a + (1.0 - p) ** a)


def snap_times(x, a, h):
    """For each frame, the fractional frame of the original to show (see the module notes). Returns
    (times, number of moves retimed)."""
    x = np.asarray(x, dtype=np.float64)
    t = np.arange(len(x), dtype=np.float64)
    if a == 1.0:
        return t, 0
    found = [(s, e) for s, e in moves(x, max(h, 1e-9)) if x[e] != x[s]]
    for s, e in found:
        segment = x[s:e + 1]
        p = np.maximum.accumulate((segment - segment[0]) / (segment[-1] - segment[0]))
        p = p + np.arange(len(segment)) * 1e-9      # strictly increasing, for the inverse
        t[s:e + 1] = s + np.interp(contrast(p, a), p, np.arange(len(segment), dtype=np.float64))
    return t, len(found)


def bend(joints):
    """A finger's total bend in degrees: the sum of its joints' rotation angles (n,)."""
    return np.degrees(sum(angles(q) for q in joints))


# The picking hand ----------------------------------------------------------------------------------------------

def strokes(q, gain, a, h, cutoff, fs):
    """Range and stroke Snap on the picking hand's turn q (n, 4) relative to its forearm (§5.3, §5.4): the detail
    is retimed along its main axis (moves of at least `h` degrees), then scaled by `gain`, and capped at the
    source's 99.9th percentile times the gain, or the source's own size on that frame if it is larger (the cap
    guards against spikes the retiming carries to other frames). Returns (q', {"axis", "share", "moves",
    "capped"})."""
    base, detail = split(q, cutoff, fs)
    axis, share = principal(detail)
    times, count = snap_times(np.degrees(detail @ axis), a, h)
    retimed = retime_vectors(detail, times)
    sizes = np.linalg.norm(detail, axis=1)
    cap = np.maximum(np.percentile(sizes, 99.9), sizes) if len(detail) else sizes
    norms = np.linalg.norm(retimed, axis=1)
    capped = norms > cap * (1.0 + 1e-9)
    retimed[capped] *= (cap[capped] / norms[capped])[:, None]
    return join(base, retimed * gain), {"axis": axis, "share": share, "moves": count, "capped": capped}


# Fingers -------------------------------------------------------------------------------------------------------

def clamp_joint(source, q, margin):
    """q (n, 4) with its rotation vector's component along the source joint's main axis kept within the source's
    range plus `margin` radians (§5.7). Returns (q, frames that were clamped (n,) bool)."""
    r0, r = qlog(continuous(source)), qlog(q)
    axis, _ = principal(r0)
    along0 = r0 @ axis
    along = r @ axis
    kept = np.clip(along, along0.min() - margin, along0.max() + margin)
    clamped = np.abs(kept - along) > 1e-9
    return continuous(qexp(r + (kept - along)[:, None] * axis)), clamped


def finger(joints, a, gain, h, cutoff, fs, margin=None):
    """Snap, then Range, then the clamp on one finger (§5.4, §5.3, §5.7). `joints`: its joints' rotations
    [(n, 4)], proximal first; the snap is driven by its total bend, with moves of at least `h` degrees, and its
    joints share the retiming. `margin` None: no clamp. Returns ([q'], clamped frames (n,) bool, moves)."""
    times, count = snap_times(bend(joints), a, h)
    out = []
    clamped = np.zeros(len(joints[0]), dtype=bool)
    for q in joints:
        new = retime_quaternions(q, times) if count else continuous(q)
        new = scale_detail(new, gain, cutoff, fs)
        if margin is not None:
            new, hit = clamp_joint(q, new, margin)
            clamped |= hit
        out.append(new)
    return out, clamped, count


# Roll ----------------------------------------------------------------------------------------------------------

def twist(q, axis):
    """The twist of q (n, 4) about the unit `axis` (3,): normalise((w, (v · a) a)), the same for q = swing · twist
    and q = twist · swing. A half-turn swing has no defined twist: it gives the identity."""
    q = np.asarray(q, dtype=np.float64)
    axis = normalize(axis)
    along = q[..., 1:] @ axis
    t = np.concatenate((q[..., :1], along[..., None] * axis), axis=-1)
    norm = np.linalg.norm(t, axis=-1, keepdims=True)
    return continuous(np.where(norm > 1e-9, t / np.maximum(norm, 1e-12), IDENTITY))


def twist_angles(q, axis):
    """Signed twist angles (radians, within ±π) of q about `axis`."""
    t = twist(q, axis)
    angle = 2.0 * np.arctan2(t[..., 1:] @ normalize(axis), t[..., 0])
    return (angle + np.pi) % (2.0 * np.pi) - np.pi


# Swing ---------------------------------------------------------------------------------------------------------

def strum(pick, cutoff, fs, lead):
    """(s, u, share): the strum signal s(t + lead) (n,) and its direction u (3,) from pick points (n, 3) in chest
    space: their motion above `cutoff` along its main direction, which has `share` of it."""
    pick = np.asarray(pick, dtype=np.float64)
    detail = pick - lowpass(pick, cutoff, fs)
    u, share = principal(detail)
    s = detail @ u
    index = np.arange(len(s), dtype=np.float64)
    return np.interp(index + lead, index, s), u, share


def _skew(v):
    """[v]× (n, 3, 3)."""
    zero = np.zeros(len(v))
    x, y, z = v[:, 0], v[:, 1], v[:, 2]
    return np.stack((np.stack((zero, -z, y), -1), np.stack((z, zero, -x), -1), np.stack((-y, x, zero), -1)), -2)


def _about(q, point):
    """4x4 matrices (n, 4, 4) of the rotations q (n, 4) about the points (n, 3)."""
    out = np.zeros((len(q), 4, 4))
    rot = to_matrices(q)
    out[:, :3, :3] = rot
    out[:, :3, 3] = point - np.einsum("nij,nj->ni", rot, point)
    out[:, 3, 3] = 1.0
    return out


def _moved(matrix, point):
    return np.einsum("nij,nj->ni", matrix[:, :3, :3], point) + matrix[:, :3, 3]


STRAIGHT_ANGLE = np.radians(15.0)       # an elbow bent less than this has no hinge axis to turn about


def swing_ik(shoulder, elbow, wrist, target, elbow_share, passes=3, damping=1e-6):
    """Turn an arm so that its wrist reaches `target` (all (n, 3) points), by damped least squares (§5.5): the
    upper arm turns about the shoulder (3 DOF), the forearm about the elbow's hinge axis
    h = normalise((e - s) × (w - e)), weighted elbow_share : 1 - elbow_share. Returns (A_upper, A_forearm,
    straight): the (n, 4, 4) rigid transforms to apply (on the left) to the poses of the bones the upper arm
    carries and of the forearm and the bones it carries, and the frames whose elbow was too straight for a hinge,
    where only the shoulder turned."""
    shoulder, elbow0, wrist0 = (np.asarray(p, dtype=np.float64) for p in (shoulder, elbow, wrist))
    target = np.asarray(target, dtype=np.float64)
    n = len(shoulder)
    a_upper = np.tile(np.eye(4), (n, 1, 1))
    a_forearm = a_upper.copy()
    straight = np.zeros(n, dtype=bool)
    scale = np.median(np.linalg.norm(wrist0 - shoulder, axis=1)) if n else 1.0
    weights = np.array((1.0 - elbow_share,) * 3 + (elbow_share,))
    lam = damping * max(scale, 1e-12) ** 2
    for _ in range(passes):
        s, e, w = shoulder, _moved(a_upper, elbow0), _moved(a_forearm, wrist0)
        upper, lower = e - s, w - e
        hinge = np.cross(upper, lower)
        size = np.linalg.norm(hinge, axis=1)
        straight |= size < np.sin(STRAIGHT_ANGLE) * np.linalg.norm(upper, axis=1) * np.linalg.norm(lower, axis=1)
        hinge = hinge / np.maximum(size, 1e-12)[:, None]
        jac = np.zeros((n, 3, 4))
        jac[:, :, :3] = -_skew(w - s)                  # ω × (w - s)
        jac[:, :, 3] = np.where(straight[:, None], 0.0, np.cross(hinge, lower))
        jw = jac * weights
        system = jw @ np.transpose(jac, (0, 2, 1)) + lam * np.eye(3)
        x = (np.transpose(jw, (0, 2, 1)) @ np.linalg.solve(system, (target - w)[:, :, None]))[:, :, 0]
        turn = qexp(x[:, :3])
        at_shoulder = _about(turn, s)
        a_upper = at_shoulder @ a_upper
        a_forearm = at_shoulder @ a_forearm
        bend_at = _about(qexp(qrot(turn, hinge) * x[:, 3:4]), _moved(at_shoulder, e))
        a_forearm = bend_at @ a_forearm
    return a_upper, a_forearm, straight


# Measures ------------------------------------------------------------------------------------------------------

def travel(points, cutoff, fs):
    """(RMS, 99th percentile) of the distance of points (n, 3) from their low-passed path: the motion above
    `cutoff`."""
    points = np.asarray(points, dtype=np.float64)
    distance = np.linalg.norm(points - lowpass(points, cutoff, fs), axis=1)
    if not len(distance):
        return 0.0, 0.0
    return float(np.sqrt((distance ** 2).mean())), float(np.percentile(distance, 99))


def detail_rms(q, cutoff, fs):
    """RMS angle (radians) of the rotation detail above `cutoff`."""
    _, detail = split(q, cutoff, fs)
    return float(np.sqrt((np.linalg.norm(detail, axis=1) ** 2).mean())) if len(detail) else 0.0


def speeds(q, fs):
    """Angular speeds (radians per second) between consecutive quaternions (n - 1,)."""
    q = continuous(q)
    return angles(qmul(qinv(q[:-1]), q[1:])) * fs


def transitions(flex):
    """10-90 % durations in frames of the presses and releases in a finger's bend (n,): the moves that cross from
    below 30 % to above 70 % of its 10th-90th percentile range, or back."""
    flex = np.asarray(flex, dtype=np.float64)
    if len(flex) < 3:
        return []
    lo, hi = np.percentile(flex, 10), np.percentile(flex, 90)
    norm = (flex - lo) / max(hi - lo, 1e-9)
    state, out = None, []
    for i, v in enumerate(norm):
        new = 'LOW' if v < 0.3 else 'HIGH' if v > 0.7 else state
        if state is not None and new != state:
            sign = 1 if new == 'HIGH' else -1
            a = i
            while a > 0 and (norm[a - 1] - norm[a]) * sign < 0.0:
                a -= 1
            b = i
            while b < len(norm) - 1 and (norm[b + 1] - norm[b]) * sign > 0.0:
                b += 1
            segment = (norm[a:b + 1] - norm[a]) / (norm[b] - norm[a])
            out.append(int(np.argmax(segment >= 0.9) - np.argmax(segment >= 0.1)))
        state = new
    return out
