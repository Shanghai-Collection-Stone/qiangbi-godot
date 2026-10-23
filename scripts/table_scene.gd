class_name TableScene
extends Node3D
## 3D 赌桌：房间、吊灯、行刑人、霰弹枪、子弹、道具，以及所有演出动画。
## 规则不在这里，main.gd 根据 GameState 调用这里的函数。

signal item_clicked(index: int)
signal gun_clicked
signal hover_changed(text: String)

const P := GameState.PLAYER
const D := GameState.DEALER
const CAMERA_POS := Vector3(0, 0.85, 1.3)
const CAMERA_TARGET := Vector3(0, 0.28, -0.5)
const HEAD_POS := Vector3(0, 1.0, -1.2)
const SHOULDERS := [Vector3(-0.36, 0.62, -1.28), Vector3(0.36, 0.62, -1.28)]
const HAND_REST := [Vector3(-0.3, 0.015, -0.74), Vector3(0.3, 0.015, -0.74)]
const HAND_CUFFED := [Vector3(-0.07, 0.015, -0.7), Vector3(0.07, 0.015, -0.7)]
## 道具格：每边 8 格，左右各 2×2
const SLOT_COLS := [-0.76, -0.52, 0.52, 0.76]
const SLOT_ROWS := [[0.26, 0.47], [-0.36, -0.58]]
const SLOT_FILL_ORDER := [1, 4, 3, 6, 0, 5, 2, 7]
const ITEM_SCALE := 1.2
const SHELL_ROW_Z := 0.14
const GUN_SCALE := 1.2
## 行刑人的手臂：上臂、前臂长度和肘部弯曲方向（和 art/blender/build_dealer.py 一致）
## @keyword-cn 手臂长度, 肘部方向
## @keyword-en arm-length, elbow-pole
const UPPER_ARM := 0.48
const FOREARM := 0.5
const ELBOW_POLES := [Vector3(-0.8, -1.0, -0.25), Vector3(0.8, -1.0, -0.25)]
## 前臂接到手上的位置：张开的手、握拳的手（各自本地坐标）
const OPEN_WRIST := Vector3(0, 0.025, -0.06)
const FIST_WRIST := Vector3(0, -0.085, -0.062)
## 霰弹枪上的关键点（枪本地坐标）：托底板中心、手枪握把中心和轴向、前段枪管握持点
## @keyword-cn 枪托位置, 握把位置
## @keyword-en gun-butt, grip-point
const BUTT := Vector3(0, -0.07, 0.47)
const PISTOL_GRIP := Vector3(0, -0.085, 0.195)
const PISTOL_GRIP_AXIS := Vector3(0, -0.83, 0.56)
const BARREL_GRIP := Vector3(0, 0.0, -0.5)
## 行刑人每个持枪姿势下两只手握哪里：[hands[0]（画面左边，行刑人的右手）, hands[1]]
## grip = 手枪握把（扣扳机），pump = 泵动护木（跟着拉枪栓动），barrel = 前段枪管
const DEALER_GRIPS := {
	"dealer_hold": ["grip", "pump"],
	"dealer_at_player": ["grip", "pump"],
	"dealer_at_self": ["barrel", "pump"],
}
## 缩放动画的终点；不能是 0，否则带碰撞体或灯光的节点求逆矩阵会报错
const TINY := Vector3(0.001, 0.001, 0.001)
## 吊灯：灯罩中心和天花板上的挂点（吊灯绕挂点摆动）
## @keyword-cn 吊灯位置, 挂点
## @keyword-en lamp-position, lamp-pivot
const LAMP_POS := Vector3(0, 1.5, -0.25)
const LAMP_PIVOT := Vector3(0, 2.45, -0.25)
## 吊灯光锥着色器
## @keyword-cn 光锥着色器, 体积光
## @keyword-en light-cone-shader, fake-volumetric
const LIGHT_CONE_SHADER := preload("res://shaders/light_cone.gdshader")
## 房间里的蜡烛火焰和墙缝绿光的位置（和 art/blender/build_room.py 里的模型对齐）
## @keyword-cn 蜡烛灯光, 墙缝绿光
## @keyword-en candle-lights, crack-glow
const CANDLE_LIGHTS := [Vector3(2.267, 0.3, -1.5), Vector3(-1.23, -0.5, -2.2)]
const CRACK_LIGHT_POS := Vector3(0.85, 0.4, -2.35)

var sfx: Sfx
## 玩家能否点击道具和枪
var interactive := false:
	set(v):
		interactive = v
		if not v:
			_set_hover(null)
var gun_pose := "rest"
var camera: Camera3D
var gun: Node3D
var hands: Array[Node3D] = []
var items := [[], []]

