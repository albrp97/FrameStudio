import unittest

from framestudio.crop_window import crop_window_filter_string, crop_window_filters


class CropWindowFilterTests(unittest.TestCase):
    def test_window_inside_scaled_frame_keeps_plain_crop(self):
        steps = crop_window_filters(1920, 1080, 100, 50, 1280, 720)

        self.assertEqual(steps, (("crop", "1280:720:100:50"),))
        self.assertEqual(crop_window_filter_string(steps), "crop=1280:720:100:50")

    def test_scaled_frame_smaller_than_window_is_padded_centered(self):
        steps = crop_window_filters(640, 360, -320, -180, 1280, 720)

        self.assertEqual(steps, (("pad", "1280:720:320:180:color=black"),))

    def test_window_partly_outside_frame_crops_visible_part_and_pads(self):
        steps = crop_window_filters(1000, 1000, -200, 100, 800, 800)

        self.assertEqual(
            steps,
            (
                ("crop", "600:800:0:100"),
                ("pad", "800:800:200:0:color=black"),
            ),
        )

    def test_window_fully_outside_frame_is_solid_black(self):
        steps = crop_window_filters(640, 360, 5000, 0, 1280, 720)

        self.assertEqual(
            steps,
            (
                ("crop", "1:1:0:0"),
                ("drawbox", "x=0:y=0:w=1:h=1:color=black:t=fill"),
                ("pad", "1280:720:0:0:color=black"),
            ),
        )

    def test_large_offsets_always_produce_window_sized_output(self):
        for crop_x, crop_y in ((-1_000_000, 0), (0, 1_000_000), (-640, -360), (900, -900)):
            steps = crop_window_filters(640, 360, crop_x, crop_y, 1280, 720)
            final_name, final_args = steps[-1]
            if final_name == "pad":
                self.assertTrue(final_args.startswith("1280:720:"), final_args)
            else:
                self.assertEqual(final_name, "crop")
                self.assertTrue(final_args.startswith("1280:720:"), final_args)


if __name__ == "__main__":
    unittest.main()
