rebuild: clean package

build:
	mkdir build
	rcc -g python -o lib/resources.py --format-version 1 resources.qrc
	cp keyboard-mapper.py build/__main__.py
	zip -j build/keyboard-mapper.zip build/__main__.py
	zip -r build/keyboard-mapper.zip lib
	echo "#!/usr/bin/env python3" > build/keyboard-mapper
	cat build/keyboard-mapper.zip >> build/keyboard-mapper
	chmod +x build/keyboard-mapper
	rm build/keyboard-mapper.zip build/__main__.py

package: build
	cp CHANGELOG.md LICENSE README.md build/
	cd build
	zip keyboard-mapper.zip keyboard-mapper CHANGELOG.md LICENSE README.md

install: build
	cp build/keyboard-mapper /usr/local/bin/keyboard-mapper

clean:
	rm -rf build