var _head: Node3D
var _upper_arms: Array[Node3D] = []
var _forearms: Array[Node3D] = []
var _elbows: Array[Node3D] = []
## 握枪时显示的握拳手（张开的手 hands[i] 这时隐藏，但位置跟着走，松手时从这里收回）
var _fists: Array[Node3D] = []
var _holding := false
## 两只手当前握的位置，以及换握法时的过渡（0 = 还在旧位置，1 = 到新位置）
var _grips := ["grip", "pump"]
var _grips_from := ["grip", "pump"]
var _grip_blend := 1.0
var _skin: StandardMaterial3D
var _tentacle: ShaderMaterial
var _pupil: StandardMaterial3D
var _lamp: SpotLight3D
var _lamp_pivot: Node3D
var _candles: Array[OmniLight3D] = []
var _crack_light: OmniLight3D
var _light_cone: ShaderMaterial
## 吊灯摆角 (绕 x, 绕 z) 和角速度；开枪时给一下冲量
var _swing := Vector2.ZERO
var _swing_vel := Vector2.ZERO
var _muzzle: Marker3D
var _muzzle_light: OmniLight3D
var _muzzle_flash: Node3D
var _smoke: CPUParticles3D
var _gun_flash: OmniLight3D
var _cuffs := [null, null]
var _table_shells: Array[Node3D] = []
var _hover: Node3D = null
var _time := 0.0
var _shake := 0.0
## 行刑人中弹时头部后仰（由补间驱动）
var _head_kick := 0.0


func _ready() -> void:
	_build_environment()
	_build_room()
	_build_table()
	_build_lamp()
	_build_dealer()
	_build_gun()
	camera = Camera3D.new()
	camera.fov = 68.0
	camera.near = 0.03
	add_child(camera)
	camera.position = CAMERA_POS
	camera.look_at(CAMERA_TARGET)
	camera.current = true


## 每帧：吊灯闪烁与摆动、光锥跟着闪、行刑人头部和手臂、镜头晃动
## @keyword-cn 每帧更新, 吊灯摆动
## @keyword-en frame-update, lamp-swing
func _process(delta: float) -> void:
	_time += delta
	var flicker := 1.0
	if fmod(_time, 7.3) < 0.3:
		flicker = 0.35 if int(_time * 30.0) % 3 == 0 else 1.0
	_lamp.light_energy = 4.5 * flicker * (0.97 + 0.03 * sin(_time * 13.0))
	_light_cone.set_shader_parameter("flicker", _lamp.light_energy / 4.5)
	# 吊灯是个阻尼单摆（摆长约 1 米），平时有一点点气流晃动
	var idle := Vector2(sin(_time * 0.8), cos(_time * 0.55)) * 0.004
	_swing_vel += (-(_swing - idle) * 9.0 - _swing_vel * 0.5) * delta
	_swing += _swing_vel * delta
	_lamp_pivot.rotation = Vector3(_swing.x, 0, _swing.y)
	for i in _candles.size():
		_candles[i].light_energy = 0.75 + 0.12 * sin(_time * 9.0 + i * 2.1) + 0.08 * sin(_time * 23.0 + i * 5.3)
	_crack_light.light_energy = 0.55 + 0.35 * (0.5 + 0.5 * sin(_time * 0.9))

	_head.position = HEAD_POS + Vector3(sin(_time * 0.9) * 0.01, sin(_time * 1.3) * 0.008, -_head_kick * 0.12)
	_head.rotation = Vector3(-_head_kick * 0.6 + sin(_time * 0.7) * 0.03, sin(_time * 0.4) * 0.06, sin(_time * 0.6) * 0.04)
	for i in 2:
		var wrist: Vector3
		if _holding:
			var t := _grip_transform(i, _grips[i])
			if _grip_blend < 1.0 and _grips_from[i] != _grips[i]:
				t = _grip_transform(i, _grips_from[i]).interpolate_with(t, _grip_blend)
			_fists[i].transform = t
			hands[i].position = t.origin
			wrist = t * FIST_WRIST
		else:
			wrist = hands[i].position + OPEN_WRIST
		_solve_arm(i, wrist)

	_shake = move_toward(_shake, 0.0, delta * 0.25)
	var jitter := Vector3(randf_range(-1, 1), randf_range(-1, 1), 0) * _shake
	var sway := Vector3(sin(_time * 0.5), sin(_time * 0.73), 0) * 0.004
	camera.position = CAMERA_POS + sway + jitter
	camera.look_at(CAMERA_TARGET + jitter * 0.5)


# ---------------------------------------------------------------- 搭建场景

## 黑色背景、偏青的环境光、距离雾，自发光物体带柔光
## @keyword-cn 环境设置, 柔光
## @keyword-en world-environment, glow-bloom
func _build_environment() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color.BLACK
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.26, 0.38, 0.32)
	env.ambient_light_energy = 0.22
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.fog_enabled = true
	env.fog_light_color = Color(0.015, 0.028, 0.022)
	env.fog_density = 0.12
	# 灯泡、枪口火光、红灯这些自发光的东西带一圈柔光
	env.glow_enabled = true
	env.glow_intensity = 0.7
	env.glow_bloom = 0.02
	env.glow_hdr_threshold = 0.9
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SCREEN
	var world_env := WorldEnvironment.new()
	world_env.environment = env
	add_child(world_env)


