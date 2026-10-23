# art 模块

## 模块名称 (Module Name)

art · 美术资源与生产管线

## 概述 (Overview)

游戏用到的全部 3D 模型和贴图，以及生成它们的管线：概念图和贴图原图由 Codex 图像生成画出（`art/source/`），`process_textures.py` 把原图加工成 64–256px 的像素贴图（`art/textures/`），`build_*.py` 在 Blender 4.5 里用脚本建模并导出 glb（`art/models/`）。游戏侧由 `scripts/props.gd` 加载这些资源。`art/source/` 和 `art/blender/` 带 `.gdignore`，Godot 不会导入。

## 文件清单 (File List)

- `blender/kit.py` — 建模脚本共用工具：Godot↔Blender 坐标换算、命名材质、图元、放样/车削、盒式 UV、合并与原点、导出 glb、EEVEE 预览渲染。
- `blender/process_textures.py` — 贴图加工：居中裁切、交叉淡化无缝、面积平均缩小、调色、特效图亮度转 alpha。
- `blender/build_shotgun.py` — 泵动霰弹枪（Body / BarrelFront / Sight / Pump）→ `models/shotgun.glb`。
- `blender/build_shell.py` — 12 号霰弹（Shell）→ `models/shell.glb`。
- `blender/build_items.py` — 8 件道具，每件一个 glb → `models/items/<id>.glb`。
- `blender/build_dealer.py` — 行刑人（Chair / Body / Head+瞳孔 / HandL/R / GripL/R / UpperArmL/R / ForearmL/R / ElbowL/R）→ `models/dealer.glb`。
- `blender/build_room.py` — 赌桌、吊灯、房间 → `models/table.glb`、`models/lamp.glb`、`models/room.glb`。
- `models/` — 导出的 glb（生成物，勿手改）。
- `textures/` — 加工后的像素贴图（生成物，勿手改）。
- `music/` — 背景音乐（OGG，循环播放）：`bleak_terminal.ogg`、`omen.ogg`，来源和许可见下方「音乐来源」。
- `source/concepts/`、`source/textures/`、`source/labels/` — Codex 生成的原图；`source/previews/` — 建模脚本渲染的检查图。

## 函数清单 (Function List)

