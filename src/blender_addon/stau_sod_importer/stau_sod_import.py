# noinspection PyUnresolvedReferences
import bpy
# noinspection PyUnresolvedReferences
import bmesh
# noinspection PyUnresolvedReferences
from bpy.props import StringProperty, BoolProperty, EnumProperty
# noinspection PyUnresolvedReferences
from bpy.types import Operator
# noinspection PyUnresolvedReferences
from bpy_extras.io_utils import ImportHelper  # ImportHelper is a helper class, defines filename and invoke() function which calls the file selector.
from .stau_sod_io import *
from .stau_utils import *
import numpy as np
import mathutils

class ImportSodData(Operator, ImportHelper):
    """Import SOD model files from Star Trek Armada I & II"""
    bl_idname = "import_file.sod_data"
    bl_label = "Import SOD Data"

    # ImportHelper mixin class uses this
    filename_ext = ".sod"

    filter_glob: StringProperty(
        default="*.sod",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.

    # TODO: add this somewhere else (can't open file selector inside file selector)
    texture_path: StringProperty(
        name="Texture Folder",
        description="Folder containing the textures for the sod model",
        subtype='DIR_PATH'
    )

    def execute(self, context):
        return read_sod_data(context, self.filepath, self.texture_path)


def read_sod_data(context, filepath, texture_path):
    print("reading sod data...")

    print("context", context)
    print("texture_folder", texture_path)

    sod_parser = SodIO()
    sod: Sod = sod_parser.read_file(filepath)

    # TODO: get texture folder path
    texture_folder = 'D:\\Program Files (x86)\\Activision\\Star Trek Armada II\\Textures\\RGB'

    print("adding model to scene...")
    sod_importer = SodImporter(sod, texture_folder)
    sod_importer.build_scene_tree()
    set_view3d_shading('MATERIAL')  # MATERIAL, RENDERED

    return {'FINISHED'}


class SodImporter:
    materials = {}

    def __init__(self, sod: Sod, texture_folder: str):
        self.texture_folder = texture_folder

        if sod.materials:
            mat_id = 0
            for material in sod.materials:
                material['material_id'] = mat_id
                material['diffuse_color'].append(1)  # add alpha
                self.materials[material['name']] = material
                mat_id += 1

        self.object_name = sod.name.lower().replace('.sod', '')

        # extract nodes with mesh
        # works with flat hierarchy (Armada II only for now) //TODO: discover all nodes #
        mesh_nodes = list(filter(lambda x: x['type'] == 'MESH', sod.nodes))
        n_meshes = len(mesh_nodes)
        print(f'found {n_meshes} meshes')

        if n_meshes == 0:
            raise print('Warning: no mesh was found')

        # # get mesh with highest fidelity
        # self.meshdata = mesh_nodes[0]
        # if n_meshes > 1:
        #     curr_lod = self.getLodFrom(self.meshdata)
        #     print('curr_lod', curr_lod)

        #     for i in range(1, len(mesh_nodes)):  # skip fist index
        #         next_lod = self.getLodFrom(mesh_nodes[i])
        #         print('next_lod', next_lod)
        #         if next_lod < curr_lod:
        #             self.meshdata = mesh_nodes[i]
        #             curr_lod = next_lod

        #     print('picked mesh with lod: ', curr_lod)

        self.nodes = sod.nodes

    def get_lod_from(self, mesh_node):
        lod_from_parent = self.parse_lod_level(mesh_node['parent'])
        lod_from_node = self.parse_lod_level(mesh_node['id'])
        return lod_from_node if lod_from_node < lod_from_parent else lod_from_parent

    def parse_lod_level(self, string):
        if 'lod' in string:
            lod = string[string.find('lod') + 3:].replace('_', '')
            if lod is '':
                return 0
            try:
                return int(lod)
            except ValueError as e:
                return 99
        else:
            # raise Exception('InvalidNodeTypeError')
            return 99

    def create_mesh_object(self, parent_transform, mesh_node):

        cull = mesh_node['data']['cull_type']
        blend_mode = mesh_node['data']['texture_material']

        lod = self.get_lod_from(mesh_node)
        suffix = '.tga' if lod in [0, 1, 99] else '_' + str(lod) + '.tga'

        tex = self.texture_folder + "\\" + mesh_node['data']['texture'] + suffix
        if 'borgification' in mesh_node['data']:
            tex_borg = self.texture_folder + "\\" + mesh_node['data']['borgification']['texture'] + suffix
        else:
            tex_borg = None

        vertices = mesh_node['data']['vertices']
        uvs = mesh_node['data']['texture_coordinates']

        # vertex faces
        vertex_lighting_groups = mesh_node['data']['vertex_lighting_groups']
        faces = []
        tex_indices = []

        for vlg in vertex_lighting_groups:

            vertex_faces = vlg['faces']
            l_material_name = vlg['lighting_material']

            material = self.materials[l_material_name]
            min_index = len(faces)
            material['min_face_index'] = min_index
            material['max_face_index'] = min_index + len(vertex_faces)

            # faces_, tex_indices_ = self.__split_into_vertex_and_texture_indices(vertex_faces)
            # faces.extend(faces_)
            # tex_indices.extend(tex_indices_)

            for vertex_face in vertex_faces:
                faces_ = []
                tex_indices_ = []
                for f_tx_i in vertex_face:
                    faces_.append(f_tx_i[0])
                    tex_indices_.append(f_tx_i[1])
                faces.append(faces_)
                tex_indices.append(tex_indices_)

            # mesh
            # mesh = self.createMesh(self.object_name, vertices, faces)

            # # uvs
            # self.createUVMap(mesh, self.object_name + '_uvmap', uvs, faces, tex_indicies)

            # material
            # color = material['diffuse_color']
            # color.append(1)  # add alpha
            # mat = self.createMaterial(self.object_name + '_mat_' + l_material_name, rgba=color, texture=tex)
            # mesh.materials.append(mat)

        # mesh
        mesh, obj = self.create_mesh(mesh_node['id'], vertices, faces)

        # local transforms
        pos_xyz = mesh_node['local_transform'][3]
        # obj.location = (pos_xyz[0], pos_xyz[2], pos_xyz[1])  # swap z and y
        obj.location = (pos_xyz[0], pos_xyz[1], pos_xyz[2])

        m1 = self.create_transformation_matrix(mesh_node['local_transform'])

        if parent_transform:
            m2 = self.create_transformation_matrix(parent_transform)
            m1 = m1.__matmul__(m2)

        obj.rotation_euler = m1.to_euler()

        # uvs
        self.create_uv_map(mesh, mesh_node['id'] + '_uvmap', uvs, faces, tex_indices)

        # create material slots
        # for i in range(len(self.materials)):
        #     mesh.materials.append(None)

        # materials
        for material_data in self.materials.values():
            color = material_data['diffuse_color']
            material = self.create_material(mesh_node['id'] + '_mat_' + material_data['name'], rgba=color, texture=tex)
            # mesh.materials[material['material_id']] = mat
            mesh.materials.append(material)

        # append extra borg material
        if tex_borg:
            for material_data in self.materials.values():
                color = material_data['diffuse_color']
                mat_base_borgified = self.create_material(mesh_node['id'] + '_mat_' + material_data['name'] + '_borgified', rgba=color, texture=tex_borg)
                mesh.materials.append(mat_base_borgified)

        return obj

    def __split_into_vertex_and_texture_indices(self, vertex_faces):
        faces = []
        tex_indices = []
        for vertex_face in vertex_faces:
            face = []
            tex_index = []
            for i in vertex_face:
                face.append(i[0])
                tex_index.append(i[1])
            faces.append(face)
            tex_indices.append(tex_index)
        return faces, tex_indices

    def get_material_id_from_face_index(self, face_index):
        for material in self.materials.values():
            if 'min_face_index' in material:
                if material['min_face_index'] <= face_index < material['max_face_index']:
                    return material['material_id']
        return 0

    def get_uv_from_face_and_vertex_index(self, faces, face_index, tex_indicies, vertex_index, uvs):
        i = faces[face_index].index(vertex_index)
        tex_index = tex_indicies[face_index][i]
        return uvs[tex_index]

    def get_image(self, file_name):
        for img in bpy.data.images:  # use cached image if possible
            if img.filepath == file_name:
                return img
        return bpy.data.images.load(file_name)

    def create_material(self, mat_name, rgba=None, texture=None):
        material = bpy.data.materials.new(mat_name)
        material.use_nodes = True
        material.node_tree.nodes.remove(material.node_tree.nodes['Principled BSDF'])
        material.blend_method = 'OPAQUE'  # default -> OPAQUE
        material.use_backface_culling = False  # default -> False

        material_output = material.node_tree.nodes.get('Material Output')
        location = material_output.location

        offset = 200
        if rgba and texture is None:
            diffuse = material.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
            diffuse.location = (location[0] - offset, location[1])
            diffuse.inputs['Color'].default_value = rgba
            material.node_tree.links.new(material_output.inputs['Surface'], diffuse.outputs['BSDF'])
            return material

        if texture:
            tex_image = material.node_tree.nodes.new('ShaderNodeTexImage')
            tex_image.location = (location[0] - offset * 4 - 50, location[1])
            tex_image.image = self.get_image(texture)
            tex_image.interpolation = 'Closest'

            # glowing stuff
            emission = material.node_tree.nodes.new('ShaderNodeEmission')
            emission.location = (location[0] - offset * 2, location[1] + 50)
            material.node_tree.links.new(emission.inputs['Color'], tex_image.outputs['Color'])
            material.node_tree.links.new(emission.inputs['Strength'], tex_image.outputs['Alpha'])

            add_shader = material.node_tree.nodes.new('ShaderNodeAddShader')
            add_shader.location = (location[0] - offset, location[1])
            material.node_tree.links.new(material_output.inputs['Surface'], add_shader.outputs['Shader'])
            material.node_tree.links.new(add_shader.inputs[0], emission.outputs['Emission'])

            if rgba is None:
                material.node_tree.links.new(add_shader.inputs[1], tex_image.outputs['Color'])
            else:
                mix_rgb = material.node_tree.nodes.new('ShaderNodeMixRGB')
                mix_rgb.location = (location[0] - offset * 3 + 50, location[1] - 100)
                mix_rgb.blend_type = 'OVERLAY'
                mix_rgb.inputs['Fac'].default_value = 1
                mix_rgb.inputs['Color2'].default_value = rgba

                diffuse = material.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
                diffuse.location = (location[0] - offset * 2, location[1] - 100)

                material.node_tree.links.new(mix_rgb.inputs['Color1'], tex_image.outputs['Color'])
                material.node_tree.links.new(diffuse.inputs['Color'], mix_rgb.outputs['Color'])
                material.node_tree.links.new(add_shader.inputs[1], diffuse.outputs['BSDF'])

        return material

    def create_uv_map(self, mesh, name, uvs, faces, tex_indices):
        mesh.uv_layers.new(name=name)
        bm = bmesh.new()
        bm.from_mesh(mesh)

        uv_layer = bm.loops.layers.uv[0]

        for face in bm.faces:
            face.material_index = self.get_material_id_from_face_index(face.index)

            for loop in face.loops:
                uv = self.get_uv_from_face_and_vertex_index(faces, face.index, tex_indices, loop.vert.index, uvs)
                loop[uv_layer].uv = (uv[0], 1 - uv[1])

        bm.to_mesh(mesh)

    def create_mesh(self, name, vertices, faces):
        mesh = bpy.data.meshes.new("MESH_" + name)
        obj = bpy.data.objects.new(mesh.name, mesh)

        bpy.context.scene.collection.objects.link(obj)  # add to scene root
        bpy.context.view_layer.objects.active = obj  # mark as active

        mesh.from_pydata(vertices, [], faces)  # vertices, edges, faces
        return mesh, obj

    def create_empty_object(self, name, parent_transform, local_transform, display_type, display_size):
        obj = bpy.data.objects.new(name, None)
        bpy.context.scene.collection.objects.link(obj)

        obj.empty_display_size = display_size
        obj.empty_display_type = display_type  # PLAIN_AXES, ARROWS, CUBE, SPHERE, CIRCLE, SINGLE_ARROW, CONE, IMAGE
        obj.show_name = True

        # obj.location = (local_transform[3][0], local_transform[3][2], local_transform[3][1])  # swap z and y
        obj.location = (local_transform[3][0], local_transform[3][1], local_transform[3][2])

        m1 = self.create_transformation_matrix(local_transform)

        if parent_transform:
            m2 = self.create_transformation_matrix(parent_transform)
            m1 = m1.__matmul__(m2)

        obj.rotation_euler = m1.to_euler()

        return obj

    def create_transformation_matrix(self, local_transform) -> mathutils.Matrix:
        vec = np.array(local_transform[0:3])
        for i in range(3):
            vec[i, 0] *= -1
            y = vec[i, 1]
            vec[i, 1] = vec[i, 2]
            vec[i, 2] = y
        return mathutils.Matrix(vec)

    def build_scene_tree(self):
        obj_tree = {}
        scene_root_node = None
        parent_transform = None

        nodes_by_parent = {}
        for node in self.nodes:

            if node['parent'] == '':  # Scene Root
                scene_root_node = node['id']
                parent_transform = node['local_transform']
                node_obj = self.create_empty_object(node['type'] + "_" + node['id'], None, node['local_transform'], 'CUBE', 30)
                obj_tree[node['id']] = node_obj
                continue

            if node['parent'] not in nodes_by_parent.keys():
                nodes_by_parent[node['parent']] = []

            nodes_by_parent[node['parent']].append(node)

        for node in nodes_by_parent[scene_root_node]:
            node_obj = self.create_empty_object(node['type'] + "_" + node['id'], parent_transform, node['local_transform'], 'PLAIN_AXES', 35)
            node_obj.parent = obj_tree[scene_root_node]
            obj_tree[node['id']] = node_obj

            if node['id'] in nodes_by_parent.keys():
                self.build_hierarchy(node, nodes_by_parent, obj_tree)

    def build_hierarchy(self, parent_node, nodes_by_parent, obj_tree):
        for node in nodes_by_parent[parent_node['id']]:
            child_obj = None
            if node['type'] == 'MESH':
                child_obj = self.create_mesh_object(parent_node['local_transform'], node)
            else:
                child_obj = self.create_empty_object(node['type'] + "_" + node['id'], parent_node['local_transform'], node['local_transform'], 'CUBE', 0.25)

            child_obj.parent = obj_tree[parent_node['id']]
            obj_tree[node['id']] = child_obj

            if node['id'] in nodes_by_parent.keys():
                self.build_hierarchy(node, nodes_by_parent, obj_tree)
