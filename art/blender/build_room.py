"""构建《枪毙·最后一发》的赌桌、工业吊灯和地下室房间。

输出 ``art/models/table.glb``、``lamp.glb``、``room.glb``，并把三组检查图写到
``art/source/previews/room/``。运行方式：
``blender -b --factory-startup --python art/blender/build_room.py``。
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bmesh
import bpy
from mathutils import Vector

import kit


def create_materials():
    """创建本脚本使用的全部命名材质。
    @keyword-en room-materials, named-materials
    @keyword-cn 房间材质, 命名材质
    """
    specs = {
        "wood": ((0.35, 0.18, 0.08), 0.6, 0.0, None, "wood.png"),
        "wood_dark": ((0.16, 0.09, 0.05), 0.7, 0.0, None, "wood.png"),
        "leather": ((0.22, 0.05, 0.04), 0.6, 0.0, None, "leather.png"),
        "felt": ((0.12, 0.2, 0.15), 0.95, 0.0, None, "felt.png"),
        "concrete": ((0.2, 0.2, 0.19), 0.95, 0.0, None, "concrete.png"),
        "tiles": ((0.25, 0.24, 0.2), 0.6, 0.0, None, "tiles.png"),
        "metal_dark": ((0.15, 0.15, 0.17), 0.5, 0.7, None, "metal.png"),
        "rust": ((0.35, 0.17, 0.08), 0.9, 0.3, None, "rust.png"),
        "brass": ((0.8, 0.6, 0.22), 0.35, 0.8, None, None),
        "black": ((0.005, 0.005, 0.005), 1.0, 0.0, None, None),
        "red_paint": ((0.45, 0.05, 0.03), 0.6, 0.0, None, None),
        "lamp_shade": ((0.12, 0.18, 0.14), 0.5, 0.3, None, None),
        "lamp_inner": ((0.8, 0.78, 0.7), 0.6, 0.0, None, None),
        "bulb": ((1.0, 0.85, 0.6), 0.3, 0.0, (1.0, 0.55, 0.2), None),
        "poster": ((0.5, 0.4, 0.35), 0.9, 0.0, None, "poster.png"),
        "speaker": ((0.02, 0.02, 0.02), 0.9, 0.0, None, None),
        "exit_glow": ((1.0, 0.15, 0.1), 0.35, 0.0, (1.0, 0.03, 0.01), None),
        "amber": ((0.45, 0.18, 0.03), 0.25, 0.0, None, None),
        "tentacle": ((0.08, 0.10, 0.06), 0.35, 0.0, None, "tentacle.png"),
        "flesh": ((0.25, 0.05, 0.07), 0.5, 0.0, None, "flesh.png"),
        "wax": ((0.75, 0.70, 0.58), 0.6, 0.0, None, None),
        "candle_glow": ((1.0, 0.60, 0.20), 0.25, 0.0, (1.0, 0.30, 0.05), None),
        "sigil": ((0.40, 0.05, 0.05), 0.75, 0.0, None, "sigil.png"),
        "scrawl": ((0.35, 0.03, 0.03), 0.8, 0.0, None, "scrawl.png"),
    }
    return {
        key: kit.material(key, color, rough, metal, emission=emit, preview_texture=texture)
        for key, (color, rough, metal, emit, texture) in specs.items()
    }


def add_torus(name, major_radius, minor_radius, center, axis, mat, major_segments=16, minor_segments=6):
    """创建沿指定 Godot 轴向的低模圆环。
    @keyword-en torus-primitive, ring-mesh
    @keyword-cn 圆环图元, 环形网格
    """
    bpy.ops.mesh.primitive_torus_add(
        align="WORLD", major_segments=major_segments, minor_segments=minor_segments,
        location=kit.g(center), major_radius=major_radius, minor_radius=minor_radius,
    )
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = kit.axis_rotation(axis)
    kit.assign(obj, mat)
    return obj


def add_beam(parts, name, start, end, radius, mat, segments=8):
    """在两个 Godot 坐标点之间添加圆柱梁并收集到部件列表。
    @keyword-en point-beam, cylinder-link
    @keyword-cn 点间圆梁, 圆柱连接
    """
    a = Vector(start)
    b = Vector(end)
    obj = kit.cylinder(name, radius, (b - a).length, (a + b) * 0.5,
                       axis=(b - a), mat=mat, segments=segments)
    parts.append(obj)
    return obj


def finish_join(parts, name, origin=(0, 0, 0), uv_groups=None):
    """合并逻辑部件、设置原点，并按材质名应用盒式 UV。
    @keyword-en logical-join, origin-uv
    @keyword-cn 逻辑合并, 原点贴图
    """
    obj = kit.join(parts, name)
    kit.set_origin(obj, origin)
    if uv_groups:
        for material_name, size in uv_groups.items():
            # 合并网格只能整体投影；材质密度相近时按主要材质尺寸处理。
            if any(slot.material and slot.material.name == material_name for slot in obj.material_slots):
                kit.box_uv(obj, size=size)
                break
    return obj


def build_table(mats):
    """构建带软包边、裙板、装饰钉和车削腿的赌桌。
    @keyword-en build-table, roulette-table
    @keyword-cn 构建赌桌, 轮盘赌桌
    """
    parts = []
    felt = kit.box("FeltTop", (2.10, 0.06, 1.55), (0, -0.03, -0.03), mats["felt"], bevel=0.003)
    kit.apply_all(felt)
    kit.box_uv(felt, 0.5)
    parts.append(felt)

    # 木框和裙板留出足够的中央道具区域。
    for name, size, center in (
        ("FrameFront", (2.28, 0.105, 0.075), (0, -0.055, 0.7825)),
        ("FrameBack", (2.28, 0.105, 0.075), (0, -0.055, -0.8425)),
        ("FrameLeft", (0.075, 0.105, 1.55), (-1.0875, -0.055, -0.03)),
        ("FrameRight", (0.075, 0.105, 1.55), (1.0875, -0.055, -0.03)),
        ("ApronFront", (2.10, 0.10, 0.055), (0, -0.155, 0.77)),
        ("ApronBack", (2.10, 0.10, 0.055), (0, -0.155, -0.83)),
        ("ApronLeft", (0.055, 0.10, 1.50), (-1.04, -0.155, -0.03)),
        ("ApronRight", (0.055, 0.10, 1.50), (1.04, -0.155, -0.03)),
    ):
        piece = kit.box(name, size, center, mats["wood"], bevel=0.004)
        kit.apply_all(piece)
        kit.box_uv(piece, 0.3)
        parts.append(piece)

    # 四段圆润软垫，内边界严格落在指定范围之外。
    for name, size, center in (
        ("RailFront", (2.28, 0.09, 0.075), (0, 0.005, 0.7475)),
        ("RailBack", (2.28, 0.09, 0.075), (0, 0.005, -0.8075)),
        ("RailLeft", (0.105, 0.09, 1.48), (-1.0325, 0.005, -0.03)),
        ("RailRight", (0.105, 0.09, 1.48), (1.0325, 0.005, -0.03)),
    ):
        piece = kit.box(name, size, center, mats["leather"], bevel=0.018)
        kit.apply_all(piece)
        kit.box_uv(piece, 0.3)
        parts.append(piece)

    profile = [(0.052, 0.0), (0.052, 0.05), (0.067, 0.075), (0.073, 0.14),
               (0.052, 0.22), (0.045, 0.37), (0.064, 0.45), (0.072, 0.53),
               (0.057, 0.61)]
    for index, (x, z) in enumerate(((-0.95, 0.62), (0.95, 0.62), (-0.95, -0.68), (0.95, -0.68))):
        parts.append(kit.lathe(f"Leg{index + 1}", profile, (x, -0.75, z), "y", mats["wood"], 12))

    # 前后可见面的黄铜装饰钉。
    for side_z in (-0.884, 0.824):
        for x in (-0.92, -0.61, -0.30, 0.0, 0.30, 0.61, 0.92):
            parts.append(kit.sphere("BrassStud", 0.013, (x, -0.105, side_z), mats["brass"], 8, 4,
                                    scale=(1.0, 1.0, 0.45)))

    # 法阵标签略高于绒布；从玩家侧看，图片上边朝后墙（-z）。
    bm = bmesh.new()
    coords = [(-0.475, 0.0012, 0.425), (0.475, 0.0012, 0.425),
              (0.475, 0.0012, -0.525), (-0.475, 0.0012, -0.525)]
    verts = [bm.verts.new(kit.g(co)) for co in coords]
    uv = bm.loops.layers.uv.new("UVMap")
    face = bm.faces.new(verts)
    for loop, value in zip(face.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop[uv].uv = value
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(kit.mesh_object("TableSigil", bm, mats["sigil"]))

    table = finish_join(parts, "Table")
    return table


def build_lamp(mats):
    """构建双层搪瓷灯罩、电线灯座以及独立灯泡子节点。
    @keyword-en build-lamp, industrial-lamp
    @keyword-cn 构建吊灯, 工业吊灯
    """
    anchor = (0, 1.5, -0.25)
    parts = []
    outer = [(0.305, -0.11), (0.30, -0.095), (0.27, -0.065), (0.225, -0.025),
             (0.17, 0.025), (0.115, 0.075), (0.075, 0.105), (0.07, 0.11)]
    inner = [(0.285, -0.103), (0.265, -0.078), (0.215, -0.035), (0.16, 0.015),
             (0.105, 0.062), (0.064, 0.095), (0.06, 0.103)]
    parts.append(kit.lathe("ShadeOuter", outer, anchor, "y", mats["lamp_shade"], 20))
    parts.append(kit.lathe("ShadeInner", inner, anchor, "y", mats["lamp_inner"], 20))
    parts.append(add_torus("RolledRim", 0.295, 0.012, (0, 1.392, -0.25), "y", mats["metal_dark"], 20, 5))
    parts.append(kit.cylinder("Socket", 0.055, 0.11, (0, 1.655, -0.25), "y", mats["metal_dark"], 12))
    parts.append(kit.cylinder("Cable", 0.006, 0.79, (0, 2.105, -0.25), "y", mats["black"], 8))
    lamp = finish_join(parts, "Lamp", anchor)

    bulb_profile = [(0.015, -0.055), (0.035, -0.045), (0.052, -0.015), (0.058, 0.02),
                    (0.047, 0.052), (0.027, 0.075), (0.022, 0.095)]
    bulb = kit.lathe("Bulb", bulb_profile, (0, 1.365, -0.25), "y", mats["bulb"], 12)
    kit.smooth(bulb, 50)
    kit.set_origin(bulb, (0, 1.42, -0.25))
    kit.parent(bulb, lamp)
    return lamp, bulb


def make_poster(mats):
    """创建带卷角且以整张标签图映射的竖版海报。
    @keyword-en poster-label, curled-corner
    @keyword-cn 海报标签, 卷起角
    """
    bm = bmesh.new()
    # 从正面看，右上角向房间内卷起。
    coords = [(-1.16, 0.75, -2.594), (-0.74, 0.75, -2.594),
              (-1.16, 1.35, -2.594), (-0.78, 1.35, -2.594), (-0.74, 1.31, -2.55)]
    verts = [bm.verts.new(kit.g(co)) for co in coords]
    uv = bm.loops.layers.uv.new("UVMap")
    for indices, uvs in (((0, 1, 3, 2), ((0, 0), (1, 0), (0.90, 1), (0, 1))),
                         ((1, 4, 3), ((1, 0), (1, 1), (0.90, 1)))):
        face = bm.faces.new([verts[i] for i in indices])
        for loop, value in zip(face.loops, uvs):
            loop[uv].uv = value
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit.mesh_object("Poster", bm, mats["poster"])


def make_speaker_cone(name, center, radius, mats):
    """创建朝房间内部凹入的低模扬声器纸盆。
    @keyword-en speaker-cone, recessed-driver
    @keyword-cn 扬声器纸盆, 凹陷单元
    """
    profile = [(radius, -0.018), (radius * 0.72, 0.0), (radius * 0.20, 0.07)]
    cone = kit.lathe(name, profile, center, "z", mats["speaker"], 16)
    return cone


def build_floor_walls(mats):
    """构建地板、三面混凝土墙和天花板基础体块。
    @keyword-en room-shell, basement-walls
    @keyword-cn 房间外壳, 地下室墙体
    """
    floor = kit.box("Floor", (5.6, 0.10, 6.7), (0, -0.80, 0.65), mats["tiles"])
    kit.apply_all(floor)
    kit.box_uv(floor, 1.6)
    kit.set_origin(floor, (0, 0, 0))

    walls_parts = [
        kit.box("BackWall", (5.6, 3.2, 0.10), (0, 0.85, -2.70), mats["concrete"]),
        kit.box("LeftWall", (0.10, 3.2, 6.7), (-2.80, 0.85, 0.65), mats["concrete"]),
        kit.box("RightWall", (0.10, 3.2, 6.7), (2.80, 0.85, 0.65), mats["concrete"]),
        kit.box("BackSkirt", (5.5, 0.12, 0.045), (0, -0.69, -2.635), mats["wood_dark"], bevel=0.002),
        kit.box("LeftSkirt", (0.045, 0.12, 6.6), (-2.735, -0.69, 0.65), mats["wood_dark"], bevel=0.002),
        kit.box("RightSkirt", (0.045, 0.12, 6.6), (2.735, -0.69, 0.65), mats["wood_dark"], bevel=0.002),
    ]
    walls = finish_join(walls_parts, "Walls", uv_groups={"concrete": 1.5})
    ceiling = kit.box("Ceiling", (5.6, 0.10, 6.7), (0, 2.50, 0.65), mats["concrete"])
    kit.apply_all(ceiling)
    kit.box_uv(ceiling, 1.5)
    kit.set_origin(ceiling, (0, 0, 0))
    return floor, walls, ceiling


def build_pipes(mats):
    """构建后墙与左墙锈管、管箍、托架和红色阀门手轮。
    @keyword-en build-pipes, valve-piping
    @keyword-cn 构建管道, 阀门管路
    """
    parts = []
    parts.append(kit.cylinder("MainPipe", 0.05, 5.35, (0, 1.95, -2.59), "x", mats["rust"], 12))
    parts.append(kit.cylinder("UpperPipe", 0.035, 5.35, (0, 2.10, -2.60), "x", mats["rust"], 10))
    parts.append(kit.cylinder("VerticalPipe", 0.05, 2.70, (-1.50, 0.60, -2.59), "y", mats["rust"], 12))
    parts.append(kit.sphere("Elbow", 0.064, (-1.50, 1.95, -2.59), mats["rust"], 12, 6))
    # 左墙两根纵深方向管道。
    parts.append(kit.cylinder("LeftPipeA", 0.045, 3.3, (-2.69, 2.02, -0.95), "z", mats["rust"], 10))
    parts.append(kit.cylinder("LeftPipeB", 0.032, 2.5, (-2.68, 1.82, -1.35), "z", mats["rust"], 10))
    for x in (-2.45, -1.25, -0.05, 1.15, 2.35):
        parts.append(kit.cylinder("PipeClamp", 0.062, 0.035, (x, 1.95, -2.59), "x", mats["metal_dark"], 12))
        parts.append(kit.box("PipeBracket", (0.045, 0.17, 0.045), (x, 1.91, -2.625), mats["metal_dark"], bevel=0.002))
    # 红色阀门圆环与五根辐条，平面平行于后墙。
    valve_center = (-1.50, 0.50, -2.50)
    parts.append(add_torus("ValveWheel", 0.15, 0.018, valve_center, "z", mats["red_paint"], 16, 5))
    parts.append(kit.cylinder("ValveHub", 0.035, 0.08, valve_center, "z", mats["red_paint"], 10))
    for i in range(5):
        angle = math.tau * i / 5
        end = (valve_center[0] + 0.135 * math.cos(angle),
               valve_center[1] + 0.135 * math.sin(angle), valve_center[2])
        add_beam(parts, "ValveSpoke", valve_center, end, 0.010, mats["red_paint"], 6)
    return finish_join(parts, "Pipes", uv_groups={"rust": 0.3})


def build_door_and_exit(mats):
    """构建后墙木门、分格、门把手和带护罩的红色出口灯。
    @keyword-en door-exit, guarded-light
    @keyword-cn 门与出口灯, 护罩灯
    """
    door_parts = [
        kit.box("DoorSlab", (0.60, 1.90, 0.07), (1.60, 0.20, -2.605), mats["wood_dark"], bevel=0.004),
        kit.box("DoorTopFrame", (0.76, 0.075, 0.095), (1.60, 1.19, -2.56), mats["wood_dark"], bevel=0.003),
        kit.box("DoorLeftFrame", (0.075, 2.04, 0.095), (1.225, 0.27, -2.56), mats["wood_dark"], bevel=0.003),
        kit.box("DoorRightFrame", (0.075, 2.04, 0.095), (1.975, 0.27, -2.56), mats["wood_dark"], bevel=0.003),
        kit.box("LowerPanel", (0.42, 0.55, 0.018), (1.60, -0.32, -2.555), mats["wood_dark"], bevel=0.008),
        kit.box("UpperPanel", (0.42, 0.78, 0.018), (1.60, 0.55, -2.555), mats["wood_dark"], bevel=0.008),
        kit.sphere("DoorKnob", 0.045, (1.82, 0.12, -2.50), mats["brass"], 12, 6, scale=(1, 1, 0.8)),
    ]
    door = finish_join(door_parts, "Door", uv_groups={"wood_dark": 0.6})

    exit_parts = [
        kit.box("ExitBox", (0.30, 0.08, 0.06), (1.60, 1.32, -2.59), mats["metal_dark"], bevel=0.006),
        kit.box("ExitFace", (0.24, 0.045, 0.009), (1.60, 1.32, -2.554), mats["exit_glow"], bevel=0.003),
    ]
    for x in (1.50, 1.60, 1.70):
        exit_parts.append(kit.cylinder("GuardVertical", 0.006, 0.12, (x, 1.32, -2.535), "y", mats["metal_dark"], 6))
    for y in (1.285, 1.355):
        exit_parts.append(kit.cylinder("GuardHorizontal", 0.006, 0.28, (1.60, y, -2.535), "x", mats["metal_dark"], 6))
    exit_sign = finish_join(exit_parts, "ExitSign")
    return door, exit_sign


def build_speakers(mats):
    """构建朝房间中心略微偏转的双层音箱堆。
    @keyword-en build-speakers, speaker-stack
    @keyword-cn 构建音箱, 音箱堆叠
    """
    parts = []
    for index, y in enumerate((-0.29, 0.53)):
        parts.append(kit.box(f"SpeakerCabinet{index}", (0.72, 0.78, 0.42), (-2.20, y, -2.18),
                             mats["wood_dark"], rot=(0, -0.16, 0), bevel=0.008))
        parts.append(kit.box("SpeakerBaffle", (0.60, 0.66, 0.025), (-2.165, y, -1.955),
                             mats["speaker"], rot=(0, -0.16, 0), bevel=0.004))
        parts.append(make_speaker_cone("Woofer", (-2.12, y - 0.10, -1.925), 0.19, mats))
        parts.append(make_speaker_cone("Tweeter", (-2.12, y + 0.20, -1.925), 0.075, mats))
    return finish_join(parts, "Speakers", uv_groups={"wood_dark": 0.6})


def build_crates(mats):
    """构建右墙木箱堆以及箱顶的空琥珀酒瓶。
    @keyword-en build-crates, bottle-stack
    @keyword-cn 构建木箱, 酒瓶堆放
    """
    parts = []
    crates = [((2.30, -0.49, -1.62), (0.72, 0.50, 0.58), 0.05),
              ((2.18, -0.11, -1.72), (0.58, 0.34, 0.48), -0.10),
              ((2.42, -0.50, -0.98), (0.52, 0.48, 0.46), -0.06)]
    for center, size, angle in crates:
        parts.append(kit.box("Crate", size, center, mats["wood_dark"], rot=(0, angle, 0), bevel=0.006))
        # 正面两道板条强化酒箱轮廓。
        for dy in (-size[1] * 0.32, size[1] * 0.32):
            parts.append(kit.box("CrateSlat", (size[0] * 0.88, 0.045, 0.025),
                                 (center[0], center[1] + dy, center[2] + size[2] * 0.52),
                                 mats["wood_dark"], rot=(0, angle, 0), bevel=0.002))
    for index, x in enumerate((2.02, 2.20, 2.37)):
        base_y = 0.06 + (0.015 if index == 1 else 0.0)
        parts.append(kit.cylinder("BottleBody", 0.038, 0.22, (x, base_y + 0.11, -1.70), "y", mats["amber"], 10,
                                  radius_top=0.032))
        parts.append(kit.cylinder("BottleNeck", 0.017, 0.10, (x, base_y + 0.27, -1.70), "y", mats["amber"], 10))
        parts.append(add_torus("BottleLip", 0.017, 0.005, (x, base_y + 0.325, -1.70), "y", mats["amber"], 10, 4))
    return finish_join(parts, "Crates", uv_groups={"wood_dark": 0.6})


def build_room(mats):
    """汇总地下室全部顶层逻辑节点并统一设置世界原点。
    @keyword-en build-room, room-assembly
    @keyword-cn 构建房间, 房间装配
    """
    floor, walls, ceiling = build_floor_walls(mats)
    pipes = build_pipes(mats)
    door, exit_sign = build_door_and_exit(mats)
    speakers = build_speakers(mats)
    poster = make_poster(mats)
    kit.set_origin(poster, (0, 0, 0))
    crates = build_crates(mats)

    # 后墙裂缝：黑色深缝、锯齿状混凝土碎边，以及向外鼓出的腐肉结节。
    crack_parts = []
    bm = bmesh.new()
    crack_outline = [(0.83, -0.75, -2.643), (0.70, -0.42, -2.643),
                     (0.78, -0.08, -2.643), (0.65, 0.26, -2.643),
                     (0.74, 0.66, -2.643), (0.76, 1.04, -2.643),
                     (0.84, 1.45, -2.643), (0.91, 1.10, -2.643),
                     (1.02, 0.72, -2.643), (1.00, 0.32, -2.643),
                     (1.09, -0.04, -2.643), (0.96, -0.39, -2.643)]
    crack_verts = [bm.verts.new(kit.g(co)) for co in crack_outline]
    bm.faces.new(crack_verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    crack_parts.append(kit.mesh_object("CrackVoid", bm, mats["black"]))
    edge_marks = [
        (0.73, -0.57, 0.07, 0.24, -0.20), (0.72, -0.20, 0.09, 0.25, 0.24),
        (0.68, 0.17, 0.08, 0.25, -0.28), (0.71, 0.56, 0.09, 0.28, 0.18),
        (0.77, 0.94, 0.08, 0.25, -0.15), (0.82, 1.28, 0.06, 0.25, 0.22),
        (0.94, -0.57, 0.08, 0.25, 0.18), (1.01, -0.19, 0.10, 0.27, -0.26),
        (1.05, 0.18, 0.08, 0.24, 0.20), (1.00, 0.57, 0.09, 0.28, -0.16),
        (0.94, 0.94, 0.07, 0.25, 0.22), (0.87, 1.29, 0.05, 0.24, -0.18),
    ]
    for index, (x, y, width, height, angle) in enumerate(edge_marks):
        crack_parts.append(kit.box(f"CrackStone{index}", (width, height, 0.045), (x, y, -2.615),
                                   mats["concrete"], rot=(0, 0, angle), bevel=0.004))
    for index, (center, scale) in enumerate((
        ((0.83, -0.48, -2.585), (1.0, 1.8, 0.45)),
        ((0.91, -0.08, -2.575), (1.35, 1.0, 0.50)),
        ((0.80, 0.37, -2.580), (1.0, 1.5, 0.48)),
        ((0.91, 0.75, -2.582), (1.25, 1.0, 0.45)),
        ((0.84, 1.10, -2.588), (0.9, 1.35, 0.42)),
    )):
        growth = kit.sphere(f"CrackFlesh{index}", 0.065, center, mats["flesh"], 10, 6, scale=scale)
        kit.apply_all(growth)
        kit.box_uv(growth, 0.3)
        crack_parts.append(growth)
    wall_crack = finish_join(crack_parts, "WallCrack")

    # 裂缝触手均限制在门左侧，并以分散相位供游戏着色器摆动。
    tentacle_specs = [
        ([(0.84, 0.96, -2.59), (0.70, 1.13, -2.58), (0.52, 1.28, -2.56), (0.43, 1.47, -2.55)], 0.046, 0.004, 0.04, 0.07),
        ([(0.88, 0.72, -2.59), (1.02, 0.91, -2.58), (1.22, 1.05, -2.56), (1.38, 1.03, -2.55)], 0.045, 0.004, 0.18, 0.06),
        ([(0.84, 0.39, -2.59), (0.65, 0.49, -2.58), (0.47, 0.40, -2.56), (0.42, 0.20, -2.54)], 0.040, 0.004, 0.33, 0.05),
        ([(0.91, 0.17, -2.59), (1.08, 0.20, -2.48), (1.23, 0.13, -2.25), (1.17, 0.24, -2.02), (1.02, 0.33, -1.93)], 0.052, 0.004, 0.47, 0.06),
        ([(0.82, -0.18, -2.59), (0.67, -0.37, -2.54), (0.59, -0.61, -2.48), (0.64, -0.73, -2.28), (0.79, -0.73, -2.06)], 0.050, 0.004, 0.62, 0.05),
        ([(0.92, -0.42, -2.59), (1.04, -0.61, -2.53), (1.16, -0.73, -2.40), (1.32, -0.73, -2.20)], 0.043, 0.004, 0.76, 0.04),
        ([(0.86, 0.57, -2.59), (0.81, 0.64, -2.39), (0.72, 0.58, -2.18), (0.78, 0.47, -2.00), (0.90, 0.52, -1.92)], 0.038, 0.004, 0.91, 0.05),
    ]
    tentacle_parts = []
    for index, (points, root, tip, phase, sway) in enumerate(tentacle_specs):
        tentacle_parts.append(kit.tentacle(f"CrackTentacle{index}", points, root, tip, mats["tentacle"],
                                           phase=phase, sway=sway, segments=8, steps=6))
    tentacles = finish_join(tentacle_parts, "Tentacles")
    # 多根带同名颜色层的网格合并时 Blender 偶尔保留一层纯白副本；只留摆动数据层。
    for attr in list(tentacles.data.color_attributes):
        if all(all(abs(channel - 1.0) < 1e-5 for channel in item.color) for item in attr.data):
            tentacles.data.color_attributes.remove(attr)
    if tentacles.data.color_attributes:
        tentacles.data.color_attributes[0].name = "Col"
        tentacles.data.color_attributes.active_color = tentacles.data.color_attributes[0]
        tentacles.data.color_attributes.render_color_index = 0

    # 左后角铸铁排水口、栅格、肉环和四根钻出的短触手。
    drain_parts = [
        kit.cylinder("DrainDisk", 0.18, 0.018, (-1.60, -0.740, -1.75), "y", mats["metal_dark"], 20),
        add_torus("DrainRim", 0.165, 0.014, (-1.60, -0.725, -1.75), "y", mats["metal_dark"], 20, 5),
    ]
    for offset in (-0.105, -0.052, 0.0, 0.052, 0.105):
        drain_parts.append(kit.box("DrainGrate", (0.025, 0.018, 0.28),
                                   (-1.60 + offset, -0.722, -1.75), mats["metal_dark"], bevel=0.002))
    flesh_ring = add_torus("DrainFlesh", 0.19, 0.030, (-1.60, -0.710, -1.75), "y", mats["flesh"], 20, 6)
    kit.apply_all(flesh_ring)
    kit.box_uv(flesh_ring, 0.3)
    drain_parts.append(flesh_ring)
    drain_specs = [
        ([(-1.66, -0.72, -1.75), (-1.76, -0.48, -1.73), (-1.82, -0.19, -1.65), (-1.72, 0.06, -1.55), (-1.58, -0.02, -1.48)], 0.052, 0.08, 0.03),
        ([(-1.55, -0.72, -1.72), (-1.43, -0.49, -1.67), (-1.35, -0.26, -1.55), (-1.42, -0.07, -1.43), (-1.54, -0.12, -1.39)], 0.045, 0.29, 0.03),
        ([(-1.61, -0.72, -1.81), (-1.60, -0.45, -1.94), (-1.54, -0.21, -2.08), (-1.42, -0.02, -2.05), (-1.35, -0.10, -1.95)], 0.047, 0.53, 0.025),
        ([(-1.68, -0.72, -1.70), (-1.86, -0.55, -1.62), (-1.99, -0.34, -1.66), (-1.96, -0.17, -1.80)], 0.040, 0.77, 0.025),
    ]
    for index, (points, root, phase, sway) in enumerate(drain_specs):
        drain_parts.append(kit.tentacle(f"DrainTentacle{index}", points, root, 0.004, mats["tentacle"],
                                        phase=phase, sway=sway, segments=8, steps=5))
    floor_tentacles = finish_join(drain_parts, "FloorTentacles")

    # 两组仪式蜡烛：A 在右侧最高木箱顶面，B 在排水口旁的地砖上。
    candle_parts = []
    candle_groups = [
        [(2.05, 0.060, -1.55, 0.18, 0.030), (2.15, 0.060, -1.47, 0.12, 0.027),
         (2.27, 0.060, -1.54, 0.22, 0.032), (2.36, 0.060, -1.58, 0.15, 0.026),
         (2.46, 0.060, -1.56, 0.19, 0.029), (2.31, 0.060, -1.66, 0.11, 0.025)],
        [(-1.25, -0.750, -2.25, 0.20, 0.031), (-1.14, -0.750, -2.19, 0.13, 0.027),
         (-1.34, -0.750, -2.15, 0.16, 0.029), (-1.18, -0.750, -2.34, 0.24, 0.033),
         (-1.39, -0.750, -2.30, 0.11, 0.025), (-1.08, -0.750, -2.29, 0.18, 0.028)],
    ]
    for group_index, group in enumerate(candle_groups):
        avg_x = sum(item[0] for item in group) / len(group)
        avg_z = sum(item[2] for item in group) / len(group)
        base_y = group[0][1]
        candle_parts.append(kit.cylinder("WaxPuddle", 0.19, 0.008, (avg_x, base_y + 0.004, avg_z),
                                         "y", mats["wax"], 16, radius_top=0.14))
        for index, (x, y, z, height, radius) in enumerate(group):
            profile = [(radius * 1.08, 0.0), (radius, height * 0.82),
                       (radius * 1.10, height - 0.010), (radius * 0.54, height - 0.003),
                       (0.0, height - 0.011)]
            candle_parts.append(kit.lathe(f"Candle{group_index}_{index}", profile, (x, y, z),
                                           "y", mats["wax"], 10))
            for drip_index, angle in enumerate((0.45 + index, 2.7 + index * 0.6)):
                drip_y = y + height * (0.48 - drip_index * 0.12)
                candle_parts.append(kit.sphere("WaxDrip", radius * 0.26,
                                                (x + math.cos(angle) * radius * 0.92, drip_y,
                                                 z + math.sin(angle) * radius * 0.92), mats["wax"], 8, 4,
                                                scale=(0.65, 2.2, 0.65)))
            wick_top = y + height + 0.006
            candle_parts.append(kit.cylinder("Wick", 0.0022, 0.018, (x, y + height - 0.002, z),
                                             "y", mats["black"], 6))
            flame_profile = [(0.0, 0.0), (0.007, 0.007), (0.005, 0.018), (0.0, 0.028)]
            candle_parts.append(kit.lathe("Flame", flame_profile, (x, wick_top, z),
                                           "y", mats["candle_glow"], 8))
    candles = finish_join(candle_parts, "Candles")

    # 两张血字贴片使用整图 UV；左墙朝 +x，后墙朝 +z。
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    scrawl_quads = [
        ([(-2.744, 0.20, -1.90), (-2.744, 0.20, -0.70),
          (-2.744, 1.30, -0.70), (-2.744, 1.30, -1.90)], ((0, 0), (1, 0), (1, 1), (0, 1))),
        ([(2.00, 0.30, -2.644), (2.65, 0.30, -2.644),
          (2.65, 1.20, -2.644), (2.00, 1.20, -2.644)], ((0, 0), (1, 0), (1, 1), (0, 1))),
    ]
    for coords, uvs in scrawl_quads:
        verts = [bm.verts.new(kit.g(co)) for co in coords]
        face = bm.faces.new(verts)
        for loop, value in zip(face.loops, uvs):
            loop[uv].uv = value
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    scrawl = kit.mesh_object("Scrawl", bm, mats["scrawl"])
    kit.set_origin(scrawl, (0, 0, 0))

    return [floor, walls, ceiling, pipes, door, exit_sign, speakers, poster, crates,
            wall_crack, tentacles, floor_tentacles, candles, scrawl]


def render_all_previews(table, lamp, room_objects):
    """从玩家、桌面、房间、裂缝和排水口机位渲染检查图。
    @keyword-en preview-angles, scene-review
    @keyword-cn 预览角度, 场景检查
    """
    all_objects = [table, lamp, *room_objects]
    kit.render_preview("room/player_view.png", direction=(0, 0.20, 1.8), target=(0, 0.65, -0.42),
                       distance=1.72, fov=84, resolution=(960, 640), objs=all_objects)
    kit.render_preview("room/table_closeup.png", direction=(1.25, 1.15, 1.4), target=(0, -0.10, -0.05),
                       distance=2.45, fov=48, resolution=(800, 600), objs=[table])
    ceiling = next(obj for obj in room_objects if obj.name == "Ceiling")
    ceiling.hide_render = True
    kit.render_preview("room/room_overview.png", direction=(2.0, 1.6, 4.0), target=(0, 0.48, -0.25),
                       distance=4.0, fov=62, resolution=(960, 640), objs=all_objects)
    ceiling.hide_render = False
    kit.render_preview("room/crack.png", direction=(0.12, 0.10, 1.0), target=(0.88, 0.32, -2.47),
                       distance=2.55, fov=48, resolution=(800, 640), objs=room_objects)
    kit.render_preview("room/drain.png", direction=(0.85, 0.65, 1.0), target=(-1.48, -0.35, -1.90),
                       distance=1.45, fov=48, resolution=(800, 640), objs=room_objects)


def main():
    """重置场景，构建、导出模型，打印预算并渲染预览。
    @keyword-en build-entry, export-assets
    @keyword-cn 构建入口, 导出资产
    """
    kit.reset_scene()
    mats = create_materials()
    table = build_table(mats)
    lamp, bulb = build_lamp(mats)
    room_objects = build_room(mats)

    # room.glb 全节点统一带颜色层，避免 glTF 为同名材质拆出带/不带顶点色的重名变体。
    for obj in room_objects:
        if not obj.data.color_attributes:
            kit.fill_color(obj, (1.0, 1.0, 1.0))

    kit.export_glb([table], "table.glb")
    kit.export_glb([lamp], "lamp.glb")
    kit.export_glb(room_objects, "room.glb", vertex_color="ACTIVE")
    print("BUDGET table", kit.triangle_count([table]), "/ 3500")
    print("BUDGET lamp", kit.triangle_count([lamp, bulb]), "/ 1200")
    print("BUDGET room total", kit.triangle_count(room_objects))
    print("BUDGET cthulhu additions", kit.triangle_count(room_objects[9:]), "/ 9000")
    render_all_previews(table, lamp, room_objects)


if __name__ == "__main__":
    main()
