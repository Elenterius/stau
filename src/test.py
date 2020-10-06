#!/usr/bin/env python3
import json
import struct

import numpy

from sod_utils import sod_io as sodio
import time


def parse_sod_and_dump(file_path: str, file_name):
    print()
    print(f"parsing {file_path}...")

    sod_io = sodio.SodIO()
    start_time = time.process_time_ns()
    sod = sod_io.read_file(file_path)
    print(f"finished parsing in {(time.process_time_ns() - start_time)/1e+6} ms")

    with open(f'../dump/{file_name}.json', 'w') as outfile:
        json.dump(sod.to_dict(), outfile)

    print("\nwriting sod...")
    start_time = time.process_time_ns()
    sod_io.write_file(sod, f'../dump/{file_name}.sod')
    print(f"finished writing in {(time.process_time_ns() - start_time)/1e+6} ms")


def reparse_dumped_sod(file_name: str):
    print()
    print(f"re-parsing ../dump/{file_name}.sod...")

    sod_io = sodio.SodIO()
    start_time = time.process_time_ns()
    sod = sod_io.read_file(f'../dump/{file_name}.sod')
    print(f"finished parsing in {(time.process_time_ns() - start_time)/1e+6} ms")

    with open(f'../dump/{file_name}2.json', 'w') as outfile:
        json.dump(sod.to_dict(), outfile)

    print("\nwriting sod...")
    start_time = time.process_time_ns()
    sod_io.write_file(sod, f'../dump/{file_name}2.sod')
    print(f"finished writing in {(time.process_time_ns() - start_time)/1e+6} ms")


def dump_sod(filename):
    parse_sod_and_dump(f'D:\\Program Files (x86)\\Activision\\Star Trek Armada II\\SOD\\{filename}.sod', filename)
    reparse_dumped_sod(filename)


def print_floats(value):
    print(value)
    print(float(numpy.float32(value)))
    print(struct.unpack('<f', struct.pack('<f', value))[0])


if __name__ == '__main__':
    # print_floats(1.93)
    # dump_sod('fbattle')
    # dump_sod('8472_mother')
    dump_sod('fconst')

