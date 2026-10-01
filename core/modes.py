"""The mode of each frame (§5.8): the scene's settings, or a frame range solved in another mode.

A range override applies its mode's switch (magnets.MODE_PRESETS) for its frames, on top of the scene's settings:
the neck aim on or off, and the fretboard-edge magnet's power and filter. Outside the ranges the scene's settings
are used as they are, whatever the user edited after choosing the scene's mode. Where enabled ranges overlap,
the one lower in the list wins.

A frame starts a new run where it is solved under another switch than the frame before. There a bake starts its
filters and the snap magnets' hysteresis afresh: their history belongs to the other mode's magnets. The neck aim
weight cross-fades over FADE_FRAMES frames from the run's start, from the weight the frame before had to the new
one, so the guitar eases between its aimed and its mounted rotation. Everything here depends on the frame alone,
so Solve Frame shows the frame as a bake solves it.
"""

from dataclasses import dataclass

from .magnets import MODE_PRESETS

FADE_FRAMES = 5
SCENE = -1                  # the run key of frames without an override


@dataclass(frozen=True)
class FrameMode:
    """How one frame is solved."""
    mode: str                   # 'FOLLOW' or 'ALIGN'
    override: int               # index of the range override that applies, or SCENE
    aim_weight: float           # the neck aim weight after the cross-fade (0: no aim)
    run_start: bool             # the frame before was solved under another switch

    def magnet(self, item, name):
        """The value of magnet `item`'s setting `name` on this frame."""
        if self.override != SCENE:
            switched = MODE_PRESETS[self.mode]["magnets"].get(item.preset_id, {})
            if name in switched:
                return switched[name]
        return getattr(item, name)


class Schedule:
    """The FrameMode of any frame for a scene's settings (read once)."""

    def __init__(self, settings):
        self.scene_mode = settings.mode
        self.weight = settings.aim_weight
        self.scene_aims = settings.aim_enabled
        self.ranges = [(index, item.frame_start, item.frame_end, item.mode)
                       for index, item in enumerate(settings.range_overrides)
                       if item.enabled and item.frame_end >= item.frame_start]

    def override(self, frame):
        """Index of the override that applies at `frame`, or SCENE."""
        found = SCENE
        for index, start, end, _mode in self.ranges:
            if start <= frame <= end:
                found = index
        return found

    def mode(self, override):
        return self.scene_mode if override == SCENE else next(m for i, _s, _e, m in self.ranges if i == override)

    def _key(self, frame):
        """What decides a run: frames with the same key are solved under the same switch."""
        override = self.override(frame)
        return SCENE if override == SCENE else self.mode(override)

    def _target(self, frame):
        override = self.override(frame)
        aims = self.scene_aims if override == SCENE else MODE_PRESETS[self.mode(override)]["aim_enabled"]
        return self.weight if aims else 0.0

    def _weight(self, frame, depth=0):
        key = self._key(frame)
        target = self._target(frame)
        for back in range(1, FADE_FRAMES):
            if self._key(frame - back) != key:
                if depth > 2 * len(self.ranges) + 2:
                    return target
                before = self._weight(frame - back, depth + 1)
                return before + (target - before) * back / FADE_FRAMES
        return target

    def at(self, frame):
        override = self.override(frame)
        return FrameMode(self.mode(override), override, self._weight(frame),
                         self._key(frame - 1) != self._key(frame))

    def runs(self, start, end):
        """[(first frame, last frame, FrameMode of the first)] of the runs in start..end."""
        runs = []
        for frame in range(start, end + 1):
            if frame == start or self._key(frame - 1) != self._key(frame):
                runs.append([frame, frame, self.at(frame)])
            else:
                runs[-1][1] = frame
        return [tuple(run) for run in runs]
