#!/usr/bin/env python3
import json
from sod_utils import sod_io as sodio
import time


def test_sod_reader_writer_1():
    print("=== testing sod parsing ===")
    root_path = 'D:\\Program Files (x86)\\Activision\\Star Trek Armada II\\SOD'
    texture_path = 'D:\\Program Files (x86)\\Activision\\Star Trek Armada II\\Textures\\RGB'

    sod_parser = sodio.SodParserAndWriter(root_path, texture_path)
    start_time = time.process_time_ns()
    sod = sod_parser._read_file('fbattle.sod')
    print(f"finished parsing in {time.process_time_ns() - start_time}ns")

    with open('fbattle.json', 'w') as outfile:
        json.dump(sod, outfile)

    print("=== testing sod writer ===")
    start_time = time.process_time_ns()
    sod_parser.write_file(sod, 'fbattle.sod')
    print(f"finished writing in {time.process_time_ns() - start_time}ns")


def test_sod_reader_writer_2():
    print("=== testing sod parsing ===")
    root_path = ''
    texture_path = 'D:\\Program Files (x86)\\Activision\\Star Trek Armada II\\Textures\\RGB'

    sod_parser = sodio.SodParserAndWriter(root_path, texture_path)
    start_time = time.process_time_ns()
    sod = sod_parser.read_file('fbattle.sod')
    print(f"finished parsing in {time.process_time_ns() - start_time}ns")

    with open('fbattle2.json', 'w') as outfile:
        json.dump(sod, outfile)

    print("=== testing sod writer ===")
    start_time = time.process_time_ns()
    sod_parser.write_file(sod, 'fbattle2.sod')
    print(f"finished writing in {time.process_time_ns() - start_time}ns")


if __name__ == '__main__':
    test_sod_reader_writer_1()
    test_sod_reader_writer_2()
