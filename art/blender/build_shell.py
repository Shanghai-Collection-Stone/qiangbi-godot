"""构建一枚竖立的 12 号霰弹并导出 ``art/models/shell.glb``。

同时渲染红色实弹近景到 ``art/source/previews/gun/shell_close.png``。
运行：blender -b --factory-startup --python art/blender/build_shell.py
"""

import math
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit


def hull_mesh(mat):
    """生成带柱面标签 UV 的塑料壳体和六瓣内凹星形折口。
    @keyword-en shell-hull, star-crimp
    @keyword-cn 霰弹塑料壳, 星形折口
    """
    segments = 12
    verts = []
    faces = []
    for y in (0.012, 0.067):
        for index in range(segments):
            angle = 2.0 * math.pi * index / segments
            verts.append(tuple(kit.g(0.016 * math.cos(angle), y, 0.016 * math.sin(angle))))
    for index in range(segments):
        nxt = (index + 1) % segments
        faces.append((index, nxt, segments + nxt, segments + index))
    inner_start = len(verts)
    for index in range(6):
        angle = 2.0 * math.pi * (index + 0.5) / 6
        verts.append(tuple(kit.g(0.0052 * math.cos(angle), 0.0645, 0.0052 * math.sin(angle))))
    center = len(verts)
    verts.append(tuple(kit.g(0, 0.064, 0)))
    for petal in range(6):
        outer_a = segments + petal * 2
        outer_b = segments + (petal * 2 + 1) % segments
        outer_c = segments + (petal * 2 + 2) % segments
        inner = inner_start + petal
        inner_next = inner_start + (petal + 1) % 6
        faces.extend(((outer_a, outer_b, inner), (outer_b, outer_c, inner), (outer_c, inner_next, inner),
                      (inner, inner_next, center)))
    mesh = bpy.data.meshes.new("Hull")
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    mesh.update()
    obj = bpy.data.objects.new("Hull", mesh)
    bpy.context.scene.collection.objects.link(obj)
    kit.assign(obj, mat)

    bm = bmesh.new()
    bm.from_mesh(mesh)
    uv = bm.loops.layers.uv.verify()
    for face_index, face in enumerate(bm.faces):
        if face_index >= segments:
            for loop in face.loops:
                loop[uv].uv = (0.02, 0.98)
            continue
        index = face_index
        u0 = index / segments
        u1 = (index + 1) / segments
        for loop, coords in zip(face.loops, ((u0, 0), (u1, 0), (u1, 1), (u0, 1))):
            loop[uv].uv = coords
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    return obj


def ordered_slots(obj, materials):
    """按 hull、brass 的稳定顺序去重并重建霰弹材质槽。
    @keyword-en shell-material-order, surface-slots
    @keyword-cn 霰弹材质排序, 表面槽位
    """
    old_names = [slot.material.name if slot.material else "" for slot in obj.material_slots]
    face_names = [old_names[poly.material_index] for poly in obj.data.polygons]
    obj.data.materials.clear()
    for mat in materials:
        obj.data.materials.append(mat)
    indices = {mat.name: index for index, mat in enumerate(materials)}
    for poly, name in zip(obj.data.polygons, face_names):
        poly.material_index = indices[name]
    return obj


def build_shell():
    """组合塑料壳、黄铜底座、宽底缘与底火为单一 Shell 网格。
    @keyword-en build-shell, twelve-gauge
    @keyword-cn 构建霰弹, 十二号口径
    """
    hull = kit.material("hull", (0.64, 0.025, 0.018), 0.5, 0.0, preview_texture="shell_hull.png")
    brass = kit.material("brass", (0.8, 0.6, 0.22), 0.35, 0.8)
    plastic = hull_mesh(hull)
    base_profile = [(0.0185, 0.0), (0.0185, 0.0025), (0.0172, 0.0034), (0.0172, 0.014)]
    base = kit.lathe("BrassBase", base_profile, (0, 0, 0), "y", brass, 12)
    primer = kit.cylinder("Primer", 0.004, 0.0007, (0, 0.00035, 0), "y", brass, 12)
    shell = kit.join([plastic, base, primer], "Shell")
    ordered_slots(shell, [hull, brass])
    kit.set_origin(shell, (0, 0, 0))
    kit.smooth(shell, 32)
    for polygon in shell.data.polygons:
        if min(shell.data.vertices[index].co.z for index in polygon.vertices) > 0.063:
            polygon.use_smooth = False
    return shell


def render_shell(shell):
    """渲染一张显示红色壳身、黄铜底座和折口的近景预览。
    @keyword-en shell-preview, close-up
    @keyword-cn 霰弹预览, 近景渲染
    """
    kit.render_preview("gun/shell_close.png", direction=(0.65, 1.20, 0.85),
                       target=(0, 0.033, 0), distance=0.20, fov=30,
                       resolution=(620, 620), objs=[shell])


def main():
    """重置场景、构建霰弹、导出 GLB、输出面数并渲染预览。
    @keyword-en export-shell, shell-pipeline
    @keyword-cn 导出霰弹, 霰弹流程
    """
    kit.reset_scene()
    shell = build_shell()
    print("SHELL_TRIANGLES", kit.triangle_count([shell]))
    kit.export_glb([shell], "shell.glb")
    render_shell(shell)


if __name__ == "__main__":
    main()
