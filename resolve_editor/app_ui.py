from __future__ import annotations

from typing import Any

from .app_helpers import KEY_BINDINGS
from .timeline import create_timeline_canvas


def build_editor_ui(window: Any, Gtk: Any, Gdk: Any) -> None:
    header = Gtk.HeaderBar()
    window.set_titlebar(header)

    open_source = Gtk.Button(label="Select video(s)")
    open_source.connect("clicked", window._on_open_source_clicked)
    header.pack_start(open_source)

    open_project = Gtk.Button(label="Open project")
    open_project.connect("clicked", window._on_open_project_clicked)
    header.pack_start(open_project)

    export = Gtk.Button(label="Export video")
    export.connect("clicked", window._on_export_clicked)
    export.set_sensitive(False)
    header.pack_end(export)
    window.export_button = export

    save = Gtk.Button(label="Save project")
    save.connect("clicked", window._on_save_clicked)
    header.pack_end(save)

    reopen = Gtk.Button(label="Reopen project")
    reopen.connect("clicked", window._on_reopen_clicked)
    header.pack_end(reopen)

    root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    root.set_margin_top(12)
    root.set_margin_bottom(12)
    root.set_margin_start(12)
    root.set_margin_end(12)
    window.set_child(root)

    window.preview = Gtk.Picture()
    window.preview.set_hexpand(True)
    window.preview.set_vexpand(True)
    window.preview.set_content_fit(Gtk.ContentFit.CONTAIN)
    preview_frame = Gtk.Frame()
    preview_frame.set_child(window.preview)
    root.append(preview_frame)

    controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    root.append(controls)

    window.play_button = Gtk.Button(label="Play")
    window.play_button.set_tooltip_text("Play or pause playback (Space)")
    window.play_button.connect("clicked", window._on_play_clicked)
    controls.append(window.play_button)

    window.position_label = Gtk.Label(label="00:00")
    window.position_label.set_tooltip_text("Current source position")
    controls.append(window.position_label)

    timeline_frame = Gtk.Frame()
    timeline_frame.set_label("Timeline / clips")
    timeline_layout = Gtk.Box(
        orientation=Gtk.Orientation.VERTICAL,
        spacing=6,
    )
    timeline_toolbar = Gtk.Box(
        orientation=Gtk.Orientation.HORIZONTAL,
        spacing=6,
    )
    timeline_toolbar.append(Gtk.Label(label="Zoom", xalign=0.0))

    window.timeline_zoom_label = Gtk.Label(label="100%")
    window.timeline_zoom_label.set_width_chars(6)
    timeline_toolbar.append(window.timeline_zoom_label)

    window.timeline_output_label = Gtk.Label(label="Final output: 00:00")
    window.timeline_output_label.set_tooltip_text("Duration of included clips in the final export")
    timeline_toolbar.append(window.timeline_output_label)

    timeline_toolbar_spacer = Gtk.Box()
    timeline_toolbar_spacer.set_hexpand(True)
    timeline_toolbar.append(timeline_toolbar_spacer)

    key_bindings = Gtk.Button(label="Key bindings")
    key_bindings.set_tooltip_text("Show keyboard and timeline controls")
    key_bindings.connect("clicked", window._on_key_bindings_clicked)
    timeline_toolbar.append(key_bindings)
    window.key_bindings_button = key_bindings
    window.key_bindings_window = None
    timeline_layout.append(timeline_toolbar)

    TimelineCanvas = create_timeline_canvas(Gtk)
    window.timeline_canvas = TimelineCanvas(
        on_seek=window._on_timeline_view_seek,
        on_segment_selected=window._on_timeline_segment_selected,
        on_selection_changed=window._on_timeline_selection_changed,
        selection_modifier_mask=int(Gdk.ModifierType.CONTROL_MASK),
        range_selection_modifier_mask=int(Gdk.ModifierType.SHIFT_MASK),
    )
    window.timeline_canvas.set_tooltip_text(
        "Click/drag to seek; normal wheel seeks; Ctrl+wheel zooms; "
        "Alt/Shift/horizontal wheel scrolls; Ctrl-click selects multiple clips"
        "; Shift-click selects an inclusive range"
    )
    timeline_scroll = Gtk.EventControllerScroll.new(Gtk.EventControllerScrollFlags.BOTH_AXES)
    timeline_scroll.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
    timeline_scroll.connect("scroll", window._on_timeline_scroll)
    window.timeline_canvas.add_controller(timeline_scroll)

    timeline_viewport = Gtk.ScrolledWindow()
    timeline_viewport.set_policy(
        Gtk.PolicyType.AUTOMATIC,
        Gtk.PolicyType.NEVER,
    )
    timeline_viewport.set_min_content_height(132)
    timeline_viewport.set_child(window.timeline_canvas)
    timeline_layout.append(timeline_viewport)
    window.timeline_viewport = timeline_viewport
    adjustment = timeline_viewport.get_hadjustment()
    adjustment.connect(
        "notify::page-size",
        window._on_timeline_viewport_changed,
    )
    adjustment.connect(
        "notify::upper",
        window._on_timeline_viewport_changed,
    )
    window._on_timeline_viewport_changed(adjustment, None)

    timeline_selection = Gtk.Label(label="No clip selected")
    timeline_selection.set_xalign(0.0)
    timeline_selection.set_wrap(True)
    timeline_layout.append(timeline_selection)
    window.timeline_selection_label = timeline_selection

    timeline_frame.set_child(timeline_layout)
    root.append(timeline_frame)

    export_progress_panel = Gtk.Box(
        orientation=Gtk.Orientation.VERTICAL,
        spacing=4,
    )
    export_progress_bar = Gtk.ProgressBar()
    export_progress_bar.set_show_text(True)
    export_progress_bar.set_text("0.0%")
    export_progress_panel.append(export_progress_bar)
    export_progress_label = Gtk.Label(label="")
    export_progress_label.set_xalign(0.0)
    export_progress_label.set_wrap(True)
    export_progress_panel.append(export_progress_label)
    export_progress_panel.set_visible(False)
    root.append(export_progress_panel)
    window.export_progress_panel = export_progress_panel
    window.export_progress_bar = export_progress_bar
    window.export_progress_label = export_progress_label

    window.status_label = Gtk.Label(label="Select source video(s) or open a project file")
    window.status_label.set_xalign(0.0)
    window.status_label.set_wrap(True)
    root.append(window.status_label)


