# SOILS — Song Outside-In List Sorter

A Python reference implementation of a looping shuffle that limits how soon a
song can repeat when one playthrough ends and the next begins.

**Maintained by [Paul R. Wade (@prw760)](https://github.com/prw760).**
MIT licensed · No runtime dependencies · Python 3.8+

[![Tests](https://github.com/prw760/SongOutsideInListSorter/actions/workflows/tests.yml/badge.svg)](https://github.com/prw760/SongOutsideInListSorter/actions/workflows/tests.yml)

## The problem

Independently shuffling a playlist on each loop can put the same song at the end
of one loop and the beginning of the next. Every song still gets a turn, but a
listener can hear an immediate repeat.

SOILS carries the previous loop's order forward. It builds the next loop from
the outside in: choose an opening band from earlier tracks, choose a closing
band with a preference for later tracks, then shuffle the remaining middle.
The previous closing band cannot appear in the next opening band.

```text
Previous loop: [ earlier tracks ............ | closing shield ]
                    |                              X
                    v                              | excluded
Next loop:     [ opening shield | shuffled middle | closing shield ]
```

## What it guarantees

For a **fixed playlist of distinct tracks**, played sequentially without edits
or resets, the distance between consecutive plays of a track is **at least
`shield_size + 1`**. A distance of 8 means seven other tracks play between them.
Each track appears exactly once per loop.

For 30 distinct tracks:

| Method | Shield size | Guaranteed repeat distance |
| --- | ---: | ---: |
| Independent shuffle each loop | — | At least 1 (immediate repeats possible) |
| SOILS, `shield_ratio=0.25` | 7 | At least 8 |
| SOILS, `shield_ratio=0.5` | 15 | At least 16 |

These are lower bounds; an individual run need not reach them. Equal play
frequency does **not** mean uniformly random ordering. Stronger shields reduce
mixing; at a 50% shield with an even track count, tracks stay in the same half
of the playlist across loops. See [the algorithm and proof](ALGORITHM.md).

## Try it

Clone the repository and run the demonstration using Python 3.8 or newer:

```bash
git clone https://github.com/prw760/SongOutsideInListSorter.git
cd SongOutsideInListSorter
python3 demo.py --tracks 30 --loops 400 --shield-ratio 0.25 --seed 1848
```

The demo prints two consecutive loops and compares repeat-distance histograms
with independent reshuffling. In a local run with these parameters, the
baseline's shortest repeat distance was 1 and SOILS' was 8. The baseline had
364 repeat distances of 7 or less; SOILS had zero. These are simulation results,
not measurements from a music player. Seeded output may vary between Python
versions.

Use the class directly from the repository:

```python
import random
from playlist_script import SmartPlaylist

playlist = SmartPlaylist(
    [f"Song {number}" for number in range(1, 31)],
    shield_ratio=0.25,
    rng=random.Random(1848),
)

for _ in range(60):  # two full playthroughs
    print(playlist.get_next_track())
```

To import it from another project, install this checkout into that project's
virtual environment with `python3 -m pip install .`. This documentation does
not assume that a package named `soils` on a package index is this project.

## API

| Member | Behavior |
| --- | --- |
| `SmartPlaylist(tracks, shield_ratio=0.25, rng=None)` | Create a nonempty playlist; optionally supply `random.Random(seed)`. |
| `get_next_track()` | Consume the next track; create a new loop when needed. |
| `peek_next_track()` | Return the next track without consuming it; may create a new loop. |
| `add_track(track)` | Insert a track into the unplayed part of the current loop. |
| `remove_track(track)` | Remove the first equal occurrence and adjust the playback index. |
| `shield_size` | Band size calculated from the current pool size and shield ratio. |
| `current_order` | A copy of the current loop's order. |
| `remaining_in_loop` | Number of unconsumed entries in the current loop. |
| `loop_count` | Number of loops constructed, including the initial loop. |
| `reset()` | Discard history and start a fresh first loop. |

`shield_ratio` must satisfy `0 < shield_ratio <= 0.5`. An empty initial playlist
raises `ValueError`; requesting a track after removing all entries raises
`RuntimeError`. Use the add/remove methods instead of modifying `master_pool`
directly.

## Scope and tradeoffs

- This is a standalone algorithm and demo, not an audio player or an installed
  Spotify or Quod Libet integration.
- The repeat-distance guarantee assumes distinct tracks under Python equality.
  Duplicate entries can represent the same song and defeat a song-level bound.
- Mid-loop add/remove operations preserve playback position as documented, but
  the fixed-playlist guarantee does not cover edits, resets, manual jumps, or
  actual listening when returned tracks are skipped.
- The first loop is an ordinary shuffle. There is no persistent listening
  history between program runs.
- The current list-based implementation uses quadratic work to build a loop
  and linear storage. Large-library integration needs performance measurements.

## Validation and contributions

```bash
python3 test_playlist.py
python3 test_playlist.py --tracks 250
python3 test_playlist.py --tracks 8
```

The 19-test suite covers protected loop boundaries, once-per-loop coverage,
mid-loop edits, input validation, and seeded reproducibility. GitHub Actions
runs these commands on Python 3.9, 3.11, and 3.13.

See [CONTRIBUTING.md](CONTRIBUTING.md) for reproducible bug reports and proposed
changes. Useful next steps include player integration, measuring performance
on larger playlists, and defining history behavior for skips and edits.

An optional Quod Libet integration has been proposed in
[quodlibet/quodlibet#4970](https://github.com/quodlibet/quodlibet/issues/4970).
It is a request for maintainer feedback; no integration PR has been submitted
or accepted.

## Credits and license

Project maintained by Paul R. Wade. Development has used AI assistance: the
initial implementation records Claude as a coauthor, and Codex assisted with
the documentation and publication preparation. The code, tests, and stated
limitations are available for independent review.

[MIT License](LICENSE), copyright 2026 Paul R. Wade.
