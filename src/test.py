#!/usr/bin/env python3
import json

from sod_utils.sod_io import SodIO, Sod, NodeType
import time


def parse_sod_and_dump(file_path: str, file_name):
    print()
    print(f"parsing {file_path}...")

    sod_io = SodIO()
    start_time = time.process_time_ns()
    sod: Sod = sod_io.read_file(file_path)
    print(f"finished parsing in {(time.process_time_ns() - start_time) / 1e+6} ms")

    with open(f'../dump/{file_name}.json', 'w') as outfile:
        json.dump(sod.to_dict(), outfile)

    print("\nwriting sod...")
    start_time = time.process_time_ns()
    sod_io.write_file(sod, f'../dump/{file_name}.sod')
    print(f"finished writing in {(time.process_time_ns() - start_time) / 1e+6} ms")


def dump_sod(filename):
    parse_sod_and_dump(f'D:\\Program Files (x86)\\Activision\\Star Trek Armada II\\SOD\\{filename}.sod', filename)
    parse_sod_and_dump(f'../dump/{filename}.sod', filename + "_2")


def parse_sod(filename: str):
    file_path = f'D:\\Program Files (x86)\\Activision\\Star Trek Armada II\\SOD\\{filename}.sod'
    print(f"parsing {file_path}...")

    sod: Sod = SodIO().read_file(file_path)

    print()
    print("LOD Geometry count:", len(sod.geometry))
    print("Mesh count:", len(sod.meshes))
    print("Material count:", len(sod.materials))
    print("Light Count:", len(sod.lights))

    print(sod.geometry)
    for node in sod.nodes:
        if node["parent"].lower() == "lod0":
            print(node)

    print()
    print("Hardpoint count:", len(sod.hardpoints))
    print("Damage count:", len(sod.damage))

    # for node in sod.nodes:
    #     # if node["type"] == NodeType.NULL_OR_HARDPOINT.name:
    #     if node["parent"].lower() == "lights":
    #         print(node["id"],  node["type"])


import numpy as np
import mathutils


if __name__ == '__main__':
    # dump_sod('fbattle')
    # dump_sod('8472_mother')
    # dump_sod('fconst')
    # parse_sod('fconst')
    # parse_sod('fbattle')

    # right up front
    vectors = np.array([[1.0, 0.0, -0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 0.9999999403953552]])
    for i in range(3):
        vectors[i, 0] *= -1
        y = vectors[i, 1]
        vectors[i, 1] = vectors[i, 2]
        vectors[i, 2] = y

    vectors2 = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    for i in range(3):
        vectors2[i, 0] *= -1
        y = vectors2[i, 1]
        vectors2[i, 1] = vectors2[i, 2]
        vectors2[i, 2] = y

    m1 = mathutils.Matrix(vectors)
    m2 = mathutils.Matrix(vectors2)
    m1 = m1.__matmul__(m2)
    print(m1)
    print(np.rad2deg(m1.to_euler()))
    print(np.rad2deg(m2.to_euler()))

