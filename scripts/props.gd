class_name Props
extends RefCounted
## 模型、材质和贴图的入口。模型由 art/blender/ 下的 Blender 脚本生成（art/models/*.glb），
## 贴图由 Codex 生成后经 art/blender/process_textures.py 缩成像素贴图（art/textures/*.png）。
## glb 里的材质只是占位：加载时按材质名换成这里定义的材质（像素贴图 + 最近邻采样）。
## 模型约定：霰弹枪枪口朝本地 -Z；子弹、道具的原点在底部中心。

## 模型和贴图目录（由 art 模块生成）
## @keyword-cn 资源目录, 模型目录
## @keyword-en asset-dir, model-dir
const MODEL_DIR := "res://art/models/"
const TEXTURE_DIR := "res://art/textures/"
## 触手摆动着色器
## @keyword-cn 触手着色器, 顶点动画
## @keyword-en tentacle-shader, vertex-animation
const TENTACLE_SHADER := preload("res://shaders/tentacle.gdshader")

## 材质表：key → [颜色, 粗糙度, 金属度, 贴图名（空 = 无贴图）, 自发光强度（0 = 不发光）]
## key 与 Blender 脚本里的材质名逐字一致。
## @keyword-cn 材质规格, 材质键
## @keyword-en material-spec, material-key
const MATERIALS := {
	"felt": [Color(1, 1, 1), 0.95, 0.0, "felt", 0.0],
	"wood": [Color(1, 1, 1), 0.6, 0.0, "wood", 0.0],
	"wood_dark": [Color(0.5, 0.45, 0.42), 0.75, 0.0, "wood", 0.0],
	"leather": [Color(0.9, 0.85, 0.85), 0.55, 0.0, "leather", 0.0],
	"concrete": [Color(0.85, 0.85, 0.85), 0.95, 0.0, "concrete", 0.0],
	"tiles": [Color(0.8, 0.8, 0.8), 0.55, 0.0, "tiles", 0.0],
	"metal": [Color(1, 1, 1), 0.4, 0.7, "metal", 0.0],
	"metal_dark": [Color(0.55, 0.55, 0.58), 0.5, 0.6, "metal", 0.0],
	"metal_bright": [Color(0.85, 0.87, 0.9), 0.25, 0.85, "", 0.0],
	"rust": [Color(1, 1, 1), 0.9, 0.3, "rust", 0.0],
	"brass": [Color(0.8, 0.6, 0.22), 0.35, 0.8, "", 0.0],
	"rubber": [Color(0.04, 0.04, 0.04), 0.9, 0.0, "", 0.0],
	"black": [Color(0.01, 0.01, 0.01), 1.0, 0.0, "", 0.0],
	"plastic_black": [Color(0.05, 0.05, 0.055), 0.45, 0.0, "", 0.0],
	"cloth": [Color(1, 1, 1), 1.0, 0.0, "cloth", 0.0],
	"shirt": [Color(0.7, 0.68, 0.62), 0.9, 0.0, "", 0.0],
	"tie": [Color(0.45, 0.04, 0.04), 0.55, 0.0, "", 0.0],
	"skin": [Color(1, 1, 1), 0.7, 0.0, "skin", 0.0],
	"teeth": [Color(0.86, 0.8, 0.6), 0.45, 0.0, "", 0.0],
	"mouth": [Color(0.12, 0.01, 0.02), 1.0, 0.0, "", 0.0],
	"hull": [Color(1, 1, 1), 0.5, 0.0, "shell_hull", 0.0],
	"lens": [Color(0.6, 0.85, 0.95, 0.45), 0.05, 0.0, "", 0.3],
	"cigs": [Color(1, 1, 1), 0.8, 0.0, "cigs", 0.0],
	"paper": [Color(0.92, 0.91, 0.87), 0.9, 0.0, "", 0.0],
	"filter": [Color(0.8, 0.5, 0.2), 0.9, 0.0, "", 0.0],
	"beer": [Color(1, 1, 1), 0.35, 0.5, "beer", 0.0],
	"pills": [Color(1, 1, 1), 0.8, 0.0, "pills", 0.0],
	"amber": [Color(0.55, 0.25, 0.05), 0.2, 0.0, "", 0.0],
	"cap_white": [Color(0.88, 0.88, 0.85), 0.6, 0.0, "", 0.0],
	"phone": [Color(1, 1, 1), 0.45, 0.0, "phone", 0.0],
	"inverter": [Color(1, 1, 1), 0.5, 0.4, "inverter", 0.0],
	"inverter_glow": [Color(0.78, 0.42, 0.98), 1.0, 0.0, "", 1.6],
	"red_paint": [Color(0.55, 0.08, 0.05), 0.6, 0.0, "", 0.0],
	"lamp_shade": [Color(0.2, 0.28, 0.22), 0.5, 0.3, "", 0.0],
	"lamp_inner": [Color(0.85, 0.82, 0.72), 0.6, 0.0, "", 0.0],
	"bulb": [Color(1, 0.85, 0.6), 1.0, 0.0, "", 3.0],
	"poster": [Color(0.9, 0.9, 0.9), 0.9, 0.0, "poster", 0.0],
	"speaker": [Color(0.03, 0.03, 0.03), 0.9, 0.0, "", 0.0],
	"exit_glow": [Color(1, 0.15, 0.1), 1.0, 0.0, "", 2.5],
	"slot": [Color(1, 1, 1), 1.0, 0.0, "", 0.0],
	"flesh": [Color(0.9, 0.85, 0.85), 0.45, 0.0, "flesh", 0.0],
	"wax": [Color(0.78, 0.74, 0.62), 0.6, 0.0, "", 0.0],
	"claw": [Color(0.13, 0.11, 0.1), 0.35, 0.0, "", 0.0],
	"candle_glow": [Color(1, 0.62, 0.25), 1.0, 0.0, "", 3.0],
	"sigil": [Color(0.42, 0.2, 0.2, 0.8), 0.95, 0.0, "sigil", 0.0],
	"scrawl": [Color(0.55, 0.3, 0.3, 0.9), 0.95, 0.0, "scrawl", 0.0],
	"eye_wet": [Color(0.05, 0.015, 0.015), 0.08, 0.0, "", 0.0],
	# 行刑人三个形态的部件
	"porcelain": [Color(0.82, 0.8, 0.76), 0.45, 0.0, "", 0.0],
	"hat": [Color(0.45, 0.45, 0.5), 0.35, 0.0, "cloth", 0.0],
	"bone": [Color(0.78, 0.72, 0.58), 0.5, 0.0, "", 0.0],
	"vein_glow": [Color(0.45, 1.0, 0.5), 1.0, 0.0, "", 1.4],
	"eye_white": [Color(0.85, 0.8, 0.62), 0.2, 0.0, "", 0.0],
	"iris_glow": [Color(1.0, 0.45, 0.1), 1.0, 0.0, "", 2.4],
}

