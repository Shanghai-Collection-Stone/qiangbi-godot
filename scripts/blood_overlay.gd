class_name BloodOverlay
extends TextureRect
## 玩家中弹时糊在镜头上的血（shaders/blood_overlay.gdshader）：每次中弹现画一张 320×180 的遮罩，
## 最近邻放大到整个画面，和画面的像素一样大。血斑多落在画面四周（中间留出来看得清桌面），
## 往下淌出几道血痕，几秒后慢慢淡掉。

## 遮罩分辨率：画面 640×360 的一半
## @keyword-cn 溅血遮罩, 遮罩尺寸
## @keyword-en blood-mask, mask-size
const SIZE := Vector2i(320, 180)
const SHADER := preload("res://shaders/blood_overlay.gdshader")

var _mat: ShaderMaterial
var _tween: Tween
var _rng := RandomNumberGenerator.new()


func _init() -> void:
	mouse_filter = MOUSE_FILTER_IGNORE
	stretch_mode = STRETCH_SCALE
	texture_filter = TEXTURE_FILTER_NEAREST
	_mat = ShaderMaterial.new()
	_mat.shader = SHADER
	material = _mat
	_rng.randomize()
	visible = false


## 溅一脸血：damage 越大血斑越多越大；血痕 2.6 秒淌完，2 秒后开始淡出
## @keyword-cn 溅血, 中弹溅血
## @keyword-en splash-blood, hit-splash
func splash(damage: int) -> void:
	texture = ImageTexture.create_from_image(_paint(damage))
	visible = true
	if _tween:
		_tween.kill()
	_set_param(1.0, "amount")
	_set_param(0.0, "drip")
	_tween = create_tween()
	_tween.tween_method(_set_param.bind("drip"), 0.0, 1.0, 2.6)
	_tween.parallel().tween_method(_set_param.bind("amount"), 1.0, 0.0, 2.2).set_delay(2.0)
	_tween.tween_callback(hide)


## 立刻擦干净（新开一盘时）
## @keyword-cn 擦掉血, 清屏
## @keyword-en clear-blood, wipe
func clear() -> void:
	if _tween:
		_tween.kill()
	hide()


func _set_param(v: float, param: String) -> void:
	_mat.set_shader_parameter(param, v)


## 画遮罩：R = 血斑，G = 血痕流到这里的时刻（0..1），B = 明暗
## @keyword-cn 画血斑, 血痕
## @keyword-en paint-mask, drip-lines
func _paint(damage: int) -> Image:
	var img := Image.create(SIZE.x, SIZE.y, false, Image.FORMAT_RGBA8)
	for _k in 3 + damage * 2:
		var p := _edge_point()
		var r := _rng.randf_range(6.0, 15.0) + damage * 2.0
		_blob(img, p, r)
		for _s in 8:
			var drop := p + Vector2.from_angle(_rng.randf() * TAU) * _rng.randf_range(r, r * 2.4)
			_blob(img, drop, _rng.randf_range(1.0, 2.5))
		for _d in _rng.randi_range(1, 3):
			_drip(img, Vector2(p.x + _rng.randf_range(-r, r) * 0.6, p.y + r * 0.6), _rng.randf_range(15.0, 70.0))
	return img


## 画面四周随机一点：上下各 30 像素、左右各 50 像素的边带
## @keyword-cn 边缘取点, 四周
## @keyword-en edge-point, border-band
func _edge_point() -> Vector2:
	match _rng.randi_range(0, 3):
		0:
			return Vector2(_rng.randf() * SIZE.x, _rng.randf() * 30.0)
		1:
			return Vector2(_rng.randf() * SIZE.x, SIZE.y - _rng.randf() * 30.0)
		2:
			return Vector2(_rng.randf() * 50.0, _rng.randf() * SIZE.y)
	return Vector2(SIZE.x - _rng.randf() * 50.0, _rng.randf() * SIZE.y)


## 一团边缘起伏的血斑，左上一侧亮一点像湿的高光
## @keyword-cn 屏幕血斑, 湿润高光
## @keyword-en blood-blob, wet-highlight
func _blob(img: Image, center: Vector2, r: float) -> void:
	var phase := _rng.randf() * TAU
	var shade := _rng.randf_range(0.0, 0.3)
	for y in range(maxi(0, int(center.y - r * 1.3)), mini(SIZE.y, int(center.y + r * 1.3) + 1)):
		for x in range(maxi(0, int(center.x - r * 1.3)), mini(SIZE.x, int(center.x + r * 1.3) + 1)):
			var d := Vector2(x, y) - center
			var edge := r * (1.0 + 0.18 * sin(d.angle() * 5.0 + phase) + 0.1 * sin(d.angle() * 11.0 + phase * 2.0))
			if d.length() <= edge:
				var c := img.get_pixel(x, y)
				var lit := 0.5 if (d + Vector2(r, r) * 0.35).length() < r * 0.3 else 0.0
				img.set_pixel(x, y, Color(1.0, c.g, maxf(c.b, shade + lit), 1.0))


## 一道往下淌的血痕：每个像素记下血流到这里的时刻
## @keyword-cn 血痕下淌, 流淌时刻
## @keyword-en drip-line, arrival-time
func _drip(img: Image, start: Vector2, length: float) -> void:
	var width := _rng.randi_range(1, 2)
	var x := start.x
	for t in int(length):
		var y := int(start.y) + t
		if y >= SIZE.y:
			break
		x += _rng.randf_range(-0.15, 0.15)
		for w in width:
			var px := int(x) + w
			if px < 0 or px >= SIZE.x:
				continue
			var c := img.get_pixel(px, y)
			if c.r == 0.0:
				img.set_pixel(px, y, Color(0.0, maxf(0.004, (t + 1.0) / length), 0.2, 1.0))
