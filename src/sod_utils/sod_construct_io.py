from abc import ABC

from construct import *


class BorgTextureAdapter(Adapter, ABC):
    def _decode(self, obj, context, path):
        if obj == '':
            return context._.texture + "_B"
        return obj

    def _encode(self, obj, context, path):
        if obj == context._.texture + "_B":
            return ''
        return obj


material: Struct = Struct(
    "name" / PascalString(Int16ul, "ascii"),
    "ambient_color" / NamedTuple("color", "r g b", Float32l[3]),
    "diffuse_color" / NamedTuple("color", "r g b", Float32l[3]),
    "specular_color" / NamedTuple("color", "r g b", Float32l[3]),
    "specular_shininess" / Float32l,
    "lighting_model" / Enum(Int8ul, constant=0, lambert=1, phong=2),
    "alpha_map_illumination" / If(this._root.version > 1.81, Int8ul)
)

mesh: Struct = Struct(
    "texture_material" / IfThenElse(this._root.version > 1.61, PascalString(Int16ul, "ascii"), Computed("default")),
    "bump_map" / IfThenElse(this._root.version > 1.9101, FocusedSeq("bm", Default(Int32ul, 0) * "unknown", "bm" / Int32ul), Computed(0)),
    "texture" / PascalString(Int16ul, "ascii"),
    If(this._root.version == 1.91, Default(Int16ul, 0)),
    "borgification" / If(this._root.version > 1.9101, Struct(
        Default(Int16ul, 0) * "unknown",
        Default(Int16ul, 0) * "unknown",
        "bump_map" / If(this._.bump_map == 2, FocusedSeq("bm", "bm" / PascalString(Int16ul, "ascii"), Int16ul, Int16ul)),
        "texture" / BorgTextureAdapter(PascalString(Int16ul, "ascii")),
        Default(Int16ul, 0) * "unknown",
    )),
    "vertex_count" / Rebuild(Int16ul, len_(this.vertices)),
    "texture_coord_count" / Rebuild(Int16ul, len_(this.texture_coordinates)),
    "vlg_count" / Rebuild(Int16ul, len_(this.vertex_lighting_groups)),
    "vertices" / NamedTuple("vector3", "x y z", Float32l[3])[this.vertex_count],
    "texture_coordinates" / NamedTuple("vector2", "u v", Float32l[2])[this.texture_coord_count],
    "vertex_lighting_groups" / Struct(
        "face_count" / Rebuild(Int16ul, len_(this.faces)),
        "lighting_material" / PascalString(Int16ul, "ascii"),
        "faces" / NamedTuple("face_vertex", "idx_vertex idx_tex_cord", Int16ul[2])[3][this.face_count]
    )[this.vlg_count],
    "cull_type" / Enum(Int8ul, no_cull=0, backface_cull=1),
    Const(0, Int16ul) * "end of mesh node, 0 is required",
)

node: Struct = Struct(
    "type" / Enum(Int16ul, null_or_hardpoint=0, mesh=1, sprite=3, lod_control=11, emitter=12),
    "id" / PascalString(Int16ul, "ascii"),
    "parent_id" / PascalString(Int16ul, "ascii"),
    "local_transform" / NamedTuple("matrix34", "right up front position", NamedTuple("vector3", "x y z", Float32l[3])[4]),
    "data" / Switch(this.type,
                    {
                        "null_or_hardpoint": Pass,
                        "mesh": mesh,
                        "sprite": Pass,
                        "lod_control": Pass,
                        "emitter": Struct("emitter_id" / PascalString(Int16ul, "ascii"))
                    })
)

animation: Struct = Struct(
    "transforms" / PrefixedArray(Int16ul, Struct(
        "node_ref" / PascalString(Int16ul, "ascii"),
        "keyframe_count" / Rebuild(Int16ul, len_(this.data)),
        "period" / Float32l,
        "type" / Enum(Int16ul, position=0, scale=5),
        "data" / Switch(this.type,
                        {
                            "position": Array(this.keyframe_count, NamedTuple("matrix34", "right up front position", NamedTuple("vector3", "x y z", Float32l[3])[4])),
                            "scale": Float32l[this.keyframe_count]
                        }),
    )),
    "texture_references" / PrefixedArray(Int16ul, Struct(
        "type" / Const(4, Int8ul) * "has to be 4",
        "node_ref" / PascalString(Int16ul, "ascii"),
        "anim" / PascalString(Int16ul, "ascii"),
        "playback_offset" / Float32l
    ))
)


class VersionNumberValidator(Validator, ABC):
    def _validate(self, obj, context, path):
        return 1.6 <= obj <= 1.93


sod_format: Struct = Struct(
    "magic" / Const(b'Storm3D_SW'),
    "version" / VersionNumberValidator(Float32l),
    "data" / Struct(
        "legacy_data" / If(this._root.version <= 1.81, PrefixedArray(Int16ul, Struct(
            "id1" / PascalString(Int16ul, "ascii"),
            "id2" / PascalString(Int16ul, "ascii"),
            "unknown" / Int8ul[7]
        ))),
        "materials" / PrefixedArray(Int16ul, material),
        "nodes" / PrefixedArray(Int16ul, node),
        "animation" / animation
    )
)

if __name__ == '__main__':
    # filename = 'fbattle'
    # filename = '8472_mother'
    filename = 'fconst'
    file_path = f'D:\\Program Files (x86)\\Activision\\Star Trek Armada II\\SOD\\{filename}.sod'

    with open(file_path, 'rb') as binary_io:
        data: Container = sod_format.parse_stream(binary_io).get("data")

    nodes: ListContainer = data.get("nodes")
    if nodes:
        meshes: list = []
        for node in nodes:
            type: EnumIntegerString = node.type
            if type.lower() == "mesh":
                meshes.append(node)

        print()
        print("Mesh Count:", len(meshes))
        print("--------------------------------------------------")
        for mesh_node in meshes:
            print("id:", mesh_node.get("id"))
            print("parent:", mesh_node.get("parent_id"))
            print("vertices:", mesh_node.get("data").get("vertex_count"))
            print("--------------------------------------------------")

# import json
# with open(f'../../dump/{filename}_99.json', 'w') as outfile:
#     json.dump(data, outfile)
