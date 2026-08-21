"""Test suite for the SOILS outside-in playlist sorter.

The sample songlist is 30 tracks by default.  Override it without editing the
file, either way:

    python test_playlist.py --tracks 100
    SOILS_TEST_TRACKS=100 python -m unittest test_playlist
"""

import os
import sys
import unittest

from playlist_script import SmartPlaylist

DEFAULT_TRACK_COUNT = 30


def resolve_track_count(argv=None, environ=None, default=DEFAULT_TRACK_COUNT):
    """Read the sample songlist size from `--tracks N` or $SOILS_TEST_TRACKS.

    The `--tracks` flag is stripped out of `argv` so unittest's own parser
    never sees it.  A flag beats the environment; the environment beats the
    default.
    """
    argv = sys.argv if argv is None else argv
    environ = os.environ if environ is None else environ

    count = None
    raw_env = environ.get("SOILS_TEST_TRACKS")
    if raw_env:
        count = int(raw_env)

    i = 1
    while i < len(argv):
        arg = argv[i]
        if arg == "--tracks":
            count = int(argv[i + 1])
            del argv[i : i + 2]
            continue
        if arg.startswith("--tracks="):
            count = int(arg.split("=", 1)[1])
            del argv[i]
            continue
        i += 1

    if count is None:
        return default
    if count < 4:
        raise ValueError("The sample songlist needs at least 4 tracks.")
    return count


TRACK_COUNT = resolve_track_count()


