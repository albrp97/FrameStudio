#!/bin/sh
set -eu
PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BIN_DIR=${HOME}/bin
mkdir -p "$BIN_DIR"
for obsolete in \
  framestudio-media \
  framestudio-concat \
  framestudio-fps \
  framestudio-editor \
  resolve-editor \
  resolve-media \
  resolve-concat \
  resolve-fps
do
  rm -f "$BIN_DIR/$obsolete"
done
python3 - "$PROJECT_DIR" "$BIN_DIR" <<'PY'
import os
import shlex
import sys
from pathlib import Path

project_dir, bin_dir = map(Path, sys.argv[1:])
command = bin_dir / "framestudio"
command.write_text(
    "#!/bin/sh\n"
    f'exec /usr/bin/env python3 {shlex.quote(str(project_dir / "framestudio.py"))} "$@"\n',
    encoding="utf-8",
)
command.chmod(0o755)
data_home = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")
if not data_home.is_absolute():
    data_home = Path.home() / ".local/share"
applications = data_home / "applications"
applications.mkdir(parents=True, exist_ok=True)
quoted_command = str(command).replace("%", "%%")
for character in ('\\', '"', '`', '$'):
    quoted_command = quoted_command.replace(character, "\\" + character)
quoted_command = quoted_command.replace("\\", "\\\\")
desktop = applications / "io.github.framestudio.editor.desktop"
desktop.write_text(
    "[Desktop Entry]\n"
    "Type=Application\n"
    "Name=FrameStudio\n"
    "Comment=Edit and export local video projects\n"
    f'Exec=/usr/bin/env "{quoted_command}"\n'
    "Icon=multimedia-video-player\n"
    "Terminal=false\n"
    "StartupNotify=true\n"
    "Categories=AudioVideo;Video;AudioVideoEditing;\n"
    "Keywords=video;editor;timeline;framestudio;\n",
    encoding="utf-8",
)
print(f"Installed desktop launcher: {desktop}")
PY
printf '%s\n' \
  "Installed $BIN_DIR/framestudio -> $PROJECT_DIR/framestudio.py" \
  "Removed obsolete workflow aliases from $BIN_DIR"