def build_key_bindings_window(window: Any, Gtk: Any) -> None:
    bindings_window = Gtk.Window()
    bindings_window.set_title("Key bindings")
    bindings_window.set_transient_for(window)
    bindings_window.set_modal(True)
    bindings_window.set_destroy_with_parent(True)
    bindings_window.set_default_size(640, 520)
    bindings_window.connect("close-request", window._on_key_bindings_window_close)

    content = Gtk.Box(
        orientation=Gtk.Orientation.VERTICAL,
        spacing=12,
    )
    content.set_margin_top(16)
    content.set_margin_bottom(16)
    content.set_margin_start(16)
    content.set_margin_end(16)
    bindings_window.set_child(content)

    heading = Gtk.Label(label="Keyboard and timeline controls")
    heading.set_xalign(0.0)
    heading.add_css_class("heading")
    content.append(heading)

    panel = Gtk.Box(
        orientation=Gtk.Orientation.VERTICAL,
        spacing=8,
    )

    for shortcut, description in KEY_BINDINGS:
        row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=12,
        )
        shortcut_label = Gtk.Label(label=shortcut)
        shortcut_label.set_xalign(0.0)
        shortcut_label.set_width_chars(24)
        shortcut_label.add_css_class("monospace")
        row.append(shortcut_label)

        description_label = Gtk.Label(label=description)
        description_label.set_xalign(0.0)
        description_label.set_hexpand(True)
        description_label.set_wrap(True)
        row.append(description_label)
        panel.append(row)

    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scroll.set_hexpand(True)
    scroll.set_vexpand(True)
    scroll.set_min_content_width(560)
    scroll.set_min_content_height(420)
    scroll.set_child(panel)
    content.append(scroll)

    footer = Gtk.Box(
        orientation=Gtk.Orientation.HORIZONTAL,
        spacing=8,
    )
    footer_spacer = Gtk.Box()
    footer_spacer.set_hexpand(True)
    footer.append(footer_spacer)
    close_button = Gtk.Button(label="Close")
    close_button.connect("clicked", lambda _button: bindings_window.close())
    footer.append(close_button)
    content.append(footer)
    window.key_bindings_window = bindings_window
