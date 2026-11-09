# Contributing to SOILS

Bug reports, explanations of edge cases, and focused pull requests are welcome.
For larger changes or player integrations, open an issue first so the intended
behavior and scope can be discussed.

## Run locally

Use Python 3.8 or newer. The implementation, demo, and tests use only the
standard library; no dependency installation is needed to run them from the
repository root.

```bash
python3 test_playlist.py
python3 test_playlist.py --tracks 250
python3 test_playlist.py --tracks 8
python3 demo.py --tracks 30 --loops 400 --shield-ratio 0.25 --seed 1848
```

CI tests Python 3.9, 3.11, and 3.13. Keep implementation changes compatible
with the Python version declared in `pyproject.toml`, or discuss changing it.

## Report a bug

Open a [GitHub issue](https://github.com/prw760/SongOutsideInListSorter/issues)
with the Python version, track count, shield ratio, random seed, relevant
operations in order, expected behavior, and actual output. A short script
using synthetic track names is ideal; personal listening history is unnecessary.

For a claimed repeat-distance failure, specify whether tracks were distinct
and whether the playlist was edited, reset, or skipped. The assumptions in
[ALGORITHM.md](ALGORITHM.md) determine which guarantee applies.

## Submit a change

1. Fork the repository and make a branch for a focused change.
2. Explain the problem and resulting behavior in the pull request.
3. For behavior changes, add a regression test that demonstrates the problem.
   Use explicit random seeds when checking a reproducible sequence.
4. Run the test commands above and report the results and Python version.
5. Update the relevant documentation if guarantees, limitations, or APIs change.

Useful areas include performance measurements, tests for unusual playlist
operations, and optional integrations with open-source players. Describe any
AI assistance honestly and review generated changes before submitting them.

Contributions are made under the repository's [MIT License](LICENSE).
