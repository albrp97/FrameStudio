from framestudio.export_types import OutputPolicy


def make_output_policy() -> OutputPolicy:
    return OutputPolicy(
        width=1920,
        height=1080,
        scaling_mode="contain-letterbox",
        frame_rate="60/1",
        timebase="1/1000000",
        container="mp4",
        video_codec="libx264",
        audio_codec="aac",
        pixel_format="yuv420p",
        audio_stream_present=True,
        requires_normalization=True,
        reason="test",
    )
