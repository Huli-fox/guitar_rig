"""Guitar frame normalisation (§3.1) and neck measurements (§12).

The guitar frame has +X along the neck toward the headstock, +Z out of the string face and Y = Z × X. It is
found from surface samples of the guitar meshes:
  1. PCA gives the long axis and the thin axis.
  2. The narrower end of the slice-width profile is the headstock.
  3. The string face is +Z, by a majority of three cues: long thin loose parts (strings) lie on it; the neck
     sits toward it relative to the body; the headstock is set back from it (angled back, or recessed as on
     Fender necks). On the eight SAO props each cue is right on its own. The plan's fallback, the flatter face
     of the neck, was wrong on half of them and is not used.
  4. Z is refined to the mean normal of the body's top face, and X to the neck centreline.
Everything works on numpy arrays in one coordinate space (world, or GTR_ROOT local), so it can be tested without
Blender objects; `gather` collects the arrays from mesh objects. Thresholds are relative to the guitar's length
and width, so any unit works.
"""

import math
from dataclasses import dataclass, field

import numpy as np

SAMPLES = 150_000           # surface samples; the sampling is seeded, so results are repeatable
BINS = 200                  # slices along X (about 5 mm on a 1 m guitar)
HEADSTOCK_SHARE = 0.4       # share of the length at each end compared to find the headstock
NECK_MAX_WIDTH = 0.35       # neck slices are narrower than this share of the widest slice
NECK_MIN_LENGTH = 0.15      # share of the length a neck must span
NECK_FIT_TOL = 0.06         # relative width deviation from the neck's taper line that ends the neck
NECK_GAP = 2                # outlier slices tolerated inside the neck
BODY_MIN_WIDTH = 0.5        # body slices are wider than this share of the widest slice
STRING_MIN_VERTICES = 4     # a string-like part has this many vertices (long sliver triangles are not strings),
STRING_MIN_LENGTH = 0.3     # spans this share of the length...
STRING_MAX_THIN = 0.004     # ...its thinnest spread (std) is below this share of the length...
STRING_MAX_WIDE = 0.03      # ...and its middle spread below this share
TOP_NORMAL_CONE = math.radians(25.0)
MAX_YAW_FIX = math.radians(10.0)
HEADSTOCK_MIN_SAMPLES = 100
CUE_MIN = {'strings': 0.1, 'neck_offset': 0.08, 'headstock': 0.1}
CUE_TITLES = {'strings': "strings", 'neck_offset': "neck position", 'headstock': "headstock set-back"}
HEADSTOCK_MIN_RATIO = 1.5


class FrameError(ValueError):
    """The geometry is empty or too degenerate to find a frame."""


@dataclass
class Geometry:
    triangles: np.ndarray       # (T, 3, 3) triangle corners
    triangle_parts: np.ndarray  # (T,) loose-part id of each triangle
    vertices: np.ndarray        # (V, 3) all vertices
    part_ids: np.ndarray        # (V,) loose-part id of each vertex, unique across objects


@dataclass
class Samples:
    points: np.ndarray          # (N, 3)
    normals: np.ndarray         # (N, 3) unit normals of the sampled faces (sign not reliable)
    parts: np.ndarray           # (N,) loose-part id of the sampled face

    def subset(self, mask):
        return Samples(self.points[mask], self.normals[mask], self.parts[mask])

    def transformed(self, matrix):
        """The samples mapped by a 4x4 matrix (numpy or mathutils) with uniform scale."""
        m = np.asarray(matrix, dtype=float)
        rot = m[:3, :3]
        normals = self.normals @ rot.T
        normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
        return Samples(self.points @ rot.T + m[:3, 3], normals, self.parts)


@dataclass
class Neck:
    """Neck measurements in frame coordinates. The joint is the body end, the nut the headstock end."""
    joint_x: float
    nut_x: float
    width_joint: float
    width_nut: float
    center_y: float
    fret_z: float               # fretboard top (95th percentile of the neck's Z)
    back_z: float               # neck back (5th percentile)

    @property
    def length(self):
        return self.nut_x - self.joint_x

    @property
    def width(self):
        return 0.5 * (self.width_joint + self.width_nut)

    @property
    def thickness(self):
        return self.fret_z - self.back_z

    def as_dict(self):
        return {key: float(getattr(self, key)) for key in self.__dataclass_fields__}

    def scaled(self, factor):
        return Neck(**{key: value * factor for key, value in self.as_dict().items()})


