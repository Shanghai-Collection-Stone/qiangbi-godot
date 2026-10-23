"""构建雷明顿 870 风格低多边形泵动霰弹枪并导出 ``art/models/shotgun.glb``。

同时渲染侧视、右前上方和锯短状态预览到 ``art/source/previews/gun/``。
运行：blender -b --factory-startup --python art/blender/build_shotgun.py
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit


def prism_x(name, profile, width, mat, bevel=0.0):
    """把 Godot y-z 平面轮廓挤成沿 x 轴有厚度的硬表面零件。
    @keyword-en profile-extrusion, hard-surface
    @keyword-cn 轮廓挤出, 硬表面
    """
    count = len(profile)
    verts = []
    for x in (-width / 2.0, width / 2.0):
        verts.extend([kit.g(x, y, z) for y, z in profile])
    faces = [tuple(range(count - 1, -1, -1)), tuple(range(count, count * 2))]
    for i in range(count):
        j = (i + 1) % count
        faces.append((i, j, count + j, count + i))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    kit.assign(obj, mat)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    if bevel:
        kit.add_bevel(obj, bevel, 2)
    return obj


def path_tube(name, points, radius, mat, closed=False, sides=6):
    """沿 Godot y-z 平面路径生成细管，用于扳机护圈和弯曲扳机。
    @keyword-en path-tube, trigger-geometry
    @keyword-cn 路径圆管, 扳机几何
    """
    verts = []
    rings = []
    total = len(points)
    for index, (y, z) in enumerate(points):
        prev = points[(index - 1) % total] if closed or index > 0 else points[index]
        nxt = points[(index + 1) % total] if closed or index < total - 1 else points[index]
        tangent = Vector((nxt[0] - prev[0], nxt[1] - prev[1])).normalized()
        normal = Vector((-tangent.y, tangent.x))
        ring = []
        for side in range(sides):
            angle = 2.0 * math.pi * side / sides
            x = radius * math.sin(angle)
            offset = radius * math.cos(angle)
            ring.append(len(verts))
            verts.append(kit.g(x, y + normal.x * offset, z + normal.y * offset))
        rings.append(ring)
    faces = []
    links = total if closed else total - 1
    for index in range(links):
        nxt = (index + 1) % total
        for side in range(sides):
            side2 = (side + 1) % sides
            faces.append((rings[index][side], rings[index][side2], rings[nxt][side2], rings[nxt][side]))
    if not closed:
        faces.extend((tuple(reversed(rings[0])), tuple(rings[-1])))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    kit.assign(obj, mat)
    return obj


def catmull(keys, t):
    """在 [(t, 值), ...] 关键点之间做 Catmull-Rom 插值（两端钳住），让枪托轮廓线平滑无折角。
    @keyword-en catmull-rom, smooth-curve
    @keyword-cn 样条插值, 平滑曲线
    """
    ts = [k[0] for k in keys]
    i = max(0, min(len(keys) - 2, next((j for j in range(len(ts) - 1) if t <= ts[j + 1]), len(ts) - 2)))
    p0 = keys[max(i - 1, 0)][1]
    p1, p2 = keys[i][1], keys[i + 1][1]
    p3 = keys[min(i + 2, len(keys) - 1)][1]
    u = (t - ts[i]) / (ts[i + 1] - ts[i])
    return 0.5 * (2 * p1 + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u
                  + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)


def loft_rings(name, rings, mat, grain_axis):
    """把截面环（Godot 坐标点列，所有环点数相同）放样成两端封口的网格。
    UV：u 沿截面周长，v 沿 grain_axis（Godot 方向向量）投影，木纹顺着枪托长度方向，1 UV = 0.3 米。
    @keyword-en loft-rings, wood-grain-uv
    @keyword-cn 截面放样, 木纹UV
    """
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    vs = [[bm.verts.new(kit.g(p)) for p in ring] for ring in rings]
    n = len(rings[0])
    axis = Vector(grain_axis).normalized()

    def coords(ring_index, i):
        """第 ring_index 个截面第 i 个点的 UV（u 沿周长，v 沿木纹轴）。
        @keyword-en ring-uv, grain-coords
        @keyword-cn 截面UV, 木纹坐标
        """
        p = Vector(rings[ring_index][i % n])
        return (i / n * 0.45, p.dot(axis) / 0.3)

    for r in range(len(rings) - 1):
        for i in range(n):
            face = bm.faces.new((vs[r][i], vs[r][(i + 1) % n], vs[r + 1][(i + 1) % n], vs[r + 1][i]))
            for loop, (rr, ii) in zip(face.loops, ((r, i), (r, i + 1), (r + 1, i + 1), (r + 1, i))):
                loop[uv].uv = coords(rr, ii)
    for ring, flip in ((vs[0], True), (vs[-1], False)):
        face = bm.faces.new(list(reversed(ring)) if flip else ring)
        for loop in face.loops:
            loop[uv].uv = (loop.vert.co.x / 0.3, loop.vert.co.z / 0.3)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit.mesh_object(name, bm, mat)


def rounded_section(center, right, up, half_w, half_h, segments=16, power=2.5):
    """圆角矩形截面：center 为中心，right/up 为截面平面内的两根 Godot 单位向量。
    @keyword-en rounded-section, superellipse
    @keyword-cn 圆角截面, 超椭圆
    """
    pts = []
    for i in range(segments):
        a = 2.0 * math.pi * i / segments
        c, s = math.cos(a), math.sin(a)
        x = half_w * math.copysign(abs(c) ** (2.0 / power), c)
        y = half_h * math.copysign(abs(s) ** (2.0 / power), s)
        pts.append(tuple(Vector(center) + Vector(right) * x + Vector(up) * y))
    return pts


def build_stock(mats):
    """枪托：主体沿 z 放样（上沿 comb 斜线、下沿斜向托踵、握把颈收细），
    下沿在握把处弯下成为手枪握把、后面收出腹部凹弧，托底接黑色橡胶底板。
    @keyword-en lofted-stock, pistol-grip
    @keyword-cn 放样枪托, 手枪握把
    """
    top = [(0.14, 0.032), (0.17, 0.012), (0.25, -0.002), (0.462, -0.012)]
    # 下沿：从机匣下方弯下去成为手枪握把，握把后面向上收（腹部的凹弧），再一路斜到托踵
    bottom = [(0.14, -0.04), (0.165, -0.085), (0.195, -0.122), (0.215, -0.127), (0.235, -0.11),
              (0.27, -0.093), (0.33, -0.1), (0.462, -0.132)]
    half = [(0.14, 0.024), (0.18, 0.0175), (0.21, 0.0185), (0.30, 0.02), (0.462, 0.022)]
    rings = []
    for k in range(25):
        # 站点前密后疏：握把一带曲线变化快
        z = 0.14 + (0.462 - 0.14) * (k / 24) ** 1.3
        t, b = catmull(top, z), catmull(bottom, z)
        rings.append(rounded_section((0, (t + b) / 2, z), (1, 0, 0), (0, 1, 0), catmull(half, z), (t - b) / 2))
    stock = loft_rings("Stock", rings, mats["wood"], (0, 0, 1))

    last = rings[-1]
    pad = loft_rings("ButtPad", [last, [(x, y, z + 0.018) for x, y, z in last]], mats["rubber"], (0, 0, 1))
    parts = [stock, pad]
    for y in (-0.035, -0.055, -0.075, -0.095, -0.115):
        parts.append(kit.box("PadRib", (0.04, 0.003, 0.003), (0, y, 0.4805), mats["rubber"]))
    return parts


def ordered_slots(obj, materials):
    """按游戏约定重排并去重网格材质槽，同时保持每个面的材质归属。
    @keyword-en material-order, surface-slots
    @keyword-cn 材质排序, 表面槽位
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


