"""把 Codex 生成的原图（art/source/textures、art/source/labels，约 1024px）加工成游戏用的低分辨率贴图。

步骤：按目标比例居中裁切 → 需要平铺的做交叉淡化无缝处理 → 面积平均缩小 → 调亮度/饱和度 →
特效贴图用亮度生成 alpha → 写到 art/textures/<名字>.png。

运行：blender -b --factory-startup --python art/blender/process_textures.py
"""

import os

import bpy
import numpy as np

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SOURCE_DIR = os.path.join(ROOT, "art", "source")
OUT_DIR = os.path.join(ROOT, "art", "textures")

# 名字: (源文件, 输出宽, 输出高, 模式, 亮度, 饱和度)
# 模式：tile = 双向无缝；tile_x = 只做左右无缝（绕圆柱一圈的标签）；plain = 只缩放；sprite = 黑底特效，亮度当 alpha；
#       decal = 黑底颜料贴花（法阵、血字），稍亮一点就不透明
SPECS = {
    "felt": ("textures/felt.png", 256, 256, "tile", 0.62, 0.6),
    "wood": ("textures/wood.png", 128, 128, "tile", 1.0, 0.95),
    "concrete": ("textures/concrete.png", 256, 256, "tile", 0.9, 0.8),
    "tiles": ("textures/tiles.png", 256, 256, "plain", 0.8, 0.8),
    "metal": ("textures/metal.png", 128, 128, "tile", 1.0, 0.7),
    "rust": ("textures/rust.png", 128, 128, "tile", 0.85, 0.85),
    "cloth": ("textures/cloth.png", 128, 128, "tile", 1.0, 0.8),
    "skin": ("textures/skin_deep.png", 256, 256, "tile", 1.0, 0.9),
    "tentacle": ("textures/tentacle.png", 64, 96, "tile", 1.0, 1.0),
    "flesh": ("textures/flesh.png", 128, 128, "tile", 0.9, 1.0),
    "sigil": ("labels/sigil.png", 192, 192, "decal", 1.0, 1.0),
    "scrawl": ("labels/scrawl.png", 192, 128, "decal", 1.0, 1.0),
    "leather": ("textures/leather.png", 128, 128, "tile", 1.0, 0.9),
    "cigs": ("labels/cigs.png", 64, 96, "plain", 1.0, 1.0),
    "beer": ("labels/beer.png", 128, 64, "tile_x", 1.0, 1.0),
    "pills": ("labels/pills.png", 128, 64, "tile_x", 1.0, 1.0),
    "phone": ("labels/phone.png", 64, 96, "plain", 1.0, 1.0),
    "inverter": ("labels/inverter.png", 96, 96, "plain", 1.0, 1.0),
    "shell_hull": ("labels/shell_hull.png", 64, 96, "tile_x", 1.0, 0.0),
    "poster": ("labels/poster_cult.png", 96, 144, "plain", 0.9, 0.9),
    "muzzle_flash": ("labels/muzzle_flash.png", 128, 128, "sprite", 1.0, 1.0),
    "smoke": ("labels/smoke.png", 128, 128, "sprite", 1.0, 0.0),
}
SEAM_BAND = 0.12

def load_rgba(path):
    """读 PNG 为 (高, 宽, 4) 的 float 数组（Blender 的行序：从下往上，读写一致即可）。

    @keyword-en load-image, read-pixels
    @keyword-cn 读取图片, 读像素
    """
    img = bpy.data.images.load(path)
    w, h = img.size
    buf = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(buf)
    bpy.data.images.remove(img)
    return buf.reshape(h, w, 4)

def save_rgba(arr, path, alpha):
    """把 (高, 宽, 4) float 数组写成 PNG（alpha=False 时存 RGB）。

    @keyword-en save-image, write-png
    @keyword-cn 保存图片, 写PNG
    """
    h, w, _ = arr.shape
    img = bpy.data.images.new(os.path.basename(path), w, h, alpha=alpha)
    img.pixels.foreach_set(np.ascontiguousarray(arr, dtype=np.float32).ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)

def crop_to_aspect(arr, w, h):
    """居中裁切到目标宽高比。

    @keyword-en center-crop, aspect-ratio
    @keyword-cn 居中裁切, 宽高比
    """
    sh, sw, _ = arr.shape
    target = w / h
    if sw / sh > target:
        cw = int(round(sh * target))
        x0 = (sw - cw) // 2
        return arr[:, x0:x0 + cw]
    ch = int(round(sw / target))
    y0 = (sh - ch) // 2
    return arr[y0:y0 + ch]

