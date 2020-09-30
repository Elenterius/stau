#!/usr/bin/env python3

# SOD IO
__author__ = 'Elenterius'
__version__ = '1.3'

# implemented based on:
#   Storm3D Object Definition (SOD) File Format (Version 1.8)
#   Author: Steve Williams

import struct
# uses tweaks from "Armada I/II SOD Importer V1.0.1 for 3dsMax" by Mr. Vulcan for reading SOD files with versions > 1.8
from enum import IntEnum, Enum
from typing import BinaryIO, List

# data types in little-endian byte order
import numpy


class NodeType(Enum):
    NULL_OR_HARDPOINT = 0
    LOD_CONTROL = 11
    SPRITE = 3
    MESH = 1
    EMITTER = 12

    @classmethod
    def _missing_(cls, value):
        print(f"Warning: unknown node type with value {value}, using NULL_OR_HARDPOINT instead")
        return NodeType.NULL_OR_HARDPOINT


class LightingModel(IntEnum):
    CONSTANT = 0
    LAMBERT = 1
    PHONG = 2

    @classmethod
    def _missing_(cls, value):
        print(f"Warning: unknown lighting model with value {value}, using CONSTANT instead")
        return NodeType.CONSTANT


class Sod:
    def __init__(self, file_name, version=1.93):
        self._file_name = file_name
        self._version = version
        self.__materials = None
        self._nodes = None
        self._animation_transforms = None
        self._animation_tex_refs = None

    def set_name(self, name: str):
        self._file_name = name

    @property
    def name(self) -> str:
        return self._file_name

    def get_version_as_float32(self):
        return numpy.float32(self._version)

    def set_version(self, value: float):
        self._version = value

    @property
    def version(self) -> float:
        return self._version

    def set_materials(self, materials: List):
        self.__materials = materials

    @property
    def materials(self):
        return self.__materials

    def set_nodes(self, nodes: List):
        self._nodes = nodes

    @property
    def nodes(self):
        return self._nodes

    def set_animation_transforms(self, animation_transforms: List):
        self._animation_transforms = animation_transforms

    @property
    def animation_transforms(self):
        return self._animation_transforms

    def set_animation_tex_refs(self, animation_tex_refs: List):
        self._animation_tex_refs = animation_tex_refs

    @property
    def animation_tex_refs(self):
        return self._animation_tex_refs

    def to_dict(self):
        return {
            'file_name': self._file_name,
            'version': self._version,
            'materials': self.__materials,
            'nodes': self._nodes,
            'anim_transforms': self._animation_transforms,
            'anim_textures': self._animation_tex_refs
        }