- `kit.g(x, y, z)` — Godot 坐标 (x 右, y 上, z 朝镜头) 换成 Blender 坐标 (x 右, y 朝里, z 上) | keywords: godot-to-blender, coordinate-convert, 坐标换算, Godot坐标
- `kit.axis_rotation(axis)` — 返回把 Blender 默认 +Z 朝向的图元（圆柱、圆锥）转到指定 Godot 轴的欧拉角 | keywords: axis-rotation, primitive-orient, 轴向旋转, 图元朝向
- `kit.reset_scene()` — 清空场景里的物体、网格和材质，得到一个干净的工作区 | keywords: reset-scene, clear-scene, 重置场景, 清空场景
- `kit.material(key, color, roughness, metallic, emission, preview_texture)` — 取得或新建名为 key 的材质（key 与游戏里 Props.material 的名字一致） | keywords: named-material, material-key, 命名材质, 材质键
- `kit.assign(obj, mat)` — 把材质设为物体唯一的材质槽 | keywords: assign-material, material-slot, 指定材质, 材质槽
- `kit._link(obj)` — 把新物体放进当前场景的根集合 | keywords: link-object, scene-collection, 加入场景, 场景集合
- `kit.mesh_object(name, bm, mat)` — 把 bmesh 写成新网格物体并放进场景 | keywords: mesh-object, bmesh-to-object, 网格物体, 生成物体
- `kit.box(name, size, center, mat, rot, bevel)` — 建一个盒子。size、center 用 Godot 坐标 (宽 x, 高 y, 深 z)；rot 是 Godot 轴上的欧拉角 (弧度) | keywords: box-primitive, cube, 盒子, 立方体
- `kit.cylinder(name, radius, length, center, axis, mat, segments, radius_top, cap)` — 建一个圆柱/圆台，沿 Godot 轴 axis 摆放，center 是中心点。带默认 UV（侧面横向展开 0..1） | keywords: cylinder-primitive, tube, 圆柱, 圆台
- `kit.sphere(name, radius, center, mat, segments, rings, scale)` — 建一个 UV 球，scale 用 Godot 轴 (x, y, z) | keywords: sphere-primitive, uv-sphere, 球体, 椭球
- `kit.lathe(name, profile, center, axis, mat, segments)` — 车床旋转体：profile 是 [(半径, 沿轴高度), ...]，从底到顶，绕 Godot 轴 axis 旋转一周 | keywords: lathe, revolve-profile, 车削, 旋转体
- `kit._godot_euler(rot)` — Godot 欧拉角 (rx, ry, rz)，按 Godot 默认的 YXZ 顺序，换成 Blender 欧拉角 | keywords: euler-convert, yxz-order, 欧拉角换算, 旋转顺序
- `kit.add_bevel(obj, width, segments)` — 加倒角修改器（导出时应用），让低模边缘在灯光下有高光 | keywords: bevel-modifier, edge-highlight, 倒角, 边缘高光
- `kit.apply_all(obj)` — 应用物体的全部修改器和变换，结果直接写进网格 | keywords: apply-modifiers, apply-transform, 应用修改器, 应用变换
- `kit.join(objs, name)` — 把多个物体（应用修改器和变换后）合并成一个，材质槽自动合并 | keywords: join-objects, merge-mesh, 合并物体, 合并网格
- `kit.fill_color(obj, color)` — 给网格的每个顶点写同一个颜色属性 "Col"（RGB，线性值） | keywords: fill-vertex-color, color-attribute, 填充顶点色, 颜色属性
- `kit.tentacle(name, points, radius_root, radius_tip, mat, phase, sway, segments, steps, suckers)` — 触手：沿 Godot 坐标控制点（从根到尖）的 Catmull-Rom 曲线放样成锥管，尖端收成一点 | keywords: tentacle-tube, sway-convention, 触手, 摆动约定
- `kit.set_origin(obj, point)` — 把物体原点移到 Godot 坐标 point，网格位置不变（动画节点要用：泵动护木、手、头） | keywords: set-origin, pivot, 设置原点, 枢轴
- `kit.parent(child, parent_obj)` — 把 child 挂到 parent_obj 下并保持世界位置不变（导出成 Godot 子节点） | keywords: parent-object, hierarchy, 父子关系, 层级
- `kit.box_uv(obj, size, offset)` — 世界空间盒式投影 UV：1 个 UV 单位 = size 米，按面法线主轴选投影平面，平铺贴图密度一致 | keywords: box-uv, triplanar-projection, 盒式UV, 投影展开
- `kit.smooth(obj, angle)` — 按角度平滑着色：小于 angle 度的边平滑，硬边保留 | keywords: smooth-shading, auto-smooth, 平滑着色, 自动光滑
- `kit.triangle_count(objs)` — 统计物体（含修改器结果）的三角形总数，用来控制面数预算 | keywords: triangle-count, poly-budget, 三角面数, 面数预算
- `kit.export_glb(objs, rel_path, vertex_color)` — 把 objs（连同它们的子物体）导出为 art/models/<rel_path>.glb，Y 轴朝上，应用修改器，不嵌贴图 | keywords: export-glb, gltf-export, 导出模型, 导出glb
- `kit.render_preview(rel_path, direction, target, distance, fov, resolution, objs)` — 渲染一张预览图到 art/source/previews/<rel_path>：相机从 Godot 方向 direction 看向物体中心 | keywords: render-preview, eevee-render, 渲染预览, 预览图
- `process_textures.load_rgba(path)` — 读 PNG 为 (高, 宽, 4) 的 float 数组（Blender 的行序：从下往上，读写一致即可） | keywords: load-image, read-pixels, 读取图片, 读像素
- `process_textures.save_rgba(arr, path, alpha)` — 把 (高, 宽, 4) float 数组写成 PNG（alpha=False 时存 RGB） | keywords: save-image, write-png, 保存图片, 写PNG
- `process_textures.crop_to_aspect(arr, w, h)` — 居中裁切到目标宽高比 | keywords: center-crop, aspect-ratio, 居中裁切, 宽高比
- `process_textures.seamless_axis(arr, axis)` — 沿一个轴做交叉淡化无缝：去掉末尾一条带，把它淡入到开头，使首尾相接处连续 | keywords: seamless-tile, crossfade, 无缝平铺, 交叉淡化
- `process_textures._area_matrix(src, dst)` — 面积平均重采样矩阵 (dst × src)：每个目标像素平均它覆盖的源像素（按覆盖比例加权） | keywords: resample-matrix, box-filter, 重采样矩阵, 盒式滤波
- `process_textures.downscale(arr, w, h)` — 面积平均缩小到 w × h（不模糊、不锐化，像素块干净） | keywords: area-downscale, resample, 面积缩小, 重采样
- `process_textures.grade(arr, brightness, saturation)` — 调亮度与饱和度（在 sRGB 值上做，够用） | keywords: color-grade, saturation, 调色, 饱和度
- `process_textures.sprite_alpha(arr)` — 黑底特效图：用最大通道当 alpha，并把颜色除回去（反预乘），边缘不会发黑 | keywords: sprite-alpha, unpremultiply, 特效透明, 反预乘
- `process_textures.decal_alpha(arr)` — 黑底贴花（法阵、血字）：暗红颜料本身就不亮，所以亮度只要过一点阈值就基本不透明，颜色反预乘回去 | keywords: decal-alpha, paint-mask, 贴花透明, 颜料遮罩
- `process_textures.process(name, spec)` — 按 SPECS 里的一行加工一张贴图并写出。源文件不存在时跳过 | keywords: process-texture, texture-pipeline, 贴图加工, 贴图流水线
- `process_textures.main()` — 处理全部贴图 | keywords: process-all, batch-textures, 批量处理, 全部贴图
- `build_shotgun.prism_x(name, profile, width, mat, bevel)` — 把 Godot y-z 平面轮廓挤成沿 x 轴有厚度的硬表面零件 | keywords: profile-extrusion, hard-surface, 轮廓挤出, 硬表面
- `build_shotgun.path_tube(name, points, radius, mat, closed, sides)` — 沿 Godot y-z 平面路径生成细管，用于扳机护圈和弯曲扳机 | keywords: path-tube, trigger-geometry, 路径圆管, 扳机几何
- `build_shotgun.catmull(keys, t)` — 在 [(t, 值), ...] 关键点之间做 Catmull-Rom 插值（两端钳住），让枪托轮廓线平滑无折角 | keywords: catmull-rom, smooth-curve, 样条插值, 平滑曲线
- `build_shotgun.loft_rings(name, rings, mat, grain_axis)` — 把截面环（Godot 坐标点列，所有环点数相同）放样成两端封口的网格 | keywords: loft-rings, wood-grain-uv, 截面放样, 木纹UV
- `build_shotgun.loft_rings.coords(ring_index, i)` — 第 ring_index 个截面第 i 个点的 UV（u 沿周长，v 沿木纹轴） | keywords: ring-uv, grain-coords, 截面UV, 木纹坐标
- `build_shotgun.rounded_section(center, right, up, half_w, half_h, segments, power)` — 圆角矩形截面：center 为中心，right/up 为截面平面内的两根 Godot 单位向量 | keywords: rounded-section, superellipse, 圆角截面, 超椭圆
- `build_shotgun.build_stock(mats)` — 枪托：主体沿 z 放样（上沿 comb 斜线、下沿斜向托踵、握把颈收细）， | keywords: lofted-stock, pistol-grip, 放样枪托, 手枪握把
- `build_shotgun.ordered_slots(obj, materials)` — 按游戏约定重排并去重网格材质槽，同时保持每个面的材质归属 | keywords: material-order, surface-slots, 材质排序, 表面槽位
- `build_shotgun.make_materials()` — 创建霰弹枪所需的全部命名材质和预览参数 | keywords: shotgun-materials, preview-shading, 霰弹枪材质, 预览着色
- `build_shotgun.build_body(mats)` — 构建机匣、后段双管、扳机组、木枪托与橡胶底板并合并为 Body | keywords: shotgun-body, receiver-stock, 枪身主体, 机匣枪托
- `build_shotgun.build_barrel_front(mats)` — 构建可隐藏的前段枪管、弹仓、滚花帽、枪管箍与枪口内膛 | keywords: barrel-front, sawed-section, 前段枪管, 锯短部件
- `build_shotgun.build_sight(mats)` — 构建枪口附近的黄铜准星珠与深色钢底座 | keywords: front-sight, brass-bead, 前准星, 黄铜珠
- `build_shotgun.build_pump(mats)` — 以锯齿半径轮廓构建带十道环形凹槽的木质泵动护木 | keywords: pump-forearm, ring-grooves, 泵动护木, 环形凹槽
- `build_shotgun.render_views(body, front, sight, pump)` — 渲染完整枪的两张观察图和隐藏前段后的锯短状态图 | keywords: shotgun-preview, sawed-preview, 霰弹枪预览, 锯短预览
- `build_shotgun.main()` — 重置场景、构建霰弹枪、导出 GLB、输出面数并渲染最终预览 | keywords: build-shotgun, export-shotgun, 构建霰弹枪, 导出霰弹枪
- `build_shell.hull_mesh(mat)` — 生成带柱面标签 UV 的塑料壳体和六瓣内凹星形折口 | keywords: shell-hull, star-crimp, 霰弹塑料壳, 星形折口
- `build_shell.ordered_slots(obj, materials)` — 按 hull、brass 的稳定顺序去重并重建霰弹材质槽 | keywords: shell-material-order, surface-slots, 霰弹材质排序, 表面槽位
- `build_shell.build_shell()` — 组合塑料壳、黄铜底座、宽底缘与底火为单一 Shell 网格 | keywords: build-shell, twelve-gauge, 构建霰弹, 十二号口径
- `build_shell.render_shell(shell)` — 渲染一张显示红色壳身、黄铜底座和折口的近景预览 | keywords: shell-preview, close-up, 霰弹预览, 近景渲染
- `build_shell.main()` — 重置场景、构建霰弹、导出 GLB、输出面数并渲染预览 | keywords: export-shell, shell-pipeline, 导出霰弹, 霰弹流程
- `build_items.make_materials()` — 创建八件道具使用的命名材质 | keywords: item-materials, material-keys, 道具材质, 材质键
- `build_items.torus(name, major, minor, center, mat, major_segments, minor_segments, rot)` — 创建以 Godot y 为法线的低模圆环 | keywords: torus-ring, low-poly-ring, 圆环, 低模环
- `build_items.polygon_prism(name, outline, bottom, top, mat)` — 把 Godot xz 平面轮廓挤成指定高度的薄实体 | keywords: polygon-prism, custom-outline, 多边形棱柱, 自定义轮廓
- `build_items.label_quad(name, width, length, y, center, mat, top_toward_negative_z)` — 创建整张竖版标签铺满的朝上矩形面 | keywords: label-quad, full-image-uv, 标签面, 整图UV
- `build_items.label_disk(name, radius, y, center, mat, segments)` — 创建中心映射到 UV 中心、外缘映射到半径 0.5 的圆形标签盘 | keywords: label-disk, radial-uv, 圆盘标签, 径向UV
- `build_items.finish_item(parts, item_id)` — 合并部件、清理材质槽并把原点设到底面中心 | keywords: finish-item, single-root, 完成道具, 单根节点
- `build_items.build_magnifier(m)` — 构建平放的镀铬放大镜 | keywords: build-magnifier, tabletop-prop, 构建放大镜, 桌面道具
- `build_items.build_cigarette(m)` — 构建打开、凹皱并露出香烟的烟盒 | keywords: build-cigarette, open-cigarette-pack, 构建香烟, 打开烟盒
- `build_items.build_beer(m)` — 构建带凹痕、卷边和拉环的立式啤酒罐 | keywords: build-beer, dented-can, 构建啤酒, 凹陷罐
- `build_items.ring_prism(name, outer, inner, bottom, top, mat)` — 带洞的薄实体：outer、inner 是点数相同的 Godot xz 轮廓（同向），之间的环形区域挤出成 bottom..top 的厚度 | keywords: ring-prism, holed-outline, 带孔棱柱, 镂空轮廓
- `build_items.rounded_outline(cx, cz, half_x, half_z, power, segments)` — Godot xz 平面上的圆角矩形轮廓（超椭圆） | keywords: rounded-outline, superellipse, 圆角轮廓, 超椭圆
- `build_items.blot(cx, cz, radius, seed, points)` — 不规则的小斑块轮廓（锈斑用） | keywords: irregular-blot, rust-patch, 不规则斑块, 锈斑
- `build_items.build_saw(m)` — 构建平放的小手锯：梯形锯片下沿一排三角锯齿（朝 +z），根部插进带握孔的红色 D 形锯柄， | keywords: build-saw, toothed-blade, 构建手锯, 锯齿刀片
- `build_items.build_handcuffs(m)` — 构建双环、锁盒、齿臂和交错链节的手铐 | keywords: build-handcuffs, chained-rings, 构建手铐, 链接双环
- `build_items.build_phone(m)` — 构建贴有整面屏幕键盘标签的廉价直板手机 | keywords: build-phone, candybar-phone, 构建手机, 直板机
- `build_items.build_inverter(m)` — 构建带发光环、面板、按钮和线缆头的极性反转器 | keywords: build-inverter, glowing-device, 构建反转器, 发光装置
- `build_items.build_medicine(m)` — 构建琥珀药瓶、环绕标签、防滑盖和散落药片 | keywords: build-medicine, pill-bottle, 构建药瓶, 过期药
- `build_items.render_isolated(obj, item_id)` — 隐藏其余模型并渲染单件三分之四俯视近景 | keywords: isolated-preview, item-closeup, 单件预览, 道具近景
- `build_items.main()` — 生成、导出、统计并预览全部八件道具 | keywords: build-all-items, export-previews, 构建全部道具, 导出预览
- `build_dealer.create_materials()` — 创建行刑人使用的全部命名材质 | keywords: dealer-materials, named-materials, 行刑人材质, 命名材质
- `build_dealer.vertex_color_skin(mat)` — 让皮肤材质的预览乘上顶点色 "Col"（游戏里由 Godot 材质的 vertex_color_use_as_albedo 实现同样效果） | keywords: vertex-color-material, skin-preview, 顶点色材质, 皮肤预览
- `build_dealer.gauss(dx, dy, sx, sy, power)` — 二维高斯衰减，power > 1 时中心更平、边缘更陡（适合眼窝这种深坑） | keywords: gaussian-falloff, sculpt-brush, 高斯衰减, 雕刻笔刷
- `build_dealer.smoothstep(edge0, edge1, x)` — GLSL 同名函数：x 在两个边界之间平滑过渡到 0..1 | keywords: smoothstep, smooth-transition, 平滑过渡, 插值
- `build_dealer.smile_y(x)` — 咧嘴笑弧的中线高度（头部局部坐标），嘴角一直翘到颧骨下面 | keywords: smile-curve, mouth-arc, 笑弧, 嘴型曲线
- `build_dealer.smile_h(x)` — 笑弧在 x 处的张口半高，越到嘴角越窄 | keywords: mouth-opening, smile-height, 张口高度, 嘴宽
- `build_dealer.seam_points(side)` — 嘴角往颧骨方向的缝线两端点（头部局部 x, y） | keywords: stitch-seam, mouth-corner, 缝线, 嘴角
- `build_dealer._seam_distance(x, y, side)` — 点 (x, y) 到某一侧缝线线段的最近距离（头部局部坐标） | keywords: seam-distance, point-segment, 缝线距离, 点线距离
- `build_dealer.head_base(ux, uy, uz)` — 头的基本形：蛋形长颅（后脑往后上方拉长）、下半部收窄成尖下巴、脸正面略压平 | keywords: egg-skull, base-shape, 蛋形头骨, 基本形
- `build_dealer.head_shape(ux, uy, uz)` — 把单位球面上的点（Godot 头部局部方向）雕成行刑人的头，返回头部局部坐标 (x, y, z) | keywords: head-sculpt, displacement-shape, 头部雕刻, 位移塑形
- `build_dealer.head_color(x, y, uz)` — 头部顶点色（乘在皮肤贴图上）：眼窝和鼻孔渐变到黑，口腔渐变到暗红，缝线发紫红，凹陷处略暗 | keywords: vertex-color, baked-shading, 顶点色, 烘焙明暗
- `build_dealer.head_color.mix(c, target, k)` — 颜色线性插值 | keywords: color-lerp, mix-color, 颜色插值, 混色
- `build_dealer.oriented_box(name, center, axes, size, mat)` — 沿任意 Godot 坐标轴组摆放的小长方体（缝线、纽扣等贴表面的细节）。axes 为三根单位向量 | keywords: oriented-box, surface-detail, 定向盒子, 表面细节
- `build_dealer.ray_front(bvh, x, y, origin_z)` — 从 Godot +z 方向朝 -z 打射线，返回 (命中点 Godot 坐标, 法线 Godot 方向)，没打中返回 None | keywords: front-raycast, surface-sample, 正面射线, 表面采样
- `build_dealer.superellipse_ring(y, half_width, depth_front, depth_back, center_z, segments, power)` — 躯干放样用的圆角矩形截面（Godot 坐标点列），前半可以比后半更饱满 | keywords: superellipse, loft-section, 圆角截面, 放样截面
- `build_dealer.loft(name, rings, mat)` — 把一串同点数的截面（Godot 坐标，自下而上）放样成封口的管状网格 | keywords: loft-mesh, section-sweep, 截面放样, 管状网格
- `build_dealer.surface_panel(name, outline, bvh, offset, mat, thickness, cuts)` — 把一个 Godot (x, y) 平面轮廓从正面投影到躯干表面上，沿法线浮起 offset，做成贴身的衣片 | keywords: surface-panel, projected-decal, 贴身衣片, 投影贴片
- `build_dealer.cone_between(name, base, tip, radius, mat, segments)` — 在两个 Godot 坐标点之间生成带底盖的低模圆锥 | keywords: cone-between, pointed-detail, 两点圆锥, 尖锐细节
- `build_dealer.cylinder_between(name, start, end, radius, mat, segments, radius_end)` — 生成连接两个 Godot 坐标点的圆柱或圆台 | keywords: cylinder-between, limb-segment, 两点圆柱, 肢体分节
- `build_dealer.build_chair(mats)` — 构建带皮革软包、铆钉和球形顶饰的高背椅 | keywords: dealer-chair, high-back-chair, 行刑人椅子, 高背椅
- `build_dealer.build_body(mats)` — 构建瘦长西装躯干：圆角截面放样的身体，贴着胸口投影的马甲、衬衫、领带、翻领和纽扣，加脖子和领圈 | keywords: dealer-body, three-piece-suit, 行刑人躯干, 三件套西装
- `build_dealer.build_head(mats)` — 构建行刑人的头：密细分球按 head_shape 位移雕刻成一个整体，眼窝/口腔/缝线的明暗按 head_color 烘焙进顶点色， | keywords: dealer-head, grinning-skull, 行刑人头部, 咧嘴骷髅
- `build_dealer.build_head.surface(x, y)` — 头部表面在 (x, y) 处的点和法线（头部局部坐标），打不中时退回一个默认值 | keywords: head-surface, raycast-fallback, 头部表面, 射线取点
- `build_dealer.build_beard(mats, surface)` — 下颌和下巴上长出的触手须（11 根）：外圈 6 根沿下颌两侧、内圈 5 根在下巴，垂到胸口，尖端向外卷起 | keywords: tentacle-beard, cthulhu-jaw, 触手须, 克苏鲁下颌
- `build_dealer.build_hand(name, center, side, mats)` — 构建一只平放、长指、关节突出的骨感手掌 | keywords: skeletal-hand, articulated-fingers, 骨感手掌, 分节手指
- `build_dealer.build_arm_segment(name, profile, mats, cuff)` — 手臂的一段（上臂或前臂）：沿本地 Y 轴长 1 米、原点居中的袖管，-y 端是近端（肩或肘） | keywords: arm-segment, unit-sleeve, 手臂分段, 单位袖管
- `build_dealer.build_elbow(name, mats)` — 肘关节：一个袖子布料的球，游戏每帧放到肘部，盖住上臂和前臂的接缝 | keywords: elbow-joint, sleeve-ball, 肘关节, 关节球
- `build_dealer.fist_point(x, phi, radius)` — 握拳手指绕杆的位置：杆沿本地 X 轴，phi 从掌心一侧（-Z）经顶部（+Y）转到前面（+Z）再到底下 | keywords: fist-curl, finger-arc, 握拳弧线, 手指弯曲
- `build_dealer.build_fist(name, side, mats)` — 握拳的手（握枪用）：握住一根沿本地 X 轴、半径 FIST_BAR 的杆，原点在杆的中心； | keywords: gripping-fist, gun-grip-hand, 握拳手, 握枪手
- `build_dealer.solve_elbow(shoulder, wrist, pole)` — 两段手臂的解析 IK（和 table_scene.gd 的 _solve_arm 同一算法）：返回肘部位置，够不着时沿直线拉长 | keywords: two-bone-ik, elbow-solve, 两段IK, 肘部求解
- `build_dealer.place_segment(obj, start, end)` — 仅为预览把单位长的手臂段摆到两点之间（Godot 坐标） | keywords: preview-segment, place-between, 预览手臂段, 两点摆放
- `build_dealer.reset_transform(obj)` — 把物体恢复到导出所需的原点、零旋转、单位缩放 | keywords: reset-transform, export-ready, 重置变换, 导出就绪
- `build_dealer.render_previews(objects)` — 渲染玩家视角（手放桌上，手臂按 IK 弯肘）、头部正侧面和握拳手的检查图 | keywords: dealer-previews, visual-inspection, 行刑人预览, 视觉检查
- `build_dealer.print_statistics(objects)` — 打印各逻辑节点与头部组合的三角面数统计 | keywords: dealer-statistics, triangle-budget, 行刑人统计, 三角面预算
- `build_dealer.main()` — 重置场景、构建全部节点、导出 GLB 并生成预览 | keywords: build-dealer, export-dealer, 构建行刑人, 导出行刑人
- `build_room.create_materials()` — 创建本脚本使用的全部命名材质 | keywords: room-materials, named-materials, 房间材质, 命名材质
- `build_room.add_torus(name, major_radius, minor_radius, center, axis, mat, major_segments, minor_segments)` — 创建沿指定 Godot 轴向的低模圆环 | keywords: torus-primitive, ring-mesh, 圆环图元, 环形网格
- `build_room.add_beam(parts, name, start, end, radius, mat, segments)` — 在两个 Godot 坐标点之间添加圆柱梁并收集到部件列表 | keywords: point-beam, cylinder-link, 点间圆梁, 圆柱连接
- `build_room.finish_join(parts, name, origin, uv_groups)` — 合并逻辑部件、设置原点，并按材质名应用盒式 UV | keywords: logical-join, origin-uv, 逻辑合并, 原点贴图
- `build_room.build_table(mats)` — 构建带软包边、裙板、装饰钉和车削腿的赌桌 | keywords: build-table, roulette-table, 构建赌桌, 轮盘赌桌
- `build_room.build_lamp(mats)` — 构建双层搪瓷灯罩、电线灯座以及独立灯泡子节点 | keywords: build-lamp, industrial-lamp, 构建吊灯, 工业吊灯
- `build_room.make_poster(mats)` — 创建带卷角且以整张标签图映射的竖版海报 | keywords: poster-label, curled-corner, 海报标签, 卷起角
- `build_room.make_speaker_cone(name, center, radius, mats)` — 创建朝房间内部凹入的低模扬声器纸盆 | keywords: speaker-cone, recessed-driver, 扬声器纸盆, 凹陷单元
- `build_room.build_floor_walls(mats)` — 构建地板、三面混凝土墙和天花板基础体块 | keywords: room-shell, basement-walls, 房间外壳, 地下室墙体
- `build_room.build_pipes(mats)` — 构建后墙与左墙锈管、管箍、托架和红色阀门手轮 | keywords: build-pipes, valve-piping, 构建管道, 阀门管路
- `build_room.build_door_and_exit(mats)` — 构建后墙木门、分格、门把手和带护罩的红色出口灯 | keywords: door-exit, guarded-light, 门与出口灯, 护罩灯
- `build_room.build_speakers(mats)` — 构建朝房间中心略微偏转的双层音箱堆 | keywords: build-speakers, speaker-stack, 构建音箱, 音箱堆叠
- `build_room.build_crates(mats)` — 构建右墙木箱堆以及箱顶的空琥珀酒瓶 | keywords: build-crates, bottle-stack, 构建木箱, 酒瓶堆放
- `build_room.build_room(mats)` — 汇总地下室全部顶层逻辑节点并统一设置世界原点 | keywords: build-room, room-assembly, 构建房间, 房间装配
- `build_room.render_all_previews(table, lamp, room_objects)` — 从玩家、桌面、房间、裂缝和排水口机位渲染检查图 | keywords: preview-angles, scene-review, 预览角度, 场景检查
- `build_room.main()` — 重置场景，构建、导出模型，打印预算并渲染预览 | keywords: build-entry, export-assets, 构建入口, 导出资产

