# FrameStudio

FrameStudio is a local Linux video editor with a GTK 4 interface, FFmpeg
playback and export, a deterministic CLI, and preserved media-preparation
commands.

This directory contains GitHub project configuration. The complete product
guide is in the [repository README](../README.md), including:

- editor features and timeline controls;
- installation and GUI usage;
- project files, autosave, and crash recovery;
- safe, resumable export;
- CLI editing and export commands;
- the preserved `media`, `concat`, and `fps` commands;
- current boundaries and future product direction.

## Quick start

```sh
./install.sh
framestudio
```

Open a source or a saved project directly:

```sh
framestudio --source ~/Videos/source.mp4
framestudio --project ~/Videos/project.framestudio.json
```

FrameStudio never overwrites the original source media. Exports are verified
before publication, and compatible cancelled or failed exports can resume
from their validated checkpoints.
