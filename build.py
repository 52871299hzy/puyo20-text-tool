#!/usr/bin/env python3
# coding=utf-8
import math
import sys
import json
import re
from PIL import Image, ImageDraw, ImageFont
import subprocess

FONT_FILE='./NotoSansCJK-Medium.ttc'

# 22x22 is default for Wii version
GRID_HEIGHT=22
GRID_WIDTH=22

FONT_SIZE=22


def cut(x, l):
    A = []
    a = len(x) // l + 1
    for i in range(a):
        if (i + 1) * l > len(x):
            A.append(x[i * l:])
        else:
            A.append(x[i * l:(i + 1) * l])
    return A

# Builds image for fnt file. Currently only supports square characters.


def build_image(filename, data):
    words = 512 // GRID_WIDTH
    Data = cut(data, words)
    Line = len(data) // words + 1
    Length = 2 ** math.ceil(math.log(Line * GRID_HEIGHT, 2))
    image = Image.new(mode='RGBA', size=(512, Length))
    draw = ImageDraw.Draw(im=image)
    for i in range(Line):
        for j in range(len(Data[i])):
            text = Data[i][j]
            font = ImageFont.truetype(FONT_FILE, FONT_SIZE)
            # bbox = draw.textbbox((0, 0), text, font=font)
            draw.text(xy=(GRID_WIDTH * j, GRID_HEIGHT * i - 8), anchor='la',
                      text=text, fill='#FFFFFF', font=font)
            # SOMETIMES the ascender is 8 pixels higher than actual top.
            # However if I use anchor "lt" some characters will become weird.
            # Such as "一", it will become "▔".
            # And it seems that this only applies to some fonts (Noto Sans CJK Medium in my case).
    image.save(filename, 'PNG')

# Builds character map from text. Returns a char-int dict.


def build_charmap(text):
    charset = set()
    for section in text:
        for line in section:
            unescaped = re.sub(r'<.*?>', '', line)
            for ch in unescaped:
                if ch not in ['\r', '\n']:
                    charset.add(ch)
    charmap = {}
    count = 0
    for ch in sorted(charset):
        charmap[ch] = count
        count += 1
    return charmap


def build_fnt(filename, charlist, imgfilename):
    font = ImageFont.truetype(FONT_FILE, FONT_SIZE)
    with open(filename, 'wb') as f:
        f.write(b'FNT\x00')
        f.write((GRID_HEIGHT-2).to_bytes(4, 'little'))
        f.write((GRID_WIDTH-1).to_bytes(4, 'little'))
        f.write(len(charlist).to_bytes(4, 'little'))
        for ch in charlist:
            f.write(ch.encode('utf-16le'))
            f.write((int(font.getlength(ch)-1)).to_bytes(2, 'little'))


def build_mtx(filename, text, charmap):
    header_length = 8
    section_offsets = []
    line_offsets = []
    data = b''

    for section in text:
        section_offsets.append(len(line_offsets)*4)
        for line in section:
            line_offsets.append(len(data))
            i = 0
            while i < len(line):
                ch = line[i]
                if ch not in ['<', '\n', '\r']:
                    data += charmap[ch].to_bytes(2, 'little')
                    i += 1
                else:
                    if ch == '\n':
                        data += b'\xfd\xff'
                        i += 1
                    elif ch == '\r':
                        data += b'\xfe\xff'
                        i += 1
                    elif re.match(r'^<arrow>', line[i:]):
                        data += b'\x13\xf8'
                        i += len('<arrow>')
                    elif re.match(r'^<clear>', line[i:]):
                        data += b'\x12\xf8'
                        i += len('<clear>')
                    elif re.match(r'^</color>', line[i:]):
                        data += b'\x01\xf8'
                        i += len('</color>')
                    elif match := re.match(r'^<color:(?P<value>\d+?)>', line[i:]):
                        data += b'\x00\xf8'
                        data += int(match.groups()[0]).to_bytes(2, 'little')
                        i += match.span()[1]
                    elif match := re.match(r'^<wait:(?P<value>\d+?)>', line[i:]):
                        data += b'\x81\xf8'
                        data += int(match.groups()[0]).to_bytes(2, 'little')
                        i += match.span()[1]
                    elif match := re.match(r'^<speed:(?P<value>\d+?)>', line[i:]):
                        data += b'\x80\xf8'
                        data += int(match.groups()[0]).to_bytes(2, 'little')
                        i += match.span()[1]
                    else:
                        raise NotImplementedError(line[i:])
            data += b'\xff\xff'

    with open(filename, 'wb') as f:
        f.write((header_length + len(section_offsets)*4 +
                len(line_offsets)*4 + len(data)).to_bytes(4, 'little'))
        f.write(b'\x08\x00\x00\x00')
        header_length += len(section_offsets)*4
        for i in section_offsets:
            f.write((i+header_length).to_bytes(4, 'little'))
        header_length += len(line_offsets)*4
        for i in line_offsets:
            f.write((i+header_length).to_bytes(4, 'little'))
        f.write(data)


def main():
    if len(sys.argv) != 4:
        print("Usage: build.py <input.json> <output.fnt> <output.mtx>")
        exit(1)

    with open(sys.argv[1], 'r') as f:
        text = json.load(f)

    charmap = build_charmap(text)

    build_image('tmp.png', list(charmap))

    build_fnt(sys.argv[2], list(charmap), 'tmp.png')

    build_mtx(sys.argv[3], text, charmap)

    subprocess.run(['mono', 'VrConvert.exe', '-e', 'tmp.png',
                   'gvr', 'rgb5a3', 'rgb5a3', '-gcix'])

    with open(sys.argv[2], 'ab') as f:
        with open('tmp.gvr', 'rb') as f2:
            f.write(f2.read())


if __name__ == '__main__':
    main()
