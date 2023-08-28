#!/usr/bin/env sh

convert favicon.svg -resize 128x128 favicon.png
convert favicon.png -define icon:auto-resize=128,64,48,32,16 favicon.ico
