from __future__ import annotations

from typing import Any

from .app_helpers import KEY_BINDINGS
from .composition import MAX_OFFSET_X, MAX_OFFSET_Y, MAX_ZOOM, MIN_ZOOM
from .persistence import autosave_exists
from .timeline import create_timeline_canvas


def build_editor_ui(window: Any, Gtk: Any, Gdk: Any) -> None:
    header = Gtk.HeaderBar()
    window.set_titlebar(header)

    open_source = Gtk.Button(label="Select video(s)")
    open_source.connect("clicked", window._on_open_source_clicked)
    header.pack_start(open_source)
    window.open_source_button = open_source

    open_project = Gtk.Button(label="Open project")
    open_project.connect("clicked", window._on_open_project_clicked)
    header.pack_start(open_project)
    window.open_project_button = open_project

    recover_autosave = Gtk.Button(label="Recover autosave")
    recover_autosave.set_tooltip_text(
        "Open the latest crash-recovery project without changing the normal project path"
    )
    recover_autosave.connect("clicked", window._on_recover_autosave_clicked)
    recover_autosave.set_sensitive(autosave_exists())
    header.pack_start(recover_autosave)
    window.recover_autosave_button = recover_autosave

    export = Gtk.Button(label="Export video")
    export.connect("clicked", window._on_export_clicked)
    export.set_sensitive(False)
    header.pack_end(export)
    window.export_button = export

    save = Gtk.Button(label="Save project")
    save.connect("clicked", window._on_save_clicked)
    header.pack_end(save)
    window.save_button = save

    reopen = Gtk.Button(label="Reopen project")
    reopen.connect("clicked", window._on_reopen_clicked)
    header.pack_end(reopen)
    window.reopen_button = reopen

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

    composition_controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    composition_controls.append(Gtk.Label(label="Focus", xalign=0.0))

    zoom_adjustment = Gtk.Adjustment.new(
        MIN_ZOOM,
        MIN_ZOOM,
        MAX_ZOOM,
        0.1,
        1.0,
        0.0,
    )
    window.focus_zoom_spin = Gtk.SpinButton.new(zoom_adjustment, 0.1, 2)
    window.focus_zoom_spin.set_tooltip_text(
        "Selected clip zoom (1.00x to 8.00x); scroll up/down to adjust by 0.10x"
    )
    window.focus_zoom_spin.connect("value-changed", window._on_focus_control_changed)
    composition_controls.append(Gtk.Label(label="Zoom"))
    composition_controls.append(window.focus_zoom_spin)

    offset_x_adjustment = Gtk.Adjustment.new(
        0.0,
        -MAX_OFFSET_X,
        MAX_OFFSET_X,
        10.0,
        100.0,
        0.0,
    )
    window.focus_offset_x_spin = Gtk.SpinButton.new(offset_x_adjustment, 10.0, 0)
    window.focus_offset_x_spin.set_tooltip_text(
        "Selected clip horizontal focus offset; scroll up/down by 10 pixels"
    )
    window.focus_offset_x_spin.connect("value-changed", window._on_focus_control_changed)
    composition_controls.append(Gtk.Label(label="X"))
    composition_controls.append(window.focus_offset_x_spin)

    offset_y_adjustment = Gtk.Adjustment.new(
        0.0,
        -MAX_OFFSET_Y,
        MAX_OFFSET_Y,
        10.0,
        100.0,
        0.0,
    )
    window.focus_offset_y_spin = Gtk.SpinButton.new(offset_y_adjustment, 10.0, 0)
    window.focus_offset_y_spin.set_tooltip_text(
        "Selected clip vertical focus offset; scroll up/down by 10 pixels"
    )
    window.focus_offset_y_spin.connect("value-changed", window._on_focus_control_changed)
    composition_controls.append(Gtk.Label(label="Y"))
    composition_controls.append(window.focus_offset_y_spin)

    copy_focus = Gtk.Button(label="Copy to selection")
    copy_focus.set_tooltip_text(
        "Copy the primary selected clip's focus to the other selected clips"
    )
    copy_focus.connect("clicked", window._on_copy_focus_clicked)
    composition_controls.append(copy_focus)
    window.copy_focus_button = copy_focus

    clean_focus = Gtk.Button(label="Clean modifications")
    clean_focus.set_tooltip_text("Reset focus and triplicate settings on the selected clips")
    clean_focus.connect("clicked", window._on_clean_visual_clicked)
    composition_controls.append(clean_focus)
    window.clean_focus_button = clean_focus

    triplicate = Gtk.Button(label="Enable triplicate")
    triplicate.set_tooltip_text(
        "Render the selected clips as linked left, center, and right copies"
    )
    triplicate.connect("clicked", window._on_triplicate_clicked)
    composition_controls.append(triplicate)
    window.triplicate_button = triplicate

    for field, control in (
        ("zoom", window.focus_zoom_spin),
        ("offset_x", window.focus_offset_x_spin),
        ("offset_y", window.focus_offset_y_spin),
    ):
        scroll = Gtk.EventControllerScroll.new(Gtk.EventControllerScrollFlags.VERTICAL)
        scroll.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        scroll.connect("scroll", window._on_focus_control_scroll, field)
        control.add_controller(scroll)

    root.append(composition_controls)

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

    fit_thirty_minutes = Gtk.Button(label="30 min")
    fit_thirty_minutes.set_tooltip_text("Fit the timeline scale so 30 minutes spans the viewport")
    fit_thirty_minutes.connect("clicked", window._fit_timeline_to_thirty_minutes)
    timeline_toolbar.append(fit_thirty_minutes)
    window.fit_thirty_minutes_button = fit_thirty_minutes

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

    audio_status = Gtk.Label(label="Audio decisions: no project loaded")
    audio_status.set_xalign(0.0)
    audio_status.set_wrap(True)
    timeline_layout.append(audio_status)
    window.audio_status_label = audio_status

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
    cancel_export = Gtk.Button(label="Cancel export")
    cancel_export.set_halign(Gtk.Align.START)
    cancel_export.set_visible(False)
    cancel_export.connect("clicked", window._on_cancel_export_clicked)
    export_progress_panel.append(cancel_export)
    export_progress_panel.set_visible(False)
    root.append(export_progress_panel)
    window.export_progress_panel = export_progress_panel
    window.export_progress_bar = export_progress_bar
    window.export_progress_label = export_progress_label
    window.cancel_export_button = cancel_export

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
