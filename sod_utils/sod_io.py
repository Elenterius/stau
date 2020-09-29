#!/usr/bin/env python3

# SOD Reader
__author__ = 'Elenterius'
__version__ = '1.2'

# written based on:
#   Storm3D Object Definition (SOD) File Format (Version 1.8)
#   Author: Steve Williams

# uses tweaks from "Armada I/II SOD Importer V1.0.1 for 3dsMax" by Mr. Vulcan for reading SOD files with versions > 1.8

import enum
import struct
from os import walk

from typing import BinaryIO

# data types in little-endian byte order
UINT8 = '<B'  # unsigned char (1 byte)
UINT8_BYTES_SIZE = struct.calcsize(UINT8)

UINT16 = '<H'  # unsigned short (2 bytes)
UINT16_BYTES_SIZE = struct.calcsize(UINT16)

UINT32 = '<I'  # unsigned int (4 bytes)
UINT32_BYTES_SIZE = struct.calcsize(UINT32)

FLOAT = '<f'  # float (4 bytes)
FLOAT_BYTE_SIZE = struct.calcsize(FLOAT)


class NodeType(enum.Enum):
    NULL_OR_HARDPOINT = 0
    LOD_CONTROL = 11
    SPRITE = 3
    MESH = 1
    EMITTER = 12

    @classmethod
    def _missing_(cls, value):
        return NodeType.NULL_OR_HARDPOINT


def read_string(binary_io: BinaryIO):
    # read string length
    length = read_uint16(binary_io)

    # read string
    str_bytes = binary_io.read(UINT8_BYTES_SIZE * length)
    i_tuple = struct.unpack('<' + str(length) + 'B', str_bytes)
    string = bytes(i_tuple).decode('ascii')
    if string == '0':  # 0 indicates null string
        string = None
    return string


def write_string(string: str, binary_io: BinaryIO):
    if string is None:
        string = '0'  # indicates null string

    str_bytes = string.encode('ascii')
    length = len(str_bytes)
    write_uint16(length, binary_io)

    for byte_ in str_bytes:
        byte_ = struct.pack(f'<B', byte_)
        binary_io.write(byte_)


def read_uint8(binary_io: BinaryIO):
    bytes_ = binary_io.read(UINT8_BYTES_SIZE)
    value = struct.unpack(UINT8, bytes_)[0]
    return value


def write_uint8(value, binary_io: BinaryIO):
    bytes_ = struct.pack(UINT8, value)
    binary_io.write(bytes_)


def read_uint16(binary_io: BinaryIO):
    bytes_ = binary_io.read(UINT16_BYTES_SIZE)
    value = struct.unpack(UINT16, bytes_)[0]
    return value


def write_uint16(value, binary_io: BinaryIO):
    bytes_ = struct.pack(UINT16, value)
    binary_io.write(bytes_)


def read_uint32(binary_io: BinaryIO):
    bytes_ = binary_io.read(UINT32_BYTES_SIZE)
    value = struct.unpack(UINT32, bytes_)[0]
    return value


def write_uint32(value, binary_io: BinaryIO):
    bytes_ = struct.pack(UINT32, value)
    binary_io.write(bytes_)


def read_float(binary_io: BinaryIO):
    f_bytes = binary_io.read(FLOAT_BYTE_SIZE)
    f = struct.unpack(FLOAT, f_bytes)[0]
    return f


def write_float(value, binary_io: BinaryIO):
    bytes_ = struct.pack(FLOAT, value)
    binary_io.write(bytes_)


def read_color(binary_io: BinaryIO):
    r = read_float(binary_io)
    g = read_float(binary_io)
    b = read_float(binary_io)
    return [r, g, b]


def write_color(colors, binary_io: BinaryIO):
    write_float(colors[0], binary_io)  # r
    write_float(colors[1], binary_io)  # g
    write_float(colors[2], binary_io)  # b


def read_vector2(binary_io: BinaryIO):
    u = read_float(binary_io)
    v = read_float(binary_io)
    return [u, v]


def write_vector2(vector2, binary_io: BinaryIO):
    write_float(vector2[0], binary_io)  # u
    write_float(vector2[1], binary_io)  # v


