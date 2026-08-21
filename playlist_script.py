"""SOILS - Song Outside-In List Sorter.

A shuffle that treats the *seam* between playthroughs as the thing worth
getting right.

Ordinary shuffle deals a fresh random permutation for every loop, which lets a
track close one loop and open the next.  SOILS builds each loop from the
outside in: it fixes the two outer bands first -- the head of the new loop and
its tail -- and only then fills the interior at random.

The head band is drawn exclusively from tracks that sat near the *front* of the
previous loop (longest since heard), and the tail band from tracks that sat
near its *back*.  Nothing in the previous loop's closing band can reach the new
loop's opening band, so spacing across the seam is bounded below rather than
left to chance.
"""

from __future__ import annotations

import random
from typing import Any, Iterable, List, Optional, Sequence

__all__ = ["SmartPlaylist"]


class SmartPlaylist:
    """A looping playlist whose loop seams are protected by a shield band.

    Parameters
    ----------
    tracks:
        The tracks to play.  Any objects are accepted; equal objects are
        treated as interchangeable by :meth:`remove_track`.
    shield_ratio:
        Fraction of the pool reserved as the shield band at each end of a
        loop.  Must satisfy ``0 < shield_ratio <= 0.5``: a shield of zero
        removes the guarantee the algorithm exists to provide, and a shield
        larger than half the list leaves nothing to fill the loop with.
    rng:
        Optional :class:`random.Random` for reproducible shuffles.
    """

    def __init__(
        self,
        tracks: Iterable[Any],
        shield_ratio: float = 0.25,
        rng: Optional[random.Random] = None,
    ) -> None:
        pool = list(tracks)
        if not pool:
            raise ValueError("A playlist needs at least one track.")
        if isinstance(shield_ratio, bool) or not isinstance(shield_ratio, (int, float)):
            raise ValueError("shield_ratio must be a number between 0 and 0.5.")
        if not 0 < shield_ratio <= 0.5:
            raise ValueError(
                "shield_ratio must be greater than 0 and no more than 0.5 "
                f"(got {shield_ratio!r}). A shield of 0 disables the seam "
                "guarantee; a shield above 50% cannot be filled."
            )

        self.master_pool: List[Any] = pool
        self.shield_ratio: float = float(shield_ratio)
        self._rng = rng if rng is not None else random.Random()

        self.loop_count: int = 0
        self._order: List[Any] = []
        self._index: int = 0
        self._previous_order: List[Any] = []

        self._build_loop()

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def shield_size(self) -> int:
        """Size of each outer band, for the pool's *current* length.

        Recomputed on demand so adding or removing tracks mid-loop resizes the
        shield instead of leaving it stale.
        """
        n = len(self.master_pool)
        if n < 2:
            return 0
        return max(1, min(int(n * self.shield_ratio), n // 2))

    @property
    def current_order(self) -> List[Any]:
        """The running order of the loop in progress."""
        return list(self._order)

    @property
    def remaining_in_loop(self) -> int:
        """How many tracks are left before the next seam."""
        return max(0, len(self._order) - self._index)

    def __len__(self) -> int:
        return len(self.master_pool)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"SmartPlaylist(tracks={len(self.master_pool)}, "
            f"shield_ratio={self.shield_ratio}, shield_size={self.shield_size}, "
            f"loop={self.loop_count}, position={self._index})"
        )

    # ------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------

    def get_next_track(self) -> Any:
        """Return the next track, rolling into a fresh loop when one ends."""
        if not self.master_pool:
            raise RuntimeError("The playlist is empty; there is nothing to play.")
        if self._index >= len(self._order):
            self._build_loop()
        track = self._order[self._index]
        self._index += 1
        return track

    def peek_next_track(self) -> Any:
        """Return the next track without consuming it."""
        if not self.master_pool:
            raise RuntimeError("The playlist is empty; there is nothing to play.")
        if self._index >= len(self._order):
            self._build_loop()
        return self._order[self._index]

    def reset(self) -> None:
        """Forget all history and start over from a fresh first loop."""
        self.loop_count = 0
        self._order = []
        self._previous_order = []
        self._build_loop()

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add_track(self, track: Any) -> None:
        """Add a track, slotting it somewhere in the unplayed remainder.

        The new track joins the loop in progress rather than waiting for the
        next one, so it is heard once per loop like everything else.
        """
        self.master_pool.append(track)
        position = self._rng.randint(self._index, len(self._order))
        self._order.insert(position, track)

    def remove_track(self, track: Any) -> None:
        """Remove a track from the pool and from the loop in progress.

        If the track already played this loop, the playback index shifts back
        with it so the caller does not skip the following track.
        """
        try:
            self.master_pool.remove(track)
        except ValueError:
            raise ValueError(f"{track!r} is not in this playlist.") from None

        try:
            position = self._order.index(track)
        except ValueError:
            return
        del self._order[position]
        if position < self._index:
            self._index -= 1

    # ------------------------------------------------------------------
    # The algorithm
    # ------------------------------------------------------------------

    def _build_loop(self) -> None:
        """Lay out the next loop: outer bands first, interior last."""
        self._previous_order = list(self._order)
        self._order = self._outside_in_order(self._previous_order)
        self._index = 0
        self.loop_count += 1

    def _outside_in_order(self, previous: Sequence[Any]) -> List[Any]:
        pool = list(self.master_pool)
        n = len(pool)
        shield = self.shield_size

        # First loop, or a shield too small to mean anything: plain shuffle.
        if not previous or shield < 1:
            self._rng.shuffle(pool)
            return pool

        # Only tracks still in the pool carry history forward; anything added
        # mid-loop has no history and is treated as freshly available.
        history = [t for t in previous if t in pool]
        if len(history) < n:
            history += [t for t in pool if t not in history]

        # Outer regions of the *previous* loop.  The front region is clamped so
        # it can never reach into the previous loop's closing band -- that
        # clamp is what makes the safety tenet hold.
        span = min(2 * shield, n - shield)
        front_region = history[:span]
        back_region = history[n - span:]

        remaining = list(pool)

        # 1. Outside: the new loop's opening band, drawn only from tracks that
        #    sat near the front of the previous loop.
        head = self._take(front_region, shield, remaining)

        # 2. Outside: the new loop's closing band, drawn from tracks that sat
        #    near the back of the previous loop and were not spent on the head.
        tail = self._take(back_region, shield, remaining)

        # 3. Inside: whatever is left, freely shuffled.
        middle = list(remaining)
        self._rng.shuffle(middle)

        return head + middle + tail

    def _take(self, region: Sequence[Any], count: int, remaining: List[Any]) -> List[Any]:
        """Pull `count` still-unused tracks, preferring ones from `region`.

        Falls back to the wider remainder when the two regions overlap enough
        that `region` alone cannot fill the band -- which starts to happen once
        the shield ratio climbs past a quarter of the list.
        """
        candidates = [t for t in region if t in remaining]
        self._rng.shuffle(candidates)
        chosen = candidates[:count]
        if len(chosen) < count:
            leftovers = [t for t in remaining if t not in chosen]
            self._rng.shuffle(leftovers)
            chosen += leftovers[: count - len(chosen)]
        for track in chosen:
            remaining.remove(track)
        self._rng.shuffle(chosen)
        return chosen
