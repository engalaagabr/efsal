#!/bin/bash
set -e

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Installing Efsal from $APP_DIR..."

# Copy desktop file and update paths
mkdir -p ~/.local/share/applications
sed "s|Exec=.*|Exec=python3 -m app|g; s|Path=.*|Path=$APP_DIR|g" data/io.github.efsal.desktop > ~/.local/share/applications/io.github.efsal.desktop

# Copy icon
mkdir -p ~/.local/share/icons/hicolor/scalable/apps
mkdir -p ~/.local/share/icons/hicolor/512x512/apps

if [ -f "data/io.github.efsal.svg" ]; then
    cp data/io.github.efsal.svg ~/.local/share/icons/hicolor/scalable/apps/
fi
if [ -f "data/io.github.efsal.png" ]; then
    cp data/io.github.efsal.png ~/.local/share/icons/hicolor/512x512/apps/
fi

# Update icon cache
gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor || true

echo "Installation complete! You can now launch Efsal from your application menu."