@dataclass
class Measurements:
    bounds_min: np.ndarray
    bounds_max: np.ndarray
    neck: Neck = None

    @property
    def size(self):
        return self.bounds_max - self.bounds_min

    @property
    def length(self):
        return float(self.size[0])

    def as_dict(self):
        return {"bounds_min": [float(v) for v in self.bounds_min],
                "bounds_max": [float(v) for v in self.bounds_max],
                "neck": self.neck.as_dict() if self.neck is not None else None}

    @classmethod
    def from_dict(cls, data):
        neck = data.get("neck")
        return cls(np.array(data["bounds_min"], dtype=float), np.array(data["bounds_max"], dtype=float),
                   Neck(**neck) if neck else None)

    def scaled(self, factor):
        return Measurements(self.bounds_min * factor, self.bounds_max * factor,
                            self.neck.scaled(factor) if self.neck is not None else None)


@dataclass
class Cue:
    name: str
    score: float                # signed: positive means the current +Z is the string face
    valid: bool
    detail: str


@dataclass
class Detection:
    axes: np.ndarray            # (3, 3) columns X, Y, Z of the guitar frame
    measurements: Measurements  # in frame coordinates (points @ axes)
    headstock_ratio: float
    cues: list = field(default_factory=list)
    confidence: str = 'LOW'     # 'HIGH', 'MEDIUM' or 'LOW'
    messages: list = field(default_factory=list)


# Geometry ---------------------------------------------------------------------------------------------------------

def loose_parts(count, edges):
    """Loose-part label of each of `count` vertices from an (E, 2) edge array (label propagation)."""
    labels = np.arange(count)
    if len(edges) == 0:
        return labels
    a, b = edges[:, 0], edges[:, 1]
    while True:
        low = np.minimum(labels[a], labels[b])
        new = labels.copy()
        np.minimum.at(new, a, low)
        np.minimum.at(new, b, low)
        new = new[new]          # pointer jumping: labels are vertex indices
        if np.array_equal(new, labels):
            return labels
        labels = new


def gather(objects, depsgraph, to_space=None):
    """Geometry of the evaluated mesh `objects` in world space, or mapped by the 4x4 `to_space` (world -> target)."""
    to_space = np.identity(4) if to_space is None else np.asarray(to_space, dtype=float)
    triangles, triangle_parts, vertices, part_ids = [], [], [], []
    next_id = 0
    for obj in objects:
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        try:
            mesh.calc_loop_triangles()
            co = np.empty(len(mesh.vertices) * 3)
            mesh.vertices.foreach_get("co", co)
            m = to_space @ np.asarray(obj.matrix_world, dtype=float)
            co = co.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]
            tris = np.empty(len(mesh.loop_triangles) * 3, dtype=np.int64)
            mesh.loop_triangles.foreach_get("vertices", tris)
            edges = np.empty(len(mesh.edges) * 2, dtype=np.int64)
            mesh.edges.foreach_get("vertices", edges)
        finally:
            evaluated.to_mesh_clear()
        if not len(co):
            continue
        labels = loose_parts(len(co), edges.reshape(-1, 2))
        _, labels = np.unique(labels, return_inverse=True)
        labels = labels.reshape(-1) + next_id
        tris = tris.reshape(-1, 3)
        triangles.append(co[tris])
        triangle_parts.append(labels[tris[:, 0]])
        vertices.append(co)
        part_ids.append(labels)
        next_id = int(labels.max()) + 1
    if not vertices:
        return Geometry(np.zeros((0, 3, 3)), np.zeros(0, dtype=np.int64), np.zeros((0, 3)),
                        np.zeros(0, dtype=np.int64))
    return Geometry(np.concatenate(triangles), np.concatenate(triangle_parts), np.concatenate(vertices),
                    np.concatenate(part_ids))


def transformed(geometry, matrix):
    """The geometry mapped by a 4x4 matrix."""
    m = np.asarray(matrix, dtype=float)
    rot, loc = m[:3, :3].T, m[:3, 3]
    return Geometry(geometry.triangles @ rot + loc, geometry.triangle_parts, geometry.vertices @ rot + loc,
                    geometry.part_ids)


