"""Show what the outside-in sort buys you, next to a naive per-loop reshuffle."""

import argparse
import random
from collections import Counter

from playlist_script import SmartPlaylist


def gaps_for(stream):
    """Distance between consecutive plays of the same track."""
    last, gaps = {}, []
    for position, track in enumerate(stream):
        if track in last:
            gaps.append(position - last[track])
        last[track] = position
    return gaps


def naive_stream(tracks, loops, rng):
    """The baseline: reshuffle the whole list every loop, seams be damned."""
    stream = []
    for _ in range(loops):
        loop = list(tracks)
        rng.shuffle(loop)
        stream += loop
    return stream


def soils_stream(tracks, loops, shield_ratio, rng):
    playlist = SmartPlaylist(tracks, shield_ratio=shield_ratio, rng=rng)
    return [playlist.get_next_track() for _ in range(len(tracks) * loops)]


def histogram(gaps, buckets, width=44):
    counts = Counter()
    for gap in gaps:
        for low, high in buckets:
            if low <= gap <= high:
                counts[(low, high)] += 1
                break
    tallest = max(counts.values()) if counts else 1
    lines = []
    for low, high in buckets:
        count = counts[(low, high)]
        if high == float("inf"):
            label = f"{low}+"
        elif low == high:
            label = f"{low}"
        else:
            label = f"{low}-{high}"
        bar = "█" * round(width * count / tallest)
        lines.append(f"  {label:>7} │{bar} {count}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tracks", type=int, default=30, help="sample songlist size (default: 30)")
    parser.add_argument("--loops", type=int, default=400, help="loops to simulate (default: 400)")
    parser.add_argument("--shield-ratio", type=float, default=0.25, help="shield band fraction (default: 0.25)")
    parser.add_argument("--seed", type=int, default=1848, help="RNG seed for a repeatable run")
    args = parser.parse_args()

    tracks = [f"Song #{i}" for i in range(1, args.tracks + 1)]
    playlist = SmartPlaylist(tracks, shield_ratio=args.shield_ratio, rng=random.Random(args.seed))
    shield = playlist.shield_size

    print(f"{args.tracks} tracks · shield_ratio={args.shield_ratio} · shield band = {shield} tracks\n")

    print("First two loops, with the seam marked:")
    first = [playlist.get_next_track() for _ in range(args.tracks)]
    second = [playlist.get_next_track() for _ in range(args.tracks)]
    numbers = lambda loop: " ".join(t.split("#")[1].rjust(3) for t in loop)
    print(f"  loop 1  {numbers(first)}")
    print(f"  loop 2  {numbers(second)}")
    print(f"\n  loop 1 closed with {first[-1]!r}")
    print(f"  loop 2 opened with {second[:shield]}")
    print(f"  closer inside the opening shield? {first[-1] in second[:shield]}")

    soils = soils_stream(tracks, args.loops, args.shield_ratio, random.Random(args.seed))
    naive = naive_stream(tracks, args.loops, random.Random(args.seed))
    soils_gaps, naive_gaps = gaps_for(soils), gaps_for(naive)

    print(f"\n{args.loops} loops simulated:\n")
    print(f"  {'':<26}{'min gap':>9}{'mean gap':>10}{'gaps < shield':>15}")
    for name, gaps in (("naive per-loop reshuffle", naive_gaps), ("SOILS outside-in", soils_gaps)):
        tight = sum(1 for g in gaps if g <= shield)
        print(f"  {name:<26}{min(gaps):>9}{sum(gaps) / len(gaps):>10.1f}{tight:>15}")

    buckets = [(1, 1), (2, shield), (shield + 1, args.tracks), (args.tracks + 1, float("inf"))]
    print("\n  naive per-loop reshuffle")
    print(histogram(naive_gaps, buckets))
    print("\n  SOILS outside-in")
    print(histogram(soils_gaps, buckets))


if __name__ == "__main__":
    main()
