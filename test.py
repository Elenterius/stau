#!/usr/bin/env python3
import json
import struct

import numpy

from sod_utils import sod_io as sodio
import time


def test_sod_reader_writer_1():
    print("=== testing sod parsing ===")
    texture_path = 'D:\\Program Files (x86)\\Activision\\Star Trek Armada II\\Textures\\RGB'
    file_path = 'D:\\Program Files (x86)\\Activision\\Star Trek Armada II\\SOD\\fbattle.sod'

    sod_io = sodio.SodIO()
    start_time = time.process_time_ns()
    sod = sod_io.read_file(file_path)
    print(f"finished parsing in {time.process_time_ns() - start_time}ns")

    with open('dump/fbattle.json', 'w') as outfile:
        json.dump(sod.to_dict(), outfile)

    print("=== testing sod writer ===")
    start_time = time.process_time_ns()
    sod_io.write_file(sod, 'dump/fbattle.sod')
    print(f"finished writing in {time.process_time_ns() - start_time}ns")


def test_sod_reader_writer_2():
    print("=== testing sod parsing ===")
    texture_path = 'D:\\Program Files (x86)\\Activision\\Star Trek Armada II\\Textures\\RGB'

    sod_io = sodio.SodIO()
    start_time = time.process_time_ns()
    sod = sod_io.read_file('dump/fbattle.sod')
    print(f"finished parsing in {time.process_time_ns() - start_time}ns")

    with open('dump/fbattle2.json', 'w') as outfile:
        json.dump(sod.to_dict(), outfile)

    print("=== testing sod writer ===")
    start_time = time.process_time_ns()
    sod_io.write_file(sod, 'dump/fbattle2.sod')
    print(f"finished writing in {time.process_time_ns() - start_time}ns")


def print_floats():
    print(1.93)
    print(float(numpy.float32(1.93)))
    print(struct.unpack('<f', struct.pack('<f', 1.93))[0])


if __name__ == '__main__':
    test_sod_reader_writer_1()
    test_sod_reader_writer_2()
    print_floats()