## 房间模型（地砖、墙、管道、门、音箱、海报、木箱、墙缝触手、排水口触手、蜡烛、血字），门上红灯、冷色补光、墙缝绿光和蜡烛灯
## @keyword-cn 房间模型, 补光
## @keyword-en room-model, fill-light
func _build_room() -> void:
	add_child(Props.model("room"))
	var red := OmniLight3D.new()
	red.light_color = Color(0.9, 0.12, 0.08)
	red.light_energy = 1.4
	red.omni_range = 2.6
	red.position = Vector3(1.6, 1.3, -2.3)
	add_child(red)
	# 左后角一点冷色补光，让音箱、海报和管道从黑暗里透出轮廓
	var cold := OmniLight3D.new()
	cold.light_color = Color(0.35, 0.62, 0.66)
	cold.light_energy = 0.55
	cold.omni_range = 2.3
	cold.position = Vector3(-1.6, 1.5, -1.9)
	add_child(cold)
	# 墙上裂缝里透出的病态绿光，慢慢地一明一暗
	_crack_light = OmniLight3D.new()
	_crack_light.light_color = Color(0.45, 0.85, 0.5)
	_crack_light.omni_range = 1.9
	_crack_light.position = CRACK_LIGHT_POS
	add_child(_crack_light)
	# 每组仪式蜡烛一盏暖色小灯，各自闪烁
	for pos in CANDLE_LIGHTS:
		var candle := OmniLight3D.new()
		candle.light_color = Color(1, 0.6, 0.28)
		candle.omni_range = 1.5
		candle.position = pos
		add_child(candle)
		_candles.append(candle)


## 赌桌模型和两边各 8 个道具格
## @keyword-cn 赌桌模型, 道具格
## @keyword-en table-model, item-slots
func _build_table() -> void:
	add_child(Props.model("table"))
	var slot_mesh := PlaneMesh.new()
	slot_mesh.size = Vector2(0.2, 0.2)
	for side in 2:
		for slot in GameState.MAX_ITEMS:
			Props.part(self, slot_mesh, Props.material("slot"), slot_position(side, slot) + Vector3(0, 0.001, 0))


## 吊灯挂在天花板的挂点上，灯、光锥和主光源一起摆动
## @keyword-cn 吊灯, 光锥
## @keyword-en pendant-lamp, light-cone
func _build_lamp() -> void:
	_lamp_pivot = Node3D.new()
	_lamp_pivot.position = LAMP_PIVOT
	add_child(_lamp_pivot)
	var lamp := Props.model("lamp")
	lamp.position = -LAMP_PIVOT
	_lamp_pivot.add_child(lamp)
	var hang := LAMP_POS - LAMP_PIVOT
	_lamp = SpotLight3D.new()
	_lamp.light_color = Color(1, 0.82, 0.58)
	_lamp.spot_range = 3.5
	_lamp.spot_angle = 50.0
	_lamp.spot_attenuation = 0.7
	_lamp.shadow_enabled = true
	_lamp.position = hang + Vector3(0, -0.1, 0)
	_lamp.rotation = Vector3(-PI / 2.0, 0, 0)
	_lamp_pivot.add_child(_lamp)

	var cone := CylinderMesh.new()
	cone.top_radius = 0.26
	cone.bottom_radius = 1.05
	cone.height = 1.45
	cone.radial_segments = 24
	cone.cap_top = false
	cone.cap_bottom = false
	_light_cone = ShaderMaterial.new()
	_light_cone.shader = LIGHT_CONE_SHADER
	Props.part(_lamp_pivot, cone, _light_cone, hang + Vector3(0, -0.8, 0))
	_build_dust()

	var face := SpotLight3D.new()
	face.light_color = Color(0.8, 0.95, 0.85)
	face.light_energy = 2.2
	face.spot_range = 1.6
	face.spot_angle = 20.0
	face.position = Vector3(0, 1.45, -0.5)
	add_child(face)
	face.look_at(HEAD_POS + Vector3(0, -0.15, 0))
	var fill := OmniLight3D.new()
	fill.light_color = Color(0.55, 0.7, 0.75)
	fill.light_energy = 0.35
	fill.omni_range = 1.6
	fill.position = Vector3(0, 0.55, 0.85)
	add_child(fill)


## 吊灯光里慢慢飘的灰尘
## @keyword-cn 灰尘粒子, 浮尘
## @keyword-en dust-particles, floating-dust
func _build_dust() -> void:
	var dust := CPUParticles3D.new()
	dust.amount = 60
	dust.lifetime = 12.0
	dust.preprocess = 12.0
	# 只在灯光照到的那一柱空间里（灰尘是不受光照的加色小点，放到暗处会像星星）
	dust.emission_shape = CPUParticles3D.EMISSION_SHAPE_RING
	dust.emission_ring_axis = Vector3.UP
	dust.emission_ring_height = 0.9
	dust.emission_ring_radius = 0.55
	dust.emission_ring_inner_radius = 0.0
	dust.position = LAMP_POS + Vector3(0, -0.85, 0)
	dust.direction = Vector3.UP
	dust.spread = 180.0
	dust.initial_velocity_min = 0.004
	dust.initial_velocity_max = 0.02
	dust.gravity = Vector3(0, -0.003, 0)
	var quad := QuadMesh.new()
	quad.size = Vector2(0.007, 0.007)
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	m.vertex_color_use_as_albedo = true
	quad.material = m
	dust.mesh = quad
	var fade := Gradient.new()
	fade.set_color(0, Color(1, 0.85, 0.6, 0))
	fade.set_color(1, Color(1, 0.85, 0.6, 0))
	fade.add_point(0.2, Color(0.9, 0.75, 0.5, 0.6))
	fade.add_point(0.8, Color(0.9, 0.75, 0.5, 0.6))
	dust.color_ramp = fade
	add_child(dust)


