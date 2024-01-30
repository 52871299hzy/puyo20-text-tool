#!/usr/bin/env python3
# coding=utf-8
import sys
import json
import struct


def read_fnt(filename):
    with open(filename, 'rb') as f:
        content = f.read()
    if content[:4] != b'FNT\x00':
        raise RuntimeError('Not a valid FNT file')
    charcnt = struct.unpack('<i', content[12:16])[0]
    print(f'{charcnt=}')
    charlist = []
    for i in range(charcnt):
        charlist.append(content[16+4*i:16+4*i+2].decode('utf-16le'))
    return charlist


def read_mtx(filename, charlist):
    with open(filename, 'rb') as f:
        content = f.read()
    if struct.unpack('<i', content[:4])[0] != len(content):
        raise RuntimeError('Not a valid MTX file')
    text = []
    section_offsets = [struct.unpack('<i', content[8:12])[0]]
    for i in range(12, section_offsets[0], 4):
        section_offsets.append(struct.unpack('<i', content[i:i+4])[0])
    string_offsets = []
    for i in range(len(section_offsets)):
        string_offsets.append(
            [struct.unpack('<i', content[section_offsets[i]:section_offsets[i]+4])[0]])
        for j in range(section_offsets[i]+4, section_offsets[i+1] if i < len(section_offsets)-1 else string_offsets[0][0], 4):
            string_offsets[i].append(struct.unpack('<i', content[j:j+4])[0])
    for i in range(len(string_offsets)):
        section = string_offsets[i]
        text.append([])
        for offset in section:
            current_str = ''
            char = struct.unpack('<H', content[offset:offset+2])[0]
            while char != 0xffff:
                match char:
                    case 0xfffd:
                        current_str += '\n'
                    case 0xfffe:
                        current_str += '\r'
                    case 0xf813:
                        current_str += '<arrow>'
                    case 0xf812:
                        current_str += '<clear>'
                    case 0xf800:
                        offset += 2
                        current_str += f'<color:{struct.unpack("<H", content[offset:offset+2])[0]}>'
                    case 0xf801:
                        current_str += '</color>'
                    case 0xf880:
                        offset += 2
                        current_str += f'<speed:{struct.unpack("<H", content[offset:offset+2])[0]}>'
                    case 0xf881:
                        offset += 2
                        current_str += f'<wait:{struct.unpack("<H", content[offset:offset+2])[0]}>'
                    case _:
                        current_str += charlist[char]
                offset += 2
                char = struct.unpack('<H', content[offset:offset+2])[0]
            text[i].append(current_str)
    return text


def main():
    if len(sys.argv) != 4:
        print("Usage: extract.py <input.fnt> <input.mtx> <output.json>")
        exit(1)
    charlist = read_fnt(sys.argv[1])
    print(charlist)
    text = read_mtx(sys.argv[2], charlist)
    with open(sys.argv[3], 'w') as f:
        json.dump(text, f, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    main()
