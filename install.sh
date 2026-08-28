#!/bin/sh
set -eu
PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BIN_DIR=${HOME}/bin
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/framestudio" <<EOF
#!/bin/sh
exec /usr/bin/env python3 "$PROJECT_DIR/framestudio.py" "\$@"
EOF
chmod +x "$BIN_DIR/framestudio"
cat > "$BIN_DIR/framestudio-media" <<EOF
#!/bin/sh
exec /usr/bin/env python3 "$PROJECT_DIR/framestudio_media.py" "\$@"
EOF
chmod +x "$BIN_DIR/framestudio-media"
cat > "$BIN_DIR/framestudio-concat" <<EOF
#!/bin/sh
exec /usr/bin/env python3 "$PROJECT_DIR/framestudio_concat.py" "\$@"
EOF
chmod +x "$BIN_DIR/framestudio-concat"
cat > "$BIN_DIR/framestudio-fps" <<EOF
#!/bin/sh
exec /usr/bin/env python3 "$PROJECT_DIR/framestudio_fps.py" "\$@"
EOF
chmod +x "$BIN_DIR/framestudio-fps"
cat > "$BIN_DIR/framestudio-editor" <<EOF
#!/bin/sh
exec /usr/bin/env python3 "$PROJECT_DIR/framestudio.py" "\$@"
EOF
chmod +x "$BIN_DIR/framestudio-editor"
cat > "$BIN_DIR/resolve-editor" <<EOF
#!/bin/sh
exec /usr/bin/env python3 "$PROJECT_DIR/resolve_editor.py" "\$@"
EOF
chmod +x "$BIN_DIR/resolve-editor"
cat > "$BIN_DIR/resolve-media" <<EOF
#!/bin/sh
exec /usr/bin/env python3 "$PROJECT_DIR/resolve_media.py" "\$@"
EOF
chmod +x "$BIN_DIR/resolve-media"
cat > "$BIN_DIR/resolve-concat" <<EOF
#!/bin/sh
exec /usr/bin/env python3 "$PROJECT_DIR/resolve_concat.py" "\$@"
EOF
chmod +x "$BIN_DIR/resolve-concat"
cat > "$BIN_DIR/resolve-fps" <<EOF
#!/bin/sh
exec /usr/bin/env python3 "$PROJECT_DIR/resolve_fps.py" "\$@"
EOF
chmod +x "$BIN_DIR/resolve-fps"
printf '%s\n' \
  "Installed $BIN_DIR/framestudio -> $PROJECT_DIR/framestudio.py" \
  "Installed $BIN_DIR/framestudio-editor -> $PROJECT_DIR/framestudio.py" \
  "Installed $BIN_DIR/framestudio-media -> $PROJECT_DIR/framestudio_media.py" \
  "Installed $BIN_DIR/framestudio-concat -> $PROJECT_DIR/framestudio_concat.py" \
  "Installed $BIN_DIR/framestudio-fps -> $PROJECT_DIR/framestudio_fps.py" \
  "Installed legacy Resolve aliases in $BIN_DIR"
