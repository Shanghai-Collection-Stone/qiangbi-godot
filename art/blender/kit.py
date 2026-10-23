"""Blender 建模脚本共用的小工具：坐标换算、命名材质、UV、导出 glb、渲染预览。

约定（所有 build_*.py 都遵守）：
- 坐标一律用 **Godot 坐标** 描述（x 右、y 上、-z 朝屏幕里），用 g() 换成 Blender 坐标。
- 材质名就是游戏里 Props.material() 的 key（如 "metal"、"wood"），Godot 加载模型后按名字换成自己的材质；
  glb 里不嵌贴图，材质只带颜色，贴图只用于预览渲染。
- 每个顶层物体导出成 Godot 场景根节点下的一个直接子节点，物体名就是节点名。

运行：blender -b --factory-startup --python art/blender/build_xxx.py
"""

import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
MODELS_DIR = os.path.join(ROOT, "art", "models")
TEXTURES_DIR = os.path.join(ROOT, "art", "textures")
PREVIEWS_DIR = os.path.join(ROOT, "art", "source", "previews")


def g(x, y=0.0, z=0.0):
    """Godot 坐标 (x 右, y 上, z 朝镜头) 换成 Blender 坐标 (x 右, y 朝里, z 上)。

    @keyword-en godot-to-blender, coordinate-convert
    @keyword-cn 坐标换算, Godot坐标
    """
    if isinstance(x, (tuple, list, Vector)):
        x, y, z = x
    return Vector((x, -z, y))


def axis_rotation(axis):
    """返回把 Blender 默认 +Z 朝向的图元（圆柱、圆锥）转到指定 Godot 轴的欧拉角。

    axis 取 "x" / "y" / "z"（Godot 轴），或任意 Godot 方向向量。

    @keyword-en axis-rotation, primitive-orient
    @keyword-cn 轴向旋转, 图元朝向
    """
    if isinstance(axis, str):
        axis = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[axis]
    target = g(axis).normalized()
    return Vector((0, 0, 1)).rotation_difference(target).to_euler()


def reset_scene():
    """清空场景里的物体、网格和材质，得到一个干净的工作区。

    @keyword-en reset-scene, clear-scene
    @keyword-cn 重置场景, 清空场景
    """
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.cameras, bpy.data.lights):
        for item in list(block):
            block.remove(item)


def material(key, color, roughness=0.8, metallic=0.0, emission=None, preview_texture=None):
    """取得或新建名为 key 的材质（key 与游戏里 Props.material 的名字一致）。

    color 是 (r, g, b) 线性色，只用于预览和兜底；preview_texture 为 art/textures 下的文件名，
    存在时预览渲染会带贴图，导出时不嵌入。

    @keyword-en named-material, material-key
    @keyword-cn 命名材质, 材质键
    """
    if key in bpy.data.materials:
        return bpy.data.materials[key]
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    nodes = m.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 2.0
    path = os.path.join(TEXTURES_DIR, preview_texture) if preview_texture else ""
    if path and os.path.exists(path):
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(path, check_existing=True)
        tex.interpolation = "Closest"
        mix = nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        sockets = {s.identifier: s for s in mix.inputs}
        sockets["Factor_Float"].default_value = 1.0
        sockets["A_Color"].default_value = (*color, 1.0)
        result = next(s for s in mix.outputs if s.identifier == "Result_Color")
        m.node_tree.links.new(tex.outputs["Color"], sockets["B_Color"])
        m.node_tree.links.new(result, bsdf.inputs["Base Color"])
    m.diffuse_color = (*color, 1.0)
    return m


def assign(obj, mat):
    """把材质设为物体唯一的材质槽。

    @keyword-en assign-material, material-slot
    @keyword-cn 指定材质, 材质槽
    """
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj


def _link(obj):
    """把新物体放进当前场景的根集合。
    @keyword-en link-object, scene-collection
    @keyword-cn 加入场景, 场景集合
    """
    bpy.context.scene.collection.objects.link(obj)
    return obj


def mesh_object(name, bm, mat=None):
    """把 bmesh 写成新网格物体并放进场景。

    @keyword-en mesh-object, bmesh-to-object
    @keyword-cn 网格物体, 生成物体
    """
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = _link(bpy.data.objects.new(name, me))
    if mat is not None:
        assign(obj, mat)
    return obj


