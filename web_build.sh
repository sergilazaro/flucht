#!/usr/bin/env bash

rm -r temp_web_build
mkdir temp_web_build
mkdir temp_web_build/Flucht

cp Flucht/game_pygame.py temp_web_build/Flucht/main.py
cp Flucht/common_code.py temp_web_build/Flucht/

pygbag --template flucht.tmpl --cdn "./" --icon Flucht/icon_32.ico --build temp_web_build/Flucht

cp -r cdn/* temp_web_build/Flucht/build/web/

rm Flucht_pygame_wasm.zip
bash -c "cd temp_web_build/Flucht/build/web/ && zip -r ../../../../Flucht_pygame_wasm.zip *"

rm -r temp_web_build
