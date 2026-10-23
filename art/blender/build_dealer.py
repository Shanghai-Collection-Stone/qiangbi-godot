"""构建《枪毙·最后一发》的行刑人角色，导出 ``art/models/dealer.glb``。

同时渲染玩家视角、头部正面和头部侧面预览到
``art/source/previews/dealer/``。运行方式：
``blender -b --factory-startup --python art/blender/build_dealer.py``。
"""

import math
import random
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit


def create_materials():
    """创建行刑人使用的全部命名材质。
    @keyword-en dealer-materials, named-materials
    @keyword-cn 行刑人材质, 命名材质
    """
    return {
        "wood_dark": kit.material("wood_dark", (0.16, 0.09, 0.05), 0.7, 0.0, preview_texture="wood.png"),
        "leather": kit.material("leather", (0.22, 0.05, 0.04), 0.6, 0.0, preview_texture="leather.png"),
        "brass": kit.material("brass", (0.8, 0.6, 0.22), 0.35, 0.8),
        "cloth": kit.material("cloth", (0.06, 0.06, 0.07), 1.0, 0.0, preview_texture="cloth.png"),
        "shirt": kit.material("shirt", (0.6, 0.58, 0.52), 0.9, 0.0),
        "tie": kit.material("tie", (0.35, 0.02, 0.02), 0.6, 0.0),
        "skin": vertex_color_skin(kit.material("skin", (0.55, 0.6, 0.5), 0.6, 0.0, preview_texture="skin.png")),
        "tentacle": kit.material("tentacle", (0.35, 0.4, 0.3), 0.35, 0.0, preview_texture="tentacle.png"),
        "claw": kit.material("claw", (0.12, 0.1, 0.09), 0.4, 0.0),
        "teeth": kit.material("teeth", (0.75, 0.68, 0.48), 0.45, 0.0),
        "mouth": kit.material("mouth", (0.08, 0.01, 0.015), 1.0, 0.0),
        "black": kit.material("black", (0.005, 0.005, 0.005), 1.0, 0.0),
        "pupil": kit.material("pupil", (1.0, 1.0, 0.95), 0.15, 0.0, emission=(1.0, 1.0, 0.95)),
        "eye_wet": kit.material("eye_wet", (0.05, 0.015, 0.015), 0.08, 0.0),
        # 三个形态各自的部件
        "porcelain": vertex_color_skin(kit.material("porcelain", (0.82, 0.8, 0.76), 0.45, 0.0)),
        "hat": kit.material("hat", (0.03, 0.03, 0.035), 0.55, 0.0, preview_texture="cloth.png"),
        "bone": kit.material("bone", (0.78, 0.72, 0.58), 0.5, 0.0),
        "vein_glow": kit.material("vein_glow", (0.3, 0.8, 0.35), 1.0, 0.0, emission=(0.22, 0.6, 0.26)),
        "flesh": kit.material("flesh", (0.5, 0.2, 0.2), 0.45, 0.0, preview_texture="flesh.png"),
        "eye_white": kit.material("eye_white", (0.85, 0.8, 0.62), 0.2, 0.0),
        "iris_glow": kit.material("iris_glow", (1.0, 0.45, 0.1), 1.0, 0.0, emission=(1.0, 0.45, 0.1)),
    }


def vertex_color_skin(mat):
    """让皮肤材质的预览乘上顶点色 "Col"（游戏里由 Godot 材质的 vertex_color_use_as_albedo 实现同样效果）。
    @keyword-en vertex-color-material, skin-preview
    @keyword-cn 顶点色材质, 皮肤预览
    """
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    source = bsdf.inputs["Base Color"].links[0].from_socket if bsdf.inputs["Base Color"].is_linked else None
    attr = nodes.new("ShaderNodeVertexColor")
    attr.layer_name = "Col"
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    sockets = {s.identifier: s for s in mix.inputs}
    sockets["Factor_Float"].default_value = 1.0
    if source is not None:
        mat.node_tree.links.new(source, sockets["A_Color"])
    else:
        sockets["A_Color"].default_value = bsdf.inputs["Base Color"].default_value
    mat.node_tree.links.new(attr.outputs["Color"], sockets["B_Color"])
    mat.node_tree.links.new(next(s for s in mix.outputs if s.identifier == "Result_Color"), bsdf.inputs["Base Color"])
    return mat


HEAD_CENTER = Vector((0.0, 1.0, -1.2))
# 额头上一排三只小眼（头部局部 x, y）
FOREHEAD_EYES = ((-0.025, 0.098), (0.0, 0.105), (0.025, 0.098))
TORSO_Z = -1.30
# 由 Godot 方向向量换到 Blender（线性部分，和 kit.g 一致）
G2B = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
# 两只主眼的眼窝中心（头部局部 x, y）
MAIN_EYES = ((-0.06, 0.035), (0.06, 0.035))
# 胸口裂开的那只眼的中心（形态三）
CHEST_EYE = Vector((0.0, 0.33, -1.16))
# 行刑人每条命（每一局）一个形态：每个形态显示哪些「形态部件」节点。
# 不在任何列表里的节点（身体、头、手……）所有形态都显示。必须和 scripts/table_scene.gd 的 FORM_NODES 一致。
FORM_NODES = {
    1: ("Mask", "Hat", "WatchChain"),
    2: ("MaskShard", "Beard", "BackTentacles2", "WatchChain"),
    3: ("Beard", "BeardLong", "Horns", "Veins", "BackTentacles3", "ChestRift", "ChestEye"),
}
FORM_PART_NAMES = sorted({name for names in FORM_NODES.values() for name in names})


def gauss(dx, dy, sx, sy, power=1.0):
    """二维高斯衰减，power > 1 时中心更平、边缘更陡（适合眼窝这种深坑）。
    @keyword-en gaussian-falloff, sculpt-brush
    @keyword-cn 高斯衰减, 雕刻笔刷
    """
    return math.exp(-(((dx / sx) ** 2 + (dy / sy) ** 2) ** power))


def smoothstep(edge0, edge1, x):
    """GLSL 同名函数：x 在两个边界之间平滑过渡到 0..1。
    @keyword-en smoothstep, smooth-transition
    @keyword-cn 平滑过渡, 插值
    """
    t = min(max((x - edge0) / (edge1 - edge0), 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)


def smile_y(x):
    """咧嘴笑弧的中线高度（头部局部坐标），嘴角一直翘到颧骨下面。
    @keyword-en smile-curve, mouth-arc
    @keyword-cn 笑弧, 嘴型曲线
    """
    return -0.095 + 4.0 * x * x


def smile_h(x):
    """笑弧在 x 处的张口半高，越到嘴角越窄。
    @keyword-en mouth-opening, smile-height
    @keyword-cn 张口高度, 嘴宽
    """
    t = min(abs(x) / 0.125, 1.0)
    return 0.027 * (1.0 - t * t) ** 0.7


def seam_points(side):
    """嘴角往颧骨方向的缝线两端点（头部局部 x, y）。
    @keyword-en stitch-seam, mouth-corner
    @keyword-cn 缝线, 嘴角
    """
    return (side * 0.121, smile_y(0.121)), (side * 0.14, 0.03)


def _seam_distance(x, y, side):
    """点 (x, y) 到某一侧缝线线段的最近距离（头部局部坐标）。
    @keyword-en seam-distance, point-segment
    @keyword-cn 缝线距离, 点线距离
    """
    (x0, y0), (x1, y1) = seam_points(side)
    vx, vy = x1 - x0, y1 - y0
    t = min(max(((x - x0) * vx + (y - y0) * vy) / (vx * vx + vy * vy), 0.0), 1.0)
    return math.hypot(x - (x0 + vx * t), y - (y0 + vy * t))


def head_base(ux, uy, uz):
    """头的基本形：蛋形长颅（后脑往后上方拉长）、下半部收窄成尖下巴、脸正面略压平。
    返回头部局部坐标，五官位移和顶点色都以它为参照。
    @keyword-en egg-skull, base-shape
    @keyword-cn 蛋形头骨, 基本形
    """
    x, y, z = ux * 0.145, uy * 0.21, uz * 0.15
    if uy < 0.0:
        t = -uy
        x *= 1.0 - 0.45 * t ** 1.6
        z *= 1.0 - 0.2 * t ** 2
    if uy > 0.0:
        z -= 0.045 * uy * uy * (1.0 - 0.6 * max(uz, 0.0))
    return x, y, z * (1.0 - 0.07 * smoothstep(0.05, 0.55, uz))


def head_normal(x, y, z):
    """基本形在头部局部点 (x, y, z) 处的近似法线（按椭球 0.145 × 0.21 × 0.15 求梯度）。
    @keyword-en head-normal, ellipsoid-gradient
    @keyword-cn 头部法线, 椭球梯度
    """
    return Vector((x / 0.145 ** 2, y / 0.21 ** 2, z / 0.15 ** 2)).normalized()


def head_point(ux, uy, uz, offset=0.0):
    """单位方向 (ux, uy, uz) 上的基本形表面点（头部局部坐标），沿近似法线外推 offset。面具壳用它，表面光滑不带五官。
    @keyword-en head-offset-point, mask-surface
    @keyword-cn 头部外推点, 面具曲面
    """
    p = Vector(head_base(ux, uy, uz))
    return p + head_normal(*p) * offset


def head_half_width(y):
    """基本形在高度 y（头部局部）处的半宽：正面射线在 |x| 小于它时才打得中头。
    @keyword-en head-silhouette, half-width
    @keyword-cn 头部轮廓, 半宽
    """
    uy = max(-1.0, min(1.0, y / 0.21))
    half = 0.145 * math.sqrt(max(0.0, 1.0 - uy * uy))
    if uy < 0.0:
        half *= 1.0 - 0.45 * (-uy) ** 1.6
    return half


_BASE_BVH = []


def base_front(x, y):
    """不带五官的光滑基本形在正面 (x, y) 处的点和法线（头部局部 Godot 坐标），打不中返回 None。
    面具贴着它投影，五官的凹凸不会印到瓷面上。
    @keyword-en smooth-base-surface, mask-projection
    @keyword-cn 光滑基本形, 面具投影
    """
    if not _BASE_BVH:
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=5, radius=1.0)
        for v in bm.verts:
            u = v.co.normalized()
            bx, by, bz = head_base(u.x, u.z, -u.y)
            v.co = Vector((bx, -bz, by))
        bm.normal_update()
        _BASE_BVH.append(BVHTree.FromBMesh(bm))
        bm.free()
    return ray_front(_BASE_BVH[0], x, y, 0.5)


