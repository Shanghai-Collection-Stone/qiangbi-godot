"""为《枪毙·最后一发》生成八件桌面道具。

输出 ``art/models/items/*.glb`` 与 ``art/source/previews/items/*.png``。
在仓库根目录运行：
``blender -b --factory-startup --python art/blender/build_items.py``。
"""

import math
import random
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bmesh
import bpy
from mathutils import Vector

import kit


def make_materials():
    """创建八件道具使用的命名材质。
    @keyword-en item-materials, material-keys
    @keyword-cn 道具材质, 材质键
    """
    return {
        "metal_bright": kit.material("metal_bright", (0.8, 0.8, 0.82), 0.25, 0.9),
        "metal": kit.material("metal", (0.3, 0.31, 0.33), 0.4, 0.8, preview_texture="metal.png"),
        "metal_dark": kit.material("metal_dark", (0.15, 0.15, 0.17), 0.5, 0.7, preview_texture="metal.png"),
        "lens": kit.material("lens", (0.5, 0.75, 0.85), 0.05, 0.0),
        "plastic_black": kit.material("plastic_black", (0.03, 0.03, 0.035), 0.5, 0.0),
        "cigs": kit.material("cigs", (0.8, 0.75, 0.65), 0.8, 0.0, preview_texture="cigs.png"),
        "paper": kit.material("paper", (0.9, 0.9, 0.86), 0.9, 0.0),
        "filter": kit.material("filter", (0.75, 0.45, 0.18), 0.9, 0.0),
        "beer": kit.material("beer", (0.7, 0.5, 0.15), 0.35, 0.6, preview_texture="beer.png"),
        "rust": kit.material("rust", (0.35, 0.17, 0.08), 0.9, 0.3, preview_texture="rust.png"),
        "red_paint": kit.material("red_paint", (0.45, 0.05, 0.03), 0.6, 0.0),
        "brass": kit.material("brass", (0.8, 0.6, 0.22), 0.35, 0.8),
        "phone": kit.material("phone", (0.05, 0.05, 0.05), 0.5, 0.0, preview_texture="phone.png"),
        "inverter": kit.material("inverter", (0.15, 0.12, 0.18), 0.5, 0.4, preview_texture="inverter.png"),
        "inverter_glow": kit.material("inverter_glow", (0.6, 0.3, 0.9), 0.25, 0.0, emission=(0.6, 0.3, 0.9)),
        "pills": kit.material("pills", (0.85, 0.83, 0.78), 0.8, 0.0, preview_texture="pills.png"),
        "amber": kit.material("amber", (0.45, 0.18, 0.03), 0.25, 0.0),
        "cap_white": kit.material("cap_white", (0.85, 0.85, 0.82), 0.6, 0.0),
    }


def torus(name, major, minor, center, mat, major_segments=16, minor_segments=6, rot=(0, 0, 0)):
    """创建以 Godot y 为法线的低模圆环。
    @keyword-en torus-ring, low-poly-ring
    @keyword-cn 圆环, 低模环
    """
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major, minor_radius=minor,
        major_segments=major_segments, minor_segments=minor_segments,
        location=kit.g(center), rotation=kit._godot_euler(rot),
    )
    obj = bpy.context.object
    obj.name = name
    kit.assign(obj, mat)
    return obj


def polygon_prism(name, outline, bottom, top, mat):
    """把 Godot xz 平面轮廓挤成指定高度的薄实体。
    @keyword-en polygon-prism, custom-outline
    @keyword-cn 多边形棱柱, 自定义轮廓
    """
    n = len(outline)
    verts = [tuple(kit.g(x, bottom, z)) for x, z in outline]
    verts += [tuple(kit.g(x, top, z)) for x, z in outline]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    kit.assign(obj, mat)
    return obj


def label_quad(name, width, length, y, center, mat, top_toward_negative_z=True):
    """创建整张竖版标签铺满的朝上矩形面。
    @keyword-en label-quad, full-image-uv
    @keyword-cn 标签面, 整图UV
    """
    cx, cz = center
    x0, x1 = cx - width / 2, cx + width / 2
    z0, z1 = cz - length / 2, cz + length / 2
    verts = [tuple(kit.g(x0, y, z0)), tuple(kit.g(x1, y, z0)),
             tuple(kit.g(x1, y, z1)), tuple(kit.g(x0, y, z1))]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], [(0, 1, 2, 3)])
    uv = mesh.uv_layers.new(name="UVMap")
    coords = ((0, 1), (1, 1), (1, 0), (0, 0)) if top_toward_negative_z else ((0, 0), (1, 0), (1, 1), (0, 1))
    for loop, coord in zip(mesh.polygons[0].loop_indices, coords):
        uv.data[loop].uv = coord
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    kit.assign(obj, mat)
    return obj


