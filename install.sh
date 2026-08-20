#!/bin/sh
set -eu
PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BIN_DIR=${HOME}/bin
mkdir -p "$BIN_DIR"
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
echo "Installed $BIN_DIR/resolve-media -> $PROJECT_DIR/resolve_media.py"
echo "Installed $BIN_DIR/resolve-concat -> $PROJECT_DIR/resolve_concat.py"
echo "Installed $BIN_DIR/resolve-fps -> $PROJECT_DIR/resolve_fps.py"