def read_vector3(binary_io: BinaryIO):
    x = read_float(binary_io)
    y = read_float(binary_io)
    z = read_float(binary_io)
    return [x, y, z]


def write_vector3(vector3, binary_io: BinaryIO):
    write_float(vector3[0], binary_io)  # x
    write_float(vector3[1], binary_io)  # y
    write_float(vector3[2], binary_io)  # z


def read_matrix34(binary_io: BinaryIO):
    right = read_vector3(binary_io)
    up = read_vector3(binary_io)
    front = read_vector3(binary_io)
    position = read_vector3(binary_io)
    return [right, up, front, position]


def write_matrix34(matrix34, binary_io: BinaryIO):
    write_vector3(matrix34[0], binary_io)  # right
    write_vector3(matrix34[1], binary_io)  # up
    write_vector3(matrix34[2], binary_io)  # front
    write_vector3(matrix34[3], binary_io)  # position


def read_face_vertex(binary_io: BinaryIO):
    index_vertices = read_uint16(binary_io)
    index_texture_cords = read_uint16(binary_io)
    return [index_vertices, index_texture_cords]


def write_face_vertex(face_vertex, binary_io: BinaryIO):
    write_uint16(face_vertex[0], binary_io)  # index_vertices
    write_uint16(face_vertex[1], binary_io)  # index_texture_cords


def read_face(binary_io: BinaryIO):
    face_vertices = read_face_vertex_array(3, binary_io)
    return face_vertices


def write_face(face_vertices, binary_io: BinaryIO):
    write_face_vertex(face_vertices[0], binary_io)
    write_face_vertex(face_vertices[1], binary_io)
    write_face_vertex(face_vertices[2], binary_io)


def read_vertex_lighting_group(binary_io: BinaryIO):
    n_faces = read_uint16(binary_io)
    lighting_material = read_string(binary_io)  # 0 -> default
    faces = read_face_array(n_faces, binary_io)
    return {'lighting_material': lighting_material, 'faces': faces}


def write_vertex_lighting_group(vlg: dict, binary_io: BinaryIO):
    write_uint16(len(vlg['faces']), binary_io)
    if vlg['lighting_material'] is None:
        write_string('0', binary_io)
    else:
        write_string(vlg['lighting_material'], binary_io)

    for face_vertices in vlg['faces']:
        write_face(face_vertices, binary_io)


def read_anim_channel(binary_io: BinaryIO):
    anim = dict()
    anim['node_ref'] = read_string(binary_io)  # node to which this animation channel refers
    n_keyframes = read_uint16(binary_io)
    anim['period'] = read_float(binary_io)  # length of time one loop of this channel lasts
    anim['type'] = read_uint16(binary_io)  # 0 -> position, 5 -> scale  (unused in sod version 1.8)

    if anim['type'] == 0:
        # animation transforms, evenly spaced over time 'channel period'
        anim['keyframe_data'] = read_matrix34_array(n_keyframes, binary_io)

    elif anim['type'] == 5:
        anim['keyframe_data'] = read_float_array(n_keyframes, binary_io)

    return anim


def write_anim_channel(anim_channel: dict, binary_io: BinaryIO):
    write_string(anim_channel['node_ref'], binary_io)
    n_keyframes = len(anim_channel['keyframe_data'])
    write_uint16(n_keyframes, binary_io)
    write_float(anim_channel['period'], binary_io)
    write_uint16(anim_channel['type'], binary_io)

    if anim_channel['type'] == 0:
        for data in anim_channel['keyframe_data']:
            write_matrix34(data, binary_io)
    elif anim_channel['type'] == 5:
        for data in anim_channel['keyframe_data']:
            write_float(data, binary_io)


def read_anim_reference(binary_io: BinaryIO):
    ref = dict()
    ref['type'] = read_uint8(binary_io)  # must be 4
    ref['node'] = read_string(binary_io)  # node to which this animation applies
    ref['anim'] = read_string(binary_io)  # animation (as defined in .spr files) that is to be applied to this node
    ref['playback_offset'] = read_float(binary_io)  # Time offset in seconds to be applied to this animation reference
    return ref


