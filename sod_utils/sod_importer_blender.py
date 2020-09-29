#!/usr/bin/env python3

# SOD Importer for Blender 2.8x
__author__ = 'Elenterius'
__version__ = '0.3'

import sys
# sys.path.append('"D:\\Program Files\\Blender Foundation\\Blender 2.81\\2.81\\scripts\\modules"')
import bmesh
import bpy

sys.path.append('E:\\PycharmProjects\\stau\\sod_utils')
from sod_utils.sod_io import SodIO, Sod

texture_path = 'D:\\Program Files (x86)\\Activision\\Star Trek Armada II\\Textures\\RGB'
file_path = 'D:\\Program Files (x86)\\Activision\\Star Trek Armada II\\SOD\\Fbattle.sod'
sod_reader = SodIO()
sod = sod_reader.read_file(file_path)


def set_view3d_shading(mode="SOLID", screens=[]):
    screens = screens if screens else [bpy.context.screen]
    for s in screens:
        for spc in s.areas:
            if spc.type == "VIEW_3D":
                spc.spaces[0].shading.type = mode
                break


class SodImporter:
    materials = {}

    def __init__(self, sod: Sod):
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

    def create_mesh_object(self, mesh_node):

        cull = mesh_node['data']['cull_type']
        blend_mode = mesh_node['data']['texture_material']

        lod = self.get_lod_from(mesh_node)
        suffix = '.tga' if lod in [0, 1, 99] else '_' + str(lod) + '.tga'

        tex = mesh_node['data']['texture'] + suffix
        tex_borg = mesh_node['data']['borgification']['texture'] + suffix

        vertices = mesh_node['data']['vertices']
        uvs = mesh_node['data']['texture_coordinates']

        # vertex faces
        vert_lgroups = mesh_node['data']['vertex_lighting_groups']

        faces = []
        tex_indices = []

        for vert_lgroup in vert_lgroups:

            vert_faces = vert_lgroup['faces']

            l_material_name = vert_lgroup['lighting_material']

            material = self.materials[l_material_name]
            min_index = len(faces)
            material['min_face_index'] = min_index
            material['max_face_index'] = min_index + len(vert_faces)

            for vface in vert_faces:
                f = []
                t = []
                for i in vface:
                    f.append(i[0])
                    t.append(i[1])
                faces.append(f)
                tex_indices.append(t)

            # # mesh
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

        pos_xyz = mesh_node['local_transform'][3]
        obj.location = [pos_xyz[0], pos_xyz[2], pos_xyz[1]]

        # uvs
        self.create_uv_map(mesh, mesh_node['id'] + '_uvmap', uvs, faces, tex_indices)

        # create material slots
        for i in range(len(self.materials)):
            mesh.__materials.append(None)

        # materials
        for material in self.materials.values():
            color = material['diffuse_color']
            mat = self.create_material(mesh_node['id'] + '_mat_' + material['name'], rgba=color, texture=tex)
            mesh.__materials[material['material_id']] = mat

        # append extra borg material
        for material in self.materials.values():
            color = material['diffuse_color']
            mat_base_borgified = self.create_material(mesh_node['id'] + '_mat_' + material['name'] + '_borgified', rgba=color, texture=tex_borg)
            mesh.__materials.append(mat_base_borgified)

        return obj

    def __split_into_vertex_and_texture_indicies(self, vertex_faces):
        faces = []
        tex_indices = []
        for vface in vertex_faces:
            f = []
            t = []
            for i in vface:
                f.append(i[0])
                t.append(i[1])
            faces.append(f)
            tex_indices.append(t)
        return faces, tex_indices

    def get_material_id_from_face_index(self, face_index):
        for material in self.materials.values():
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
        mat = bpy.data.__materials.new(name=mat_name)
        mat.use_nodes = True
        mat.node_tree._nodes.remove(mat.node_tree._nodes['Principled BSDF'])
        mat.blend_method = 'OPAQUE'  # default -> OPAQUE
        mat.use_backface_culling = False  # default -> False

        material_output = mat.node_tree._nodes.get('Material Output')
        location = material_output.location

        offset = 200
        if rgba and texture is None:
            diffuse = mat.node_tree._nodes.new('ShaderNodeBsdfDiffuse')
            diffuse.location = (location[0] - offset, location[1])
            diffuse.inputs['Color'].default_value = rgba
            mat.node_tree.links.new(material_output.inputs['Surface'], diffuse.outputs['BSDF'])
            return mat

        if texture:
            tex_image = mat.node_tree._nodes.new('ShaderNodeTexImage')
            tex_image.location = (location[0] - offset * 4 - 50, location[1])
            tex_image.image = self.get_image(texture)
            tex_image.interpolation = 'Closest'

            # glowing stuff
            emission = mat.node_tree._nodes.new('ShaderNodeEmission')
            emission.location = (location[0] - offset * 2, location[1] + 50)
            mat.node_tree.links.new(emission.inputs['Color'], tex_image.outputs['Color'])
            mat.node_tree.links.new(emission.inputs['Strength'], tex_image.outputs['Alpha'])

            add_shader = mat.node_tree._nodes.new('ShaderNodeAddShader')
            add_shader.location = (location[0] - offset, location[1])
            mat.node_tree.links.new(material_output.inputs['Surface'], add_shader.outputs['Shader'])
            mat.node_tree.links.new(add_shader.inputs[0], emission.outputs['Emission'])

            if rgba is None:
                mat.node_tree.links.new(add_shader.inputs[1], tex_image.outputs['Color'])
            else:
                mix_rgb = mat.node_tree._nodes.new('ShaderNodeMixRGB')
                mix_rgb.location = (location[0] - offset * 3 + 50, location[1] - 100)
                mix_rgb.blend_type = 'OVERLAY'
                mix_rgb.inputs['Fac'].default_value = 1
                mix_rgb.inputs['Color2'].default_value = rgba

                diffuse = mat.node_tree._nodes.new('ShaderNodeBsdfDiffuse')
                diffuse.location = (location[0] - offset * 2, location[1] - 100)

                mat.node_tree.links.new(mix_rgb.inputs['Color1'], tex_image.outputs['Color'])
                mat.node_tree.links.new(diffuse.inputs['Color'], mix_rgb.outputs['Color'])
                mat.node_tree.links.new(add_shader.inputs[1], diffuse.outputs['BSDF'])

        return mat

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
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(mesh.name, mesh)

        bpy.context.scene.collection.objects.link(obj)  # add to scene root
        bpy.context.view_layer.objects.active = obj  # mark as active

        mesh.from_pydata(vertices, [], faces)  # vertices, edges, faces
        return mesh, obj

    def create_empty_object(self, name, pos_xyz, display_type, display_size):
        obj = bpy.data.objects.new(name, None)
        bpy.context.scene.collection.objects.link(obj)

        obj.empty_display_size = display_size
        obj.empty_display_type = display_type  # PLAIN_AXES, ARROWS, CUBE, SPHERE, CIRCLE, SINGLE_ARROW, CONE, IMAGE
        obj.show_name = True

        obj.location = [pos_xyz[0], pos_xyz[2], pos_xyz[1]]
        return obj

    def build_scene_tree(self):
        obj_tree = {}
        scene_root_node = None

        cached_nodes_by_parent = {}
        for node in self.nodes:

            if node['parent'] == '':  # Scene Root
                scene_root_node = node['id']
                node_obj = self.create_empty_object(node['id'], node['local_transform'][3], 'CUBE', 30)
                obj_tree[node['id']] = node_obj
                continue

            if node['parent'] not in cached_nodes_by_parent.keys():
                cached_nodes_by_parent[node['parent']] = []

            cached_nodes_by_parent[node['parent']].append(node)

        for node in cached_nodes_by_parent[scene_root_node]:
            node_obj = self.create_empty_object(node['id'], node['local_transform'][3], 'PLAIN_AXES', 35)
            node_obj.parent = obj_tree[scene_root_node]
            obj_tree[node['id']] = node_obj

            if node['id'] in cached_nodes_by_parent.keys():
                self.build_hierarchy(node['id'], cached_nodes_by_parent, obj_tree)

    def build_hierarchy(self, parent_id, nodes_by_parent, obj_tree):
        for node in nodes_by_parent[parent_id]:
            child_obj = None
            if node['type'] == 'MESH':
                child_obj = self.create_mesh_object(node)
            else:
                child_obj = self.create_empty_object(node['id'], node['local_transform'][3], 'CUBE', 0.25)

            child_obj.parent = obj_tree[parent_id]
            obj_tree[node['id']] = child_obj

            if node['id'] in nodes_by_parent.keys():
                self.build_hierarchy(node['id'], nodes_by_parent, obj_tree)


importer = SodImporter(sod)
importer.build_scene_tree()
set_view3d_shading('MATERIAL')  # MATERIAL, RENDERED