def make_materials():
    """创建霰弹枪所需的全部命名材质和预览参数。
    @keyword-en shotgun-materials, preview-shading
    @keyword-cn 霰弹枪材质, 预览着色
    """
    return {
        "metal": kit.material("metal", (0.3, 0.31, 0.33), 0.4, 0.8, preview_texture="metal.png"),
        "metal_dark": kit.material("metal_dark", (0.15, 0.15, 0.17), 0.5, 0.7, preview_texture="metal.png"),
        "wood": kit.material("wood", (0.35, 0.18, 0.08), 0.6, 0.0, preview_texture="wood.png"),
        "rubber": kit.material("rubber", (0.03, 0.03, 0.03), 0.9, 0.0),
        "brass": kit.material("brass", (0.8, 0.6, 0.22), 0.35, 0.8),
        "black": kit.material("black", (0.005, 0.005, 0.005), 1.0, 0.0),
    }


def build_body(mats):
    """构建机匣、后段双管、扳机组、木枪托与橡胶底板并合并为 Body。
    @keyword-en shotgun-body, receiver-stock
    @keyword-cn 枪身主体, 机匣枪托
    """
    parts = []
    receiver_profile = [
        (-0.0375, -0.10), (0.025, -0.10), (0.036, -0.078),
        (0.0375, 0.075), (0.030, 0.14), (-0.030, 0.14),
        (-0.0375, 0.105),
    ]
    receiver = prism_x("Receiver", receiver_profile, 0.055, mats["metal"])
    kit.add_bevel(receiver, 0.008, 3)
    parts.append(receiver)
    parts.append(kit.cylinder("BarrelRear", 0.020, 0.300, (0, 0.014, -0.25), "z", mats["metal"], 16))
    parts.append(kit.cylinder("MagazineRear", 0.015, 0.300, (0, -0.022, -0.25), "z", mats["metal_dark"], 14))
    parts.append(kit.cylinder("CutBore", 0.013, 0.002, (0, 0.014, -0.401), "z", mats["black"], 16))
    for z in (-0.02, 0.07):
        parts.append(kit.cylinder("Pin", 0.0035, 0.058, (0, -0.022, z), "x", mats["metal_dark"], 8))
    parts.append(kit.box("LoadingPort", (0.03, 0.004, 0.1), (0, -0.0375, -0.01), mats["black"]))

    guard_points = []
    for index in range(18):
        angle = 2.0 * math.pi * index / 18
        guard_points.append((-0.064 + 0.028 * math.sin(angle), 0.056 + 0.047 * math.cos(angle)))
    parts.append(path_tube("TriggerGuard", guard_points, 0.0032, mats["metal_dark"], True, 6))
    trigger_points = [(-0.040, 0.045), (-0.052, 0.049), (-0.066, 0.056), (-0.076, 0.068)]
    parts.append(path_tube("Trigger", trigger_points, 0.0025, mats["metal_dark"], False, 6))

    parts.append(kit.box("EjectionPort", (0.003, 0.030, 0.100), (0.0288, 0.010, -0.020), mats["black"], bevel=0.004))
    parts.append(kit.box("Bolt", (0.0015, 0.019, 0.075), (0.0306, 0.009, -0.020), mats["metal_dark"], bevel=0.003))
    # 金属件用盒式投影；枪托自带顺木纹的 UV，合并后不能再整体投影
    for p in parts:
        kit.box_uv(p, 0.2)
    parts.extend(build_stock(mats))
    body = kit.join(parts, "Body")
    ordered_slots(body, [mats[key] for key in ("metal", "metal_dark", "wood", "rubber", "black")])
    kit.set_origin(body, (0, 0, 0))
    kit.smooth(body, 50)
    return body