def write_anim_reference(anim_reference: dict, binary_io: BinaryIO):
    write_uint8(anim_reference['type'], binary_io)
    write_uint8(anim_reference['node'], binary_io)
    write_uint8(anim_reference['anim'], binary_io)
    write_float(anim_reference['playback_offset'], binary_io)


def read_float_array(n_entries, binary_file):
    typed_array = []
    for n in range(n_entries):
        typed_array.append(read_float(binary_file))
    return typed_array


def read_matrix34_array(n_entries, binary_file):
    typed_array = []
    for n in range(n_entries):
        typed_array.append(read_matrix34(binary_file))
    return typed_array


def read_anim_reference_array(n_entries, binary_file):
    typed_array = []
    for n in range(n_entries):
        typed_array.append(read_anim_reference(binary_file))
    return typed_array


def read_anim_channel_array(n_entries, binary_file):
    typed_array = []
    for n in range(n_entries):
        typed_array.append(read_anim_channel(binary_file))
    return typed_array


def read_face_vertex_array(n_entries, binary_file):
    typed_array = []
    for n in range(n_entries):
        typed_array.append(read_face_vertex(binary_file))
    return typed_array


def read_face_array(n_entries, binary_file):
    typed_array = []
    for n in range(n_entries):
        typed_array.append(read_face(binary_file))
    return typed_array


def read_vector3_array(n_entries, binary_file):
    typed_array = []
    for n in range(n_entries):
        typed_array.append(read_vector3(binary_file))
    return typed_array


def read_vector2_array(n_entries, binary_file):
    typed_array = []
    for n in range(n_entries):
        typed_array.append(read_vector2(binary_file))
    return typed_array


def read_vertex_lighting_group_array(n_entries, binary_file):
    typed_array = []
    for n in range(n_entries):
        typed_array.append(read_vertex_lighting_group(binary_file))
    return typed_array