def label_disk(name, radius, y, center, mat, segments=20):
    """创建中心映射到 UV 中心、外缘映射到半径 0.5 的圆形标签盘。
    @keyword-en label-disk, radial-uv
    @keyword-cn 圆盘标签, 径向UV
    """
    cx, cz = center
    verts = [tuple(kit.g(cx, y, cz))]
    for i in range(segments):
        a = math.tau * i / segments
        verts.append(tuple(kit.g(cx + radius * math.cos(a), y, cz + radius * math.sin(a))))
    faces = [(0, i + 1, (i + 1) % segments + 1) for i in range(segments)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    uv = mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            if vertex_index == 0:
                coord = (0.5, 0.5)
            else:
                a = math.tau * (vertex_index - 1) / segments
                coord = (0.5 + 0.5 * math.cos(a), 0.5 + 0.5 * math.sin(a))
            uv.data[loop_index].uv = coord
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    kit.assign(obj, mat)
    return obj


def finish_item(parts, item_id):
    """合并部件、清理材质槽并把原点设到底面中心。
    @keyword-en finish-item, single-root
    @keyword-cn 完成道具, 单根节点
    """
    obj = kit.join(parts, item_id)
    min_height = min(vertex.co.z for vertex in obj.data.vertices)
    for vertex in obj.data.vertices:
        vertex.co.z -= min_height
    kit.set_origin(obj, (0, 0, 0))
    return obj


def build_magnifier(m):
    """构建平放的镀铬放大镜。
    @keyword-en build-magnifier, tabletop-prop
    @keyword-cn 构建放大镜, 桌面道具
    """
    parts = []
    center = (-0.038, 0.006, -0.012)
    parts.append(torus("frame", 0.039, 0.0045, center, m["metal_bright"], 20, 6))
    parts.append(kit.sphere("lens", 0.038, center, m["lens"], 20, 6, scale=(1, 0.09, 1)))
    handle_start = (0.001, 0.007, 0.011)
    handle_end = (0.078, 0.009, 0.054)
    direction = Vector(handle_end) - Vector(handle_start)
    midpoint = (Vector(handle_end) + Vector(handle_start)) / 2
    parts.append(kit.cylinder("handle", 0.009, direction.length, midpoint, direction, m["plastic_black"], 12))
    parts.append(kit.cylinder("ferrule", 0.0105, 0.018, (0.010, 0.007, 0.018), direction, m["metal_bright"], 12))
    return finish_item(parts, "magnifier")


def build_cigarette(m):
    """构建打开、凹皱并露出香烟的烟盒。
    @keyword-en build-cigarette, open-cigarette-pack
    @keyword-cn 构建香烟, 打开烟盒
    """
    parts = []
    parts.append(kit.box("pack", (0.065, 0.025, 0.069), (-0.018, 0.0125, 0.009), m["cigs"], rot=(0, 0.02, -0.025), bevel=0.002))
    parts.append(label_quad("pack_label", 0.060, 0.064, 0.0262, (-0.018, 0.009), m["cigs"]))
    parts.append(kit.box("lid", (0.064, 0.007, 0.031), (-0.018, 0.035, -0.039), m["cigs"], rot=(0.60, 0, 0), bevel=0.0015))
    parts.append(kit.box("foil", (0.056, 0.006, 0.018), (-0.018, 0.029, -0.019), m["paper"], rot=(0.15, 0, 0), bevel=0.001))
    for i, x in enumerate((-0.033, -0.018, -0.003)):
        parts.append(kit.cylinder(f"filter_{i}", 0.0043, 0.023, (x, 0.038, -0.011), "z", m["filter"], 10))
    parts.append(kit.cylinder("loose_paper", 0.0042, 0.037, (0.044, 0.005, 0.010), (0.22, 0, 0.98), m["paper"], 10))
    parts.append(kit.cylinder("loose_filter", 0.0045, 0.014, (0.050, 0.005, 0.034), (0.22, 0, 0.98), m["filter"], 10))
    return finish_item(parts, "cigarette")


def build_beer(m):
    """构建带凹痕、卷边和拉环的立式啤酒罐。
    @keyword-en build-beer, dented-can
    @keyword-cn 构建啤酒, 凹陷罐
    """
    profile = [(0.028, 0.0), (0.032, 0.004), (0.033, 0.010), (0.033, 0.104),
               (0.030, 0.114), (0.028, 0.119), (0.028, 0.123)]
    body = kit.lathe("can_body", profile, (0, 0, 0), "y", m["beer"], 20)
    # 两处软凹痕：只收缩局部环向顶点，保留清楚的罐体轮廓。
    for vert in body.data.vertices:
        x, by, h = vert.co
        angle = math.atan2(by, x)
        if 0.035 < h < 0.092 and (abs(angle - 0.5) < 0.42 or abs(angle + 2.1) < 0.28):
            factor = 0.80 + 0.18 * abs((h - 0.064) / 0.029)
            vert.co.x *= factor
            vert.co.y *= factor
    parts = [body]
    parts.append(torus("bottom_rim", 0.029, 0.002, (0, 0.003, 0), m["metal_bright"], 20, 4))
    parts.append(torus("top_rim", 0.0278, 0.0022, (0, 0.123, 0), m["metal_bright"], 20, 4))
    parts.append(kit.cylinder("top", 0.0275, 0.002, (0, 0.122, 0), "y", m["metal_bright"], 20))
    parts.append(torus("pull_ring", 0.009, 0.002, (0.003, 0.124, 0.002), m["metal_bright"], 12, 4, rot=(0, 0, 0)))
    return finish_item(parts, "beer")


def ring_prism(name, outer, inner, bottom, top, mat):
    """带洞的薄实体：outer、inner 是点数相同的 Godot xz 轮廓（同向），之间的环形区域挤出成 bottom..top 的厚度。
    @keyword-en ring-prism, holed-outline
    @keyword-cn 带孔棱柱, 镂空轮廓
    """
    bm = bmesh.new()
    n = len(outer)
    ob = [bm.verts.new(kit.g(x, bottom, z)) for x, z in outer]
    ot = [bm.verts.new(kit.g(x, top, z)) for x, z in outer]
    ib = [bm.verts.new(kit.g(x, bottom, z)) for x, z in inner]
    it = [bm.verts.new(kit.g(x, top, z)) for x, z in inner]
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((ot[i], ot[j], it[j], it[i]))
        bm.faces.new((ob[j], ob[i], ib[i], ib[j]))
        bm.faces.new((ob[i], ob[j], ot[j], ot[i]))
        bm.faces.new((ib[j], ib[i], it[i], it[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit.mesh_object(name, bm, mat)


def rounded_outline(cx, cz, half_x, half_z, power, segments=28):
    """Godot xz 平面上的圆角矩形轮廓（超椭圆）。
    @keyword-en rounded-outline, superellipse
    @keyword-cn 圆角轮廓, 超椭圆
    """
    pts = []
    for i in range(segments):
        a = 2.0 * math.pi * i / segments
        c, s = math.cos(a), math.sin(a)
        pts.append((cx + half_x * math.copysign(abs(c) ** (2.0 / power), c),
                    cz + half_z * math.copysign(abs(s) ** (2.0 / power), s)))
    return pts


def blot(cx, cz, radius, seed, points=9):
    """不规则的小斑块轮廓（锈斑用）。
    @keyword-en irregular-blot, rust-patch
    @keyword-cn 不规则斑块, 锈斑
    """
    rnd = random.Random(seed)
    return [(cx + radius * rnd.uniform(0.55, 1.0) * math.cos(2 * math.pi * i / points) * 1.6,
             cz + radius * rnd.uniform(0.55, 1.0) * math.sin(2 * math.pi * i / points))
            for i in range(points)]


def build_saw(m):
    """构建平放的小手锯：梯形锯片下沿一排三角锯齿（朝 +z），根部插进带握孔的红色 D 形锯柄，
    三颗黄铜铆钉，锯片上有不规则锈斑。
    @keyword-en build-saw, toothed-blade
    @keyword-cn 构建手锯, 锯齿刀片
    """
    blade_y0, blade_y1 = 0.0068, 0.0093
    root_x, tip_x = -0.042, 0.092
    back_z = -0.022
    root_edge, tip_edge = 0.027, 0.006
    teeth = 16
    slope = (tip_edge - root_edge) / (tip_x - root_x)
    outline = [(root_x, back_z), (tip_x - 0.006, back_z), (tip_x, back_z + 0.006), (tip_x, tip_edge - 0.002)]
    for i in range(teeth, 0, -1):
        x1 = root_x + 0.012 + (tip_x - 0.004 - root_x - 0.012) * i / teeth
        x0 = root_x + 0.012 + (tip_x - 0.004 - root_x - 0.012) * (i - 1) / teeth
        outline.append((x1, root_edge + slope * (x1 - root_x)))
        outline.append(((x0 + x1) / 2 + 0.001, root_edge + slope * ((x0 + x1) / 2 - root_x) + 0.0045))
    outline.append((root_x + 0.012, root_edge))
    outline.append((root_x, root_edge))
    parts = [polygon_prism("blade", outline, blade_y0, blade_y1, m["metal_bright"])]
    for i, (cx, cz, r) in enumerate(((0.012, -0.006, 0.008), (0.05, 0.002, 0.006), (0.073, -0.012, 0.004))):
        parts.append(polygon_prism("rust", blot(cx, cz, r, i), blade_y1, blade_y1 + 0.0004, m["rust"]))
    handle = ring_prism("handle", rounded_outline(-0.061, 0.002, 0.034, 0.031, 3.2),
                        rounded_outline(-0.066, 0.004, 0.0165, 0.0125, 2.6), 0.0, 0.0165, m["red_paint"])
    kit.add_bevel(handle, 0.0025, 2)
    parts.append(handle)
    for z in (-0.017, -0.001, 0.015):
        parts.append(kit.cylinder("rivet", 0.0032, 0.0185, (-0.036, 0.00825, z), "y", m["brass"], 10))
    return finish_item(parts, "saw")


def build_handcuffs(m):
    """构建双环、锁盒、齿臂和交错链节的手铐。
    @keyword-en build-handcuffs, chained-rings
    @keyword-cn 构建手铐, 链接双环
    """
    parts = []
    for side, x in enumerate((-0.045, 0.045)):
        parts.append(torus(f"cuff_{side}", 0.026, 0.004, (x, 0.006, 0), m["metal_bright"], 14, 3))
        parts.append(kit.box(f"lock_{side}", (0.025, 0.012, 0.018), (x + (0.025 if side == 0 else -0.025), 0.006, 0), m["metal"], bevel=0.002))
        for j in range(4):
            parts.append(kit.box(f"tooth_{side}_{j}", (0.003, 0.009, 0.006), (x - 0.014 + j * 0.009, 0.007, -0.025), m["metal_bright"], bevel=0.0005))
    for i, x in enumerate((-0.014, 0, 0.014)):
        rot = (math.pi / 2, 0, 0) if i % 2 else (0, math.pi / 2, 0)
        parts.append(torus(f"chain_{i}", 0.008, 0.0022, (x, 0.010, 0), m["metal_bright"], 8, 3, rot=rot))
    return finish_item(parts, "handcuffs")


def build_phone(m):
    """构建贴有整面屏幕键盘标签的廉价直板手机。
    @keyword-en build-phone, candybar-phone
    @keyword-cn 构建手机, 直板机
    """
    parts = [kit.box("phone_body", (0.052, 0.016, 0.105), (0, 0.008, 0), m["plastic_black"], bevel=0.004)]
    parts.append(label_quad("phone_face", 0.046, 0.096, 0.0166, (0, 0), m["phone"]))
    parts.append(kit.cylinder("antenna", 0.0045, 0.018, (0.018, 0.010, -0.061), "z", m["plastic_black"], 10))
    parts.append(kit.sphere("antenna_tip", 0.005, (0.018, 0.010, -0.070), m["plastic_black"], 10, 5, scale=(1, 1, 0.8)))
    return finish_item(parts, "phone")


def build_inverter(m):
    """构建带发光环、面板、按钮和线缆头的极性反转器。
    @keyword-en build-inverter, glowing-device
    @keyword-cn 构建反转器, 发光装置
    """
    parts = [kit.cylinder("puck", 0.042, 0.029, (0, 0.0145, 0), "y", m["metal_dark"], 20)]
    for i in range(10):
        a = i * math.tau / 10
        parts.append(kit.box("side_rib", (0.006, 0.021, 0.006), (0.043 * math.cos(a), 0.014, 0.043 * math.sin(a)), m["metal"], rot=(0, -a, 0), bevel=0.001))
    parts.append(label_disk("top_panel", 0.028, 0.0296, (-0.004, 0), m["inverter"], 20))
    parts.append(torus("glow_ring", 0.031, 0.0032, (0, 0.031, 0), m["inverter_glow"], 18, 4))
    parts.append(kit.cylinder("button", 0.008, 0.008, (0.020, 0.034, 0.006), "y", m["red_paint"], 12))
    parts.append(kit.cylinder("cable", 0.004, 0.022, (-0.050, 0.012, 0.010), "x", m["plastic_black"], 10))
    return finish_item(parts, "inverter")


def build_medicine(m):
    """构建琥珀药瓶、环绕标签、防滑盖和散落药片。
    @keyword-en build-medicine, pill-bottle
    @keyword-cn 构建药瓶, 过期药
    """
    parts = []
    profile = [(0.022, 0), (0.026, 0.004), (0.027, 0.010), (0.027, 0.052),
               (0.023, 0.060), (0.021, 0.063), (0.021, 0.069)]
    parts.append(kit.lathe("bottle", profile, (-0.018, 0, 0), "y", m["amber"], 16))
    parts.append(kit.cylinder("label", 0.0274, 0.032, (-0.018, 0.032, 0), "y", m["pills"], 16))
    parts.append(kit.cylinder("cap", 0.025, 0.019, (-0.018, 0.0785, 0), "y", m["cap_white"], 16))
    for i in range(12):
        a = i * math.tau / 12
        parts.append(kit.box("cap_rib", (0.0035, 0.015, 0.0045), (-0.018 + 0.025 * math.cos(a), 0.078, 0.025 * math.sin(a)), m["cap_white"], rot=(0, -a, 0)))
    parts.append(kit.cylinder("pill_a", 0.008, 0.004, (0.028, 0.002, 0.014), "y", m["cap_white"], 10))
    parts.append(kit.cylinder("pill_b", 0.007, 0.004, (0.040, 0.002, -0.010), "y", m["cap_white"], 10))
    return finish_item(parts, "medicine")


def render_isolated(obj, item_id):
    """隐藏其余模型并渲染单件三分之四俯视近景。
    @keyword-en isolated-preview, item-closeup
    @keyword-cn 单件预览, 道具近景
    """
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    for other in meshes:
        other.hide_render = other != obj
    kit.render_preview(f"items/{item_id}.png", direction=(0.75, 1.05, 0.9), fov=38, resolution=(640, 480), objs=[obj])
    for other in meshes:
        other.hide_render = False


def main():
    """生成、导出、统计并预览全部八件道具。
    @keyword-en build-all-items, export-previews
    @keyword-cn 构建全部道具, 导出预览
    """
    kit.reset_scene()
    mats = make_materials()
    builders = (
        ("magnifier", build_magnifier), ("cigarette", build_cigarette),
        ("beer", build_beer), ("saw", build_saw),
        ("handcuffs", build_handcuffs), ("phone", build_phone),
        ("inverter", build_inverter), ("medicine", build_medicine),
    )
    items = []
    for item_id, builder in builders:
        obj = builder(mats)
        items.append(obj)
        kit.export_glb([obj], f"items/{item_id}.glb")
        render_isolated(obj, item_id)
        print("ITEM_STATS", item_id, kit.triangle_count([obj]), [mat.name for mat in obj.data.materials])

    positions = ((-0.33, -0.11), (-0.11, -0.11), (0.11, -0.11), (0.33, -0.11),
                 (-0.33, 0.11), (-0.11, 0.11), (0.11, 0.11), (0.33, 0.11))
    for obj, (x, z) in zip(items, positions):
        obj.location = kit.g(x, 0, z)
    kit.render_preview("items/family.png", direction=(0, 1.0, 0.8), target=(0, 0.035, 0),
                       distance=1.35, fov=38, resolution=(960, 540), objs=items)


if __name__ == "__main__":
    main()