func _build_dealer() -> void:
	_skin = Props.material("skin").duplicate()
	_pupil = Props.glow(Color(0.95, 0.95, 0.9), 2.0)
	_tentacle = Props.tentacle_material().duplicate()
	var dealer := Props.dealer(_skin, _pupil, _tentacle)
	add_child(dealer)
	_head = dealer.get_node("Head")
	for side in ["L", "R"]:
		hands.append(dealer.get_node("Hand" + side))
		_fists.append(dealer.get_node("Grip" + side))
		_upper_arms.append(dealer.get_node("UpperArm" + side))
		_forearms.append(dealer.get_node("Forearm" + side))
		_elbows.append(dealer.get_node("Elbow" + side))
	for i in 2:
		hands[i].position = HAND_REST[i]
	_show_fists(false)


func _build_gun() -> void:
	gun = Props.shotgun()
	add_child(gun)
	gun.transform = pose_transform("rest")
	_muzzle = gun.get_node("Muzzle")
	_muzzle_light = OmniLight3D.new()
	_muzzle_light.light_color = Color(1, 0.7, 0.35)
	_muzzle_light.light_energy = 0.0
	_muzzle_light.omni_range = 3.0
	_muzzle.add_child(_muzzle_light)
	_build_muzzle_flash()
	_gun_flash = OmniLight3D.new()
	_gun_flash.light_energy = 0.0
	_gun_flash.omni_range = 1.0
	_gun_flash.position = Vector3(0, 0.1, -0.1)
	gun.add_child(_gun_flash)

	var area := Area3D.new()
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(0.14, 0.2, 1.12)
	shape.shape = box
	shape.position = Vector3(0, -0.03, -0.08)
	area.add_child(shape)
	gun.add_child(area)
	area.input_event.connect(_on_gun_input)
	area.mouse_entered.connect(_set_hover.bind(gun))
	area.mouse_exited.connect(_clear_hover.bind(gun))


## 枪口火光：一张朝镜头的星形火光 + 两张沿枪管十字交叉的长条火焰；硝烟是世界空间的粒子
## @keyword-cn 枪口火光, 硝烟
## @keyword-en muzzle-flash, gun-smoke
func _build_muzzle_flash() -> void:
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.no_depth_test = false
	m.albedo_texture = Props.pixel_texture("muzzle_flash")
	m.albedo_color = Color(1.4, 1.2, 1.0)
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	_muzzle_flash = Node3D.new()
	_muzzle_flash.visible = false
	_muzzle.add_child(_muzzle_flash)
	var star_mat := m.duplicate() as StandardMaterial3D
	star_mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	var star := QuadMesh.new()
	star.size = Vector2(0.26, 0.26)
	Props.part(_muzzle_flash, star, star_mat, Vector3(0, 0, -0.04))
	var jet := QuadMesh.new()
	jet.size = Vector2(0.14, 0.34)
	Props.part(_muzzle_flash, jet, m, Vector3(0, 0, -0.15), Vector3(-PI / 2.0, 0, 0))
	Props.part(_muzzle_flash, jet, m, Vector3(0, 0, -0.15), Vector3(0, PI / 2.0, PI / 2.0))

	_smoke = CPUParticles3D.new()
	_smoke.emitting = false
	_smoke.one_shot = true
	_smoke.amount = 14
	_smoke.lifetime = 2.2
	_smoke.explosiveness = 0.85
	_smoke.local_coords = false
	_smoke.spread = 18.0
	_smoke.initial_velocity_min = 0.25
	_smoke.initial_velocity_max = 0.7
	_smoke.damping_min = 0.5
	_smoke.damping_max = 0.9
	_smoke.gravity = Vector3(0, 0.06, 0)
	_smoke.angle_min = -180.0
	_smoke.angle_max = 180.0
	_smoke.angular_velocity_min = -30.0
	_smoke.angular_velocity_max = 30.0
	_smoke.scale_amount_min = 0.6
	_smoke.scale_amount_max = 1.1
	var grow := Curve.new()
	grow.add_point(Vector2(0, 0.35))
	grow.add_point(Vector2(1, 1.6))
	_smoke.scale_amount_curve = grow
	var fade := Gradient.new()
	fade.set_color(0, Color(0.75, 0.72, 0.68, 0.55))
	fade.set_color(1, Color(0.4, 0.4, 0.42, 0))
	_smoke.color_ramp = fade
	var quad := QuadMesh.new()
	quad.size = Vector2(0.16, 0.16)
	var smoke_mat := StandardMaterial3D.new()
	smoke_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	smoke_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	smoke_mat.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	smoke_mat.vertex_color_use_as_albedo = true
	smoke_mat.albedo_texture = Props.pixel_texture("smoke")
	smoke_mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	quad.material = smoke_mat
	_smoke.mesh = quad
	add_child(_smoke)


static func slot_position(side: int, slot: int) -> Vector3:
	var col: float = SLOT_COLS[slot % 2 + (2 if slot >= 4 else 0)]
	var row: float = SLOT_ROWS[side][(slot / 2) % 2]
	return Vector3(col, 0.0, row)


