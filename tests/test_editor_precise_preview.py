from __future__ import annotations

import shutil
import struct
import subprocess
import sys
import threading
import time
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from framestudio.ffmpeg_playback import _PreviewRequestCancelled
from framestudio.playback import PlaybackBackendError
from framestudio.precise_preview import (
    MAX_HEADER_BYTES,
    PrecisePreviewClient,
    PreviewDependencyUnavailable,
    decode_header,
    encode_message,
    preview_backend_setting,
    preview_python,
)


class PrecisePreviewProtocolTests(unittest.TestCase):
    def test_round_trip_transports_integer_ticks(self):
        message = {"id": 4, "source_tick": 2_000_001, "epoch": "project-1"}
        encoded = encode_message(message)
        size = struct.unpack("!I", encoded[:4])[0]
        self.assertEqual(decode_header(encoded[4 : 4 + size]), dict(message, payload_bytes=0))

    def test_corrupt_and_oversized_headers_are_errors(self):
        for raw in (b"[]", b"not-json", b"x" * (MAX_HEADER_BYTES + 1)):
            with self.subTest(raw=raw[:12]), self.assertRaises(PlaybackBackendError):
                decode_header(raw)

    def test_backend_default_and_invalid_setting(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(preview_backend_setting(), "auto")
        with patch.dict("os.environ", {"FRAMESTUDIO_PREVIEW_BACKEND": "approximate"}):
            with self.assertRaisesRegex(PlaybackBackendError, "FRAMESTUDIO_PREVIEW_BACKEND"):
                preview_backend_setting()

    def test_explicit_runtime_wins_without_importing_av(self):
        with patch.dict("os.environ", {"FRAMESTUDIO_PREVIEW_PYTHON": "/chosen/python"}):
            self.assertEqual(preview_python(), "/chosen/python")

    def test_application_import_does_not_load_optional_native_runtime(self):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys; import framestudio.app_project; assert 'av' not in sys.modules",
            ],
            cwd=Path(__file__).resolve().parent.parent,
            capture_output=True,
            check=False,
            timeout=5,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_missing_av_is_distinct_from_decoder_failure(self):
        self.assertTrue(issubclass(PreviewDependencyUnavailable, PlaybackBackendError))

    def test_close_does_not_acquire_decode_io_lock(self):
        client = PrecisePreviewClient("cpu")
        client._io_lock.acquire()
        try:
            client.close()
            self.assertTrue(client._closed)
        finally:
            client._io_lock.release()


