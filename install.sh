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
cat > "$BIN_DIR/framestudio" <<EOF
#!/bin/sh
exec /usr/bin/env python3 "$PROJECT_DIR/framestudio.py" "\$@"
EOF
chmod +x "$BIN_DIR/framestudio"
printf '%s\n' \
  "Installed $BIN_DIR/framestudio -> $PROJECT_DIR/framestudio.py" \
  "Removed obsolete workflow aliases from $BIN_DIR"