## 两段手臂 IK：肩固定，手腕到 wrist，肘按 ELBOW_POLES 往下往外弯；够不着时整条手臂沿直线拉长
## @keyword-cn 手臂IK, 肘部求解
## @keyword-en arm-ik, elbow-solve
func _solve_arm(i: int, wrist: Vector3) -> void:
	var shoulder: Vector3 = SHOULDERS[i]
	var to := wrist - shoulder
	var d := to.length()
	var dir := to / d
	var elbow: Vector3
	if d >= UPPER_ARM + FOREARM:
		elbow = shoulder + dir * UPPER_ARM * d / (UPPER_ARM + FOREARM)
	else:
		var cos_a := clampf((UPPER_ARM * UPPER_ARM + d * d - FOREARM * FOREARM) / (2.0 * UPPER_ARM * d), -1.0, 1.0)
		var pole: Vector3 = ELBOW_POLES[i]
		var perp := (pole - dir * dir.dot(pole)).normalized()
		elbow = shoulder + dir * UPPER_ARM * cos_a + perp * UPPER_ARM * sqrt(1.0 - cos_a * cos_a)
	_place_segment(_upper_arms[i], shoulder, elbow)
	_place_segment(_forearms[i], elbow, wrist)
	_elbows[i].position = elbow


## 把沿本地 Y 轴长 1 米、原点居中的手臂段拉伸摆到两点之间
## @keyword-cn 手臂段, 两点摆放
## @keyword-en arm-segment, place-between
func _place_segment(segment: Node3D, from: Vector3, to: Vector3) -> void:
	var dir := to - from
	var rot := Basis(Quaternion(Vector3.UP, dir.normalized())) if dir.normalized().y > -0.999 else Basis(Vector3.RIGHT, PI)
	segment.transform = Transform3D(rot * Basis.from_scale(Vector3(1, dir.length(), 1)), (from + to) / 2.0)


## 握拳手在枪上某个握持点的变换：杆的轴向 = 本地 X，手腕（本地 -Y）尽量朝向肩膀
## @keyword-cn 握枪手势, 握持点
## @keyword-en gun-grip-pose, grip-anchor
func _grip_transform(i: int, where: String) -> Transform3D:
	var center: Vector3
	var axis := gun.transform.basis * Vector3.FORWARD
	match where:
		"grip":
			center = gun.transform * PISTOL_GRIP
			axis = gun.transform.basis * PISTOL_GRIP_AXIS
		"pump":
			center = gun.transform * (gun.get_node("Pump") as Node3D).position
		_:
			center = gun.transform * BARREL_GRIP
	var x := axis.normalized()
	var to_shoulder: Vector3 = SHOULDERS[i] - center
	var y := -(to_shoulder - x * x.dot(to_shoulder)).normalized()
	return Transform3D(Basis(x, y, x.cross(y)), center)


## 握枪时显示握拳手、隐藏张开的手（反之亦然）
## @keyword-cn 切换手型, 握拳手
## @keyword-en toggle-fist, hand-swap
func _show_fists(on: bool) -> void:
	for i in 2:
		hands[i].visible = not on
		_fists[i].visible = on


## 行刑人伸手去拿桌上的枪：张开的手先伸到握把和护木上方，再换成握拳
## @keyword-cn 拿起枪, 伸手
## @keyword-en grab-gun, reach
func _grab_gun() -> void:
	var targets := [_grip_transform(0, "grip").origin, _grip_transform(1, "pump").origin]
	for i in 2:
		_tween_position(hands[i], targets[i] + Vector3(0, 0.04, 0), 0.28)
	await get_tree().create_timer(0.3).timeout
	_grips = ["grip", "pump"]
	_grips_from = _grips
	_grip_blend = 1.0
	_holding = true
	_show_fists(true)


## 枪放回桌上后松手，两只手收回桌边（被铐着就收到一起）
## @keyword-cn 放下枪, 松手
## @keyword-en release-gun, let-go
func _release_gun() -> void:
	_holding = false
	_show_fists(false)
	var rest: Array = HAND_CUFFED if _cuffs[D] != null else HAND_REST
	for i in 2:
		hands[i].position += Vector3(0, 0.04, 0)
		_tween_position(hands[i], rest[i], 0.3)
	await get_tree().create_timer(0.3).timeout


# ---------------------------------------------------------------- 交互

func _on_gun_input(_camera: Node, event: InputEvent, _pos: Vector3, _normal: Vector3, _shape: int) -> void:
	if interactive and _is_click(event):
		gun_clicked.emit()


func _on_item_input(_camera: Node, event: InputEvent, _pos: Vector3, _normal: Vector3, _shape: int, model: Node3D) -> void:
	if interactive and _is_click(event) and items[P].has(model):
		item_clicked.emit(items[P].find(model))


func _is_click(event: InputEvent) -> bool:
	return event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT


func _set_hover(target: Node3D) -> void:
	if _hover == target:
		return
	if _hover and _hover != gun and is_instance_valid(_hover):
		_hover.scale = Vector3.ONE * ITEM_SCALE
	_hover = target if interactive else null
	if _hover == null:
		hover_changed.emit("")
	elif _hover == gun:
		hover_changed.emit("霰弹枪：拿起来，决定向谁开枪")
	else:
		var id: String = _hover.get_meta("id")
		# 用放大而不是抬高来高亮：抬高会让碰撞体离开鼠标，导致悬停闪烁
		_hover.scale = Vector3.ONE * ITEM_SCALE * 1.15
		hover_changed.emit("%s：%s" % [Items.display_name(id), Items.description(id)])