class SodIO:
    UINT8 = '<B'  # unsigned char (1 byte)
    UINT8_BYTES_SIZE = struct.calcsize(UINT8)

    UINT16 = '<H'  # unsigned short (2 bytes)
    UINT16_BYTES_SIZE = struct.calcsize(UINT16)

    UINT32 = '<I'  # unsigned int (4 bytes)
    UINT32_BYTES_SIZE = struct.calcsize(UINT32)

    FLOAT = '<f'  # float (4 bytes)
    FLOAT_BYTE_SIZE = struct.calcsize(FLOAT)

    MAGIC_STRING = b'Storm3D_SW'  # SOD signature
    MAGIC_STRING_SIZE = 10  # magic string size in bytes

    DEFAULT_SOD_VERSION = struct.unpack(FLOAT, struct.pack(FLOAT, 1.93))[0]

    def __init__(self):
        self.curr_sod_version = 0.0

    def read_file(self, file_path) -> Sod:
        return self.__parse_sod(file_path)

    def write_file(self, sod: Sod, file_path: str):
        self.__write_sod(sod, file_path)

    def __parse_sod(self, file_path: str) -> Sod:
        binary_io: BinaryIO
        with open(file_path, "rb") as binary_io:
            binary_io.seek(0, 2)  # seek the end
            bytes_ = binary_io.tell()  # file size
            print(f"reading {bytes_} bytes from input...")

            for i in range(bytes_):
                binary_io.seek(i)

                header_bytes = binary_io.read(self.MAGIC_STRING_SIZE)
                if header_bytes == self.MAGIC_STRING:

                    self.curr_sod_version = self.read_float(binary_io)
                    print('SOD Format Version:', numpy.float32(self.curr_sod_version))  # print version as float32 representation

                    if self.curr_sod_version > 1.6001:  # 1.6 --> can't read fconst.sod
                        sod = Sod(file_name=file_path.split("\\")[-1], version=self.curr_sod_version)
                        sod.set_materials(self.read_lighting_materials(binary_io))
                        sod.set_nodes(self.read_nodes(binary_io))
                        sod.set_animation_transforms(self.read_animation_transforms(binary_io))
                        sod.set_animation_tex_refs(self.read_anim_tex_refs(binary_io))
                        return sod
                    else:
                        raise Exception('Unsupported SOD Version')

                elif header_bytes == b'StarTrekDB':
                    raise Exception('Database found instead of Storm3D File')

    def __write_sod(self, sod: Sod, file_path):
        binary_io: BinaryIO
        with open(file_path, "wb") as binary_io:
            if self.curr_sod_version > 1.6001:
                binary_io.write(self.MAGIC_STRING)
                print('targeting sod format version:', sod.get_version_as_float32())
                self.write_float(sod.version, binary_io)
                self.write_lighting_materials(sod.materials, binary_io)
                self.write_nodes(sod.nodes, binary_io)
                self.write_animation_transforms(sod.animation_transforms, binary_io)
                self.write_anim_tex_refs(sod.animation_tex_refs, binary_io)
            else:
                raise Exception('Unsupported SOD Version')

            bytes_ = binary_io.tell()  # file size
            print(f"wrote {bytes_} bytes to {file_path}")

    def read_string(self, binary_io: BinaryIO):
        # read string length
        length = self.read_uint16(binary_io)

        # read string
        str_bytes = binary_io.read(self.UINT8_BYTES_SIZE * length)
        i_tuple = struct.unpack('<' + str(length) + 'B', str_bytes)
        string = bytes(i_tuple).decode('ascii')
        if string == '0':  # 0 indicates null string
            string = None
        return string

    def write_string(self, string: str, binary_io: BinaryIO):
        if string is None:
            string = '0'  # indicates null string

        str_bytes = string.encode('ascii')
        length = len(str_bytes)
        self.write_uint16(length, binary_io)

        for byte_ in str_bytes:
            byte_ = struct.pack(f'<B', byte_)
            binary_io.write(byte_)

    def read_uint8(self, binary_io: BinaryIO):
        bytes_ = binary_io.read(self.UINT8_BYTES_SIZE)
        value = struct.unpack(self.UINT8, bytes_)[0]
        return value

    def write_uint8(self, value, binary_io: BinaryIO):
        bytes_ = struct.pack(self.UINT8, value)
        binary_io.write(bytes_)

    def read_uint16(self, binary_io: BinaryIO):
        bytes_ = binary_io.read(self.UINT16_BYTES_SIZE)
        value = struct.unpack(self.UINT16, bytes_)[0]
        return value

    def write_uint16(self, value, binary_io: BinaryIO):
        bytes_ = struct.pack(self.UINT16, value)
        binary_io.write(bytes_)

    def read_uint32(self, binary_io: BinaryIO):
        bytes_ = binary_io.read(self.UINT32_BYTES_SIZE)
        value = struct.unpack(self.UINT32, bytes_)[0]
        return value

    def write_uint32(self, value, binary_io: BinaryIO):
        bytes_ = struct.pack(self.UINT32, value)
        binary_io.write(bytes_)

    def read_float(self, binary_io: BinaryIO):
        f_bytes = binary_io.read(self.FLOAT_BYTE_SIZE)
        f = struct.unpack(self.FLOAT, f_bytes)[0]
        # note: floats in python are double precision
        return f

    def write_float(self, value, binary_io: BinaryIO):
        bytes_ = struct.pack(self.FLOAT, value)
        binary_io.write(bytes_)

    def read_color(self, binary_io: BinaryIO):
        r = self.read_float(binary_io)
        g = self.read_float(binary_io)
        b = self.read_float(binary_io)
        return [r, g, b]

    def write_color(self, colors, binary_io: BinaryIO):
        self.write_float(colors[0], binary_io)  # r
        self.write_float(colors[1], binary_io)  # g
        self.write_float(colors[2], binary_io)  # b

    def read_vector2(self, binary_io: BinaryIO):
        u = self.read_float(binary_io)
        v = self.read_float(binary_io)
        return [u, v]

    def write_vector2(self, vector2, binary_io: BinaryIO):
        self.write_float(vector2[0], binary_io)  # u
        self.write_float(vector2[1], binary_io)  # v

    def read_vector3(self, binary_io: BinaryIO):
        x = self.read_float(binary_io)
        y = self.read_float(binary_io)
        z = self.read_float(binary_io)
        return [x, y, z]

    def write_vector3(self, vector3, binary_io: BinaryIO):
        self.write_float(vector3[0], binary_io)  # x
        self.write_float(vector3[1], binary_io)  # y
        self.write_float(vector3[2], binary_io)  # z

    def read_matrix34(self, binary_io: BinaryIO):
        right = self.read_vector3(binary_io)
        up = self.read_vector3(binary_io)
        front = self.read_vector3(binary_io)
        position = self.read_vector3(binary_io)
        return [right, up, front, position]

    def write_matrix34(self, matrix34, binary_io: BinaryIO):
        self.write_vector3(matrix34[0], binary_io)  # right
        self.write_vector3(matrix34[1], binary_io)  # up
        self.write_vector3(matrix34[2], binary_io)  # front
        self.write_vector3(matrix34[3], binary_io)  # position

    def read_face_vertex(self, binary_io: BinaryIO):
        index_vertices = self.read_uint16(binary_io)
        index_texture_cords = self.read_uint16(binary_io)
        return [index_vertices, index_texture_cords]

    def write_face_vertex(self, face_vertex, binary_io: BinaryIO):
        self.write_uint16(face_vertex[0], binary_io)  # index_vertices
        self.write_uint16(face_vertex[1], binary_io)  # index_texture_cords

    def read_face(self, binary_io: BinaryIO):
        face_vertices = self.read_face_vertex_array(3, binary_io)
        return face_vertices

    def write_face(self, face_vertices, binary_io: BinaryIO):
        self.write_face_vertex(face_vertices[0], binary_io)
        self.write_face_vertex(face_vertices[1], binary_io)
        self.write_face_vertex(face_vertices[2], binary_io)

    def read_vertex_lighting_group(self, binary_io: BinaryIO):
        n_faces = self.read_uint16(binary_io)
        lighting_material = self.read_string(binary_io)  # 0 -> default
        faces = self.read_face_array(n_faces, binary_io)
        return {'lighting_material': lighting_material, 'faces': faces}

    def write_vertex_lighting_group(self, vlg: dict, binary_io: BinaryIO):
        self.write_uint16(len(vlg['faces']), binary_io)
        if vlg['lighting_material'] is None:
            self.write_string('0', binary_io)
        else:
            self.write_string(vlg['lighting_material'], binary_io)

        for face_vertices in vlg['faces']:
            self.write_face(face_vertices, binary_io)

    def read_anim_channel(self, binary_io: BinaryIO):
        anim = dict()
        anim['node_ref'] = self.read_string(binary_io)  # node to which this animation channel refers
        n_keyframes = self.read_uint16(binary_io)
        anim['period'] = self.read_float(binary_io)  # length of time one loop of this channel lasts
        anim['type'] = self.read_uint16(binary_io)  # 0 -> position, 5 -> scale  (unused in sod version 1.8)

        if anim['type'] == 0:
            # animation transforms, evenly spaced over time 'channel period'
            anim['keyframe_data'] = self.read_matrix34_array(n_keyframes, binary_io)

        elif anim['type'] == 5:
            anim['keyframe_data'] = self.read_float_array(n_keyframes, binary_io)

        return anim

    def write_anim_channel(self, anim_channel: dict, binary_io: BinaryIO):
        self.write_string(anim_channel['node_ref'], binary_io)
        n_keyframes = len(anim_channel['keyframe_data'])
        self.write_uint16(n_keyframes, binary_io)
        self.write_float(anim_channel['period'], binary_io)
        self.write_uint16(anim_channel['type'], binary_io)

        if anim_channel['type'] == 0:
            for data in anim_channel['keyframe_data']:
                self.write_matrix34(data, binary_io)
        elif anim_channel['type'] == 5:
            for data in anim_channel['keyframe_data']:
                self.write_float(data, binary_io)

    def read_anim_reference(self, binary_io: BinaryIO):
        ref = dict()
        ref['type'] = self.read_uint8(binary_io)  # must be 4
        ref['node'] = self.read_string(binary_io)  # node to which this animation applies
        ref['anim'] = self.read_string(binary_io)  # animation (as defined in .spr files) that is to be applied to this node
        ref['playback_offset'] = self.read_float(binary_io)  # Time offset in seconds to be applied to this animation reference
        return ref

    def write_anim_reference(self, anim_reference: dict, binary_io: BinaryIO):
        self.write_uint8(anim_reference['type'], binary_io)
        self.write_uint8(anim_reference['node'], binary_io)
        self.write_uint8(anim_reference['anim'], binary_io)
        self.write_float(anim_reference['playback_offset'], binary_io)

    def read_float_array(self, n_entries, binary_file):
        typed_array = []
        for n in range(n_entries):
            typed_array.append(self.read_float(binary_file))
        return typed_array

    def read_matrix34_array(self, n_entries, binary_file):
        typed_array = []
        for n in range(n_entries):
            typed_array.append(self.read_matrix34(binary_file))
        return typed_array

    def read_anim_reference_array(self, n_entries, binary_file):
        typed_array = []
        for n in range(n_entries):
            typed_array.append(self.read_anim_reference(binary_file))
        return typed_array

    def read_anim_channel_array(self, n_entries, binary_file):
        typed_array = []
        for n in range(n_entries):
            typed_array.append(self.read_anim_channel(binary_file))
        return typed_array

    def read_face_vertex_array(self, n_entries, binary_file):
        typed_array = []
        for n in range(n_entries):
            typed_array.append(self.read_face_vertex(binary_file))
        return typed_array

    def read_face_array(self, n_entries, binary_file):
        typed_array = []
        for n in range(n_entries):
            typed_array.append(self.read_face(binary_file))
        return typed_array

    def read_vector3_array(self, n_entries, binary_file):
        typed_array = []
        for n in range(n_entries):
            typed_array.append(self.read_vector3(binary_file))
        return typed_array

    def read_vector2_array(self, n_entries, binary_file):
        typed_array = []
        for n in range(n_entries):
            typed_array.append(self.read_vector2(binary_file))
        return typed_array

    def read_vertex_lighting_group_array(self, n_entries, binary_file):
        typed_array = []
        for n in range(n_entries):
            typed_array.append(self.read_vertex_lighting_group(binary_file))
        return typed_array

    def read_lighting_materials(self, binary_io: BinaryIO):
        n_lighting_mat = self.read_uint16(binary_io)
        materials = []

        for i in range(0, n_lighting_mat):
            material = {
                'name': self.read_string(binary_io),
                'ambient_color': self.read_color(binary_io),
                'diffuse_color': self.read_color(binary_io),
                'specular_color': self.read_color(binary_io),
                'specular_shininess': self.read_float(binary_io),
                'lighting_model': LightingModel(self.read_uint8(binary_io)),
                'self_illumination_enabled': False
            }

            if self.curr_sod_version > 1.8001:
                alpha = self.read_uint8(binary_io)  # alpha map illumination
                if alpha > 0:
                    material['self_illumination_enabled'] = True

            materials.append(material)

        return materials

    def write_lighting_materials(self, materials: list, binary_io: BinaryIO):
        n_lighting_mat = len(materials)
        self.write_uint16(n_lighting_mat, binary_io)

        for material in materials:
            self.write_string(material['name'], binary_io)
            self.write_color(material['ambient_color'], binary_io)
            self.write_color(material['diffuse_color'], binary_io)
            self.write_color(material['specular_color'], binary_io)
            self.write_float(material['specular_shininess'], binary_io)
            lighting_model: LightingModel = material['lighting_model']
            self.write_uint8(lighting_model.value, binary_io)

            if self.curr_sod_version > 1.8001:
                value = 1 if material['self_illumination_enabled'] else 0
                self.write_uint8(value, binary_io)

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
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

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
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

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
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
        emitter_id = self.read_string(binary_io)
        return emitter_id

    def write_emitter_node(self, emitter_id: str, binary_io: BinaryIO):
        self.write_string(emitter_id, binary_io)

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
        mesh['texture_material'] = self.read_string(binary_io)  # 0 -> default

        mesh['bump_map'] = 0
        if self.curr_sod_version > 1.9101:
            unused = self.read_uint32(binary_io)
            mesh['bump_map'] = self.read_uint32(binary_io)

        texture = self.read_string(binary_io)  # 0 -> untextured
        mesh['texture'] = texture

        if self.curr_sod_version == 1.91:
            unknown = self.read_uint16(binary_io)

        # borg texture (assimilated entity)
        if self.curr_sod_version > 1.9101:
            mesh['borgification'] = borg = {}

            unknown = self.read_uint16(binary_io)
            unknown = self.read_uint16(binary_io)

            if mesh['bump_map'] == 2:
                borg['bump_map'] = self.read_string(binary_io)

                unknown = self.read_uint16(binary_io)
                unknown = self.read_uint16(binary_io)

            borg['texture'] = self.read_string(binary_io)  # can be empty?
            if borg['texture'].strip() == '':
                borg['texture'] = texture + '_B'

            unknown = self.read_uint16(binary_io)

        n_vertices = self.read_uint16(binary_io)
        n_texture_coords = self.read_uint16(binary_io)
        n_groups = self.read_uint16(binary_io)  # vertex lighting groups
        mesh['vertices'] = self.read_vector3_array(n_vertices, binary_io)
        mesh['texture_coordinates'] = self.read_vector2_array(n_texture_coords, binary_io)
        mesh['vertex_lighting_groups'] = self.read_vertex_lighting_group_array(n_groups, binary_io)

        mesh['cull_type'] = 'NO_CULL' if self.read_uint8(binary_io) == 0 else 'BACKFACE_CULL'  # 0 -> no cull, 1 -> backface cull

        unused = self.read_uint16(binary_io)
        if unused != 0:
            raise Exception('Invalid EndOfNode, must be 0 but is ' + str(unused))

        return mesh

    def write_mesh_node(self, mesh: dict, binary_io: BinaryIO):
        self.write_string(mesh['texture_material'], binary_io)

        if self.curr_sod_version > 1.9101:
            self.write_uint32(0, binary_io)  # unused
            self.write_uint32(mesh['bump_map'], binary_io)

        self.write_string(mesh['texture'], binary_io)

        if self.curr_sod_version == 1.91:
            self.write_uint16(0, binary_io)  # unknown

        # borg texture (assimilated entity)
        if self.curr_sod_version > 1.9101:
            self.write_uint16(0, binary_io)  # unknown
            self.write_uint16(0, binary_io)  # unknown

            borg = mesh['borgification']
            if mesh['bump_map'] == 2:
                self.write_string(borg['bump_map'], binary_io)

                self.write_uint16(0, binary_io)  # unknown
                self.write_uint16(0, binary_io)  # unknown

            self.write_string(borg['texture'], binary_io)

            self.write_uint16(0, binary_io)  # unknown

        n_vertices = len(mesh['vertices'])
        n_texture_coords = len(mesh['texture_coordinates'])
        n_groups = len(mesh['vertex_lighting_groups'])
        self.write_uint16(n_vertices, binary_io)
        self.write_uint16(n_texture_coords, binary_io)
        self.write_uint16(n_groups, binary_io)

        for vertex in mesh['vertices']:
            self.write_vector3(vertex, binary_io)

        for texture_coord in mesh['texture_coordinates']:
            self.write_vector2(texture_coord, binary_io)

        for vlg in mesh['vertex_lighting_groups']:
            self.write_vertex_lighting_group(vlg, binary_io)

        if mesh['cull_type'] == 'BACKFACE_CULL':
            self.write_uint8(1, binary_io)
        else:
            self.write_uint8(0, binary_io)  # NO_CULL

        self.write_uint16(0, binary_io)  # end of node

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
        n_nodes = self.read_uint16(binary_io)

        for i in range(0, n_nodes):
            node = {}
            node_type = NodeType(self.read_uint16(binary_io))  # 0 = null/hardpoint, 1 = mesh, 3 = sprite, 11 = LOD control node, 12 = emitter
            node['type'] = node_type.name
            node['id'] = self.read_string(binary_io)
            node['parent'] = self.read_string(binary_io)  # None if root node

            node['local_transform'] = self.read_matrix34(binary_io)  # right, up, front, position
            node['data'] = self.read_typed_node(node_type, binary_io)
            nodes.append(node)

        return nodes

    def write_nodes(self, nodes: list, binary_io: BinaryIO):
        n_nodes = len(nodes)
        self.write_uint16(n_nodes, binary_io)

        for node in nodes:
            node_type_name: str = node['type']
            node_type: NodeType = NodeType[node_type_name]
            self.write_uint16(node_type.value, binary_io)
            self.write_string(node['id'], binary_io)
            self.write_string(node['parent'], binary_io)

            self.write_matrix34(node['local_transform'], binary_io)
            self.write_typed_node(node_type, node['data'], binary_io)

    def read_animation_transforms(self, binary_io: BinaryIO):
        n_channels = self.read_uint16(binary_io)
        channels = self.read_anim_channel_array(n_channels, binary_io)
        return channels

    def write_animation_transforms(self, channels: list, binary_io: BinaryIO):
        n_channels = len(channels)
        self.write_uint16(n_channels, binary_io)
        for channel in channels:
            self.write_anim_channel(channel, binary_io)

    def read_anim_tex_refs(self, binary_io: BinaryIO):
        """
        Animation references are a way of linking texture (flipbook) animations defined in the .spr files to the geometry of a .SOD mesh node.
        An example of their usage is the flipbook animation applied to the geometry for the various shield effects in Armada
        """
        n_references = self.read_uint16(binary_io)
        references = self.read_anim_reference_array(n_references, binary_io)
        return references

    def write_anim_tex_refs(self, references: list, binary_io: BinaryIO):
        n_references = len(references)
        self.write_uint16(n_references, binary_io)
        for reference in references:
            self.write_anim_reference(reference, binary_io)