class TestInsideOutPlaylist(unittest.TestCase):

    track_count = TRACK_COUNT

    def setUp(self):
        """Runs before every single test to provide a clean sample playlist."""
        self.track_count = type(self).track_count
        self.mock_tracks = [f"Song #{i}" for i in range(1, self.track_count + 1)]
        self.playlist = SmartPlaylist(self.mock_tracks, shield_ratio=0.25)
        self.shield_size = self.playlist.shield_size

    def test_core_safety_tenet(self):
        """
        CRITICAL TEST: Verifies that the track closing Loop 1
        NEVER appears in the initial shield buffer of Loop 2.
        """
        # 1. Play through the entirety of Loop 1
        last_track_loop_1 = None
        for _ in range(self.track_count):
            last_track_loop_1 = self.playlist.get_next_track()

        # 2. Grab the opening shield band of Loop 2
        shield_buffer_loop_2 = [
            self.playlist.get_next_track() for _ in range(self.shield_size)
        ]

        # 3. Assert that the last song played is absolutely NOT in this initial block
        self.assertNotIn(
            last_track_loop_1,
            shield_buffer_loop_2,
            msg="CRITICAL FAILURE: Last song of Loop 1 repeated inside the safety shield of Loop 2!",
        )

    def test_core_safety_tenet_holds_over_many_loops(self):
        """The tenet is a guarantee, not a lucky draw -- hold it across 50 seams."""
        loops = 50
        stream = [
            self.playlist.get_next_track()
            for _ in range(self.track_count * loops)
        ]

        for seam in range(self.track_count, len(stream), self.track_count):
            loop_number = seam // self.track_count
            closing_track = stream[seam - 1]
            opening_shield = stream[seam : seam + self.shield_size]
            self.assertNotIn(
                closing_track,
                opening_shield,
                msg=f"Safety shield breached at the seam between loops {loop_number} and {loop_number + 1}.",
            )

    def test_whole_closing_band_is_kept_out_of_the_opening_band(self):
        """Stronger than the tenet: no closing-band track opens the next loop."""
        loops = 20
        stream = [
            self.playlist.get_next_track()
            for _ in range(self.track_count * loops)
        ]

        for seam in range(self.track_count, len(stream), self.track_count):
            closing_band = set(stream[seam - self.shield_size : seam])
            opening_band = set(stream[seam : seam + self.shield_size])
            self.assertEqual(
                closing_band & opening_band,
                set(),
                msg="A track from the closing band reappeared in the opening band.",
            )

    def test_every_track_plays_exactly_once_per_loop(self):
        """No track is starved and none is doubled inside a single loop."""
        played = [self.playlist.get_next_track() for _ in range(self.track_count)]
        self.assertCountEqual(played, self.mock_tracks)

    def test_dynamic_small_playlist_safety(self):
        """Verifies that the math holds together perfectly even at a small size like 10 songs."""
        small_tracks = [f"Track {i}" for i in range(10)]
        small_playlist = SmartPlaylist(small_tracks, shield_ratio=0.25)  # shield size = 2

        # Play Loop 1
        last_track = None
        for _ in range(10):
            last_track = small_playlist.get_next_track()

        # Check Loop 2 shield (size 2)
        shield = [small_playlist.get_next_track() for _ in range(2)]

        self.assertEqual(small_playlist.shield_size, 2)
        self.assertNotIn(last_track, shield, msg="Failed safety rule on a small 10-song playlist.")

    def test_mid_loop_track_addition(self):
        """Verifies that adding a track mid-loop doesn't crash the index tracking or calculations."""
        halfway = self.track_count // 2
        # Play halfway through
        for _ in range(halfway):
            self.playlist.get_next_track()

        try:
            self.playlist.add_track("🔥 Surprise New Track")
            # Play out the rest of the loop (+1 to account for the new track)
            for _ in range(self.track_count - halfway + 1):
                self.playlist.get_next_track()
        except Exception as e:
            self.fail(f"Adding a track mid-loop raised an unexpected exception: {e}")

        self.assertEqual(len(self.playlist.master_pool), self.track_count + 1)

    def test_added_track_is_heard_within_the_same_loop(self):
        """A track added mid-loop joins the loop in progress, it doesn't wait."""
        halfway = self.track_count // 2
        for _ in range(halfway):
            self.playlist.get_next_track()

        newcomer = "🔥 Surprise New Track"
        self.playlist.add_track(newcomer)
        rest_of_loop = [
            self.playlist.get_next_track()
            for _ in range(self.track_count - halfway + 1)
        ]
        self.assertIn(newcomer, rest_of_loop)

    def test_mid_loop_track_deletion(self):
        """Verifies that removing an already-played track dynamically updates the internal playback index safely."""
        # Play the first few tracks and keep note of one we've listened to
        sample = max(2, self.track_count // 3)
        played_tracks = []
        for _ in range(sample):
            played_tracks.append(self.playlist.get_next_track())

        target_to_delete = played_tracks[sample // 2]

        try:
            # Delete the track we already heard
            self.playlist.remove_track(target_to_delete)
            # Ensure the total pool size dropped by 1
            self.assertEqual(len(self.playlist.master_pool), self.track_count - 1)
        except Exception as e:
            self.fail(f"Removing a track mid-loop raised an unexpected exception: {e}")

    def test_deleting_unplayed_track_does_not_skip_its_neighbour(self):
        """Removing a track still ahead of the needle must not swallow the next one."""
        self.playlist.get_next_track()
        upcoming = self.playlist.current_order[1:]
        doomed = upcoming[2]
        expected_next = upcoming[0]

        self.playlist.remove_track(doomed)
        self.assertEqual(self.playlist.get_next_track(), expected_next)

    def test_removing_absent_track_raises(self):
        """Deleting something that was never there is a caller error, not a silent no-op."""
        with self.assertRaises(ValueError):
            self.playlist.remove_track("Song That Does Not Exist")

    def test_invalid_shield_ratio_protection(self):
        """Ensures the class rejects breaking shield values (like 0% or > 50%) immediately."""
        with self.assertRaises(ValueError):
            SmartPlaylist(self.mock_tracks, shield_ratio=0.55)  # Cannot shield more than half the list

        with self.assertRaises(ValueError):
            SmartPlaylist(self.mock_tracks, shield_ratio=0.0)  # 0% shield breaks the algorithm

        with self.assertRaises(ValueError):
            SmartPlaylist(self.mock_tracks, shield_ratio=-0.25)  # Negative shields are nonsense

    def test_empty_playlist_rejected(self):
        """A playlist with nothing in it cannot honour any guarantee."""
        with self.assertRaises(ValueError):
            SmartPlaylist([])

    def test_seeded_runs_are_reproducible(self):
        """Passing an rng makes an otherwise random ordering repeatable."""
        import random

        def run():
            playlist = SmartPlaylist(self.mock_tracks, rng=random.Random(1848))
            return [playlist.get_next_track() for _ in range(self.track_count * 2)]

        self.assertEqual(run(), run())


class TestTrackCountResolution(unittest.TestCase):
    """The songlist size defaults to 30 and can be overridden by flag or env."""

    def test_defaults_to_thirty(self):
        self.assertEqual(resolve_track_count(argv=["test_playlist.py"], environ={}), 30)

    def test_flag_overrides_default(self):
        argv = ["test_playlist.py", "--tracks", "64"]
        self.assertEqual(resolve_track_count(argv=argv, environ={}), 64)
        self.assertEqual(argv, ["test_playlist.py"], "the flag should be consumed")

    def test_equals_form_of_flag(self):
        argv = ["test_playlist.py", "--tracks=12"]
        self.assertEqual(resolve_track_count(argv=argv, environ={}), 12)
        self.assertEqual(argv, ["test_playlist.py"])

    def test_environment_override(self):
        self.assertEqual(
            resolve_track_count(argv=["test_playlist.py"], environ={"SOILS_TEST_TRACKS": "48"}),
            48,
        )

    def test_flag_beats_environment(self):
        self.assertEqual(
            resolve_track_count(
                argv=["test_playlist.py", "--tracks", "7"],
                environ={"SOILS_TEST_TRACKS": "48"},
            ),
            7,
        )

    def test_absurdly_small_songlist_rejected(self):
        with self.assertRaises(ValueError):
            resolve_track_count(argv=["test_playlist.py", "--tracks", "2"], environ={})


if __name__ == '__main__':
    print(f"Sample songlist: {TRACK_COUNT} tracks")
    unittest.main()
