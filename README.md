# SOILS — Song Outside-In List Sorter

A looping shuffle that treats the **seam between playthroughs** as the thing worth getting right.

A plain shuffle deals a fresh random permutation for every loop. Each loop is fair on its own,
but nothing connects one loop to the next, so a track can close one loop and open the next —
back to back. That is the single most noticeable failure a shuffle can have, and it is the one
ordinary shuffles do nothing about.

SOILS builds each loop **from the outside in**: it places the two outer bands first — the head
of the new loop and its tail — and only then fills the interior at random.

```
        previous loop                       new loop
  ┌──────┬──────────────┬──────┐     ┌──────┬──────────────┬──────┐
  │ head │    middle    │ tail │ ──▶ │ head │    middle    │ tail │
  └──────┴──────────────┴──────┘     └──────┴──────────────┴──────┘
     ▲                      │           ▲                      ▲
     │                      │           │                      │
     └──── drawn from ──────────────────┘                      │
                            └──── drawn from ───────────────────┘
```

The new loop's **head band** is drawn only from tracks that sat near the *front* of the previous
loop — the ones heard longest ago. Its **tail band** is drawn from tracks that sat near the
*back*. The interior is a free shuffle. Because the head band can never reach into the previous
loop's closing band, the shortest possible gap between two plays of the same track is bounded
below by construction, not left to luck.

## The guarantee

With a 30-track list and the default 25% shield (a 7-track band):

| | minimum gap between repeats | mean gap |
|---|---|---|
| naive per-loop reshuffle | **1** | 30.0 |
| SOILS, `shield_ratio=0.25` | **8** | 30.0 |
| SOILS, `shield_ratio=0.5` | **16** | 30.0 |

The minimum gap is always `shield_size + 1`. Fairness is untouched — every track still plays
exactly once per loop, so the mean gap stays at the list length.

## Usage

```python
from playlist_script import SmartPlaylist

playlist = SmartPlaylist(["Song #1", "Song #2", ...], shield_ratio=0.25)

while True:
    play(playlist.get_next_track())
```

The playlist loops forever. Each loop plays every track exactly once, and each seam honours the
shield.

### Editing while it plays

```python
playlist.add_track("Surprise New Track")   # joins the loop in progress
playlist.remove_track("Song #7")           # index shifts back, nothing gets skipped
```

`add_track` slots the newcomer somewhere in the *unplayed remainder*, so it is heard this loop
rather than waiting for the next one. `remove_track` adjusts the playback index when the removed
track had already played, so the following track is not silently swallowed. The shield resizes
itself to the new pool length automatically.

### API

| member | description |
|---|---|
| `SmartPlaylist(tracks, shield_ratio=0.25, rng=None)` | Build a playlist. Pass `rng=random.Random(seed)` for reproducible orderings. |
| `get_next_track()` | Next track, rolling into a fresh loop at the seam. |
| `peek_next_track()` | Same, without consuming it. |
| `add_track(track)` / `remove_track(track)` | Mutate the pool mid-loop. |
| `master_pool` | The live list of tracks. |
| `shield_size` | Current band size, recomputed from the pool length. |
| `current_order` / `remaining_in_loop` | The running order, and how far to the next seam. |
| `loop_count` | How many loops have been laid out. |
| `reset()` | Forget history and start from a fresh first loop. |

### `shield_ratio`

Must satisfy `0 < shield_ratio <= 0.5`. Both ends are rejected loudly with a `ValueError`:
a shield of `0` removes the guarantee the algorithm exists to provide, and a shield above half
the list leaves nothing to fill the loop with. Past `0.25` the front and back regions begin to
overlap and the tail band tops itself up from the wider remainder — the head-band guarantee is
structural and holds regardless.

## Tests

```bash
python test_playlist.py                 # 30-track sample list (default)
python test_playlist.py --tracks 100    # override the sample size
SOILS_TEST_TRACKS=100 python -m unittest test_playlist
```

The suite covers the core safety tenet at a single seam and across 50 consecutive seams, the
stronger whole-band property, per-loop fairness, mid-loop insertion and deletion, shield-ratio
validation, and reproducibility under a seeded RNG.

```bash
python demo.py            # see the ordering, and the gap histogram vs naive shuffle
```

## License

MIT — see [LICENSE](LICENSE).
