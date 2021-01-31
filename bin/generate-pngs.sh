
set -e

SRCDIR=logo/svg
DESTDIR=logo/png

echo "Regenerating PNGs from SVGs"
inkscape --batch-process -o $DESTDIR/Mesh_Logo_Black_Small.png -w 50 -h 28 $SRCDIR/Mesh_Logo_Black_Small.svg

inkscape --batch-process -o $DESTDIR/play_store_icon.png -w 512 -h 512 logo/inkscape/play_store_icon.svg