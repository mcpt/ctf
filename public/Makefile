all: logo.ico

logo@16.png:
	inkscape -w 16 -h 16 -o logo@16.png logo.svg

logo@32.png:
	inkscape -w 32 -h 32 -o logo@32.png logo.svg

logo@48.png:
	inkscape -w 48 -h 48 -o logo@48.png logo.svg

logo@64.png:
	inkscape -w 64 -h 64 -o logo@64.png logo.svg

logo.ico: logo@16.png logo@32.png logo@48.png logo@64.png
	convert logo@16.png logo@32.png logo@48.png logo@64.png logo.ico

