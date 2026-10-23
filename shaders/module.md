# shaders 模块

## 模块名称 (Module Name)

shaders · 着色器

## 概述 (Overview)

画面后期和场景特效用的着色器。

## 文件清单 (File List)

- `post.gdshader` — canvas_item 后期：色差、分离色调（暗部偏青）、颗粒、暗角、扫描线、闪光/黑屏，最后 Bayer 有序抖动 + 色阶量化。挂在 `main.gd` 的 SubViewportContainer 上。
- `light_cone.gdshader` — spatial 加色光锥，GL Compatibility 下代替体积雾。挂在 `table_scene.gd` 的吊灯下。
- `tentacle.gdshader` — spatial 触手：顶点沿长度正弦摆动（根部不动），吸盘贴图按真实长度平铺，湿滑高光。`Props.tentacle_material()` 创建，模型里材质名为 `tentacle` 的面都用它。

## 函数清单 (Function List)

- `post.hash(p)` — 屏幕像素坐标的伪随机数（颗粒用） | keywords: screen-hash, grain-noise, 伪随机, 颗粒噪声
- `post.fragment()` — 每个像素：色差 → 色调 → 颗粒 → 暗角 → 扫描线 → 闪光/黑屏 → Bayer 抖动 + 色阶量化 | keywords: post-process, bayer-dither, 后期处理, 像素抖动
- `light_cone.fragment()` — 视线正对处最亮、上浓下淡，乘上吊灯闪烁 | keywords: light-cone-shading, fake-volumetric, 光锥着色, 体积光
- `tentacle.vertex()` — 摆动：两个方向上频率不同的正弦叠加，按 UV.y² 加权，根部固定 | keywords: tentacle-sway, vertex-animation, 触手摆动, 顶点动画
- `tentacle.fragment()` — 吸盘贴图按真实长度平铺，湿滑的高光 | keywords: tentacle-shading, sucker-texture, 触手着色, 吸盘贴图

## 关键词索引 (Keyword Index)

| 中文 | English |
|---|---|
| 伪随机 | screen-hash |
| 颗粒噪声 | grain-noise |
| 后期处理 | post-process |
| 像素抖动 | bayer-dither |
| 光锥着色 | light-cone-shading |
| 体积光 | fake-volumetric |
| 触手摆动 | tentacle-sway |
| 顶点动画 | vertex-animation |
| 触手着色 | tentacle-shading |
| 吸盘贴图 | sucker-texture |

## 模块功能描述 (Module Description)

- `post.gdshader` 的 uniform：`levels`（色阶数）、`dither_strength`、`grain`、`vignette`、`scanline`、`aberration`、`tint`（整体色调）、`shadow_tint` / `shadow_tint_amount`（暗部偏色）、`flash_color`、`fade`。`main.gd` 只改 `flash_color` 和 `fade`。
- `light_cone.gdshader` 的 uniform：`color`、`strength`、`flicker`（`table_scene.gd` 每帧按吊灯亮度写入）。用在顶部开口的 CylinderMesh 上，UV.y 从顶端 0 到底端 1。
- `tentacle.gdshader` 依赖 `art/blender/kit.py` 的 `tentacle()` 网格约定：UV.x 绕一圈、UV.y 从根 0 到尖 1；顶点色 R = 摆动相位，G = 尖端摆幅（米 ×10），B = 触手长度（米 ÷2）。uniform：`albedo_tex`、`tint`（行刑人中弹时变红）、`speed`、`tile_length`（每隔多少米重复一次吸盘）。