## 关键词索引 (Keyword Index)

| 中文 | English |
|---|---|
| 坐标换算 | godot-to-blender |
| Godot坐标 | coordinate-convert |
| 轴向旋转 | axis-rotation |
| 图元朝向 | primitive-orient |
| 重置场景 | reset-scene |
| 清空场景 | clear-scene |
| 命名材质 | named-material |
| 材质键 | material-key |
| 指定材质 | assign-material |
| 材质槽 | material-slot |
| 加入场景 | link-object |
| 场景集合 | scene-collection |
| 网格物体 | mesh-object |
| 生成物体 | bmesh-to-object |
| 盒子 | box-primitive |
| 立方体 | cube |
| 圆柱 | cylinder-primitive |
| 圆台 | tube |
| 球体 | sphere-primitive |
| 椭球 | uv-sphere |
| 车削 | lathe |
| 旋转体 | revolve-profile |
| 欧拉角换算 | euler-convert |
| 旋转顺序 | yxz-order |
| 倒角 | bevel-modifier |
| 边缘高光 | edge-highlight |
| 应用修改器 | apply-modifiers |
| 应用变换 | apply-transform |
| 合并物体 | join-objects |
| 合并网格 | merge-mesh |
| 填充顶点色 | fill-vertex-color |
| 颜色属性 | color-attribute |
| 触手 | tentacle-tube |
| 摆动约定 | sway-convention |
| 设置原点 | set-origin |
| 枢轴 | pivot |
| 父子关系 | parent-object |
| 层级 | hierarchy |
| 盒式UV | box-uv |
| 投影展开 | triplanar-projection |
| 平滑着色 | smooth-shading |
| 自动光滑 | auto-smooth |
| 三角面数 | triangle-count |
| 面数预算 | poly-budget |
| 导出模型 | export-glb |
| 导出glb | gltf-export |
| 渲染预览 | render-preview |
| 预览图 | eevee-render |
| 读取图片 | load-image |
| 读像素 | read-pixels |
| 保存图片 | save-image |
| 写PNG | write-png |
| 居中裁切 | center-crop |
| 宽高比 | aspect-ratio |
| 无缝平铺 | seamless-tile |
| 交叉淡化 | crossfade |
| 重采样矩阵 | resample-matrix |
| 盒式滤波 | box-filter |
| 面积缩小 | area-downscale |
| 重采样 | resample |
| 调色 | color-grade |
| 饱和度 | saturation |
| 特效透明 | sprite-alpha |
| 反预乘 | unpremultiply |
| 贴花透明 | decal-alpha |
| 颜料遮罩 | paint-mask |
| 贴图加工 | process-texture |
| 贴图流水线 | texture-pipeline |
| 批量处理 | process-all |
| 全部贴图 | batch-textures |
| 轮廓挤出 | profile-extrusion |
| 硬表面 | hard-surface |
| 路径圆管 | path-tube |
| 扳机几何 | trigger-geometry |
| 样条插值 | catmull-rom |
| 平滑曲线 | smooth-curve |
| 截面放样 | loft-rings |
| 木纹UV | wood-grain-uv |
| 截面UV | ring-uv |
| 木纹坐标 | grain-coords |
| 圆角截面 | rounded-section |
| 超椭圆 | superellipse |
| 放样枪托 | lofted-stock |
| 手枪握把 | pistol-grip |
| 材质排序 | material-order |
| 表面槽位 | surface-slots |
| 霰弹枪材质 | shotgun-materials |
| 预览着色 | preview-shading |
| 枪身主体 | shotgun-body |
| 机匣枪托 | receiver-stock |
| 前段枪管 | barrel-front |
| 锯短部件 | sawed-section |
| 前准星 | front-sight |
| 黄铜珠 | brass-bead |
| 泵动护木 | pump-forearm |
| 环形凹槽 | ring-grooves |
| 霰弹枪预览 | shotgun-preview |
| 锯短预览 | sawed-preview |
| 构建霰弹枪 | build-shotgun |
| 导出霰弹枪 | export-shotgun |
| 霰弹塑料壳 | shell-hull |
| 星形折口 | star-crimp |
| 霰弹材质排序 | shell-material-order |
| 构建霰弹 | build-shell |
| 十二号口径 | twelve-gauge |
| 霰弹预览 | shell-preview |
| 近景渲染 | close-up |
| 导出霰弹 | export-shell |
| 霰弹流程 | shell-pipeline |
| 道具材质 | item-materials |
| 材质键 | material-keys |
| 圆环 | torus-ring |
| 低模环 | low-poly-ring |
| 多边形棱柱 | polygon-prism |
| 自定义轮廓 | custom-outline |
| 标签面 | label-quad |
| 整图UV | full-image-uv |
| 圆盘标签 | label-disk |
| 径向UV | radial-uv |
| 完成道具 | finish-item |
| 单根节点 | single-root |
| 构建放大镜 | build-magnifier |
| 桌面道具 | tabletop-prop |
| 构建香烟 | build-cigarette |
| 打开烟盒 | open-cigarette-pack |
| 构建啤酒 | build-beer |
| 凹陷罐 | dented-can |
| 带孔棱柱 | ring-prism |
| 镂空轮廓 | holed-outline |
| 圆角轮廓 | rounded-outline |
| 不规则斑块 | irregular-blot |
| 锈斑 | rust-patch |
| 构建手锯 | build-saw |
| 锯齿刀片 | toothed-blade |
| 构建手铐 | build-handcuffs |
| 链接双环 | chained-rings |
| 构建手机 | build-phone |
| 直板机 | candybar-phone |
| 构建反转器 | build-inverter |
| 发光装置 | glowing-device |
| 构建药瓶 | build-medicine |
| 过期药 | pill-bottle |
| 单件预览 | isolated-preview |
| 道具近景 | item-closeup |
| 构建全部道具 | build-all-items |
| 导出预览 | export-previews |
| 行刑人材质 | dealer-materials |
| 命名材质 | named-materials |
| 顶点色材质 | vertex-color-material |
| 皮肤预览 | skin-preview |
| 高斯衰减 | gaussian-falloff |
| 雕刻笔刷 | sculpt-brush |
| 平滑过渡 | smoothstep |
| 插值 | smooth-transition |
| 笑弧 | smile-curve |
| 嘴型曲线 | mouth-arc |
| 张口高度 | mouth-opening |
| 嘴宽 | smile-height |
| 缝线 | stitch-seam |
| 嘴角 | mouth-corner |
| 缝线距离 | seam-distance |
| 点线距离 | point-segment |
| 蛋形头骨 | egg-skull |
| 基本形 | base-shape |
| 头部雕刻 | head-sculpt |
| 位移塑形 | displacement-shape |
| 顶点色 | vertex-color |
| 烘焙明暗 | baked-shading |
| 颜色插值 | color-lerp |
| 混色 | mix-color |
| 定向盒子 | oriented-box |
| 表面细节 | surface-detail |
| 正面射线 | front-raycast |
| 表面采样 | surface-sample |
| 圆角截面 | superellipse |
| 放样截面 | loft-section |
| 截面放样 | loft-mesh |
| 管状网格 | section-sweep |
| 贴身衣片 | surface-panel |
| 投影贴片 | projected-decal |
| 两点圆锥 | cone-between |
| 尖锐细节 | pointed-detail |
| 两点圆柱 | cylinder-between |
| 肢体分节 | limb-segment |
| 行刑人椅子 | dealer-chair |
| 高背椅 | high-back-chair |
| 行刑人躯干 | dealer-body |
| 三件套西装 | three-piece-suit |
| 行刑人头部 | dealer-head |
| 咧嘴骷髅 | grinning-skull |
| 头部表面 | head-surface |
| 射线取点 | raycast-fallback |
| 触手须 | tentacle-beard |
| 克苏鲁下颌 | cthulhu-jaw |
| 骨感手掌 | skeletal-hand |
| 分节手指 | articulated-fingers |
| 手臂分段 | arm-segment |
| 单位袖管 | unit-sleeve |
| 肘关节 | elbow-joint |
| 关节球 | sleeve-ball |
| 握拳弧线 | fist-curl |
| 手指弯曲 | finger-arc |
| 握拳手 | gripping-fist |
| 握枪手 | gun-grip-hand |
| 两段IK | two-bone-ik |
| 肘部求解 | elbow-solve |
| 预览手臂段 | preview-segment |
| 两点摆放 | place-between |
| 重置变换 | reset-transform |
| 导出就绪 | export-ready |
| 行刑人预览 | dealer-previews |
| 视觉检查 | visual-inspection |
| 行刑人统计 | dealer-statistics |
| 三角面预算 | triangle-budget |
| 构建行刑人 | build-dealer |
| 导出行刑人 | export-dealer |
| 房间材质 | room-materials |
| 圆环图元 | torus-primitive |
| 环形网格 | ring-mesh |
| 点间圆梁 | point-beam |
| 圆柱连接 | cylinder-link |
| 逻辑合并 | logical-join |
| 原点贴图 | origin-uv |
| 构建赌桌 | build-table |
| 轮盘赌桌 | roulette-table |
| 构建吊灯 | build-lamp |
| 工业吊灯 | industrial-lamp |
| 海报标签 | poster-label |
| 卷起角 | curled-corner |
| 扬声器纸盆 | speaker-cone |
| 凹陷单元 | recessed-driver |
| 房间外壳 | room-shell |
| 地下室墙体 | basement-walls |
| 构建管道 | build-pipes |
| 阀门管路 | valve-piping |
| 门与出口灯 | door-exit |
| 护罩灯 | guarded-light |
| 构建音箱 | build-speakers |
| 音箱堆叠 | speaker-stack |
| 构建木箱 | build-crates |
| 酒瓶堆放 | bottle-stack |
| 构建房间 | build-room |
| 房间装配 | room-assembly |
| 预览角度 | preview-angles |
| 场景检查 | scene-review |
| 构建入口 | build-entry |
| 导出资产 | export-assets |