def sample_surface(geometry, count=SAMPLES, seed=0):
    """Area-uniform surface samples; repeatable for the same triangles."""
    triangles = geometry.triangles
    empty = Samples(np.zeros((0, 3)), np.zeros((0, 3)), np.zeros(0, dtype=np.int64))
    if len(triangles) == 0:
        return empty
    v0 = triangles[:, 0]
    e1, e2 = triangles[:, 1] - v0, triangles[:, 2] - v0
    cross = np.cross(e1, e2)
    area2 = np.linalg.norm(cross, axis=1)
    total = area2.sum()
    if total <= 0.0:
        return empty
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(triangles), size=count, p=area2 / total)
    u = rng.random((count, 2))
    outside = u.sum(axis=1) > 1.0
    u[outside] = 1.0 - u[outside]
    points = v0[idx] + e1[idx] * u[:, :1] + e2[idx] * u[:, 1:]
    normals = cross[idx] / area2[idx, None]
    return Samples(points, normals, geometry.triangle_parts[idx])


# Loose parts ------------------------------------------------------------------------------------------------------

@dataclass
class PartStats:
    ids: np.ndarray             # (P,) part ids
    counts: np.ndarray          # (P,) vertices per part
    extent: np.ndarray          # (P,) length along each part's main axis
    spread: np.ndarray          # (P, 3) standard deviations along the part's principal axes, ascending
    order: np.ndarray           # (V,) vertex indices sorted by part
    part_of: np.ndarray         # (V,) index into `ids` of each vertex in `order`