func _clear_hover(target: Node3D) -> void:
	if _hover == target:
		_set_hover(null)


# ---------------------------------------------------------------- 道具

func reset_round() -> void:
	for side in 2:
		for model in items[side]:
			model.queue_free()
		items[side].clear()
		set_cuffed(side, false)
	clear_shells()
	set_sawed(false)
	gun_pose = "rest"
	gun.transform = pose_transform("rest")
	_holding = false
	_show_fists(false)
	for i in 2:
		hands[i].position = HAND_REST[i]


func add_items(side: int, ids: Array) -> void:
	for id in ids:
		var slot := _free_slot(side)
		if slot == -1:
			continue
		var model := Props.item(id)
		model.set_meta("id", id)
		model.set_meta("slot", slot)
		model.rotation.y = (PI if side == D else 0.0) + randf_range(-0.3, 0.3)
		model.position = slot_position(side, slot) + Vector3(0, 0.3, 0)
		model.scale = Vector3.ONE * 0.01
		add_child(model)
		items[side].append(model)
		if side == P:
			_make_pickable(model)
		var tw := create_tween().set_parallel().set_trans(Tween.TRANS_BOUNCE).set_ease(Tween.EASE_OUT)
		tw.tween_property(model, "position:y", 0.0, 0.35)
		tw.tween_property(model, "scale", Vector3.ONE * ITEM_SCALE, 0.2)
		sfx.play("thud", -4.0)
		await get_tree().create_timer(0.14).timeout


func _free_slot(side: int) -> int:
	var used := []
	for model in items[side]:
		used.append(model.get_meta("slot"))
	for slot in SLOT_FILL_ORDER:
		if not used.has(slot):
			return slot
	return -1


## 道具的点击范围：贴着模型网格的包围盒（四周留 1 厘米）。
## 不能用统一的高盒子：近排道具的高盒子在屏幕上会挡住远排道具的下半截，鼠标指着远排道具却选不中
## @keyword-cn 点击范围, 道具拾取
## @keyword-en pick-shape, item-picking
func _make_pickable(model: Node3D) -> void:
	var bounds := AABB()
	var first := true
	for mi: MeshInstance3D in model.find_children("*", "MeshInstance3D", true, false):
		var to_model := Transform3D.IDENTITY
		var node: Node = mi
		while node != model:
			to_model = (node as Node3D).transform * to_model
			node = node.get_parent()
		var box_aabb: AABB = to_model * mi.get_aabb()
		bounds = box_aabb if first else bounds.merge(box_aabb)
		first = false
	bounds = bounds.grow(0.01)
	bounds.size.y = maxf(bounds.size.y, 0.03)
	var area := Area3D.new()
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = bounds.size
	shape.shape = box
	shape.position = bounds.get_center()
	area.add_child(shape)
	model.add_child(area)
	area.input_event.connect(_on_item_input.bind(model))
	area.mouse_entered.connect(_set_hover.bind(model))
	area.mouse_exited.connect(_clear_hover.bind(model))


## 道具被使用：拿起来送到目标位置然后消失。行刑人会伸手去拿。
func animate_use(side: int, index: int, id: String) -> void:
	var model: Node3D = items[side][index]
	items[side].remove_at(index)
	_clear_hover(model)
	var target := _use_target(side, id)
	var hand: Node3D = null
	var hand_home := Vector3.ZERO
	if side == D:
		hand = hands[1] if model.position.x > 0.0 else hands[0]
		hand_home = hand.position
		await _tween_position(hand, model.position + Vector3(0, 0.02, -0.04), 0.3)
		_tween_position(hand, target + Vector3(0, -0.02, -0.06), 0.45)
	var tw := create_tween().set_parallel().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	tw.tween_property(model, "position", target, 0.45)
	tw.tween_property(model, "rotation", model.rotation + Vector3(0.5, 0.9, 0), 0.45)
	await tw.finished
	await get_tree().create_timer(0.15).timeout
	var shrink := create_tween()
	shrink.tween_property(model, "scale", TINY, 0.18)
	await shrink.finished
	model.queue_free()
	if hand:
		_tween_position(hand, hand_home, 0.35)


func _use_target(side: int, id: String) -> Vector3:
	match id:
		Items.MAGNIFIER, Items.SAW, Items.INVERTER:
			return gun.global_transform * Vector3(0, 0.12, -0.2)
		Items.HANDCUFFS:
			return Vector3(0, 0.08, -0.68) if side == P else Vector3(0, 0.45, 0.9)
	return CAMERA_POS + Vector3(0, -0.2, -0.35) if side == P else HEAD_POS + Vector3(0, -0.1, 0.25)