## 模块功能描述 (Module Description)

**重新生成**（工作目录为仓库根，Blender 4.5 LTS）：

- 贴图：`blender -b --factory-startup --python art/blender/process_textures.py`（读 `art/source/textures|labels/*.png`，写 `art/textures/*.png`；裁切尺寸、平铺模式、亮度/饱和度在脚本顶部 `SPECS` 表里）。
- 模型：`blender -b --factory-startup --python art/blender/build_<名字>.py`，每个脚本同时把检查图渲染到 `art/source/previews/<分组>/`。
- 改完后在 Godot 里重新导入（`godot --headless --path . --import`）。贴图的 `.import` 已设为无损 + 生成 mipmap，glb 的 `.import` 已关闭自动 LOD，重新导入会保留这些设置。

**约定**（所有 `build_*.py` 遵守，游戏代码依赖它们）：

- 坐标按 Godot 描述：x 右、y 上、+z 朝玩家/镜头，单位米，用 `kit.g()` 换成 Blender 坐标；导出 Y 轴朝上。
- 材质名 = `scripts/props.gd` 里 `Props.MATERIALS` 的 key（`wood`、`metal`、`skin`、`hull` …）。glb 里只有占位颜色、不嵌贴图；游戏加载模型后按材质名换成带像素贴图的材质。新增材质 key 要同时加进 `Props.MATERIALS`。
- 每个顶层物体 = glb 场景根下的一个直接子节点，物体名就是节点名。游戏按名字取节点：枪的 `Pump`（原点 (0,-0.022,-0.24)，拉枪栓时沿 z 移动）、`BarrelFront`/`Sight`（锯短枪管时隐藏）；行刑人的 `Head`（原点 (0,1,-1.2)，每帧摇晃，瞳孔 `PupilL`/`PupilR`/`PupilF1..3` 是它的子节点）、`HandL`/`HandR`（张开的手，原点在掌心底部）、`GripL`/`GripR`（握枪时换上的握拳手，原点在被握的杆中心、杆沿本地 X、手腕在 `FIST_WRIST`）、`UpperArmL/R` 和 `ForearmL/R`（沿本地 Y 长 1 米、原点居中、-y 端是近端，每帧由两段 IK 拉伸到肩→肘→腕）、`ElbowL/R`（肘关节球）。手臂长度、肘部弯曲方向、`FIST_WRIST` 要和 `scripts/table_scene.gd` 的同名常量一致。
- 子弹、道具原点在底面中心；霰弹枪枪口朝 -z、枪口在 z = -0.63。
- 平铺材质用 `kit.box_uv()` 世界空间投影（米/每次平铺见各脚本）；标签类材质（烟盒、啤酒罐、药瓶、手机、反转器、弹壳、海报、法阵、血字）手动做 UV，整张标签图铺满对应面。
- 行刑人头部不分材质区：眼窝、额头三只小眼、口腔、缝线的明暗烘焙在顶点色 `Col` 里（`head_color`），导出时 `vertex_color="ACTIVE"`，游戏里 `skin` 材质开启 `vertex_color_use_as_albedo`。
- `kit.join()` 会把所有部件的 UV 统一成一层 `UVMap`（Godot 只读第一层 UV），只要有部件带 `Col` 就给其余部件补白色 `Col`。
- **触手**一律用 `kit.tentacle()` 生成、材质名 `tentacle`：UV.x 绕一圈、UV.y 从根 0 到尖 1；顶点色 R = 摆动相位、G = 尖端摆幅（米 ×10）、B = 长度（米 ÷2）；`suckers` 参数决定吸盘那一面朝哪。游戏里由 `shaders/tentacle.gdshader` 做摆动。用到触手的 glb（`dealer.glb`、`room.glb`）导出时要带 `vertex_color="ACTIVE"`。
- **房间里的克苏鲁元素**（`build_room.py` 的 `build_room()`）：后墙门左边的裂缝 `WallCrack`（破碎混凝土边、腐肉、黑色内腔）和从里面伸出的 `Tentacles`，左后角排水口 `FloorTentacles`，两组融化的仪式蜡烛 `Candles`（木箱顶上一组、排水口旁一组），左墙和后墙的血字 `Scrawl`，桌面中央的血色法阵（`Table` 的 `sigil` 面）。蜡烛火焰和裂缝的位置要和 `scripts/table_scene.gd` 的 `CANDLE_LIGHTS` / `CRACK_LIGHT_POS` 对齐。

