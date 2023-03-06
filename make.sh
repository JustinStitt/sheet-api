#!/bin/bash

pipreqs --force ./ # save dependencies
echo "[x] Saved dependencies to requirements.txt"

# generate docs
cd ./src
rm -r ./html 2> /dev/null
rm -r ../docs 2> /dev/null
pdoc --html app.py > /dev/null
mv ./html ../docs
cd ..

echo "[x] Generated app.py docs"