func set_cuffed(side: int, on: bool) -> void:
	if on == (_cuffs[side] != null):
		return
	if not on:
		_cuffs[side].queue_free()
		_cuffs[side] = null
		if side == D:
			for i in 2:
				_tween_position(hands[i], HAND_REST[i], 0.3)
		return
	var model := Props.item(Items.HANDCUFFS)
	add_child(model)
	_cuffs[side] = model
	if side == D:
		model.position = Vector3(0, 0.03, -0.66)
		for i in 2:
			_tween_position(hands[i], HAND_CUFFED[i], 0.3)
	else:
		model.position = Vector3(0, 0.5, 0.9)
		model.rotation = Vector3(1.0, 0, 0)
		model.scale = Vector3.ONE * 1.3


# ---------------------------------------------------------------- 子弹

func show_shells(shells: Array) -> void:
	clear_shells()
	var count := shells.size()
	for i in count:
		var s := Props.shell(shells[i])
		s.position = Vector3((i - (count - 1) / 2.0) * 0.065, 0.0, SHELL_ROW_Z)
		s.scale = Vector3.ONE * 0.01
		add_child(s)
		_table_shells.append(s)
		create_tween().tween_property(s, "scale", Vector3.ONE * 1.25, 0.15)
		sfx.play("insert", -10.0)
		await get_tree().create_timer(0.07).timeout


func load_shells() -> void:
	var port := gun.global_transform * Vector3(0, -0.04, 0.0)
	for s in _table_shells:
		var tw := create_tween().set_parallel()
		tw.tween_property(s, "position", port, 0.16)
		tw.tween_property(s, "scale", Vector3.ONE * 0.3, 0.16)
		await tw.finished
		sfx.play("insert", -3.0)
		s.queue_free()
		await get_tree().create_timer(0.05).timeout
	_table_shells.clear()


func clear_shells() -> void:
	for s in _table_shells:
		s.queue_free()
	_table_shells.clear()


## 放大镜：在枪的上方亮出当前那一发
func peek_shell(live: bool) -> void:
	var s := Props.shell(live, true)
	s.position = gun.global_transform.origin + Vector3(0, 0.09, 0.05)
	s.scale = Vector3.ONE * 0.01
	add_child(s)
	var tw := create_tween()
	tw.tween_property(s, "scale", Vector3.ONE * 2.0, 0.2)
	tw.parallel().tween_property(s, "rotation:y", TAU, 1.6)
	tw.tween_interval(0.2)
	tw.tween_property(s, "scale", TINY, 0.2)
	tw.tween_callback(s.queue_free)


## 拉动泵动护木；eject 为 -1 时不退壳，0/1 表示退出空包弹/实弹
func rack(eject := -1) -> void:
	var pump: Node3D = gun.get_node("Pump")
	var z0 := -0.24
	sfx.play("rack")
	var tw := create_tween()
	tw.tween_property(pump, "position:z", z0 + 0.08, 0.1)
	tw.tween_property(pump, "position:z", z0, 0.12)
	if eject != -1:
		_eject_shell(eject == 1)
	await tw.finished


func _eject_shell(live: bool) -> void:
	var s := Props.shell(live)
	var start := gun.global_transform * Vector3(0.04, 0.02, 0.0)
	var end := Vector3(clampf(start.x + 0.35, -0.9, 0.9), 0.017, clampf(start.z + 0.18, -0.25, 0.2))
	var spin := Vector3(randf_range(4, 9), randf_range(4, 9), randf_range(4, 9))
	s.position = start
	add_child(s)
	var tw := create_tween()
	tw.tween_method(_shell_arc.bind(s, start, end, spin), 0.0, 1.0, 0.55)
	tw.tween_property(s, "rotation", Vector3(PI / 2.0, randf() * TAU, 0), 0.06)
	tw.tween_interval(1.6)
	tw.tween_property(s, "scale", TINY, 0.3)
	tw.tween_callback(s.queue_free)


func _shell_arc(t: float, s: Node3D, start: Vector3, end: Vector3, spin: Vector3) -> void:
	s.position = start.lerp(end, t) + Vector3(0, sin(t * PI) * 0.22, 0)
	s.rotation = spin * t


# ---------------------------------------------------------------- 霰弹枪

## 枪在各个姿势下的变换（rest 平放桌上；player_* 玩家持枪/瞄准；dealer_* 行刑人持枪/瞄准）
## @keyword-cn 持枪姿势, 瞄准姿势
## @keyword-en gun-pose, aim-pose
func pose_transform(pose: String) -> Transform3D:
	match pose:
		# 玩家持枪：枪放在画面右下、离镜头留出距离，枪身几乎顺着视线方向，画面上接近竖直不歪
		"player_hold":
			return _aim(Vector3(0.12, 0.42, 0.68), Vector3(0.06, 0.42, -1.2))
		"player_at_dealer":
			return _aim(Vector3(0.1, 0.5, 0.62), HEAD_POS)
		"player_at_self":
			return _aim(Vector3(0.16, 0.36, 0.35), CAMERA_POS + Vector3(0.04, -0.13, 0))
		# 行刑人：枪托夹在右胸前，右手握握把、左手托护木，枪口斜指桌面
		"dealer_hold":
			return _tucked(Vector3(-0.2, 0.38, -1.05), Vector3(0.55, 0.22, 0.1))
		# 枪托顶在胸口正中，枪口直指玩家的脸（稍微偏一点，看得出枪身）
		"dealer_at_player":
			return _tucked(Vector3(-0.08, 0.5, -1.12), CAMERA_POS + Vector3(-0.08, -0.12, 0))
		# 枪托搭在桌上，两只手握着前段把枪口拉到自己下巴底下
		"dealer_at_self":
			return _tucked(Vector3(0.02, 0.26, 0.16), HEAD_POS + Vector3(0, -0.12, 0))
	return _scaled(Transform3D(Basis.looking_at(Vector3.RIGHT, Vector3.BACK), Vector3(-0.05, 0.034, -0.05)))


