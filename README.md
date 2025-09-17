# puyo20-text-tool

Tools to extract/build font files and text files for translating Wii game Puyo Puyo 20th anniversary.
Info about file formats is from [nickworonekin/puyo-text-editor](//github.com/nickworonekin/puyo-text-editor).

Currently under refactoring.

`build.py` builds both font file and text file from extracted JSON.

`extract.py` extracts readable JSON from font file and text file.

Features to (re-)implement:

- [ ] Support non-square characters
- [ ] Fix bounding box inconsistancy across different fonts
- [ ] More commandline arguments
