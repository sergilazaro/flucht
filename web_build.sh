#!/usr/bin/env bash

mkdir temp_web_build
mkdir temp_web_build/Flucht

cp Flucht/game_pygame.py temp_web_build/Flucht/main.py
cp Flucht/common_code.py temp_web_build/Flucht/

pygbag --template index.html --icon Flucht/icon_32.ico --build temp_web_build/Flucht

rm Flucht_pygame_wasm.zip
zip -rj Flucht_pygame_wasm.zip temp_web_build/Flucht/build/web/

rm -r temp_web_build