def seamless_axis(arr, axis):
    """沿一个轴做交叉淡化无缝：去掉末尾一条带，把它淡入到开头，使首尾相接处连续。

    @keyword-en seamless-tile, crossfade
    @keyword-cn 无缝平铺, 交叉淡化
    """
    a = np.moveaxis(arr, axis, 0)
    n = a.shape[0]
    band = max(2, int(n * SEAM_BAND))
    keep = n - band
    out = a[:keep].copy()
    t = (np.arange(band, dtype=np.float32) / band)
    t = t * t * (3.0 - 2.0 * t)
    t = t.reshape((band,) + (1,) * (a.ndim - 1))
    out[:band] = a[keep:] * (1.0 - t) + a[:band] * t
    return np.moveaxis(out, 0, axis)

def _area_matrix(src, dst):
    """面积平均重采样矩阵 (dst × src)：每个目标像素平均它覆盖的源像素（按覆盖比例加权）。
    @keyword-en resample-matrix, box-filter
    @keyword-cn 重采样矩阵, 盒式滤波
    """
    m = np.zeros((dst, src), dtype=np.float32)
    scale = src / dst
    for i in range(dst):
        lo, hi = i * scale, (i + 1) * scale
        for j in range(int(np.floor(lo)), min(src, int(np.ceil(hi)))):
            m[i, j] = min(hi, j + 1) - max(lo, j)
        m[i] /= m[i].sum()
    return m

def downscale(arr, w, h):
    """面积平均缩小到 w × h（不模糊、不锐化，像素块干净）。

    @keyword-en area-downscale, resample
    @keyword-cn 面积缩小, 重采样
    """
    rows = np.tensordot(_area_matrix(arr.shape[0], h), arr, axes=(1, 0))
    return np.einsum("lk,ikc->ilc", _area_matrix(arr.shape[1], w), rows)

def grade(arr, brightness, saturation):
    """调亮度与饱和度（在 sRGB 值上做，够用）。

    @keyword-en color-grade, saturation
    @keyword-cn 调色, 饱和度
    """
    rgb = arr[..., :3]
    lum = (rgb * np.array([0.299, 0.587, 0.114], dtype=np.float32)).sum(-1, keepdims=True)
    rgb = (lum + (rgb - lum) * saturation) * brightness
    arr[..., :3] = np.clip(rgb, 0.0, 1.0)
    return arr

def sprite_alpha(arr):
    """黑底特效图：用最大通道当 alpha，并把颜色除回去（反预乘），边缘不会发黑。

    @keyword-en sprite-alpha, unpremultiply
    @keyword-cn 特效透明, 反预乘
    """
    rgb = arr[..., :3]
    # 生成图的"纯黑底"其实带 0.1 左右的噪点，阈值以下全部算透明
    a = np.clip((rgb.max(-1) - 0.12) / 0.88, 0.0, 1.0)
    arr[..., 3] = a
    arr[..., :3] = np.clip(rgb / np.maximum(a[..., None], 1e-3), 0.0, 1.0)
    return arr

def decal_alpha(arr):
    """黑底贴花（法阵、血字）：暗红颜料本身就不亮，所以亮度只要过一点阈值就基本不透明，颜色反预乘回去。
    @keyword-en decal-alpha, paint-mask
    @keyword-cn 贴花透明, 颜料遮罩
    """
    rgb = arr[..., :3]
    a = np.clip((rgb.max(-1) - 0.07) * 4.0, 0.0, 1.0)
    arr[..., 3] = a
    arr[..., :3] = np.clip(rgb / np.maximum(a[..., None], 1e-3), 0.0, 1.0)
    return arr

def process(name, spec):
    """按 SPECS 里的一行加工一张贴图并写出。源文件不存在时跳过。

    @keyword-en process-texture, texture-pipeline
    @keyword-cn 贴图加工, 贴图流水线
    """
    src, w, h, mode, brightness, saturation = spec
    path = os.path.join(SOURCE_DIR, src)
    if not os.path.exists(path):
        print("SKIP (missing)", name)
        return
    arr = crop_to_aspect(load_rgba(path), w, h)
    arr[..., 3] = 1.0
    if mode == "tile":
        arr = seamless_axis(seamless_axis(arr, 1), 0)
    elif mode == "tile_x":
        arr = seamless_axis(arr, 1)
    arr = grade(downscale(arr, w, h), brightness, saturation)
    if mode == "sprite":
        arr = sprite_alpha(arr)
    elif mode == "decal":
        arr = decal_alpha(arr)
    out = os.path.join(OUT_DIR, name + ".png")
    save_rgba(arr, out, alpha=mode in ("sprite", "decal"))
    print("TEXTURE", name, w, h, mode)

def main():
    """处理全部贴图。

    @keyword-en process-all, batch-textures
    @keyword-cn 批量处理, 全部贴图
    """
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, spec in SPECS.items():
        process(name, spec)

main()