def sculpt_point(direction, offset=0.0):
    """单位方向上雕刻后的头部表面点和近似法线（头部局部坐标），点沿法线外推 offset（负数是往里埋）。
    骨角、骨刺的根部用它，头顶骨冠也算在里面。
    @keyword-en sculpt-point, horn-root
    @keyword-cn 雕刻表面点, 骨角根部
    """
    u = Vector(direction).normalized()
    p = Vector(head_shape(u.x, u.y, u.z))
    n = head_normal(*head_base(u.x, u.y, u.z))
    return p + n * offset, n


def head_shape(ux, uy, uz):
    """把单位球面上的点（Godot 头部局部方向）雕成行刑人的头，返回头部局部坐标 (x, y, z)。

    在 head_base 上叠加眼窝、眉弓、颧骨、凹颊、太阳穴、耳朵、鼻孔、笑弧口腔和缝线沟的位移。

    @keyword-en head-sculpt, displacement-shape
    @keyword-cn 头部雕刻, 位移塑形
    """
    x, y, z = head_base(ux, uy, uz)
    front = smoothstep(0.05, 0.55, uz)
    dx = dz = 0.0
    # 头顶中线一道椎骨似的骨冠：从额头上方一直到后脑，一节一节凸起，沿基本形法线往外推
    theta = math.atan2(uy, uz)
    crest = gauss(x, 0.0, 0.015, 1.0) * smoothstep(0.85, 1.15, theta) * (1.0 - smoothstep(2.6, 3.0, theta))
    crest *= 0.018 * (0.6 + 0.4 * math.cos(theta * 16.0))
    nx, ny, nz = x / 0.145 ** 2, y / 0.21 ** 2, z / 0.15 ** 2
    nl = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    x, y, z = x + nx / nl * crest, y + ny / nl * crest, z + nz / nl * crest
    for ex, ey in FOREHEAD_EYES:
        dz -= 0.012 * front * gauss(x - ex, y - ey, 0.0085, 0.0075, 1.3)
    for s in (-1.0, 1.0):
        side = smoothstep(0.3, 0.85, s * ux)
        dz -= 0.044 * front * gauss(x - s * 0.06, y - 0.035, 0.034, 0.026, 1.4)
        dz += 0.012 * front * gauss(x - s * 0.058, y - 0.08, 0.05, 0.016)
        dz += 0.006 * front * gauss(x - s * 0.022, y - 0.066, 0.016, 0.012)
        cheek = gauss(x - s * 0.094, y + 0.02, 0.028, 0.022)
        dz += 0.006 * front * cheek
        dx += s * 0.008 * cheek
        hollow = gauss(x - s * 0.085, y + 0.085, 0.03, 0.035)
        dx -= s * 0.016 * hollow * smoothstep(-0.3, 0.2, uz)
        dz -= 0.007 * front * hollow
        dx -= s * 0.012 * side * gauss(y - 0.065, z - 0.03, 0.045, 0.05)
        dx += s * 0.02 * side * gauss(y - 0.0, z + 0.015, 0.033, 0.012)
        dz -= 0.016 * front * gauss(x - s * 0.008, y + 0.03, 0.0065, 0.012)
        dz -= 0.0045 * front * math.exp(-(_seam_distance(x, y, s) / 0.0065) ** 2)
    dz += 0.004 * front * gauss(x, y - 0.005, 0.01, 0.03)
    dz += 0.012 * front * gauss(x, y + 0.185, 0.03, 0.03)
    if abs(x) < 0.14 and uz > 0.0:
        h = smile_h(x)
        inside = 1.0 - smoothstep(0.55 * h, 1.1 * h + 0.005, abs(y - smile_y(x)))
        inside *= 1.0 - smoothstep(0.112, 0.135, abs(x))
        dz -= 0.03 * front * inside
    return x + dx, y, z + dz


def head_color(x, y, uz):
    """头部顶点色（乘在皮肤贴图上）：眼窝和鼻孔渐变到黑，口腔渐变到暗红，缝线发紫红，凹陷处略暗。
    用渐变代替逐面分材质，边缘不会出现锯齿。
    @keyword-en vertex-color, baked-shading
    @keyword-cn 顶点色, 烘焙明暗
    """
    def mix(c, target, k):
        """颜色线性插值。
        @keyword-en color-lerp, mix-color
        @keyword-cn 颜色插值, 混色
        """
        return tuple(a + (b - a) * k for a, b in zip(c, target))

    front = smoothstep(0.05, 0.55, uz)
    c = (1.0, 1.0, 1.0)
    for s in (-1.0, 1.0):
        c = mix(c, (0.55, 0.5, 0.5), 0.6 * front * gauss(x - s * 0.06, y - 0.035, 0.055, 0.045))
        c = mix(c, (0.85, 0.85, 0.85), gauss(x - s * 0.085, y + 0.085, 0.03, 0.035))
        c = mix(c, (0.012, 0.01, 0.01),
                smoothstep(0.2, 0.75, front * gauss(x - s * 0.06, y - 0.035, 0.034, 0.026, 1.4)))
        c = mix(c, (0.02, 0.015, 0.015),
                smoothstep(0.25, 0.8, front * gauss(x - s * 0.008, y + 0.03, 0.0065, 0.012)))
        c = mix(c, (0.3, 0.07, 0.06), 0.85 * front * math.exp(-(_seam_distance(x, y, s) / 0.006) ** 2))
    for ex, ey in FOREHEAD_EYES:
        c = mix(c, (0.02, 0.015, 0.015), smoothstep(0.25, 0.8, front * gauss(x - ex, y - ey, 0.0085, 0.0075, 1.3)))
    if abs(x) < 0.14 and uz > 0.0:
        h = smile_h(x)
        inside = 1.0 - smoothstep(0.45 * h, 1.15 * h + 0.006, abs(y - smile_y(x)))
        inside *= 1.0 - smoothstep(0.112, 0.138, abs(x))
        c = mix(c, (0.12, 0.012, 0.018), smoothstep(0.1, 0.8, inside * front))
    return c


def oriented_box(name, center, axes, size, mat):
    """沿任意 Godot 坐标轴组摆放的小长方体（缝线、纽扣等贴表面的细节）。axes 为三根单位向量。
    @keyword-en oriented-box, surface-detail
    @keyword-cn 定向盒子, 表面细节
    """
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    basis = Matrix([G2B @ Vector(a) * s for a, s in zip(axes, size)]).transposed()
    bmesh.ops.transform(bm, matrix=basis.to_4x4(), verts=bm.verts)
    obj = kit.mesh_object(name, bm, mat)
    obj.location = kit.g(center)
    return obj


def ray_front(bvh, x, y, origin_z):
    """从 Godot +z 方向朝 -z 打射线，返回 (命中点 Godot 坐标, 法线 Godot 方向)，没打中返回 None。
    @keyword-en front-raycast, surface-sample
    @keyword-cn 正面射线, 表面采样
    """
    hit = bvh.ray_cast(kit.g(x, y, origin_z), kit.g(0, 0, -1))
    if hit[0] is None:
        return None
    loc, normal = hit[0], hit[1]
    return Vector((loc.x, loc.z, -loc.y)), Vector((normal.x, normal.z, -normal.y))


def superellipse_ring(y, half_width, depth_front, depth_back, center_z, segments=24, power=2.6):
    """躯干放样用的圆角矩形截面（Godot 坐标点列），前半可以比后半更饱满。
    @keyword-en superellipse, loft-section
    @keyword-cn 圆角截面, 放样截面
    """
    pts = []
    for i in range(segments):
        a = 2.0 * math.pi * i / segments
        c, s = math.cos(a), math.sin(a)
        x = half_width * math.copysign(abs(c) ** (2.0 / power), c)
        depth = depth_front if s > 0 else depth_back
        pts.append((x, y, center_z + depth * math.copysign(abs(s) ** (2.0 / power), s)))
    return pts