**贴图来源**：`art/source/` 里的原图都是 Codex 内置图像生成画的，品牌名均为虚构：概念参考图 8 张（含克苏鲁版行刑人正侧视、头部特写、房间氛围图）；可平铺材质 12 张（深海鳞皮 `skin_deep`、触手 `tentacle`、腐肉 `flesh` 等）；标签/贴花/特效 12 张（法阵 `sigil`、血字 `scrawl`、邪教海报 `poster_cult` 等）。`process_textures.py` 里 `decal` 模式把黑底颜料图转成半透明贴花。旧版的 `skin.png`、`poster.png` 原图保留但不再使用。

**音乐来源**：两首都是 Ruskerdax 发布在 OpenGameArt 上的 CC0（公有领域）曲目，可以随意使用、修改、商用，不要求署名（README 里仍然注明了出处）。原始 MP3 下载后只做了两件事：去掉结尾约 2 秒的静音、加 1.5 秒淡出，然后转成 OGG Vorbis（q6）。
- `omen.ogg` — "Omen"（受早期 Nine Inch Nails 和恐怖片启发的工业曲，3:44），https://opengameart.org/content/omen
- `bleak_terminal.ogg` — "Bleak Terminal"（科幻/恐怖氛围曲，1:50），https://opengameart.org/content/bleak-terminal
