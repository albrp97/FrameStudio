import unittest

from resolve_editor.playback import (
    PlaybackBackendError,
    PlaybackController,
    PlaybackState,
)


class FakeBackend:
    def __init__(self):
        self.calls = []
        self.fail = None

    def play(self):
        self.calls.append(("play",))
        if self.fail:
            raise PlaybackBackendError(self.fail)

    def pause(self):
        self.calls.append(("pause",))

    def seek(self, position):
        self.calls.append(("seek", position))

    def stop(self):
        self.calls.append(("stop",))


class EditorPlaybackTests(unittest.TestCase):
    def test_play_pause_and_seek_update_observable_state(self):
        backend = FakeBackend()
        controller = PlaybackController(backend, 10.0)

        controller.play()
        self.assertEqual(controller.snapshot().state, PlaybackState.PLAYING)
        controller.pause()
        self.assertEqual(controller.snapshot().state, PlaybackState.PAUSED)
        controller.seek(4.0)

        snapshot = controller.snapshot()
        self.assertEqual(snapshot.state, PlaybackState.PAUSED)
        self.assertEqual(snapshot.position_seconds, 4.0)
        self.assertEqual(backend.calls, [("play",), ("pause",), ("seek", 4.0)])

    def test_seek_clamps_position_and_preserves_playing_state(self):
        backend = FakeBackend()
        controller = PlaybackController(backend, 10.0)
        controller.play()
        controller.seek(20.0)

        snapshot = controller.snapshot()
        self.assertEqual(snapshot.state, PlaybackState.PLAYING)
        self.assertEqual(snapshot.position_seconds, 10.0)
        self.assertEqual(backend.calls[-1], ("seek", 10.0))

    def test_backend_failure_becomes_explicit_error_state(self):
        backend = FakeBackend()
        backend.fail = "decoder unavailable"
        controller = PlaybackController(backend, 10.0)

        controller.play()

        snapshot = controller.snapshot()
        self.assertEqual(snapshot.state, PlaybackState.ERROR)
        self.assertEqual(snapshot.error, "decoder unavailable")


if __name__ == "__main__":
    unittest.main()