def loft(name, rings, mat):
    """把一串同点数的截面（Godot 坐标，自下而上）放样成封口的管状网格。
    @keyword-en loft-mesh, section-sweep
    @keyword-cn 截面放样, 管状网格
    """
    bm = bmesh.new()
    vs = [[bm.verts.new(kit.g(p)) for p in ring] for ring in rings]
    n = len(rings[0])
    for lower, upper in zip(vs, vs[1:]):
        for i in range(n):
            bm.faces.new((lower[i], lower[(i + 1) % n], upper[(i + 1) % n], upper[i]))
    bm.faces.new(list(reversed(vs[0])))
    bm.faces.new(vs[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit.mesh_object(name, bm, mat)


def surface_panel(name, outline, bvh, offset, mat, thickness=0.0, cuts=2):
    """把一个 Godot (x, y) 平面轮廓从正面投影到躯干表面上，沿法线浮起 offset，做成贴身的衣片。
    thickness > 0 时加实体化修改器，边缘在灯光下有阴影线。
    @keyword-en surface-panel, projected-decal
    @keyword-cn 贴身衣片, 投影贴片
    """
    bm = bmesh.new()
    face = bm.faces.new([bm.verts.new((x, 0.0, y)) for x, y in outline])
    bmesh.ops.triangulate(bm, faces=[face])
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    for v in bm.verts:
        hit = ray_front(bvh, v.co.x, v.co.z, TORSO_Z + 0.5)
        if hit is None:
            v.co = kit.g(v.co.x, v.co.z, TORSO_Z + 0.12)
        else:
            v.co = kit.g(hit[0] + hit[1] * offset)
    bm.normal_update()
    bm.faces.ensure_lookup_table()
    if bm.faces and bm.faces[0].normal.y > 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    obj = kit.mesh_object(name, bm, mat)
    if thickness > 0:
        mod = obj.modifiers.new("Solidify", "SOLIDIFY")
        mod.thickness = thickness
        mod.offset = -1.0
    return obj


def cone_between(name, base, tip, radius, mat, segments=6):
    """在两个 Godot 坐标点之间生成带底盖的低模圆锥。
    @keyword-en cone-between, pointed-detail
    @keyword-cn 两点圆锥, 尖锐细节
    """
    base_b = kit.g(base)
    tip_b = kit.g(tip)
    axis = (tip_b - base_b).normalized()
    helper = Vector((0, 0, 1)) if abs(axis.z) < 0.9 else Vector((0, 1, 0))
    side = axis.cross(helper).normalized()
    up = axis.cross(side).normalized()
    bm = bmesh.new()
    ring = []
    for i in range(segments):
        angle = math.tau * i / segments
        ring.append(bm.verts.new(base_b + radius * (math.cos(angle) * side + math.sin(angle) * up)))
    tip_vert = bm.verts.new(tip_b)
    center = bm.verts.new(base_b)
    for i in range(segments):
        nxt = (i + 1) % segments
        bm.faces.new((ring[i], ring[nxt], tip_vert))
        bm.faces.new((center, ring[nxt], ring[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit.mesh_object(name, bm, mat)


def cylinder_between(name, start, end, radius, mat, segments=8, radius_end=None):
    """生成连接两个 Godot 坐标点的圆柱或圆台。
    @keyword-en cylinder-between, limb-segment
    @keyword-cn 两点圆柱, 肢体分节
    """
    start_v = Vector(start)
    end_v = Vector(end)
    direction = end_v - start_v
    obj = kit.cylinder(name, radius, direction.length, (start_v + end_v) / 2,
                       axis=direction, mat=mat, segments=segments,
                       radius_top=radius if radius_end is None else radius_end)
    return obj


def build_chair(mats):
    """构建带皮革软包、铆钉和球形顶饰的高背椅。
    @keyword-en dealer-chair, high-back-chair
    @keyword-cn 行刑人椅子, 高背椅
    """
    parts = []
    for x in (-0.48, 0.48):
        parts.append(kit.box("ChairPost", (0.075, 1.9, 0.09), (x, 0.27, -1.68), mats["wood_dark"], bevel=0.006))
        parts.append(kit.sphere("ChairFinial", 0.075, (x, 1.31, -1.68), mats["wood_dark"], segments=12, rings=6))
        parts.append(kit.cylinder("ChairNeck", 0.052, 0.11, (x, 1.225, -1.68), "y", mats["wood_dark"], segments=12))
    parts.extend([
        kit.box("ChairTop", (0.9, 0.075, 0.095), (0, 1.12, -1.68), mats["wood_dark"], bevel=0.005),
        kit.box("ChairBottom", (0.9, 0.075, 0.095), (0, -0.47, -1.68), mats["wood_dark"], bevel=0.005),
        kit.box("ChairPad", (0.79, 1.46, 0.055), (0, 0.32, -1.625), mats["leather"], bevel=0.018),
    ])
    for x in (-0.375, 0.375):
        for y in (-0.34, -0.08, 0.18, 0.44, 0.70, 0.96):
            parts.append(kit.sphere("ChairStud", 0.012, (x, y, -1.588), mats["brass"], segments=8, rings=4))
    for x in (-0.25, 0.0, 0.25):
        parts.append(kit.sphere("ChairStud", 0.012, (x, 1.01, -1.588), mats["brass"], segments=8, rings=4))
        parts.append(kit.sphere("ChairStud", 0.012, (x, -0.39, -1.588), mats["brass"], segments=8, rings=4))
    chair = kit.join(parts, "Chair")
    kit.box_uv(chair, 0.6)
    kit.set_origin(chair, (0, 0, -1.65))
    return chair


def build_body(mats):
    """构建瘦长西装躯干：圆角截面放样的身体，贴着胸口投影的马甲、衬衫、领带、翻领和纽扣，加脖子和领圈。
    @keyword-en dealer-body, three-piece-suit
    @keyword-cn 行刑人躯干, 三件套西装
    """
    sections = [
        (-0.40, 0.19, 0.13, 0.12, TORSO_Z - 0.01),
        (-0.10, 0.175, 0.125, 0.115, TORSO_Z - 0.01),
        (0.15, 0.18, 0.13, 0.115, TORSO_Z - 0.005),
        (0.35, 0.205, 0.135, 0.115, TORSO_Z),
        (0.50, 0.245, 0.125, 0.11, TORSO_Z),
        (0.575, 0.31, 0.11, 0.10, TORSO_Z),
        (0.615, 0.345, 0.095, 0.09, TORSO_Z),
        (0.645, 0.29, 0.085, 0.085, TORSO_Z + 0.005),
        (0.675, 0.19, 0.075, 0.075, TORSO_Z + 0.015),
        (0.70, 0.10, 0.06, 0.06, TORSO_Z + 0.03),
        (0.712, 0.07, 0.05, 0.05, TORSO_Z + 0.035),
    ]
    torso = loft("Torso", [superellipse_ring(*s) for s in sections], mats["cloth"])
    bm = bmesh.new()
    bm.from_mesh(torso.data)
    bm.transform(torso.matrix_world)
    bvh = BVHTree.FromBMesh(bm)
    bm.free()

    parts = [torso,
             surface_panel("Vest", [(-0.115, 0.64), (0.115, 0.64), (0.09, 0.2), (-0.09, 0.2)], bvh, 0.004,
                           mats["cloth"], 0.004),
             surface_panel("Shirt", [(-0.07, 0.712), (0.07, 0.712), (0.0, 0.45)], bvh, 0.009, mats["shirt"]),
             surface_panel("Tie", [(-0.014, 0.648), (0.014, 0.648), (0.024, 0.52), (0.0, 0.47), (-0.024, 0.52)],
                           bvh, 0.012, mats["tie"], 0.004),
             surface_panel("TieKnot", [(-0.019, 0.685), (0.019, 0.685), (0.013, 0.645), (-0.013, 0.645)],
                           bvh, 0.017, mats["tie"], 0.008, cuts=1)]
    for s in (-1.0, 1.0):
        parts.append(surface_panel("Collar", [(s * 0.07, 0.714), (s * 0.012, 0.69), (s * 0.05, 0.625)],
                                   bvh, 0.015, mats["shirt"], 0.003, cuts=1))
        lapel = [(s * 0.088, 0.712), (s * 0.165, 0.668), (s * 0.178, 0.588), (s * 0.15, 0.578), (s * 0.163, 0.54),
                 (s * 0.075, 0.30), (s * 0.048, 0.30), (s * 0.075, 0.56), (s * 0.084, 0.66)]
        if s > 0:
            lapel.reverse()
        parts.append(surface_panel("Lapel", lapel, bvh, 0.016, mats["cloth"], 0.007))
    for y in (0.43, 0.37, 0.31, 0.25):
        hit = ray_front(bvh, 0.0, y, TORSO_Z + 0.5)
        if hit is not None:
            p, n = hit
            parts.append(kit.cylinder("Button", 0.008, 0.004, p + n * 0.008, n, mats["black"], segments=8))
    parts.extend(build_suit_details(mats, bvh))
    parts.append(cylinder_between("Neck", (0, 0.66, -1.255), (0, 0.87, -1.215), 0.058, mats["skin"], 12, 0.047))
    # 脖子两侧各三道斜的鳃裂（从后上往前下）
    for s in (-1.0, 1.0):
        for k in range(3):
            y = 0.735 + 0.028 * k
            r = 0.058 + (0.047 - 0.058) * (y - 0.66) / 0.21
            cz = -1.255 + 0.04 * (y - 0.66) / 0.21
            n = Vector((s, 0.0, -0.15)).normalized()
            along = Vector((0.0, 0.8, -0.6))
            along = (along - n * along.dot(n)).normalized()
            parts.append(oriented_box("Gill", (s * r * 0.99, y, cz - 0.012), (along.cross(n).normalized(), along, n),
                                      (0.005, 0.036, 0.004), mats["mouth"]))
    parts.append(kit.lathe("CollarBand", [(0.056, 0.0), (0.054, 0.04)], (0, 0.676, -1.25), "y", mats["shirt"],
                           segments=16))
    body = kit.join(parts, "Body")
    kit.fill_color(body, (1.0, 1.0, 1.0))
    kit.box_uv(body, 0.35)
    kit.smooth(body, 50)
    kit.set_origin(body, (0, 0, 0))
    return body, build_watch_chain(mats, bvh)


def build_suit_details(mats, bvh):
    """西装上的小细节：垫肩、左胸口袋和露出的口袋巾、左翻领上的红色胸花。
    它们在低分辨率下是几个高光点和轮廓起伏，让躯干不再是一整块平板。
    @keyword-en suit-details, pocket-square
    @keyword-cn 西装细节, 口袋巾
    """
    parts = []
    for s in (-1.0, 1.0):
        parts.append(kit.sphere("ShoulderPad", 0.07, (s * 0.335, 0.6, TORSO_Z + 0.005), mats["cloth"],
                                segments=14, rings=7, scale=(1.0, 0.8, 1.0)))
    # 口袋在行刑人的左胸（画面右边，+x），翻领外侧
    parts.append(surface_panel("PocketSlit", [(0.168, 0.487), (0.238, 0.487), (0.238, 0.494), (0.168, 0.494)],
                               bvh, 0.006, mats["black"], cuts=1))
    parts.append(surface_panel("PocketSquare", [(0.175, 0.49), (0.18, 0.522), (0.192, 0.507), (0.203, 0.528),
                                                (0.215, 0.508), (0.228, 0.52), (0.232, 0.49)],
                               bvh, 0.012, mats["shirt"], 0.005, cuts=1))
    # 胸花：五瓣暗红的小花
    hit = ray_front(bvh, 0.128, 0.625, TORSO_Z + 0.5)
    if hit is not None:
        p, n = hit
        center = p + n * 0.024
        for k in range(5):
            a = 2.0 * math.pi * k / 5.0
            parts.append(kit.sphere("Petal", 0.009, center + Vector((math.cos(a), math.sin(a), 0.0)) * 0.009,
                                    mats["tie"], segments=6, rings=3))
        parts.append(kit.sphere("PetalCore", 0.006, center + n * 0.004, mats["black"], segments=6, rings=3))
    return parts


def build_watch_chain(mats, bvh):
    """马甲上的黄铜怀表链：从第二颗纽扣垂成一道弧挂进表袋，袋口露出半块怀表。
    单独一个节点 WatchChain：形态三胸口裂开时它不显示。
    @keyword-en watch-chain, pocket-watch
    @keyword-cn 怀表链, 怀表
    """
    parts = []
    for k in range(10):
        t = k / 9.0
        x = 0.012 + 0.1 * t
        y = 0.37 - 0.03 - 0.045 * math.sin(math.pi * t) + 0.01 * t
        hit = ray_front(bvh, x, y, TORSO_Z + 0.5)
        if hit is not None:
            p, n = hit
            parts.append(kit.sphere("ChainLink", 0.0055, p + n * 0.009, mats["brass"], segments=6, rings=3))
    hit = ray_front(bvh, 0.118, 0.345, TORSO_Z + 0.5)
    if hit is not None:
        p, n = hit
        parts.append(kit.cylinder("Watch", 0.016, 0.006, p + n * 0.01, n, mats["brass"], segments=12))
    chain = kit.join(parts, "WatchChain")
    kit.fill_color(chain, (1.0, 1.0, 1.0))
    kit.box_uv(chain, 0.35)
    kit.set_origin(chain, (0, 0, 0))
    return chain


def build_head(mats):
    """构建行刑人的头：密细分球按 head_shape 位移雕刻成一个整体，眼窝/口腔/缝线的明暗按 head_color 烘焙进顶点色，
    再用射线贴着表面放上下交错的尖牙、缝线和眼窝深处的瞳孔。
    @keyword-en dealer-head, grinning-skull
    @keyword-cn 行刑人头部, 咧嘴骷髅
    """
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=5, radius=1.0)
    # 脸和头顶骨冠那一条再细分一次（五官和骨冠需要更密的网格）
    face_edges = [e for e in bm.edges
                  if all(-v.co.y > 0.3 and abs(v.co.z) < 0.75 for v in e.verts)
                  or all(abs(v.co.x) < 0.2 and v.co.z > 0.2 for v in e.verts)]
    bmesh.ops.subdivide_edges(bm, edges=face_edges, cuts=1, use_grid_fill=True)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.verts.index_update()
    design = {}
    for v in bm.verts:
        u = v.co.normalized()
        ux, uy, uz = u.x, u.z, -u.y
        x, y, z = head_shape(ux, uy, uz)
        design[v.index] = (*head_base(ux, uy, uz)[:2], uz)
        v.co = Vector((x, -z, y))
    colors = [head_color(*design[v.index]) for v in bm.verts]
    bm.normal_update()
    bvh = BVHTree.FromBMesh(bm)
    me = bpy.data.meshes.new("Skull")
    bm.to_mesh(me)
    bm.free()
    attr = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    for i, col in enumerate(colors):
        attr.data[i].color = (*col, 1.0)
    skull = bpy.data.objects.new("Skull", me)
    bpy.context.scene.collection.objects.link(skull)
    skull.data.materials.append(mats["skin"])
    skull.location = kit.g(HEAD_CENTER)

    def surface(x, y):
        """头部表面在 (x, y) 处的点和法线（头部局部坐标），打不中时退回一个默认值。
        @keyword-en head-surface, raycast-fallback
        @keyword-cn 头部表面, 射线取点
        """
        hit = ray_front(bvh, x, y, 0.5)
        return hit if hit is not None else (Vector((x, y, 0.1)), Vector((0, 0, 1)))

    parts = [skull]
    rnd = random.Random(7)
    for row, count, x0 in (("Upper", 16, -0.105), ("Lower", 15, -0.098)):
        step = 0.21 / 15
        for i in range(count):
            x = x0 + i * step
            h = smile_h(x)
            if h < 0.006:
                continue
            slope = 8.0 * x
            n = Vector((-slope, 1.0)).normalized()
            if row == "Lower":
                n = -n
            cy = smile_y(x)
            length = h * rnd.uniform(0.85, 1.15)
            root2 = Vector((x, cy)) + n * 0.85 * h
            tip2 = Vector((x, cy)) + n * (0.85 * h - length)
            root, _ = surface(root2.x, root2.y)
            bottom, _ = surface(x, cy)
            tip_z = bottom.z + 0.012 + rnd.uniform(-0.002, 0.002)
            base = HEAD_CENTER + Vector((root2.x, root2.y, min(root.z, tip_z + 0.012) - 0.002))
            tip = HEAD_CENTER + Vector((tip2.x, tip2.y, tip_z))
            parts.append(cone_between(row + "Tooth", base, tip, 0.0058 * (0.75 + 0.25 * h / 0.027), mats["teeth"], 5))
    for s in (-1.0, 1.0):
        (sx0, sy0), (sx1, sy1) = seam_points(s)
        along2 = Vector((sx1 - sx0, sy1 - sy0)).normalized()
        for k in range(5):
            t = 0.15 + 0.17 * k
            p, n = surface(sx0 + (sx1 - sx0) * t, sy0 + (sy1 - sy0) * t)
            along = Vector((along2.x, along2.y, 0.0))
            along = (along - n * along.dot(n)).normalized()
            across = along.cross(n).normalized()
            parts.append(oriented_box("Stitch", HEAD_CENTER + p + n * 0.0007, (across, along, n),
                                      (0.016, 0.0028, 0.0026), mats["mouth"]))

    # 眼窝深处一颗湿润的暗红眼球，吊灯照过来有一点高光，发光的瞳孔嵌在它前面
    for ex, ey in MAIN_EYES:
        p, _ = surface(ex, ey)
        parts.append(kit.sphere("EyeWet", 0.021, HEAD_CENTER + p + Vector((0, 0, -0.008)), mats["eye_wet"],
                                segments=12, rings=6))
    # 皮肤、牙、缝线先做盒式 UV；触手自带"根 0 → 尖 1"的 UV（摆动着色器要用），合并后不能再整体投影
    for p in parts:
        kit.box_uv(p, 0.25)
    head = kit.join(parts, "Head")
    kit.smooth(head, 55)
    kit.set_origin(head, HEAD_CENTER)
    eyes = [("PupilL", -0.06, 0.035, 0.0085), ("PupilR", 0.06, 0.035, 0.0085)]
    eyes += [("PupilF%d" % (i + 1), ex, ey, 0.0048) for i, (ex, ey) in enumerate(FOREHEAD_EYES)]
    for name, ex, ey, radius in eyes:
        p, _ = surface(ex, ey)
        center = HEAD_CENTER + p + Vector((0, 0, radius + 0.0005))
        pupil = kit.sphere(name, radius, center, mats["pupil"], segments=10, rings=5)
        kit.set_origin(pupil, center)
        kit.parent(pupil, head)
    for part in build_head_form_parts(mats, surface):
        kit.set_origin(part, HEAD_CENTER)
        kit.parent(part, head)
    return head


def build_head_form_parts(mats, surface):
    """头上随形态出现的部件，都挂成 Head 的子节点（跟着头一起动）：
    触手须 Beard（形态二、三）、长触手须 BeardLong、白瓷面具 Mask 和礼帽 Hat（形态一）、
    碎面具 MaskShard（形态二）、骨角 Horns 和发光血管 Veins（形态三）。
    @keyword-en form-head-parts, per-form-parts
    @keyword-cn 形态头部部件, 分形态部件
    """
    beard = kit.join(build_beard(mats, surface), "Beard")
    beard_long = kit.join(build_beard(mats, surface, long=True), "BeardLong")
    return [beard, beard_long, build_mask(mats), build_hat(mats), build_mask_shard(mats), build_horns(mats),
            build_veins(mats, surface)]


def mask_half(y):
    """面具在高度 y 处的半宽：额头是一段椭圆弧，两腮宽，往下巴收尖；不超出头的轮廓。
    @keyword-en mask-half-width, shield-outline
    @keyword-cn 面具半宽, 盾形轮廓
    """
    if y > 0.155 or y < -0.19:
        return 0.0
    half = 0.13
    if y > 0.085:
        half *= math.sqrt(max(0.0, 1.0 - ((y - 0.085) / 0.07) ** 2))
    elif y < -0.02:
        half *= 1.0 - 0.62 * ((-0.02 - y) / 0.17) ** 1.6
    return min(half, 0.93 * head_half_width(y))


def mask_keep(x, y):
    """白瓷面具的轮廓（头部局部 x, y）：盾形里挖掉两个眼洞。
    @keyword-en mask-outline, eye-holes
    @keyword-cn 面具轮廓, 眼洞
    """
    if abs(x) > mask_half(y):
        return False
    return all(((x - ex) / 0.03) ** 2 + ((y - ey) / 0.021) ** 2 >= 1.0 for ex, ey in MAIN_EYES)


def mask_contours(x, y):
    """面具边界上离 (x, y) 最近的候选点：两侧轮廓、额头椭圆弧、下巴平边、两个眼洞椭圆。
    @keyword-en contour-candidates, edge-snap
    @keyword-cn 轮廓候选点, 边缘吸附
    """
    cands = [(math.copysign(mask_half(y), x), y), (x, -0.19)]
    if y > 0.085:
        a = math.atan2((y - 0.085) / 0.07, x / 0.13)
        cands.append((0.13 * math.cos(a), 0.085 + 0.07 * math.sin(a)))
    for ex, ey in MAIN_EYES:
        a = math.atan2((y - ey) / 0.021, (x - ex) / 0.03)
        cands.append((ex + 0.03 * math.cos(a), ey + 0.021 * math.sin(a)))
    return cands


# 面具上那道发丝裂纹（头部局部 x, y），碎面具也沿着这条线往下裂
MASK_CRACK = ((0.03, 0.15), (0.046, 0.118), (0.034, 0.092), (0.05, 0.068), (0.043, 0.056))


def _polyline_distance(x, y, points):
    """点到折线的最近距离。
    @keyword-en polyline-distance, point-to-path
    @keyword-cn 折线距离, 点到路径
    """
    best = 1e9
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        vx, vy = x1 - x0, y1 - y0
        t = min(max(((x - x0) * vx + (y - y0) * vy) / (vx * vx + vy * vy), 0.0), 1.0)
        best = min(best, math.hypot(x - (x0 + vx * t), y - (y0 + vy * t)))
    return best


def mask_paint(x, y):
    """面具上画的东西（顶点色，乘在白瓷上）：眼洞一圈黑眼线、眼下两道黑泪痕、腮红、
    一道缝着线的黑色细笑弧，还有一条发丝裂纹。线条都画粗一点，640×360 下还看得出来。
    @keyword-en mask-paint, painted-smile
    @keyword-cn 面具彩绘, 画上的笑
    """
    c = Vector((1.0, 1.0, 1.0))
    ink = Vector((0.05, 0.045, 0.045))
    for s, (ex, ey) in zip((-1.0, 1.0), MAIN_EYES):
        e = math.sqrt(((x - ex) / 0.03) ** 2 + ((y - ey) / 0.021) ** 2)
        c = c.lerp(ink, 1.0 - smoothstep(1.15, 1.8, e))
        wiggle = 0.003 * math.sin(y * 140.0 + s)
        if ey - 0.08 < y < ey - 0.012:
            fade = 1.0 - 0.7 * (ey - 0.012 - y) / 0.068
            c = c.lerp(ink, (1.0 - smoothstep(0.008, 0.011, abs(x - ex - wiggle))) * fade)
        c = c.lerp(Vector((0.85, 0.38, 0.38)), 0.65 * gauss(x - s * 0.088, y + 0.03, 0.022, 0.018))
    if abs(x) < 0.088:
        d = abs(y - (-0.112 + 2.6 * x * x))
        c = c.lerp(ink, 1.0 - smoothstep(0.01, 0.014, d))
        stitch = abs(((x + 0.088) % 0.0176) - 0.0088)
        c = c.lerp(ink, (1.0 - smoothstep(0.0016, 0.003, stitch)) * (1.0 - smoothstep(0.016, 0.02, d)))
    c = c.lerp(Vector((0.3, 0.28, 0.26)), 1.0 - smoothstep(0.0018, 0.0032, _polyline_distance(x, y, MASK_CRACK)))
    return c


def mask_shell(name, keep, contours, mat, offset=0.02, thickness=0.004, step=0.006):
    """面具壳：在头部正面 (x, y) 平面上铺一张 step 米的网格，keep(x, y) 为真的格子留下；
    边界上的顶点吸附到 contours(x, y) 给出的最近轮廓点（轮廓因此是光滑曲线而不是锯齿），
    然后每个顶点投影到光滑基本形上、沿法线外推 offset，顶点色按 mask_paint 上彩，最后实体化给出瓷片厚度。
    @keyword-en mask-shell, contour-snap
    @keyword-cn 面具壳, 轮廓吸附
    """
    nx, ny = int(0.29 / step), int(0.37 / step)
    params = [[(-0.145 + 0.29 * i / nx, -0.205 + 0.37 * j / ny) for j in range(ny + 1)] for i in range(nx + 1)]
    bm = bmesh.new()
    col = bm.verts.layers.float_color.new("Col")
    uv = bm.loops.layers.uv.new("UVMap")
    verts = {}
    for i in range(nx):
        for j in range(ny):
            corners = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            if not all(keep(*params[a][b]) for a, b in corners):
                continue
            for key in corners:
                if key not in verts:
                    verts[key] = bm.verts.new((0.0, 0.0, 0.0))
            bm.faces.new([verts[key] for key in corners])
    where = {v: params[a][b] for (a, b), v in verts.items()}
    for v in bm.verts:
        x, y = where[v]
        if v.is_boundary:
            x, y = min(contours(x, y), key=lambda c: math.hypot(c[0] - x, c[1] - y))
        hit = base_front(x, y)
        p, n = hit if hit is not None else (Vector((x, y, 0.06)), Vector((0, 0, 1)))
        v.co = kit.g(HEAD_CENTER + p + n * offset)
        v[col] = (*mask_paint(x, y), 1.0)
        where[v] = (x, y)
    for face in bm.faces:
        for loop in face.loops:
            x, y = where[loop.vert]
            loop[uv].uv = (x * 4.0 + 0.5, y * 4.0 + 0.5)
    obj = kit.mesh_object(name, bm, mat)
    obj.data.color_attributes.active_color = obj.data.color_attributes["Col"]
    mod = obj.modifiers.new("Solidify", "SOLIDIFY")
    mod.thickness = thickness
    mod.offset = -1.0
    kit.apply_all(obj)
    kit.smooth(obj, 40)
    return obj


def build_mask(mats):
    """形态一：整张白瓷面具，盖住咧嘴和额头的三只眼，只从两个眼洞里透出发光的瞳孔。
    @keyword-en porcelain-mask, form-one
    @keyword-cn 白瓷面具, 形态一
    """
    return mask_shell("Mask", mask_keep, mask_contours, mats["porcelain"])


def crack_x(y):
    """碎面具的裂口：沿 y 往下的锯齿折线，返回裂口在 y 处的 x（留下 x 更小的那半边）。
    @keyword-en crack-edge, jagged-line
    @keyword-cn 裂口, 锯齿线
    """
    pts = [(0.17, 0.03), (0.15, 0.03), (0.118, 0.046), (0.092, 0.034), (0.068, 0.05), (0.04, 0.0),
           (0.012, 0.02), (-0.015, -0.012), (-0.045, 0.006), (-0.07, -0.03), (-0.1, -0.012), (-0.13, -0.06)]
    for (y0, x0), (y1, x1) in zip(pts, pts[1:]):
        if y1 <= y <= y0:
            return x0 + (x1 - x0) * (y0 - y) / (y0 - y1)
    return -1.0


def build_mask_shard(mats):
    """形态二：面具碎掉大半，只剩右脸（画面左边）一块，沿裂纹的锯齿边，歪斜地挂在脸上，露出底下的笑。
    @keyword-en mask-shard, form-two
    @keyword-cn 碎面具, 形态二
    """
    shard = mask_shell("MaskShard", lambda x, y: mask_keep(x, y) and x < crack_x(y) and y > -0.115,
                       lambda x, y: mask_contours(x, y) + [(crack_x(y), y), (x, -0.115)],
                       mats["porcelain"], offset=0.022)
    pivot = kit.g(HEAD_CENTER + Vector((-0.07, 0.11, 0.15)))
    tilt = Matrix.Translation(pivot) @ Matrix.Rotation(0.16, 4, "Y") @ Matrix.Rotation(0.06, 4, "X") \
        @ Matrix.Translation(-pivot)
    shard.data.transform(tilt)
    return shard


def build_hat(mats):
    """形态一：黑色高礼帽，暗红缎带，帽檐两边微微上卷，往后歪一点戴在长颅上。
    @keyword-en top-hat, gentleman
    @keyword-cn 高礼帽, 绅士
    """
    base = HEAD_CENTER + Vector((0.0, 0.158, -0.035))
    crown = kit.lathe("Crown", [(0.108, 0.0), (0.11, 0.03), (0.116, 0.17), (0.12, 0.19)], base, "y",
                      mats["hat"], segments=20)
    brim = kit.lathe("Brim", [(0.108, 0.006), (0.17, 0.0), (0.19, 0.008), (0.197, 0.022), (0.189, 0.019),
                              (0.165, 0.011), (0.108, 0.015)], base, "y", mats["hat"], segments=24)
    band = kit.lathe("Band", [(0.1135, 0.015), (0.1175, 0.052)], base, "y", mats["tie"], segments=20)
    hat = kit.join([crown, brim, band], "Hat")
    kit.box_uv(hat, 0.2)
    pivot = kit.g(base)
    hat.data.transform(Matrix.Translation(pivot) @ Matrix.Rotation(-0.14, 4, "X") @ Matrix.Translation(-pivot))
    kit.smooth(hat, 50)
    return hat


def build_horns(mats):
    """形态三：沿头顶骨冠长出一排向后弯的骨刺，两边太阳穴各一根往上往后卷的大骨角。
    @keyword-en bone-horns, form-three
    @keyword-cn 骨角, 形态三
    """
    parts = []
    back = Vector((0.0, 0.25, -1.0)).normalized()
    for k, theta in enumerate((1.0, 1.35, 1.7, 2.05, 2.4)):
        root, n = sculpt_point((0.0, math.sin(theta), math.cos(theta)), -0.006)
        d = (n * 0.75 + back * 0.6).normalized()
        length = 0.075 + 0.03 * math.sin(math.pi * (k + 0.5) / 5.0)
        pts = [root, root + d * length * 0.5, root + d * length + back * length * 0.25]
        parts.append(kit.tentacle("Spike", [HEAD_CENTER + p for p in pts], 0.016, 0.0015, mats["bone"],
                                  sway=0.0, segments=7, steps=4))
    for s in (-1.0, 1.0):
        root, _ = sculpt_point((s * 0.72, 0.55, 0.4), -0.012)
        offsets = [(0, 0, 0), (s * 0.05, 0.05, -0.01), (s * 0.1, 0.12, -0.05), (s * 0.12, 0.2, -0.12),
                   (s * 0.1, 0.26, -0.2), (s * 0.06, 0.28, -0.25)]
        parts.append(kit.tentacle("Horn", [HEAD_CENTER + root + Vector(o) for o in offsets], 0.03, 0.003,
                                  mats["bone"], sway=0.0, segments=9, steps=5))
    horns = kit.join(parts, "Horns")
    kit.smooth(horns, 60)
    return horns


def build_veins(mats, surface):
    """形态三：脸上鼓起的发光绿血管，从脸中间往外随机蜿蜒，绕开眼窝和嘴。
    surface(x, y) 返回头部表面点和法线（头部局部坐标）。
    @keyword-en glowing-veins, face-veins
    @keyword-cn 发光血管, 脸部血管
    """
    rnd = random.Random(41)
    starts = [(-0.1, -0.055), (0.1, -0.05), (-0.045, 0.12), (0.05, 0.125), (-0.12, 0.04), (0.12, 0.05),
              (0.0, 0.15), (-0.035, -0.16), (0.04, -0.158)]
    parts = []
    for k, (x, y) in enumerate(starts):
        a = math.atan2(y, x) + rnd.uniform(-0.5, 0.5)
        pts = []
        for _ in range(9):
            p, n = surface(x, y)
            pts.append(HEAD_CENTER + p + n * 0.0025)
            a += rnd.uniform(-0.6, 0.6)
            x, y = x + math.cos(a) * 0.016, y + math.sin(a) * 0.016
            for ex, ey in MAIN_EYES:
                if math.hypot(x - ex, y - ey) < 0.04:
                    x, y = x + (x - ex) * 0.4, y + (y - ey) * 0.4
            if abs(y - smile_y(x)) < smile_h(x) + 0.012 and abs(x) < 0.13:
                y += 0.02 if y > smile_y(x) else -0.02
            y = max(-0.19, min(0.18, y))
            limit = 0.85 * head_half_width(y)
            x = max(-limit, min(limit, x))
        parts.append(kit.tentacle("Vein%d" % k, pts, 0.0038, 0.0012, mats["vein_glow"], sway=0.0, segments=5, steps=3))
    return kit.join(parts, "Veins")


def build_beard(mats, surface, long=False):
    """下颌和下巴上长出的触手须（11 根）：外圈 6 根沿下颌两侧、内圈 5 根在下巴，垂到胸口，尖端向外卷起。
    long 为 True 时是形态三多长出来的 5 根粗长触手（BeardLong），插在原来那些中间，一直垂到桌边。
    surface(x, y) 返回头部表面点和法线（头部局部坐标）。触手按 kit.tentacle 的约定带摆动相位和幅度。
    @keyword-en tentacle-beard, cthulhu-jaw
    @keyword-cn 触手须, 克苏鲁下颌
    """
    rnd = random.Random(31 if long else 23)
    roots = []
    if long:
        for t in (-0.9, -0.5, 0.5, 0.9):
            x = 0.068 * t
            roots.append((x, smile_y(x) - smile_h(x) - 0.034 - 0.03 * (1.0 - abs(t)), t, 0.03))
    else:
        for t in (-1.0, -0.62, -0.25, 0.25, 0.62, 1.0):
            x = 0.078 * t
            roots.append((x, smile_y(x) - smile_h(x) - 0.024 - 0.02 * (1.0 - abs(t)), t, 0.026))
        for t in (-1.0, -0.5, 0.0, 0.5, 1.0):
            roots.append((0.042 * t, -0.168 - 0.014 * (1.0 - abs(t)), t * 0.5, 0.022))
    tentacles = []
    for i, (x, y, t, radius) in enumerate(roots):
        p, n = surface(x, y)
        root = HEAD_CENTER + p - n * 0.007
        length = (0.24 + 0.13 * (1.0 - abs(t)) + rnd.uniform(-0.025, 0.025)) * (1.6 if long else 1.0)
        side = math.copysign(1.0, x) if abs(x) > 1e-4 else rnd.choice((-1.0, 1.0))
        spread = x * (2.4 if long else 0.9)
        # 垂下来，末端向外打一个小卷
        offsets = [(0.0, 0.0, 0.0), (spread * 0.15, -0.04, 0.03), (spread * 0.5, -length * 0.4, 0.045),
                   (spread * 0.85, -length * 0.7, 0.052), (spread + side * 0.025, -length * 0.88, 0.058),
                   (spread + side * 0.055, -length * 0.93, 0.07), (spread + side * 0.07, -length * 0.86, 0.078),
                   (spread + side * 0.058, -length * 0.8, 0.072)]
        pts = [root + Vector(o) for o in offsets]
        tentacles.append(kit.tentacle(("BeardLong%d" if long else "Beard%d") % i, pts, radius, 0.003,
                                      mats["tentacle"], phase=rnd.random(), sway=rnd.uniform(0.014, 0.024),
                                      segments=8, steps=5, suckers=(0, -0.3, -1)))
    return tentacles


def tentacle_path(root, angle, length, rnd, reach=0.34):
    """一根从背后长出的大触手的控制点：沿 angle（与竖直方向的夹角）伸出 length，
    中段左右 S 形扭动，越往尖端越朝玩家这边探（reach 米）并往下垂，最后向内打一个卷。
    @keyword-en tentacle-path, s-curve
    @keyword-cn 触手路径, S形曲线
    """
    d = Vector((math.sin(angle), math.cos(angle), 0.0))
    side = Vector((math.cos(angle), -math.sin(angle), 0.0))
    phase = rnd.uniform(0.0, math.tau)
    pts = []
    for f in (0.0, 0.14, 0.28, 0.42, 0.56, 0.68, 0.8, 0.9):
        wiggle = side * 0.07 * math.sin(f * math.tau * 0.9 + phase) * min(1.0, f * 2.0)
        lean = Vector((0.0, -0.18 * f ** 3, reach * f ** 1.6 - 0.05 * math.sin(f * math.pi)))
        pts.append(root + d * length * f + wiggle + lean)
    tip = pts[-1]
    pts.append(tip + d * 0.03 - side * 0.05 + Vector((0.0, -0.06, 0.05)))
    pts.append(tip - side * 0.08 + Vector((0.0, -0.1, 0.04)))
    return pts


def build_back_tentacles(mats, form):
    """从背后、肩膀后面长出来的大触手，越过肩头朝玩家这边卷过来：形态二 2 根，形态三 6 根像光环一样张开。
    游戏里由触手着色器摆动，受击时会剧烈抽动。
    @keyword-en back-tentacles, tentacle-halo
    @keyword-cn 背后触手, 触手光环
    """
    rnd = random.Random(50 + form)
    parts = []
    if form == 2:
        specs = ((-34, 0.95, 0.045), (30, 1.0, 0.045))
    else:
        specs = ((-76, 0.98, 0.06), (-50, 1.12, 0.062), (-22, 1.04, 0.055), (12, 1.08, 0.058), (40, 1.15, 0.062),
                 (68, 0.95, 0.058))
    for deg, length, radius in specs:
        a = math.radians(deg)
        root = Vector((math.copysign(0.1, deg) + 0.08 * math.sin(a), 0.5, -1.47))
        pts = tentacle_path(root, a, length, rnd, reach=0.3 if form == 2 else 0.38)
        parts.append(kit.tentacle("BackTentacle", pts, radius, 0.004, mats["tentacle"], phase=rnd.random(),
                                  sway=rnd.uniform(0.045, 0.07), segments=10, steps=6, suckers=(0, 0, 1)))
    tentacles = kit.join(parts, "BackTentacles%d" % form)
    kit.set_origin(tentacles, (0.0, 0.5, -1.47))
    return tentacles


def flesh_ring(name, center, rx, ry, tube, mat, seed=0, segments=28, sides=8):
    """一圈粗细不匀的肉唇：沿椭圆 (rx, ry)（Godot x-y 平面，朝 +z）扫一根管子，管径随机起伏。
    @keyword-en flesh-ring, wound-lips
    @keyword-cn 肉唇, 伤口边缘
    """
    rnd = random.Random(seed)
    wobble = [1.0 + rnd.uniform(-0.3, 0.35) for _ in range(segments)]
    bm = bmesh.new()
    rings = []
    for i in range(segments):
        t = 2.0 * math.pi * i / segments
        p = center + Vector((rx * math.cos(t), ry * math.sin(t), 0.0))
        n = Vector((math.cos(t) / rx, math.sin(t) / ry, 0.0)).normalized()
        r = tube * (wobble[i - 1] + 2.0 * wobble[i] + wobble[(i + 1) % segments]) / 4.0
        rings.append([bm.verts.new(kit.g(p + (n * math.cos(a) + Vector((0, 0, 1)) * math.sin(a)) * r))
                      for a in (2.0 * math.pi * k / sides for k in range(sides))])
    for i in range(segments):
        a, b = rings[i], rings[(i + 1) % segments]
        for k in range(sides):
            bm.faces.new((a[k], a[(k + 1) % sides], b[(k + 1) % sides], b[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit.mesh_object(name, bm, mat)


def ellipse_disc(name, center, rx, ry, mat, segments=24):
    """朝 +z 的实心椭圆片（伤口里黑洞洞的底）。
    @keyword-en ellipse-disc, wound-backing
    @keyword-cn 椭圆片, 伤口底
    """
    bm = bmesh.new()
    mid = bm.verts.new(kit.g(center))
    ring = [bm.verts.new(kit.g(center + Vector((rx * math.cos(t), ry * math.sin(t), 0.0))))
            for t in (2.0 * math.pi * i / segments for i in range(segments))]
    for i in range(segments):
        bm.faces.new((mid, ring[i], ring[(i + 1) % segments]))
    return kit.mesh_object(name, bm, mat)


def build_chest(mats):
    """形态三：西装胸口裂开一道竖着的肉缝，一圈肉唇和朝里的尖牙，里面一只发光的大眼（ChestEye，游戏里会盯着玩家转）。
    返回 (ChestRift, ChestEye)，各自原点在眼睛中心。
    @keyword-en chest-eye, chest-rift
    @keyword-cn 胸口之眼, 胸口裂缝
    """
    c = CHEST_EYE
    parts = [flesh_ring("RiftLips", c + Vector((0, 0, 0.014)), 0.074, 0.11, 0.02, mats["flesh"], seed=3),
             ellipse_disc("RiftHole", c + Vector((0, 0, -0.008)), 0.074, 0.11, mats["mouth"])]
    for k in range(14):
        t = 2.0 * math.pi * (k + 0.5) / 14.0
        rim = c + Vector((0.074 * math.cos(t), 0.11 * math.sin(t), 0.024))
        tip = c + Vector((0.054 * math.cos(t), 0.084 * math.sin(t), 0.036))
        parts.append(cone_between("RiftTooth", rim, tip, 0.0055, mats["teeth"], 5))
    rift = kit.join(parts, "ChestRift")
    kit.box_uv(rift, 0.15)
    kit.smooth(rift, 50)
    kit.set_origin(rift, c)
    eye = kit.join([kit.sphere("Sclera", 0.062, c, mats["eye_white"], segments=18, rings=10),
                    kit.sphere("Iris", 0.037, c + Vector((0, 0, 0.047)), mats["iris_glow"], segments=16, rings=8,
                               scale=(1.0, 1.0, 0.4)),
                    kit.box("Slit", (0.009, 0.052, 0.007), c + Vector((0, 0, 0.0625)), mats["black"])], "ChestEye")
    kit.box_uv(eye, 0.15)
    kit.smooth(eye, 50)
    kit.set_origin(eye, c)
    return rift, eye


def build_hand(name, center, side, mats):
    """构建一只平放、长指、关节突出的骨感手掌。
    @keyword-en skeletal-hand, articulated-fingers
    @keyword-cn 骨感手掌, 分节手指
    """
    cx, cy, cz = center
    parts = [
        kit.sphere("Palm", 0.055, (cx, cy + 0.023, cz + 0.010), mats["skin"], segments=10, rings=5, scale=(1.0, 0.42, 1.25)),
        cylinder_between("Wrist", (cx, cy + 0.025, cz - 0.080), (cx, cy + 0.025, cz - 0.010), 0.038, mats["skin"], 6, 0.045),
    ]
    finger_x = (-0.040, -0.014, 0.014, 0.040)
    lengths = (0.095, 0.125, 0.118, 0.100)
    for index, (offset, length) in enumerate(zip(finger_x, lengths)):
        start = Vector((cx + offset, cy + 0.026, cz + 0.045))
        bend = 0.010 + 0.004 * abs(index - 1.5)
        points = [start,
                  start + Vector((offset * 0.05, -0.003, length * 0.40)),
                  start + Vector((offset * 0.10, -0.009, length * 0.72)),
                  start + Vector((offset * 0.14, -bend, length))]
        for joint in range(3):
            parts.append(cylinder_between("Finger", points[joint], points[joint + 1], 0.010 - joint * 0.0016,
                                          mats["skin"], 6, 0.009 - joint * 0.0015))
            if joint < 2:
                parts.append(kit.sphere("Knuckle", 0.011 - joint * 0.001, points[joint + 1], mats["skin"], segments=6, rings=3,
                                        scale=(1.05, 0.65, 1.0)))
        nail_start = points[-1] + Vector((0, 0.005, -0.005))
        nail_end = points[-1] + Vector((0, -0.008, 0.026))
        parts.append(cone_between("Claw", nail_start, nail_end, 0.0058, mats["claw"], 5))
    thumb_dir = side
    thumb_start = Vector((cx + thumb_dir * 0.040, cy + 0.024, cz + 0.010))
    thumb_mid = thumb_start + Vector((thumb_dir * 0.038, -0.004, 0.032))
    thumb_tip = thumb_mid + Vector((thumb_dir * 0.018, -0.008, 0.030))
    parts.append(cylinder_between("Thumb", thumb_start, thumb_mid, 0.012, mats["skin"], 6, 0.010))
    parts.append(cylinder_between("Thumb", thumb_mid, thumb_tip, 0.010, mats["skin"], 6, 0.007))
    parts.append(cone_between("Claw", thumb_tip + Vector((0, 0.004, -0.003)), thumb_tip + Vector((thumb_dir * 0.004, -0.007, 0.022)),
                              0.0055, mats["claw"], 5))
    hand = kit.join(parts, name)
    kit.fill_color(hand, (1.0, 1.0, 1.0))
    kit.box_uv(hand, 0.25)
    kit.smooth(hand, 42)
    kit.set_origin(hand, center)
    return hand


# 手臂两段长度和肘部弯曲方向，必须和 scripts/table_scene.gd 的 UPPER_ARM / FOREARM / ELBOW_POLES 一致
UPPER_ARM = 0.48
FOREARM = 0.5
SHOULDERS = ((-0.36, 0.62, -1.28), (0.36, 0.62, -1.28))
ELBOW_POLES = ((-0.8, -1.0, -0.25), (0.8, -1.0, -0.25))
# 握拳手里被握住的杆的半径；手腕（前臂末端）在握拳手本地坐标里的位置，和 table_scene.gd 的 FIST_WRIST 一致
FIST_BAR = 0.032
FIST_WRIST = (0.0, -0.085, -0.062)


def build_arm_segment(name, profile, mats, cuff=False):
    """手臂的一段（上臂或前臂）：沿本地 Y 轴长 1 米、原点居中的袖管，-y 端是近端（肩或肘）。
    游戏每帧把它拉伸到两个关节之间；cuff 为 True 时 +y 端露一圈衬衫袖口（前臂）。
    @keyword-en arm-segment, unit-sleeve
    @keyword-cn 手臂分段, 单位袖管
    """
    parts = [kit.lathe("Sleeve", profile, (0, 0, 0), "y", mats["cloth"], segments=16)]
    if cuff:
        r = profile[-1][0] + 0.002
        parts.append(kit.lathe("Cuff", [(r, 0.44), (r, 0.5)], (0, 0, 0), "y", mats["shirt"], segments=16))
    arm = kit.join(parts, name)
    kit.box_uv(arm, 0.35)
    kit.fill_color(arm, (1.0, 1.0, 1.0))
    kit.smooth(arm, 40)
    kit.set_origin(arm, (0, 0, 0))
    return arm


def build_elbow(name, mats):
    """肘关节：一个袖子布料的球，游戏每帧放到肘部，盖住上臂和前臂的接缝。
    @keyword-en elbow-joint, sleeve-ball
    @keyword-cn 肘关节, 关节球
    """
    elbow = kit.sphere(name, 0.053, (0, 0, 0), mats["cloth"], segments=12, rings=6)
    kit.apply_all(elbow)
    kit.box_uv(elbow, 0.35)
    kit.fill_color(elbow, (1.0, 1.0, 1.0))
    return elbow


def fist_point(x, phi, radius):
    """握拳手指绕杆的位置：杆沿本地 X 轴，phi 从掌心一侧（-Z）经顶部（+Y）转到前面（+Z）再到底下。
    @keyword-en fist-curl, finger-arc
    @keyword-cn 握拳弧线, 手指弯曲
    """
    a = math.radians(phi)
    return Vector((x, radius * math.sin(a), -radius * math.cos(a)))


def build_fist(name, side, mats):
    """握拳的手（握枪用）：握住一根沿本地 X 轴、半径 FIST_BAR 的杆，原点在杆的中心；
    手背在杆后面（-Z），四指从顶上绕到前面再勾回来，指尖是黑色长爪，拇指从下面绕过来（side 决定在 ±X 哪边），
    手腕朝下后方，末端在 FIST_WRIST。
    @keyword-en gripping-fist, gun-grip-hand
    @keyword-cn 握拳手, 握枪手
    """
    radius = FIST_BAR + 0.0095
    parts = [kit.sphere("Back", 0.05, (0, -0.012, -radius - 0.008), mats["skin"], segments=12, rings=6,
                        scale=(0.92, 1.0, 0.36))]
    fingers = ((-0.033, 205), (-0.011, 245), (0.011, 240), (0.033, 215))
    for x, end in fingers:
        angles = [38, 95, 150, end]
        pts = [fist_point(x, a, radius - 0.001 * k) for k, a in enumerate(angles)]
        for k in range(3):
            parts.append(cylinder_between("Finger", pts[k], pts[k + 1], 0.0098 - k * 0.0012, mats["skin"], 6,
                                          0.0088 - k * 0.0012))
            parts.append(kit.sphere("Knuckle", 0.0108 - k * 0.0012, pts[k], mats["skin"], segments=6, rings=3))
        a = math.radians(end)
        tangent = Vector((0, math.cos(a), math.sin(a)))
        parts.append(cone_between("Claw", pts[-1], pts[-1] + tangent * 0.022, 0.0062, mats["claw"], 5))
    thumb = [Vector((side * 0.042, -0.03, -0.042)), Vector((side * 0.04, -radius * 0.95, -0.006)),
             Vector((side * 0.028, -radius * 0.72, radius * 0.6))]
    parts.append(cylinder_between("Thumb", thumb[0], thumb[1], 0.0115, mats["skin"], 6, 0.0105))
    parts.append(cylinder_between("Thumb", thumb[1], thumb[2], 0.0105, mats["skin"], 6, 0.0085))
    parts.append(kit.sphere("ThumbJoint", 0.012, thumb[1], mats["skin"], segments=6, rings=3))
    parts.append(cone_between("Claw", thumb[2], thumb[2] + (thumb[2] - thumb[1]).normalized() * 0.02, 0.006,
                              mats["claw"], 5))
    parts.append(cylinder_between("Wrist", Vector((0, -0.045, -0.047)), Vector(FIST_WRIST), 0.036, mats["skin"],
                                  8, 0.033))
    for p in parts:
        kit.box_uv(p, 0.25)
    fist = kit.join(parts, name)
    kit.fill_color(fist, (1.0, 1.0, 1.0))
    kit.smooth(fist, 50)
    kit.set_origin(fist, (0, 0, 0))
    return fist


def solve_elbow(shoulder, wrist, pole):
    """两段手臂的解析 IK（和 table_scene.gd 的 _solve_arm 同一算法）：返回肘部位置，够不着时沿直线拉长。
    @keyword-en two-bone-ik, elbow-solve
    @keyword-cn 两段IK, 肘部求解
    """
    s, w, pole = Vector(shoulder), Vector(wrist), Vector(pole)
    to = w - s
    d = to.length
    direction = to / d
    if d >= UPPER_ARM + FOREARM:
        return s + direction * UPPER_ARM * d / (UPPER_ARM + FOREARM)
    cos_a = max(-1.0, min(1.0, (UPPER_ARM ** 2 + d * d - FOREARM ** 2) / (2 * UPPER_ARM * d)))
    perp = (pole - direction * direction.dot(pole)).normalized()
    return s + direction * UPPER_ARM * cos_a + perp * UPPER_ARM * math.sqrt(1 - cos_a * cos_a)


def place_segment(obj, start, end):
    """仅为预览把单位长的手臂段摆到两点之间（Godot 坐标）。
    @keyword-en preview-segment, place-between
    @keyword-cn 预览手臂段, 两点摆放
    """
    a, b = kit.g(start), kit.g(end)
    obj.location = (a + b) / 2
    obj.rotation_euler = Vector((0, 0, 1)).rotation_difference((b - a).normalized()).to_euler()
    obj.scale = (1.0, 1.0, (b - a).length)


def reset_transform(obj):
    """把物体恢复到导出所需的原点、零旋转、单位缩放。
    @keyword-en reset-transform, export-ready
    @keyword-cn 重置变换, 导出就绪
    """
    obj.location = (0, 0, 0)
    obj.rotation_euler = (0, 0, 0)
    obj.scale = (1, 1, 1)


def show_form(form):
    """预览用：只让某个形态的部件参与渲染（不在 FORM_NODES 里的节点不受影响）。
    @keyword-en preview-form, form-visibility
    @keyword-cn 预览形态, 形态显示
    """
    for name in FORM_PART_NAMES:
        obj = bpy.data.objects.get(name)
        if obj is not None:
            obj.hide_render = name not in FORM_NODES[form]


def render_previews(objects):
    """渲染三个形态各一张玩家视角（手放桌上，手臂按 IK 弯肘）和头部 3/4 特写，
    再加不带形态部件的头部正面、侧面，以及握拳手的检查图。
    @keyword-en dealer-previews, visual-inspection
    @keyword-cn 行刑人预览, 视觉检查
    """
    posed = []
    for i, side in enumerate("LR"):
        wrist = Vector(((-0.3, 0.3)[i], 0.04, -0.82))
        elbow = solve_elbow(SHOULDERS[i], wrist, ELBOW_POLES[i])
        place_segment(objects["UpperArm" + side], SHOULDERS[i], elbow)
        place_segment(objects["Forearm" + side], elbow, wrist)
        objects["Elbow" + side].location = kit.g(elbow)
        posed += [objects["UpperArm" + side], objects["Forearm" + side], objects["Elbow" + side]]
    for side in "LR":
        objects["Grip" + side].hide_render = True
    for form in (1, 2, 3):
        show_form(form)
        kit.render_preview("dealer/player_view_form%d.png" % form, direction=(0, 0.30, 2.30), target=(0, 0.68, -1.1),
                           distance=2.6, fov=56, resolution=(768, 512))
    for obj in posed:
        reset_transform(obj)

    head_parts = {objects["Head"]} | set(objects["Head"].children)
    for obj in bpy.context.scene.objects:
        if obj not in head_parts:
            obj.hide_render = True
    for form in (1, 2, 3):
        show_form(form)
        kit.render_preview("dealer/head_form%d.png" % form, direction=(0.55, 0.12, 1.0), target=(0, 1.04, -1.15),
                           distance=1.05, fov=34, resolution=(640, 640), objs=[objects["Head"]])
    for name in FORM_PART_NAMES:
        obj = bpy.data.objects.get(name)
        if obj is not None:
            obj.hide_render = True
    kit.render_preview("dealer/head_front.png", direction=(0, 0.02, 1.0), target=(0, 1.0, -1.13),
                       distance=0.92, fov=30, resolution=(640, 640), objs=[objects["Head"]])
    kit.render_preview("dealer/head_side.png", direction=(1.0, 0.02, 0.08), target=(0, 1.0, -1.17),
                       distance=0.92, fov=30, resolution=(640, 640), objs=[objects["Head"]])
    for obj in head_parts:
        obj.hide_render = True
    objects["GripR"].hide_render = False
    bar = kit.cylinder("PreviewBar", FIST_BAR, 0.24, (0, 0, 0), "x", kit.material("metal_dark", (0.15, 0.15, 0.17)))
    kit.render_preview("dealer/fist.png", direction=(0.5, 0.35, 1.0), target=(0, -0.02, 0), distance=0.42,
                       fov=35, resolution=(640, 512), objs=[objects["GripR"], bar])
    bpy.data.objects.remove(bar, do_unlink=True)
    for obj in bpy.context.scene.objects:
        obj.hide_render = False


def print_statistics(objects):
    """打印各逻辑节点与头部组合的三角面数统计。
    @keyword-en dealer-statistics, triangle-budget
    @keyword-cn 行刑人统计, 三角面预算
    """
    for name, obj in objects.items():
        print(f"TRIS {name} {kit.triangle_count([obj])}")
        for child in obj.children:
            print(f"TRIS {name}/{child.name} {kit.triangle_count([child])}")


def main():
    """重置场景、构建全部节点、导出 GLB 并生成预览。
    @keyword-en build-dealer, export-dealer
    @keyword-cn 构建行刑人, 导出行刑人
    """
    kit.reset_scene()
    mats = create_materials()
    objects = {
        "Chair": build_chair(mats),
        "Body": None,
        "Head": build_head(mats),
        "HandL": build_hand("HandL", (-0.3, 0.015, -0.74), 1, mats),
        "HandR": build_hand("HandR", (0.3, 0.015, -0.74), -1, mats),
        "GripL": build_fist("GripL", 1, mats),
        "GripR": build_fist("GripR", -1, mats),
        "BackTentacles2": build_back_tentacles(mats, 2),
        "BackTentacles3": build_back_tentacles(mats, 3),
    }
    objects["Body"], objects["WatchChain"] = build_body(mats)
    objects["ChestRift"], objects["ChestEye"] = build_chest(mats)
    # 袖管轮廓带几道起伏，像布料在肘弯和小臂上堆出的褶
    upper = [(0.058, -0.5), (0.06, -0.42), (0.055, -0.3), (0.057, -0.2), (0.052, -0.05), (0.054, 0.1),
             (0.05, 0.25), (0.052, 0.38), (0.049, 0.5)]
    fore = [(0.051, -0.5), (0.049, -0.38), (0.052, -0.28), (0.047, -0.12), (0.049, 0.0), (0.045, 0.18),
            (0.047, 0.3), (0.044, 0.44)]
    for side in "LR":
        objects["UpperArm" + side] = build_arm_segment("UpperArm" + side, upper, mats)
        objects["Forearm" + side] = build_arm_segment("Forearm" + side, fore, mats, cuff=True)
        objects["Elbow" + side] = build_elbow("Elbow" + side, mats)
    print_statistics(objects)
    kit.export_glb(list(objects.values()), "dealer.glb", vertex_color="ACTIVE")
    render_previews(objects)


if __name__ == "__main__":
    main()