func _aim(from: Vector3, target: Vector3) -> Transform3D:
	return _scaled(Transform3D(Basis.looking_at(target - from, Vector3.UP), from))


## 托底板放在 butt、枪口朝 target 的枪变换
## @keyword-cn 枪托定位, 持枪瞄准
## @keyword-en butt-placement, shouldered-aim
func _tucked(butt: Vector3, target: Vector3) -> Transform3D:
	var t := _aim(butt, target)
	t.origin = butt - t.basis * BUTT
	return t


func _scaled(t: Transform3D) -> Transform3D:
	return Transform3D(t.basis * Basis.from_scale(Vector3.ONE * GUN_SCALE), t.origin)


## 枪换到某个姿势。行刑人的姿势：先伸手握住枪再一起动，换姿势时两只手在握持点之间平滑换手；
## 枪放回桌上（rest）时手跟着放下，然后松手收回
## @keyword-cn 移动枪, 握枪动画
## @keyword-en move-gun, hold-animation
func gun_to(pose: String, duration := 0.5) -> void:
	gun_pose = pose
	var grips: Array = DEALER_GRIPS.get(pose, [])
	if not grips.is_empty() and not _holding:
		await _grab_gun()
	elif grips.is_empty() and _holding and pose != "rest":
		await _release_gun()
	if _holding:
		_grips_from = _grips
		_grips = grips if not grips.is_empty() else ["grip", "pump"]
		_grip_blend = 0.0
	var from := gun.transform
	var to := pose_transform(pose)
	var tw := create_tween().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	tw.tween_method(_lerp_gun.bind(from, to), 0.0, 1.0, duration)
	tw.parallel().tween_property(self, "_grip_blend", 1.0, duration)
	await tw.finished
	if _holding and grips.is_empty():
		await _release_gun()


func _lerp_gun(w: float, from: Transform3D, to: Transform3D) -> void:
	gun.transform = from.interpolate_with(to, w)


## 开枪演出：火光、枪口灯、硝烟、吊灯被震得摆起来、镜头震动和后坐
## @keyword-cn 开枪演出, 后坐
## @keyword-en fire-effects, recoil
func fire(sawed: bool) -> void:
	_muzzle_flash.visible = true
	_muzzle_flash.scale = Vector3.ONE * (1.5 if sawed else 1.0)
	_muzzle_flash.rotation.z = randf() * TAU
	_muzzle_light.light_energy = 14.0
	var tw := create_tween().set_parallel()
	tw.tween_property(_muzzle_light, "light_energy", 0.0, 0.3)
	tw.tween_property(_muzzle_flash, "scale", TINY, 0.1).set_delay(0.03)
	tw.chain().tween_callback(func() -> void: _muzzle_flash.visible = false)
	_smoke.global_transform = _muzzle.global_transform
	_smoke.direction = Vector3.FORWARD
	_smoke.restart()
	_swing_vel += Vector2(randf_range(-0.3, 0.3), randf_range(-0.3, 0.3))
	_shake = 0.05
	var kick := create_tween()
	kick.tween_property(gun, "position", gun.position + gun.transform.basis.z * 0.07, 0.05)
	kick.tween_property(gun, "position", gun.position, 0.25)


func set_sawed(on: bool) -> void:
	gun.get_node("BarrelFront").visible = not on
	gun.get_node("Sight").visible = not on
	_muzzle.position.z = -0.41 if on else -0.63


## 道具作用在枪上时的一下彩色闪光
func flash_gun(color: Color) -> void:
	_gun_flash.light_color = color
	_gun_flash.light_energy = 4.0
	create_tween().tween_property(_gun_flash, "light_energy", 0.0, 0.5)


# ---------------------------------------------------------------- 行刑人

func set_dealer_active(on: bool) -> void:
	var c := Color(1, 0.15, 0.1) if on else Color(0.95, 0.95, 0.9)
	_pupil.albedo_color = c
	_pupil.emission = c


func dealer_hit() -> void:
	_shake = 0.03
	var tw := create_tween()
	tw.tween_property(self, "_head_kick", 1.0, 0.06)
	tw.tween_property(self, "_head_kick", 0.0, 0.9).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)
	_skin.albedo_color = Color(1, 0.3, 0.25)
	create_tween().tween_property(_skin, "albedo_color", Color.WHITE, 1.0)
	_tentacle.set_shader_parameter("tint", Color(1, 0.3, 0.25))
	create_tween().tween_method(func(c: Color) -> void: _tentacle.set_shader_parameter("tint", c),
		Color(1, 0.3, 0.25), Color.WHITE, 1.0)


func shake(amount: float) -> void:
	_shake = maxf(_shake, amount)


func _tween_position(node: Node3D, to: Vector3, duration: float) -> Signal:
	var tw := create_tween().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	tw.tween_property(node, "position", to, duration)
	return tw.finished