def box(name, size, center, mat=None, rot=(0, 0, 0), bevel=0.0):
    """建一个盒子。size、center 用 Godot 坐标 (宽 x, 高 y, 深 z)；rot 是 Godot 轴上的欧拉角 (弧度)。

    bevel > 0 时加倒角修改器（导出时应用）。

    @keyword-en box-primitive, cube
    @keyword-cn 盒子, 立方体
    """
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((size[0], size[2], size[1])), verts=bm.verts)
    obj = mesh_object(name, bm, mat)
    obj.rotation_euler = _godot_euler(rot)
    obj.location = g(center)
    if bevel > 0:
        add_bevel(obj, bevel)
    return obj


def cylinder(name, radius, length, center, axis="y", mat=None, segments=16, radius_top=None, cap=True):
    """建一个圆柱/圆台，沿 Godot 轴 axis 摆放，center 是中心点。带默认 UV（侧面横向展开 0..1）。

    @keyword-en cylinder-primitive, tube
    @keyword-cn 圆柱, 圆台
    """
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=segments,
                          radius1=radius, radius2=radius if radius_top is None else radius_top,
                          depth=length, calc_uvs=True)
    obj = mesh_object(name, bm, mat)
    obj.rotation_euler = axis_rotation(axis)
    obj.location = g(center)
    return obj


def sphere(name, radius, center, mat=None, segments=16, rings=8, scale=(1, 1, 1)):
    """建一个 UV 球，scale 用 Godot 轴 (x, y, z)。

    @keyword-en sphere-primitive, uv-sphere
    @keyword-cn 球体, 椭球
    """
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius, calc_uvs=True)
    obj = mesh_object(name, bm, mat)
    obj.scale = (scale[0], scale[2], scale[1])
    obj.location = g(center)
    return obj


def lathe(name, profile, center, axis="y", mat=None, segments=16):
    """车床旋转体：profile 是 [(半径, 沿轴高度), ...]，从底到顶，绕 Godot 轴 axis 旋转一周。

    UV：u 绕一圈 0..1，v 沿轮廓累计长度 0..1，适合贴瓶身/罐身标签。

    @keyword-en lathe, revolve-profile
    @keyword-cn 车削, 旋转体
    """
    bm = bmesh.new()
    rings = []
    for r, h in profile:
        ring = []
        for i in range(segments):
            a = 2.0 * math.pi * i / segments
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), h)))
        rings.append(ring)
    lengths = [0.0]
    for (r0, h0), (r1, h1) in zip(profile, profile[1:]):
        lengths.append(lengths[-1] + math.hypot(r1 - r0, h1 - h0))
    total = lengths[-1] or 1.0
    uv_layer = bm.loops.layers.uv.new("UVMap")
    for j in range(len(rings) - 1):
        for i in range(segments):
            i2 = (i + 1) % segments
            quad = [rings[j][i], rings[j][i2], rings[j + 1][i2], rings[j + 1][i]]
            face = bm.faces.new(quad)
            us = [i / segments, (i + 1) / segments, (i + 1) / segments, i / segments]
            vs = [lengths[j] / total, lengths[j] / total, lengths[j + 1] / total, lengths[j + 1] / total]
            for loop, u, v in zip(face.loops, us, vs):
                loop[uv_layer].uv = (u, v)
    for ring, flip in ((rings[0], True), (rings[-1], False)):
        if profile[0 if flip else -1][0] > 1e-5:
            face = bm.faces.new(list(reversed(ring)) if flip else ring)
            for loop in face.loops:
                co = loop.vert.co
                loop[uv_layer].uv = (0.5 + co.x / (4 * profile[0][0] + 1e-6), 0.5 + co.y / (4 * profile[0][0] + 1e-6))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = mesh_object(name, bm, mat)
    obj.rotation_euler = axis_rotation(axis)
    obj.location = g(center)
    return obj


_G2B = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))


