from __future__ import annotations

import gc
import importlib.util
import io
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from framestudio import precise_preview_worker as worker


@unittest.skipUnless(importlib.util.find_spec("av"), "Optional PyAV runtime is required")
class PreviewWorkerStartupTests(unittest.TestCase):
    def test_freezes_imports_before_control_thread_and_decoder_state(self):
        from framestudio import precise_preview_native as native

        events = []
        pool = MagicMock()
        pool.close.side_effect = lambda: events.append("close")
        inbox = MagicMock(stopped=True)
        stdout = SimpleNamespace(buffer=io.BytesIO())

        def create(value, result):
            def construct(*args, **kwargs):
                events.append(value)
                return result

            return construct

        enabled = gc.isenabled()
        with (
            patch.object(
                worker, "sys", SimpleNamespace(argv=["worker", "cpu", "epoch"], stdout=stdout)
            ),
            patch.object(worker, "rss_limit", return_value=1024),
            patch.object(gc, "collect", side_effect=lambda: events.append("collect")),
            patch.object(gc, "freeze", side_effect=lambda: events.append("freeze")),
            patch.object(worker, "Inbox", side_effect=create("inbox", inbox)),
            patch.object(worker.threading, "Thread", side_effect=create("thread", MagicMock())),
            patch.object(native, "DecoderPool", side_effect=create("pool", pool)),
        ):
            worker.main()
        self.assertEqual(events, ["collect", "freeze", "inbox", "thread", "pool", "close"])
        self.assertEqual(gc.isenabled(), enabled)

    def test_version_failure_does_not_freeze_or_create_live_state(self):
        stdout = SimpleNamespace(buffer=io.BytesIO())
        with (
            patch.object(
                worker, "sys", SimpleNamespace(argv=["worker", "cpu", "epoch"], stdout=stdout)
            ),
            patch.dict("sys.modules", {"av": SimpleNamespace(__version__="unsupported")}),
            patch.object(gc, "freeze") as freeze,
            patch.object(worker, "Inbox") as inbox,
        ):
            worker.main()
        freeze.assert_not_called()
        inbox.assert_not_called()
        self.assertIn(b"Precise preview requires", stdout.buffer.getvalue())