class SodParserAndWriter:

    def __init__(self, root_path, texture_path=None):
        self.root_path = root_path
        self.texture_path = texture_path
        self.cached_folders = {}
        self.sod_version = 0.0

        # //REVIEW: remove caching of folder and file names?
        for (dir_path, dir_names, file_names) in walk(root_path):
            if len(file_names) > 0:
                folder_path = dir_path.replace(root_path, '')
                if folder_path == '':
                    folder_path = '\\'  # root
                self.cached_folders[folder_path] = file_names

    def get_folder_for_file(self, file_name):
        for cached_folder_name, cached_file_names in self.cached_folders.items():
            for cached_file_name in cached_file_names:
                if file_name.lower() == cached_file_name.lower():
                    return cached_folder_name
        return None

    def read_file(self, file_path):
        return self.__parse_sod(file_path)

    def __read_file(self, file_name, folder_name=None):
        if folder_name is None:
            folder_name = self.get_folder_for_file(file_name)

        if folder_name:
            file_path = self.root_path + folder_name + '\\' + file_name
            return self.__parse_sod(file_path)
        else:
            raise FileNotFoundError(file_name)

    def write_file(self, sod: dict, file_path: str):
        self.__write_sod(sod, file_path)

    def __parse_sod(self, file_path: str):
        binary_io: BinaryIO
        with open(file_path, "rb") as binary_io:
            binary_io.seek(0, 2)  # seek the end
            bytes_ = binary_io.tell()  # file size
            print(f"reading {bytes_} bytes from file...")

            for i in range(bytes_):
                binary_io.seek(i)
                fid_header_bytes = binary_io.read(10)  # Storm3D_SW

                if fid_header_bytes == b'Storm3D_SW':  # SOD signature

                    self.sod_version = read_float(binary_io)
                    print('SOD Format Version:', self.sod_version)

                    if self.sod_version > 1.6001:  # 1.6 --> can't read fconst.sod
                        sod = {
                            'file_name': file_path.split("\\")[-1],
                            'version': self.sod_version,
                            'materials': self.read_lighting_materials(binary_io),
                            'nodes': self.read_nodes(binary_io),
                            'anim_transforms': self.read_animation_transforms(binary_io),
                            'anim_textures': self.read_anim_tex_refs(binary_io)
                        }

                        return sod
                    else:
                        raise Exception('Unsupported SOD Version')

                elif fid_header_bytes == b'StarTrekDB':
                    raise Exception('Database found instead of Storm3D File')

    def __write_sod(self, sod: dict, file_path):
        binary_io: BinaryIO
        with open(file_path, "wb") as binary_io:
            if self.sod_version > 1.6001:
                binary_io.write(b'Storm3D_SW')
                print('targeting SOD format version:', self.sod_version)
                write_float(self.sod_version, binary_io)

                self.write_lighting_materials(sod['materials'], binary_io)
                self.write_nodes(sod['nodes'], binary_io)
                self.write_animation_transforms(sod['anim_transforms'], binary_io)
                self.write_anim_tex_refs(sod['anim_textures'], binary_io)
            else:
                raise Exception('Unsupported SOD Version')

            bytes_ = binary_io.tell()  # file size
            print(f"wrote {bytes_} bytes to {file_path}")

    def read_lighting_materials(self, binary_io: BinaryIO):
        n_lighting_mat = read_uint16(binary_io)
        if n_lighting_mat > 24:
            print("Warning: Model has more than 24 materials. Meshes with multiple lighting materials may not render properly. E.g. 3dsMax")

        materials = []
        lighting_models = ['constant', 'lambert', 'phong']

        for i in range(0, n_lighting_mat):  # //REVIEW: n_lighting_mat vs. min(n_lighting_mat, 24)
            mat_id = read_string(binary_io)
            ambient_color = read_color(binary_io)
            diffuse_color = read_color(binary_io)
            specular_color = read_color(binary_io)
            specular_shininess = read_float(binary_io)
            lighting_model = lighting_models[read_uint8(binary_io)]  # constant=0, lambert=1, phong=2

            # alpha map illumination
            alpha = read_uint8(binary_io) if self.sod_version > 1.8001 else 0

            material = {
                'name': mat_id,
                'ambient_color': ambient_color,
                'diffuse_color': diffuse_color,
                'specular_color': specular_color,
                'specular_shininess': specular_shininess,
                'lighting_model': lighting_model,
                'self_illumination_enabled': True if alpha > 0 else False
            }

            materials.append(material)

        return materials

    def __lighting_model_to_int(self, model_name: str):
        if model_name == 'constant':
            return 0
        elif model_name == 'lambert':
            return 1
        elif model_name == 'phong':
            return 2
        return 0

    def write_lighting_materials(self, materials: list, binary_io: BinaryIO):
        n_lighting_mat = len(materials)
        write_uint16(n_lighting_mat, binary_io)

        for material in materials:
            write_string(material['name'], binary_io)
            write_color(material['ambient_color'], binary_io)
            write_color(material['diffuse_color'], binary_io)
            write_color(material['specular_color'], binary_io)
            write_float(material['specular_shininess'], binary_io)
            write_uint8(self.__lighting_model_to_int(material['lighting_model']), binary_io)

            if self.sod_version > 1.8001:
                value = 1 if material['self_illumination_enabled'] else 0
                write_uint8(value, binary_io)
            else:
                write_uint8(0, binary_io)

    def read_null_node(self, binary_io: BinaryIO):
        """
        No addtional data required

        Null nodes are used for two purposes :
        1. As 'glue' to stick the rest of the hierarchy together
        2. To mark specific locations in the hierachy, for example, hardpoints
        """
        return None

    def write_null_node(self, data, binary_io: BinaryIO):
        return

    def read_lod_node(self, binary_io: BinaryIO):
        """
        No addtional data required

        Storm3D uses discrete (rather than dynamic) LODs for level of detail control. Each
        child of an LOD control node indicates a discrete LOD that the graphics engine may
        use when rendering this object. LOD selection is based on visible on-screen area.
        """
        return None

    def write_lod_node(self, data, binary_io: BinaryIO):
        return

    def read_sprite_node(self, binary_io: BinaryIO):
        """
        None: The appropriate sprite node definition to use is determined from the identifier.
        The sprite node definition is defined in the .spr files

        Examples of sprite node usage include running lights in ST:Armada.
        """
        return None

    def write_sprite_node(self, data, binary_io: BinaryIO):
        return

    def read_emitter_node(self, binary_io: BinaryIO):
        # as defined by an @emitter description in the .spr files
        emitter_id = read_string(binary_io)
        return emitter_id

    def write_emitter_node(self, emitter_id: str, binary_io: BinaryIO):
        write_string(emitter_id, binary_io)

    # noinspection PyUnusedLocal
    def read_mesh_node(self, binary_io: BinaryIO):
        mesh = dict()

        """
        blending types

        default - Standard material
        additive - Use additive blending
        translucent - Semi transparent
        alphathreshold - Use for objects using alpha channel 'cut outs' - alpha channels will have hard edged 'threshold' but objects will be drawn quickly.
        alpha - Uses entire alpha channel. Object will require sorting, so will have performance implications.
        wireframe - Use wireframe graphics.
        """
        mesh['texture_material'] = read_string(binary_io)  # 0 -> default

        mesh['bump_map'] = 0
        if self.sod_version > 1.9101:
            unused = read_uint32(binary_io)
            mesh['bump_map'] = read_uint32(binary_io)

        texture = read_string(binary_io)  # 0 -> untextured
        if self.texture_path:
            mesh['texture'] = self.texture_path + '\\' + texture
        else:
            mesh['texture'] = texture

        if self.sod_version == 1.91:
            unknown = read_uint16(binary_io)

        # borg texture (assimilated entity)
        if self.sod_version > 1.9101:
            mesh['borgification'] = borg = {}

            unknown = read_uint16(binary_io)
            unknown = read_uint16(binary_io)

            if mesh['bump_map'] == 2:
                borg['bump_map'] = read_string(binary_io)
                if self.texture_path:
                    borg['bump_map'] = self.texture_path + '\\' + borg['bump_map']

                unknown = read_uint16(binary_io)
                unknown = read_uint16(binary_io)

            borg['texture'] = read_string(binary_io)  # can be empty???
            if self.texture_path:
                if borg['texture'].strip() == '':
                    borg['texture'] = texture + '_B'
                borg['texture'] = self.texture_path + '\\' + borg['texture']

            unknown = read_uint16(binary_io)

        n_vertices = read_uint16(binary_io)
        n_texture_coords = read_uint16(binary_io)
        n_groups = read_uint16(binary_io)  # vertex lighting groups
        mesh['vertices'] = read_vector3_array(n_vertices, binary_io)
        mesh['texture_coordinates'] = read_vector2_array(n_texture_coords, binary_io)
        mesh['vertex_lighting_groups'] = read_vertex_lighting_group_array(n_groups, binary_io)

        mesh['cull_type'] = 'NO_CULL' if read_uint8(binary_io) == 0 else 'BACKFACE_CULL'  # 0 -> no cull, 1 -> backface cull

        unused = read_uint16(binary_io)
        if unused != 0:
            raise Exception('Invalid EndOfNode, must be 0 but is ' + str(unused))

        return mesh

    def write_mesh_node(self, mesh: dict, binary_io: BinaryIO):
        write_string(mesh['texture_material'], binary_io)

        if self.sod_version > 1.9101:
            write_uint32(0, binary_io)  # unused
            write_uint32(mesh['bump_map'], binary_io)  # TODO: verify this

        texture: str = mesh['texture']
        texture_name = texture.split('\\')[-1]  # strip any path and get only texture name
        write_string(texture_name, binary_io)

        if self.sod_version == 1.91:
            write_uint16(0, binary_io)  # unknown

        # borg texture (assimilated entity)
        if self.sod_version > 1.9101:
            write_uint16(0, binary_io)  # unknown
            write_uint16(0, binary_io)  # unknown

            borg = mesh['borgification']
            if mesh['bump_map'] == 2:
                borge_bump_map: str = borg['bump_map']
                borge_bump_map_name = borge_bump_map.split('\\')[-1]  # strip any path and get only texture name
                write_string(borge_bump_map_name, binary_io)

                write_uint16(0, binary_io)  # unknown
                write_uint16(0, binary_io)  # unknown

            borg_texture: str = borg['texture']
            borg_texture_name = borg_texture.split('\\')[-1]  # strip any path and get only texture name
            write_string(borg_texture_name, binary_io)

            write_uint16(0, binary_io)  # unknown

        n_vertices = len(mesh['vertices'])
        n_texture_coords = len(mesh['texture_coordinates'])
        n_groups = len(mesh['vertex_lighting_groups'])
        write_uint16(n_vertices, binary_io)
        write_uint16(n_texture_coords, binary_io)
        write_uint16(n_groups, binary_io)

        for vertex in mesh['vertices']:
            write_vector3(vertex, binary_io)

        for texture_coord in mesh['texture_coordinates']:
            write_vector2(texture_coord, binary_io)

        for vlg in mesh['vertex_lighting_groups']:
            write_vertex_lighting_group(vlg, binary_io)

        if mesh['cull_type'] == 'BACKFACE_CULL':
            write_uint8(1, binary_io)
        else:
            write_uint8(0, binary_io)  # NO_CULL

        write_uint16(0, binary_io)  # end of node

    def read_typed_node(self, node_type: NodeType, binary_io: BinaryIO):
        if node_type is NodeType.NULL_OR_HARDPOINT:
            return self.read_null_node(binary_io)
        elif node_type is NodeType.LOD_CONTROL:
            return self.read_lod_node(binary_io)
        elif node_type is NodeType.SPRITE:
            return self.read_sprite_node(binary_io)
        elif node_type is NodeType.MESH:
            return self.read_mesh_node(binary_io)
        elif node_type is NodeType.EMITTER:
            return self.read_emitter_node(binary_io)
        else:
            return None

    def write_typed_node(self, node_type: NodeType, node_data, binary_io: BinaryIO):
        if node_type is NodeType.NULL_OR_HARDPOINT:
            self.write_null_node(node_data, binary_io)
        elif node_type is NodeType.LOD_CONTROL:
            self.write_lod_node(node_data, binary_io)
        elif node_type is NodeType.SPRITE:
            self.write_sprite_node(node_data, binary_io)
        elif node_type is NodeType.MESH:
            self.write_mesh_node(node_data, binary_io)
        elif node_type is NodeType.EMITTER:
            self.write_emitter_node(node_data, binary_io)

    def read_nodes(self, binary_io: BinaryIO):
        nodes = []
        n_nodes = read_uint16(binary_io)

        for i in range(0, n_nodes):
            node = {}
            node_type = NodeType(read_uint16(binary_io))  # 0 = null/hardpoint, 1 = mesh, 3 = sprite, 11 = LOD control node, 12 = emitter
            node['type'] = node_type.name
            node['id'] = read_string(binary_io)
            node['parent'] = read_string(binary_io)  # None if root node

            node['local_transform'] = read_matrix34(binary_io)  # right, up, front, position
            node['data'] = self.read_typed_node(node_type, binary_io)
            nodes.append(node)

        return nodes

    def write_nodes(self, nodes: list, binary_io: BinaryIO):
        n_nodes = len(nodes)
        write_uint16(n_nodes, binary_io)

        for node in nodes:
            node_type_name: str = node['type']
            node_type: NodeType = NodeType[node_type_name]
            write_uint16(node_type.value, binary_io)
            write_string(node['id'], binary_io)
            write_string(node['parent'], binary_io)

            write_matrix34(node['local_transform'], binary_io)
            self.write_typed_node(node_type, node['data'], binary_io)

    def read_animation_transforms(self, binary_io: BinaryIO):
        n_channels = read_uint16(binary_io)
        channels = read_anim_channel_array(n_channels, binary_io)
        return channels

    def write_animation_transforms(self, channels: list, binary_io: BinaryIO):
        n_channels = len(channels)
        write_uint16(n_channels, binary_io)
        for channel in channels:
            write_anim_channel(channel, binary_io)

    def read_anim_tex_refs(self, binary_io: BinaryIO):
        """
        Animation references are a way of linking texture (flipbook) animations defined in the .spr files to the geometry of a .SOD mesh node.
        An example of their usage is the flipbook animation applied to the geometry for the various shield effects in Armada
        """
        n_references = read_uint16(binary_io)
        references = read_anim_reference_array(n_references, binary_io)
        return references

    def write_anim_tex_refs(self, references: list, binary_io: BinaryIO):
        n_references = len(references)
        write_uint16(n_references, binary_io)
        for reference in references:
            write_anim_reference(reference, binary_io)
