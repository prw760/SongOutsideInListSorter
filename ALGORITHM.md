# Algorithm, guarantee, and tradeoffs

SOILS is a reference implementation of a constrained shuffle for repeating
playlists. Its guarantee concerns the boundary between consecutive loops.
It does not claim novelty or superiority to every shuffle algorithm.

## Definitions

Assume `n` distinct tracks, unchanged between loops, and sequential consumption
of every returned track. Let `r` be `shield_ratio`, with `0 < r <= 0.5`.

For `n >= 2`, the shield size is:

```text
s = max(1, min(floor(n * r), floor(n / 2)))
```

For one track, `s = 0`; every call necessarily repeats that track.

Repeat distance is the difference between two playback positions for the same
track. Adjacent plays have distance 1, with zero tracks between them.

## Constructing a loop

The first loop is an ordinary random permutation. For every subsequent loop:

1. Set `span = min(2 * s, n - s)`.
2. Select and shuffle `s` tracks from the previous loop's first `span` positions
   to form the new opening band. Remove them from the available pool.
3. Select and shuffle `s` available tracks, preferring the previous loop's last
   `span` positions, to form the closing band. The helper can fill a shortfall
   from the remaining pool.
4. Shuffle the remaining tracks and place them between the two bands.

The implementation is in `SmartPlaylist._outside_in_order` and `_take` in
[playlist_script.py](playlist_script.py). History reconciliation and editing
methods support mutable playlists, but the proof below assumes a fixed pool.

## Why the repeat distance is at least s + 1

Use zero-based positions. Suppose a track occurs at position `p` in the
previous loop and position `q` in the new loop. Its repeat distance is:

```text
d = n + q - p
```

There are two cases:

- If `q >= s`, then `p <= n - 1`, so `d >= n + s - (n - 1) = s + 1`.
- If `q < s`, the track belongs to the opening band. That band is drawn from
  the previous first `span` positions, and `span <= n - s`. Therefore
  `p <= n - s - 1`, so `d >= n + 0 - (n - s - 1) = s + 1`.

The opening band always has enough distinct candidates because `s <= n / 2`
implies `span >= s`. Its selection therefore needs no fallback outside the
front region under these assumptions.

Each loop is a permutation: every selection removes its tracks from the
available pool, and the middle uses the remainder. Consecutive occurrences
of each track consequently lie in adjacent loops, so the proof covers the
whole stream. The bound need not be attained in a finite run.

## Frequency is different from mixing

Each track plays once per full loop. Over indefinitely many loops, its mean
repeat distance approaches `n`: summing consecutive distances telescopes to
`k * n + p_last - p_first`, where the endpoint correction is bounded by
`n - 1`. Finite samples can differ from `n`.

SOILS deliberately excludes some permutations. Higher shield ratios protect
more spacing at the cost of mixing. With even `n` and `r = 0.5`, `s = n / 2`
and `span = n / 2`; the opening half is always drawn from the previous opening
half. Tracks cannot move between halves, although their order within each
half can change. Equal frequency alone is not evidence of good perceived
randomness, and listener studies have not been conducted here.

## Complexity and integration limits

With constant-time equality comparisons, building a loop is `O(n^2)` in the
current implementation because it repeatedly searches and removes from
lists. Storage is `O(n)`. Consuming a track inside an existing loop is `O(1)`;
crossing the boundary triggers loop construction. These are code-level bounds,
not measured latency claims.

An integration into a player needs explicit decisions about duplicate track
identity, previous/next controls, skipped tracks, queue changes, repeat mode,
and history persistence. The current proof does not establish a minimum
listening gap after such operations. No player integration is included yet.

The [demo](demo.py) compares this implementation with independent per-loop
reshuffling. It does not benchmark Spotify, Quod Libet, or their shuffle modes.