def build_barrel_front(mats):
    """构建可隐藏的前段枪管、弹仓、滚花帽、枪管箍与枪口内膛。
    @keyword-en barrel-front, sawed-section
    @keyword-cn 前段枪管, 锯短部件
    """
    parts = [
        kit.cylinder("BarrelFrontTube", 0.020, 0.230, (0, 0.014, -0.515), "z", mats["metal"], 16),
        kit.cylinder("MagazineFrontTube", 0.015, 0.180, (0, -0.022, -0.490), "z", mats["metal_dark"], 14),
        kit.cylinder("MagazineCap", 0.018, 0.028, (0, -0.022, -0.594), "z", mats["metal_dark"], 16),
        kit.box("BarrelBand", (0.046, 0.065, 0.018), (0, -0.004, -0.553), mats["metal_dark"], bevel=0.004),
        kit.cylinder("MuzzleBore", 0.013, 0.003, (0, 0.014, -0.632), "z", mats["black"], 16),
    ]
    for index in range(6):
        z = -0.584 - index * 0.004
        parts.append(kit.cylinder("CapKnurl", 0.0187, 0.0016, (0, -0.022, z), "z", mats["metal_dark"], 12))
    front = kit.join(parts, "BarrelFront")
    ordered_slots(front, [mats[key] for key in ("metal", "metal_dark", "black")])
    kit.set_origin(front, (0, 0, 0))
    kit.box_uv(front, 0.2)
    kit.smooth(front, 38)
    return front