static var _cache := {}


# ---------------------------------------------------------------- 网格节点（特效、光锥和桌上的道具格在用）

## 生成一个网格节点挂到 parent 下
## @keyword-cn 网格节点, 拼装部件
## @keyword-en mesh-part, add-mesh
static func part(parent: Node3D, mesh: Mesh, material: Material, pos := Vector3.ZERO,
		rot := Vector3.ZERO, scl := Vector3.ONE, node_name := "") -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.material_override = material
	mi.position = pos
	mi.rotation = rot
	mi.scale = scl
	if node_name != "":
		mi.name = node_name
	parent.add_child(mi)
	return mi


# ---------------------------------------------------------------- 材质

## 新建一个最近邻采样的标准材质
## @keyword-cn 新建材质, 像素材质
## @keyword-en new-material, pixel-material
static func mat(color: Color, roughness := 0.85, metallic := 0.0, texture: Texture2D = null) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.roughness = roughness
	m.metallic = metallic
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST_WITH_MIPMAPS
	if texture:
		m.albedo_texture = texture
	return m


## 不受光照影响的发光材质
## @keyword-cn 发光材质, 自发光
## @keyword-en glow-material, emissive
static func glow(color: Color, energy := 2.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.albedo_color = color
	m.emission_enabled = true
	m.emission = color
	m.emission_energy_multiplier = energy
	return m


## 按 key 取材质表里的材质，按名字缓存共享
## @keyword-cn 材质表, 材质缓存
## @keyword-en material-table, material-cache
static func material(key: String) -> StandardMaterial3D:
	if _cache.has(key):
		return _cache[key]
	var m: StandardMaterial3D
	if not MATERIALS.has(key):
		m = mat(Color.MAGENTA)
	else:
		var spec: Array = MATERIALS[key]
		var energy: float = spec[4]
		var tex_name: String = spec[3]
		if key == "slot":
			m = mat(Color.WHITE, 1.0, 0.0, _slot_texture())
		elif energy > 0.0 and key != "lens":
			m = glow(spec[0], energy)
		else:
			m = mat(spec[0], spec[1], spec[2], pixel_texture(tex_name) if tex_name != "" else null)
		if key in ["skin", "porcelain"]:
			# 行刑人头部的眼窝、口腔、缝线（面具上画的眼线、笑和裂纹）是烘焙在顶点色里的；没有顶点色的网格按白色处理
			m.vertex_color_use_as_albedo = true
		elif key in ["slot", "sigil", "scrawl"]:
			m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		if key == "lens":
			m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			m.emission_enabled = true
			m.emission = Color(0.15, 0.25, 0.3)
			m.emission_energy_multiplier = energy
	_cache[key] = m
	return m


## 触手材质（shaders/tentacle.gdshader，顶点摆动 + 吸盘贴图），所有触手共享；
## 行刑人要单独变色时自己 duplicate() 一份通过 overrides 传进 model()
## @keyword-cn 触手材质, 摆动着色器
## @keyword-en tentacle-material, sway-shader
static func tentacle_material() -> ShaderMaterial:
	if _cache.has("tentacle"):
		return _cache["tentacle"]
	var m := ShaderMaterial.new()
	m.shader = TENTACLE_SHADER
	m.set_shader_parameter("albedo_tex", pixel_texture("tentacle"))
	_cache["tentacle"] = m
	return m


## 弹壳塑料壳材质：同一张灰色贴图染成实弹红或空包弹蓝；glowing 时自发光（放大镜亮弹）
## @keyword-cn 弹壳材质, 实弹颜色
## @keyword-en shell-hull-material, live-blank-color
static func hull_material(live: bool, glowing := false) -> StandardMaterial3D:
	var key := "hull_%s%s" % ["live" if live else "blank", "_glow" if glowing else ""]
	if _cache.has(key):
		return _cache[key]
	var color := Color(0.85, 0.12, 0.08) if live else Color(0.16, 0.36, 0.85)
	var m := material("hull").duplicate() as StandardMaterial3D
	m.albedo_color = color
	if glowing:
		m.emission_enabled = true
		m.emission = color
		m.emission_energy_multiplier = 1.6
	_cache[key] = m
	return m


## 溅血贴图（白色，用材质颜色染色）：一团不规则的血斑、往外甩的尖刺和四周的小血点（程序生成，48×48）
## @keyword-cn 溅血贴图, 血斑
## @keyword-en blood-splat, splatter-texture
static func blood_splat_texture() -> ImageTexture:
	if _cache.has("blood_splat"):
		return _cache["blood_splat"]
	var rng := RandomNumberGenerator.new()
	rng.seed = 77
	var img := Image.create(48, 48, false, Image.FORMAT_RGBA8)
	var center := Vector2(24, 24)
	var lobes := []
	for _k in 7:
		lobes.append([rng.randf() * TAU, rng.randf_range(0.15, 0.4)])
	for y in 48:
		for x in 48:
			var d := Vector2(x, y) - center
			var a := d.angle()
			var r := 9.0
			for lobe in lobes:
				r += 4.0 * lobe[1] * cos(a * 3.0 + lobe[0]) + 3.0 * lobe[1] * cos(a * 7.0 + lobe[0] * 2.0)
			if d.length() < r:
				img.set_pixel(x, y, Color(1, 1, 1, 1))
	for _k in 9:
		var dir := Vector2.from_angle(rng.randf() * TAU)
		var length := rng.randf_range(6.0, 13.0)
		for t in int(length):
			var p := center + dir * (9.0 + t)
			if p.x >= 0 and p.y >= 0 and p.x < 48 and p.y < 48:
				img.set_pixelv(Vector2i(p), Color(1, 1, 1, 1))
	for _k in 16:
		var p := center + Vector2.from_angle(rng.randf() * TAU) * rng.randf_range(13.0, 22.0)
		var size := rng.randi_range(1, 2)
		for dy in size:
			for dx in size:
				var q := Vector2i(p) + Vector2i(dx, dy)
				if q.x >= 0 and q.y >= 0 and q.x < 48 and q.y < 48:
					img.set_pixelv(q, Color(1, 1, 1, 1))
	var tex := ImageTexture.create_from_image(img)
	_cache["blood_splat"] = tex
	return tex


## 加载 art/textures/ 下的像素贴图
## @keyword-cn 加载贴图, 像素贴图
## @keyword-en load-texture, pixel-texture
static func pixel_texture(tex_name: String) -> Texture2D:
	return load(TEXTURE_DIR + tex_name + ".png")


## 道具格：半透明深色底、浅色描边、四角加亮（程序生成，32×32）
## @keyword-cn 道具格, 格子贴图
## @keyword-en item-slot, slot-texture
static func _slot_texture() -> ImageTexture:
	var img := Image.create(32, 32, false, Image.FORMAT_RGBA8)
	for y in 32:
		for x in 32:
			var edge := x < 2 or y < 2 or x > 29 or y > 29
			var corner := (x < 6 or x > 25) and (y < 6 or y > 25)
			if edge and corner:
				img.set_pixel(x, y, Color(0.62, 0.6, 0.48, 0.7))
			elif edge:
				img.set_pixel(x, y, Color(0.42, 0.44, 0.36, 0.38))
			else:
				img.set_pixel(x, y, Color(0.0, 0.0, 0.0, 0.22))
	return ImageTexture.create_from_image(img)


# ---------------------------------------------------------------- 模型

## 实例化 art/models/<path>.glb，并把每个面的占位材质按名字换成材质表里的材质。
## overrides 里的 key 优先（例如行刑人每个实例自己的皮肤材质）。
## @keyword-cn 加载模型, 替换材质
## @keyword-en load-model, material-override
static func model(path: String, overrides := {}) -> Node3D:
	var node: Node3D = load(MODEL_DIR + path + ".glb").instantiate()
	_apply_materials(node, overrides)
	return node


## 递归替换节点树里所有网格的面材质（model() 的实现）
## @keyword-cn 递归换材质, 面材质
## @keyword-en apply-materials, surface-override
static func _apply_materials(node: Node, overrides: Dictionary) -> void:
	var mi := node as MeshInstance3D
	if mi and mi.mesh:
		for i in mi.mesh.get_surface_count():
			var placeholder := mi.mesh.surface_get_material(i)
			var key := placeholder.resource_name if placeholder else ""
			if overrides.has(key):
				mi.set_surface_override_material(i, overrides[key])
			elif key == "tentacle":
				mi.set_surface_override_material(i, tentacle_material())
			elif MATERIALS.has(key):
				mi.set_surface_override_material(i, material(key))
			else:
				push_warning("模型 %s 用了材质表里没有的材质「%s」" % [node.name, key])
	for child in node.get_children():
		_apply_materials(child, overrides)


## 霰弹枪：子节点 Body / BarrelFront / Sight / Pump，外加枪口标记 Muzzle
## @keyword-cn 霰弹枪, 枪模型
## @keyword-en shotgun, gun-model
static func shotgun() -> Node3D:
	var g := model("shotgun")
	g.name = "Shotgun"
	var muzzle := Marker3D.new()
	muzzle.name = "Muzzle"
	muzzle.position = Vector3(0, 0.014, -0.63)
	g.add_child(muzzle)
	return g


## 一发霰弹：实弹红、空包弹蓝；glowing 时自发光
## @keyword-cn 霰弹, 子弹模型
## @keyword-en shotgun-shell, shell-model
static func shell(live: bool, glowing := false) -> Node3D:
	return model("shell", {"hull": hull_material(live, glowing)})


## 道具模型，id 见 Items
## @keyword-cn 道具模型, 桌面道具
## @keyword-en item-model, table-item
static func item(id: String) -> Node3D:
	return model("items/" + id)


## 行刑人：椅子、身体、头（Head，带瞳孔 Pupil*、触手须）、两只手（HandL/HandR）和两条袖子（ArmL/ArmR，由场景每帧摆放）。
## skin / pupil / tentacle 是这个实例自己的材质，场景会改它们的颜色做受击和回合提示。
## @keyword-cn 行刑人, 庄家模型
## @keyword-en dealer, dealer-model
static func dealer(skin: Material, pupil: Material, tentacle: Material) -> Node3D:
	var d := model("dealer", {"skin": skin, "pupil": pupil, "tentacle": tentacle})
	d.name = "Dealer"
	return d