def _godot_euler(rot):
    """Godot 欧拉角 (rx, ry, rz)，按 Godot 默认的 YXZ 顺序，换成 Blender 欧拉角。
    @keyword-en euler-convert, yxz-order
    @keyword-cn 欧拉角换算, 旋转顺序
    """
    rx, ry, rz = rot
    m = Matrix.Rotation(ry, 3, "Y") @ Matrix.Rotation(rx, 3, "X") @ Matrix.Rotation(rz, 3, "Z")
    return (_G2B @ m @ _G2B.transposed()).to_euler()


def add_bevel(obj, width, segments=1):
    """加倒角修改器（导出时应用），让低模边缘在灯光下有高光。

    @keyword-en bevel-modifier, edge-highlight
    @keyword-cn 倒角, 边缘高光
    """
    mod = obj.modifiers.new("Bevel", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    return mod


def apply_all(obj):
    """应用物体的全部修改器和变换，结果直接写进网格。

    @keyword-en apply-modifiers, apply-transform
    @keyword-cn 应用修改器, 应用变换
    """
    bpy.context.view_layer.objects.active = obj
    for o in bpy.context.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    for mod in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return obj


def join(objs, name):
    """把多个物体（应用修改器和变换后）合并成一个，材质槽自动合并。
    只要有一个物体带颜色属性 "Col"，其余物体先补上白色的 "Col"，合并后不会出现黑色顶点色；
    所有物体的 UV 层统一成一层 "UVMap"，合并后只有一层 UV。

    @keyword-en join-objects, merge-mesh
    @keyword-cn 合并物体, 合并网格
    """
    objs = [o for o in objs if o is not None]
    for o in objs:
        apply_all(o)
    if any("Col" in o.data.color_attributes for o in objs):
        for o in objs:
            if "Col" not in o.data.color_attributes:
                fill_color(o, (1.0, 1.0, 1.0))
    # UV 层按名字合并：名字不一致会合出两层，部分部件的 UV 落进第二层，而游戏只读第一层
    for o in objs:
        layers = o.data.uv_layers
        if not layers:
            layers.new(name="UVMap")
        while len(layers) > 1:
            layers.remove(layers[-1])
        layers[0].name = "UVMap"
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    result = bpy.context.view_layer.objects.active
    result.name = name
    result.data.name = name
    return result


def fill_color(obj, color):
    """给网格的每个顶点写同一个颜色属性 "Col"（RGB，线性值）。
    @keyword-en fill-vertex-color, color-attribute
    @keyword-cn 填充顶点色, 颜色属性
    """
    me = obj.data
    attr = me.color_attributes.get("Col") or me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    for item in attr.data:
        item.color = (*color, 1.0)
    me.color_attributes.active_color = attr
    return obj


def tentacle(name, points, radius_root, radius_tip, mat, phase=0.0, sway=0.02, segments=8, steps=6, suckers=None):
    """触手：沿 Godot 坐标控制点（从根到尖）的 Catmull-Rom 曲线放样成锥管，尖端收成一点。

    suckers 是吸盘朝向（Godot 方向向量，可省略）。
    给游戏里的触手着色器用的约定：UV.x 绕一圈 0..1，UV.y 从根 0 到尖 1（也是摆动权重）；
    顶点色 "Col" 的 R = 摆动相位 phase（0..1），G = 摆动幅度 sway（米）× 10，B = 触手长度（米）÷ 2（着色器按它平铺吸盘贴图）。

    @keyword-en tentacle-tube, sway-convention
    @keyword-cn 触手, 摆动约定
    """
    pts = [Vector(g(p)) for p in points]
    ext = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    path = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for s in range(steps):
            t = s / steps
            path.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                               + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    path.append(pts[-1])
    lengths = [0.0]
    for a, b in zip(path, path[1:]):
        lengths.append(lengths[-1] + (b - a).length)
    total = lengths[-1] or 1.0
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    col = bm.verts.layers.float_color.new("Col")
    rings = []
    normal = None
    for k, p in enumerate(path):
        tangent = (path[min(k + 1, len(path) - 1)] - path[max(k - 1, 0)]).normalized()
        if normal is None:
            # 贴图中间那一列吸盘在 u = 0.5，也就是 -normal 方向；suckers 给了就让吸盘朝它
            want = -g(suckers) if suckers is not None else Vector((0, 0, 1))
            if abs(want.normalized().dot(tangent)) > 0.95:
                want = Vector((1, 0, 0))
            normal = (want - tangent * want.dot(tangent)).normalized()
        normal = (normal - tangent * normal.dot(tangent)).normalized()
        binormal = tangent.cross(normal)
        t = lengths[k] / total
        r = radius_root + (radius_tip - radius_root) * t
        ring = []
        for i in range(segments):
            a = 2.0 * math.pi * i / segments
            v = bm.verts.new(p + (normal * math.cos(a) + binormal * math.sin(a)) * r)
            v[col] = (phase, sway * 10.0, min(total / 2.0, 1.0), 1.0)
            ring.append(v)
        rings.append((ring, t))
    tip = bm.verts.new(path[-1] + (path[-1] - path[-2]).normalized() * radius_tip)
    tip[col] = (phase, sway * 10.0, min(total / 2.0, 1.0), 1.0)
    for (r0, t0), (r1, t1) in zip(rings, rings[1:]):
        for i in range(segments):
            j = (i + 1) % segments
            face = bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
            for loop, (u, v) in zip(face.loops, ((i / segments, t0), ((i + 1) / segments, t0),
                                                 ((i + 1) / segments, t1), (i / segments, t1))):
                loop[uv].uv = (u, v)
    last, _ = rings[-1]
    for i in range(segments):
        j = (i + 1) % segments
        face = bm.faces.new((last[i], last[j], tip))
        for loop, (u, v) in zip(face.loops, ((i / segments, 1.0), ((i + 1) / segments, 1.0), ((i + 0.5) / segments, 1.0))):
            loop[uv].uv = (u, v)
    first, _ = rings[0]
    bm.faces.new(list(reversed(first)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = mesh_object(name, bm, mat)
    obj.data.color_attributes.active_color = obj.data.color_attributes["Col"]
    return obj


def set_origin(obj, point):
    """把物体原点移到 Godot 坐标 point，网格位置不变（动画节点要用：泵动护木、手、头）。

    @keyword-en set-origin, pivot
    @keyword-cn 设置原点, 枢轴
    """
    apply_all(obj)
    p = g(point)
    obj.data.transform(Matrix.Translation(-p))
    obj.location = p
    return obj


def parent(child, parent_obj):
    """把 child 挂到 parent_obj 下并保持世界位置不变（导出成 Godot 子节点）。

    @keyword-en parent-object, hierarchy
    @keyword-cn 父子关系, 层级
    """
    child.parent = parent_obj
    child.matrix_parent_inverse = parent_obj.matrix_world.inverted()
    return child


def box_uv(obj, size=0.25, offset=(0.0, 0.0)):
    """世界空间盒式投影 UV：1 个 UV 单位 = size 米，按面法线主轴选投影平面，平铺贴图密度一致。

    只处理当前网格（建议在 apply_all 或 join 之后调用）。

    @keyword-en box-uv, triplanar-projection
    @keyword-cn 盒式UV, 投影展开
    """
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    uv_layer = bm.loops.layers.uv.verify()
    mw = obj.matrix_world
    for face in bm.faces:
        n = (mw.to_3x3() @ face.normal)
        ax = max(range(3), key=lambda i: abs(n[i]))
        for loop in face.loops:
            co = mw @ loop.vert.co
            if ax == 0:
                u, v = co.y * (-1 if n.x > 0 else 1), co.z
            elif ax == 1:
                u, v = co.x * (1 if n.y > 0 else -1), co.z
            else:
                u, v = co.x, co.y * (1 if n.z > 0 else -1)
            loop[uv_layer].uv = (u / size + offset[0], v / size + offset[1])
    bm.to_mesh(me)
    bm.free()
    return obj


def smooth(obj, angle=35.0):
    """按角度平滑着色：小于 angle 度的边平滑，硬边保留。

    @keyword-en smooth-shading, auto-smooth
    @keyword-cn 平滑着色, 自动光滑
    """
    for o in bpy.context.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle))
    return obj


def triangle_count(objs):
    """统计物体（含修改器结果）的三角形总数，用来控制面数预算。

    @keyword-en triangle-count, poly-budget
    @keyword-cn 三角面数, 面数预算
    """
    deps = bpy.context.evaluated_depsgraph_get()
    total = 0
    for o in objs:
        if o.type != "MESH":
            continue
        me = o.evaluated_get(deps).to_mesh()
        me.calc_loop_triangles()
        total += len(me.loop_triangles)
        o.evaluated_get(deps).to_mesh_clear()
    return total


def export_glb(objs, rel_path, vertex_color="MATERIAL"):
    """把 objs（连同它们的子物体）导出为 art/models/<rel_path>.glb，Y 轴朝上，应用修改器，不嵌贴图。

    vertex_color 传 "ACTIVE" 时导出网格当前的颜色属性（行刑人头部的烘焙明暗用）。

    @keyword-en export-glb, gltf-export
    @keyword-cn 导出模型, 导出glb
    """
    path = os.path.join(MODELS_DIR, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for o in bpy.context.selected_objects:
        o.select_set(False)
    stack = list(objs)
    while stack:
        o = stack.pop()
        o.select_set(True)
        stack.extend(o.children)
        # 用 bmesh 图层建的颜色属性只是「活动」不是「默认渲染」色；不补上的话导出器会先写一层全白的 COLOR_0，
        # 真正的数据落到 COLOR_1，而 Godot 只读 COLOR_0（面具彩绘、触手摆动参数都会丢）
        if o.type == "MESH":
            colors = o.data.color_attributes
            if colors.active_color_name and colors.default_color_name != colors.active_color_name:
                colors.default_color_name = colors.active_color_name
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True,
                              export_yup=True, export_image_format="NONE", export_materials="EXPORT",
                              export_cameras=False, export_lights=False, export_extras=False,
                              export_animations=False, export_vertex_color=vertex_color)
    print("EXPORTED", path, "tris", triangle_count([o for o in bpy.data.objects if o.select_get()]))
    return path


def render_preview(rel_path, direction=(0.6, 0.45, 1.0), target=None, distance=None, fov=35.0,
                   resolution=(768, 512), objs=None):
    """渲染一张预览图到 art/source/previews/<rel_path>：相机从 Godot 方向 direction 看向物体中心。

    target / distance 不给时按 objs（默认全部网格）的包围盒自动取景；带三点灯，深灰背景。

    @keyword-en render-preview, eevee-render
    @keyword-cn 渲染预览, 预览图
    """
    scene = bpy.context.scene
    objs = [o for o in (objs or scene.objects) if o.type == "MESH" and o.visible_get()]
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    center = g(target) if target is not None else (lo + hi) / 2
    radius = (hi - lo).length / 2
    dist = distance if distance is not None else radius / math.tan(math.radians(fov) / 2) * 1.1
    eye = center + g(direction).normalized() * dist

    temp = []
    cam_data = bpy.data.cameras.new("PreviewCam")
    cam_data.angle = math.radians(fov)
    cam_data.clip_start = 0.005
    cam = _link(bpy.data.objects.new("PreviewCam", cam_data))
    cam.location = eye
    cam.rotation_euler = (center - eye).to_track_quat("-Z", "Y").to_euler()
    temp.append(cam)
    scene.camera = cam
    for d, energy, color in (((1.0, 1.4, 1.2), 2.5, (1.0, 0.9, 0.8)), ((-1.2, 0.6, 0.4), 0.9, (0.7, 0.85, 1.0)),
                             ((0.0, 0.8, -1.4), 1.6, (1.0, 1.0, 1.0))):
        ld = bpy.data.lights.new("PreviewSun", "SUN")
        ld.energy = energy
        ld.color = color
        lo_ = _link(bpy.data.objects.new("PreviewSun", ld))
        lo_.rotation_euler = (-g(d)).to_track_quat("-Z", "Y").to_euler()
        temp.append(lo_)

    if scene.world is None:
        scene.world = bpy.data.worlds.new("PreviewWorld")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.05, 0.05, 0.055, 1.0)
    bg.inputs["Strength"].default_value = 1.0
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "Standard"
    path = os.path.join(PREVIEWS_DIR, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    for o in temp:
        bpy.data.objects.remove(o, do_unlink=True)
    print("PREVIEW", path)
    return path
