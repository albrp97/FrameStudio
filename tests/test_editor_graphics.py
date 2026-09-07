import unittest
from unittest.mock import patch

from framestudio.graphics import DEFAULT_GTK_RENDERER, configure_graphics_environment


class EditorGraphicsEnvironmentTests(unittest.TestCase):
    def test_wayland_uses_gl_renderer_when_no_renderer_is_selected(self):
        environment = {"WAYLAND_DISPLAY": "wayland-1"}

        selected = configure_graphics_environment(environment)

        self.assertEqual(selected, DEFAULT_GTK_RENDERER)
        self.assertEqual(environment["GSK_RENDERER"], "gl")

    def test_explicit_renderer_is_preserved(self):
        environment = {
            "WAYLAND_DISPLAY": "wayland-1",
            "GSK_RENDERER": "vulkan",
        }

        selected = configure_graphics_environment(environment)

        self.assertEqual(selected, "vulkan")
        self.assertEqual(environment["GSK_RENDERER"], "vulkan")

    def test_explicit_empty_renderer_is_preserved(self):
        environment = {
            "WAYLAND_DISPLAY": "wayland-1",
            "GSK_RENDERER": "",
        }

        selected = configure_graphics_environment(environment)

        self.assertEqual(selected, "")
        self.assertEqual(environment["GSK_RENDERER"], "")

    def test_non_wayland_does_not_inject_renderer(self):
        environment = {"DISPLAY": ":0"}

        selected = configure_graphics_environment(environment)

        self.assertIsNone(selected)
        self.assertNotIn("GSK_RENDERER", environment)

    def test_default_uses_process_environment_when_not_provided(self):
        with patch.dict(
            "os.environ",
            {"WAYLAND_DISPLAY": "wayland-1"},
            clear=True,
        ):
            selected = configure_graphics_environment()

        self.assertEqual(selected, DEFAULT_GTK_RENDERER)