def build_sight(mats):
    """构建枪口附近的黄铜准星珠与深色钢底座。
    @keyword-en front-sight, brass-bead
    @keyword-cn 前准星, 黄铜珠
    """
    bead = kit.sphere("SightBead", 0.005, (0, 0.040, -0.600), mats["brass"], 12, 6)
    base = kit.box("SightBase", (0.010, 0.004, 0.014), (0, 0.0355, -0.600), mats["metal_dark"], bevel=0.0015)
    sight = kit.join([bead, base], "Sight")
    ordered_slots(sight, [mats["brass"], mats["metal_dark"]])
    kit.set_origin(sight, (0, 0, 0))
    return sight


def build_pump(mats):
    """以锯齿半径轮廓构建带十道环形凹槽的木质泵动护木。
    @keyword-en pump-forearm, ring-grooves
    @keyword-cn 泵动护木, 环形凹槽
    """
    profile = [
        (0.021, -0.075), (0.025, -0.068), (0.027, -0.058),
    ]
    groove_start = -0.050
    for index in range(10):
        z = groove_start + index * 0.0105
        profile.extend([(0.027, z), (0.0238, z + 0.0025), (0.027, z + 0.0050)])
    profile.extend([(0.027, 0.058), (0.025, 0.069), (0.021, 0.075)])
    pump = kit.lathe("Pump", profile, (0, -0.022, -0.240), "z", mats["wood"], 16)
    kit.smooth(pump, 35)
    kit.set_origin(pump, (0, -0.022, -0.240))
    kit.box_uv(pump, 0.3)
    return pump


def render_views(body, front, sight, pump):
    """渲染完整枪的两张观察图和隐藏前段后的锯短状态图。
    @keyword-en shotgun-preview, sawed-preview
    @keyword-cn 霰弹枪预览, 锯短预览
    """
    objects = [body, front, sight, pump]
    kit.render_preview("gun/shotgun_side.png", direction=(-1.0, 0.03, 0.0), target=(0, -0.03, -0.07),
                       distance=2.38, fov=30, resolution=(1000, 420), objs=objects)
    kit.render_preview("gun/shotgun_three_quarter.png", direction=(0.85, 0.48, -0.72),
                       target=(0, -0.025, -0.07), distance=1.95, fov=34,
                       resolution=(900, 560), objs=objects)
    front.hide_render = True
    sight.hide_render = True
    kit.render_preview("gun/shotgun_rear.png", direction=(-0.8, 0.4, 0.75), target=(0, -0.05, 0.25),
                       distance=0.9, fov=34, resolution=(800, 560), objs=objects)
    kit.render_preview("gun/shotgun_sawed.png", direction=(0.8, 0.36, -0.65),
                       target=(0, -0.035, -0.02), distance=1.48, fov=34,
                       resolution=(800, 560), objs=[body, pump])
    front.hide_render = False
    sight.hide_render = False


def main():
    """重置场景、构建霰弹枪、导出 GLB、输出面数并渲染最终预览。
    @keyword-en build-shotgun, export-shotgun
    @keyword-cn 构建霰弹枪, 导出霰弹枪
    """
    kit.reset_scene()
    mats = make_materials()
    body = build_body(mats)
    front = build_barrel_front(mats)
    sight = build_sight(mats)
    pump = build_pump(mats)
    objects = [body, front, sight, pump]
    print("SHOTGUN_TRIANGLES", kit.triangle_count(objects))
    kit.export_glb(objects, "shotgun.glb")
    render_views(body, front, sight, pump)


if __name__ == "__main__":
    main()