class PrecisePreviewFailureTests(unittest.TestCase):
    def setUp(self):
        self.root = Path.cwd() / f".precise-preview-protocol-{uuid.uuid4().hex}"
        self.root.mkdir()
        self.addCleanup(shutil.rmtree, self.root)

    def client(self, body, timeout=0.5):
        worker = self.root / "worker.py"
        worker.write_text(
            "import sys,json,struct,time\n"
            "epoch=sys.argv[2]\n"
            "def send(header,payload=b''):\n"
            " header=dict(header,epoch=epoch,payload_bytes=len(payload))\n"
            " raw=json.dumps(header).encode()\n"
            " sys.stdout.buffer.write(struct.pack('!I',len(raw))+raw+payload)\n"
            " sys.stdout.buffer.flush()\n" + body
        )
        client = PrecisePreviewClient(
            "cpu", timeout=timeout, python=sys.executable, worker_path=worker
        )
        self.addCleanup(client.close)
        return client

    def request(self):
        return {"project_tick": 0, "width": 1, "height": 1, "slots": [{"source_tick": 0}]}

    def ready(self):
        return "send({'status':'ready','protocol':1,'av_version':'19.0.1'})\n"

    def assert_cancelled_then_latest_frame(self, body):
        client = self.client(body, timeout=2)
        cancelled = threading.Event()
        timer = threading.Timer(0.05, cancelled.set)
        timer.start()
        try:
            with self.assertRaises(_PreviewRequestCancelled):
                client.render(self.request(), cancelled=cancelled.is_set)
        finally:
            timer.join()
        pixels, receipt = client.render(self.request())
        self.assertEqual(receipt["id"], 2)
        self.assertEqual(pixels, b"\x00\x00\x00\xff")
        return client

    def test_missing_dependency_falls_back_but_wrong_version_does_not(self):
        client = self.client("send({'status':'missing_dependency','dependency':'av'})\n")
        with self.assertRaises(PreviewDependencyUnavailable):
            client.render(self.request())
        self.assertIsNone(client._process)
        client = self.client("send({'status':'ready','protocol':1,'av_version':'18.0.0'})\n")
        with self.assertRaises(PlaybackBackendError) as failure:
            client.render(self.request())
        self.assertNotIsInstance(failure.exception, PreviewDependencyUnavailable)
        self.assertIsNone(client._process)

    def test_corrupt_protocol_crash_and_timeout_reset_process(self):
        for body, expected in (
            (
                self.ready()
                + "sys.stdout.buffer.write(b'\\xff\\xff\\xff\\xff');sys.stdout.buffer.flush()\ntime.sleep(2)\n",
                "header",
            ),
            (self.ready() + "sys.exit(4)\n", "exited"),
            (self.ready() + "time.sleep(2)\n", "Timed out"),
        ):
            with self.subTest(expected=expected):
                client = self.client(body)
                with self.assertRaisesRegex(PlaybackBackendError, expected):
                    client.render(self.request())
                self.assertIsNone(client._process)

    def test_close_interrupts_blocked_io_without_waiting_for_io_lock(self):
        client = self.client(self.ready() + "time.sleep(10)\n", timeout=5)
        errors = []

        def render():
            try:
                client.render(self.request())
            except Exception as error:
                errors.append(error)

        thread = threading.Thread(target=render)
        thread.start()
        deadline = time.monotonic() + 1
        while client._process is None and time.monotonic() < deadline:
            time.sleep(0.005)
        process = client._process
        started = time.monotonic()
        client.close()
        self.assertLess(time.monotonic() - started, 0.5)
        thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertIsNotNone(process.poll())
        self.assertTrue(any(isinstance(error, _PreviewRequestCancelled) for error in errors))

    def test_superseded_response_is_drained_not_published_as_new_request(self):
        body = (
            self.ready()
            + """
while True:
 raw=sys.stdin.buffer.read(4)
 if not raw: break
 message=json.loads(sys.stdin.buffer.read(struct.unpack('!I',raw)[0]))
 if message['op']=='cancel': continue
 time.sleep(.1)
 send({'status':'frame','id':message['id'],'physical_frames':[{
  'pts':0,'time_base_num':1,'time_base_den':25,'source_tick':0,'origin_tick':0,
  'engine':'cpu','reason':'test'
 }]},b'\\x00\\x00\\x00\\xff')
"""
        )
        self.assert_cancelled_then_latest_frame(body)

    def test_missing_physical_provenance_is_protocol_corruption(self):
        client = self.client(
            self.ready()
            + "sys.stdin.buffer.read(4)\n"
            + "send({'status':'frame','id':1},b'\\x00\\x00\\x00\\xff')\n"
            + "time.sleep(1)\n"
        )
        with self.assertRaisesRegex(PlaybackBackendError, "provenance"):
            client.render(self.request())
        self.assertIsNone(client._process)

    def test_cancelled_request_retirement_replays_next_job_once(self):
        body = (
            self.ready()
            + """
raw=sys.stdin.buffer.read(4)
message=json.loads(sys.stdin.buffer.read(struct.unpack('!I',raw)[0]))
time.sleep(.1)
send({'status':'frame','id':message['id'],'retire':True,'physical_frames':[{
 'pts':0,'time_base_num':1,'time_base_den':25,'source_tick':0,'origin_tick':0,
 'engine':'cpu','reason':'test'
}]},b'\\x00\\x00\\x00\\xff')
"""
        )
        client = self.assert_cancelled_then_latest_frame(body)
        self.assertIsNone(client._process)


if __name__ == "__main__":
    unittest.main()