def part_stats(geometry):
    ids = geometry.part_ids
    order = np.argsort(ids, kind='stable')
    sorted_ids = ids[order]
    starts = np.flatnonzero(np.concatenate(([True], sorted_ids[1:] != sorted_ids[:-1])))
    counts = np.diff(np.append(starts, len(ids)))
    verts = geometry.vertices[order]
    mean = np.add.reduceat(verts, starts) / counts[:, None]
    part_of = np.repeat(np.arange(len(starts)), counts)
    d = verts - mean[part_of]
    pairs = ((0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (2, 2))
    sums = np.add.reduceat(np.stack([d[:, i] * d[:, j] for i, j in pairs], axis=1), starts)
    cov = np.empty((len(starts), 3, 3))
    for k, (i, j) in enumerate(pairs):
        cov[:, i, j] = cov[:, j, i] = sums[:, k] / counts
    values, vectors = np.linalg.eigh(cov)
    proj = np.einsum('ij,ij->i', d, vectors[part_of, :, 2])
    extent = np.maximum.reduceat(proj, starts) - np.minimum.reduceat(proj, starts)
    return PartStats(sorted_ids[starts], counts, extent, np.sqrt(np.maximum(values, 0.0)), order, part_of)


def _major_extent(points):
    centred = points - points.mean(axis=0)
    axis = np.linalg.eigh(np.cov(centred.T))[1][:, 2]
    projection = centred @ axis
    return float(projection.max() - projection.min())


def string_parts(geometry, stats=None):
    """Indices into `stats` (part_stats) of the long thin loose parts: strings, not guitar body."""
    if len(geometry.part_ids) < 2:
        return np.zeros(0, dtype=np.int64)
    stats = part_stats(geometry) if stats is None else stats
    length = _major_extent(geometry.vertices)
    thin = ((stats.counts >= STRING_MIN_VERTICES) & (stats.extent > STRING_MIN_LENGTH * length)
            & (stats.spread[:, 0] < STRING_MAX_THIN * length) & (stats.spread[:, 1] < STRING_MAX_WIDE * length))
    return np.flatnonzero(thin)


def solid_samples(samples, geometry, axes=None, stats=None, strings=None):
    """The samples without the string-like parts, so that strings do not raise the measured fretboard.

    On low-poly models every face can be a loose part, and the neck's own faces pass as strings; the strings
    are then kept when leaving them out loses the neck. `axes` gives the frame for that check (identity: the
    samples are in frame coordinates already).
    """
    if len(geometry.part_ids) < 2:
        return samples
    if strings is None:
        stats = part_stats(geometry) if stats is None else stats
        strings = string_parts(geometry, stats)
    if not len(strings):
        return samples
    solid = samples.subset(~np.isin(samples.parts, stats.ids[strings]))
    if len(solid.points) < 100:
        return samples
    axes = np.identity(3) if axes is None else axes
    if find_neck(profile(solid.points @ axes)) is None and find_neck(profile(samples.points @ axes)) is not None:
        return samples
    return solid


def measure_geometry(geometry, axes=None):
    """Bounds and neck of the geometry, strings left out where possible (see `solid_samples` and `measure`)."""
    return measure(solid_samples(sample_surface(geometry), geometry, axes), axes)


# Slice profile ----------------------------------------------------------------------------------------------------

@dataclass
class Profile:
    x0: float
    step: float
    count: np.ndarray
    y_lo: np.ndarray
    y_hi: np.ndarray
    z_lo: np.ndarray
    z_hi: np.ndarray
    index: np.ndarray           # bin of each sample

    @property
    def width(self):
        return np.where(self.count > 0, self.y_hi - self.y_lo, 0.0)

    @property
    def z_mid(self):
        return 0.5 * (self.z_lo + self.z_hi)

    @property
    def thickness(self):
        return np.where(self.count > 0, self.z_hi - self.z_lo, 0.0)

    def x_of(self, i):
        return self.x0 + i * self.step

    def bin_of(self, x):
        return np.clip(((np.asarray(x) - self.x0) / self.step).astype(int), 0, len(self.count) - 1)


def profile(coords, bins=BINS):
    x = coords[:, 0]
    x0, x1 = float(x.min()), float(x.max())
    step = max(x1 - x0, 1e-12) / bins
    index = np.clip(((x - x0) / step).astype(int), 0, bins - 1)
    count = np.bincount(index, minlength=bins)
    ranges = []
    for axis in (1, 2):
        lo = np.full(bins, np.inf)
        hi = np.full(bins, -np.inf)
        np.minimum.at(lo, index, coords[:, axis])
        np.maximum.at(hi, index, coords[:, axis])
        lo[count == 0] = 0.0
        hi[count == 0] = 0.0
        ranges += [lo, hi]
    return Profile(x0, step, count, *ranges, index)


def _runs(mask):
    """[(start, end)] inclusive index ranges of True runs."""
    padded = np.concatenate(([False], mask, [False]))
    edges = np.flatnonzero(np.diff(padded.astype(np.int8)))
    return [(int(s), int(e) - 1) for s, e in zip(edges[::2], edges[1::2])]


def find_neck(prof):
    """(first, last) bins of the neck, the headstock being at +X, or None.

    Candidates are the slices narrower than NECK_MAX_WIDTH of the widest one; the longest run of them holds the
    neck and possibly the headstock. A line is fitted to the widths of the run with trimmed least squares: the
    neck's taper is linear and it is the longest part of the run, so the headstock and heel are the outliers.
    The neck is the longest stretch of inliers.
    """
    width = prof.width
    bins = len(width)
    if width.max() <= 0.0:
        return None
    candidates = (width < NECK_MAX_WIDTH * width.max()) & (prof.count > 0)
    runs = _runs(candidates)
    if not runs:
        return None
    start, end = max(runs, key=lambda r: r[1] - r[0])
    if end - start + 1 < NECK_MIN_LENGTH * bins:
        return None
    idx = np.arange(start, end + 1)
    w = width[idx]
    median = np.median(w)
    keep = np.abs(w - median) < 0.25 * median
    fit = np.full_like(w, median)
    for _ in range(10):
        if keep.sum() < 3:
            return None
        slope, intercept = np.polyfit(idx[keep], w[keep], 1)
        fit = intercept + slope * idx
        new = np.abs(w - fit) <= NECK_FIT_TOL * np.maximum(fit, 1e-12)
        if np.array_equal(new, keep):
            break
        keep = new
    # Close gaps of up to NECK_GAP outliers, then take the longest stretch.
    closed = keep.copy()
    for s, e in _runs(~keep):
        if s > 0 and e < len(keep) - 1 and e - s + 1 <= NECK_GAP:
            closed[s:e + 1] = True
    runs = _runs(closed)
    s, e = max(runs, key=lambda r: r[1] - r[0])
    if e - s + 1 < NECK_MIN_LENGTH * bins:
        return None
    return start + s, start + e


def neck_measurements(coords, prof, span):
    first, last = span
    in_neck = (prof.index >= first) & (prof.index <= last)
    idx = np.arange(first, last + 1)
    width = prof.width[idx]
    slope, intercept = np.polyfit(idx, width, 1)
    z = coords[in_neck, 2]
    mid_y = 0.5 * (prof.y_lo[idx] + prof.y_hi[idx])
    return Neck(
        joint_x=float(prof.x_of(first)), nut_x=float(prof.x_of(last + 1)),
        width_joint=float(intercept + slope * first), width_nut=float(intercept + slope * last),
        center_y=float(np.mean(mid_y)),
        fret_z=float(np.percentile(z, 95.0)), back_z=float(np.percentile(z, 5.0)),
    )


def measure(samples, axes=None):
    """Bounds and neck of the samples in frame coordinates (samples @ axes; the identity by default)."""
    coords = samples.points if axes is None else samples.points @ axes
    prof = profile(coords)
    span = find_neck(prof)
    return Measurements(coords.min(axis=0), coords.max(axis=0),
                        neck_measurements(coords, prof, span) if span is not None else None)


# Detection --------------------------------------------------------------------------------------------------------

def _string_cue(geometry, stats, strings, axes, prof):
    """Signed position of the string parts (indices into `stats`) relative to the slice middles."""
    if len(strings) < 2:
        return Cue('strings', 0.0, False, f"{len(strings)} long thin parts")
    sel = np.isin(stats.part_of, strings)
    coords = geometry.vertices[stats.order[sel]] @ axes
    bins = prof.bin_of(coords[:, 0])
    ok = prof.count[bins] > 0
    rel = (coords[:, 2] - prof.z_mid[bins]) / np.maximum(prof.thickness[bins], 1e-12)
    owner = stats.part_of[sel][ok]
    offset = (np.bincount(owner, weights=rel[ok], minlength=len(stats.ids))[strings]
              / np.maximum(np.bincount(owner, minlength=len(stats.ids))[strings], 1))
    score = float(np.average(offset, weights=stats.extent[strings]))
    return Cue('strings', score, abs(score) > CUE_MIN['strings'], f"{len(strings)} long thin parts")


def _neck_offset_cue(prof, span):
    width = prof.width
    body = (width > BODY_MIN_WIDTH * width.max()) & (np.arange(len(width)) < span[0])
    if not body.any():
        return Cue('neck_offset', 0.0, False, "no body before the neck")
    neck = np.arange(span[0], span[1] + 1)
    thick = float(np.mean(prof.thickness[body]))
    score = (float(np.mean(prof.z_mid[neck])) - float(np.mean(prof.z_mid[body]))) / max(thick, 1e-12)
    return Cue('neck_offset', score, abs(score) > CUE_MIN['neck_offset'], "neck versus body")


def _headstock_cue(coords, prof, span):
    """The headstock's median height below the neck's, in neck thicknesses: the string face is the other way."""
    in_neck = (prof.index >= span[0]) & (prof.index <= span[1])
    in_head = prof.index > span[1]
    if np.count_nonzero(in_head) < HEADSTOCK_MIN_SAMPLES:
        return Cue('headstock', 0.0, False, "no headstock after the nut")
    z = coords[in_neck, 2]
    thick = float(np.percentile(z, 95.0) - np.percentile(z, 5.0))
    score = (float(np.median(z)) - float(np.median(coords[in_head, 2]))) / max(thick, 1e-12)
    return Cue('headstock', score, abs(score) > CUE_MIN['headstock'], "headstock versus neck")


def _decide(cues):
    """(sign, confidence) by a majority of the valid cues; a tie goes to the first valid cue (the strings)."""
    valid = [cue for cue in cues if cue.valid]
    if not valid:
        return 1.0, 'LOW'
    votes = sum(1 if cue.score > 0.0 else -1 for cue in valid)
    if votes == 0:
        return (1.0 if valid[0].score > 0.0 else -1.0), 'LOW'
    if abs(votes) == len(valid):
        return (1.0 if votes > 0 else -1.0), ('HIGH' if len(valid) > 1 else 'MEDIUM')
    return (1.0 if votes > 0 else -1.0), 'MEDIUM'


def _orthonormal(x, z):
    z = z / np.linalg.norm(z)
    x = x - z * (x @ z)
    x /= np.linalg.norm(x)
    return np.column_stack((x, np.cross(z, x), z))


def _top_normal(samples, axes, coords, prof, span):
    """Mean normal of the faces on the string side of the body, or None if there are too few."""
    width = prof.width
    body = width > BODY_MIN_WIDTH * width.max()
    if span is not None:
        body &= np.arange(len(width)) < span[0]
    in_body = body[prof.index]
    b = prof.index[in_body]
    rel = (coords[in_body, 2] - prof.z_lo[b]) / np.maximum(prof.thickness[b], 1e-12)
    normals = samples.normals[in_body]
    along = normals @ axes[:, 2]
    top = (rel > 0.5) & (np.abs(along) > math.cos(TOP_NORMAL_CONE))
    if np.count_nonzero(top) < 50:
        return None
    mean = (normals[top] * np.sign(along[top])[:, None]).sum(axis=0)
    return mean / np.linalg.norm(mean)


def detect(samples, geometry):
    """Find the guitar frame from surface samples of `geometry`, which supplies the loose parts: string-like
    parts vote on the string face and are left out of the measurements where possible."""
    stats = part_stats(geometry) if len(geometry.part_ids) else None
    strings = string_parts(geometry, stats) if stats is not None else np.zeros(0, dtype=np.int64)
    points = samples.points
    if len(points) < 100:
        raise FrameError("The meshes have no faces to measure.")
    centroid = points.mean(axis=0)
    values, vectors = np.linalg.eigh(np.cov((points - centroid).T))
    if values[2] <= 0.0 or values[0] <= 1e-10 * values[2]:
        raise FrameError("The meshes are flat or a line: they do not look like a guitar.")
    axes = np.column_stack((vectors[:, 2], vectors[:, 1], np.cross(vectors[:, 2], vectors[:, 1])))
    messages = []

    # 1. Headstock: the narrower end.
    prof = profile(points @ axes)
    width = prof.width
    share = max(1, int(HEADSTOCK_SHARE * BINS))
    ends = [float(np.mean(w[w > 0.0])) if np.any(w > 0.0) else 0.0 for w in (width[:share], width[-share:])]
    if ends[0] < ends[1]:
        axes[:, :2] *= -1.0         # half turn about Z
        ends.reverse()
    ratio = ends[0] / max(ends[1], 1e-12)
    samples = solid_samples(samples, geometry, axes, stats, strings)
    points = samples.points

    # 2. String face.
    coords = points @ axes
    prof = profile(coords)
    span = find_neck(prof)
    cues = [_string_cue(geometry, stats, strings, axes, prof)]
    if span is not None:
        cues += [_neck_offset_cue(prof, span), _headstock_cue(coords, prof, span)]
    sign, confidence = _decide(cues)
    if sign < 0.0:
        axes[:, 1:] *= -1.0         # half turn about X
        for cue in cues:
            cue.score = -cue.score

    # 3. Refine Z to the body's top face, then X to the neck centreline.
    coords = points @ axes
    prof = profile(coords)
    span = find_neck(prof)
    top = _top_normal(samples, axes, coords, prof, span)
    if top is not None:
        axes = _orthonormal(axes[:, 0], top)
    if span is not None:
        coords = points @ axes
        prof = profile(coords)
        span = find_neck(prof)
    if span is not None:
        idx = np.arange(span[0], span[1] + 1)
        slope = np.polyfit(prof.x_of(idx + 0.5), 0.5 * (prof.y_lo[idx] + prof.y_hi[idx]), 1)[0]
        if abs(math.atan(slope)) < MAX_YAW_FIX:
            axes = _orthonormal(axes[:, 0] + slope * axes[:, 1], axes[:, 2])

    measurements = measure(samples, axes)
    if ratio < HEADSTOCK_MIN_RATIO:
        confidence = 'LOW'
        messages.append(('WARNING', f"Both ends are about as wide ({ratio:.2f}×): check that +X points to the "
                                    "headstock, and use Flip X if not."))
    valid = [cue for cue in cues if cue.valid]
    if valid:
        agree = [CUE_TITLES[cue.name] for cue in valid if cue.score > 0.0]
        against = [CUE_TITLES[cue.name] for cue in valid if cue.score <= 0.0]
        text = f"String face from the {', '.join(agree)}"
        if against:
            text += f"; the {', '.join(against)} disagree{'s' if len(against) == 1 else ''}"
        messages.append(('INFO' if confidence == 'HIGH' else 'WARNING', text + "."))
    if confidence != 'HIGH' and valid:
        messages.append(('WARNING', "Check that +Z points out of the strings, and use Flip Z if not."))
    if not valid:
        messages.append(('WARNING', "The string face could not be told from the geometry: check that +Z points out "
                                    "of the strings, and use Flip Z if not."))
    if measurements.neck is None:
        messages.append(('WARNING', "No neck found: preset landmarks are fitted to the bounding box and need "
                                    "checking."))
    return Detection(axes, measurements, ratio, cues, confidence, messages)
