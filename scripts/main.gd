extends Control
## 主场景：3D 赌桌 + 像素风 HUD。负责整局流程与演出调度，规则全部在 GameState 里。
## 画面以 640×360 渲染，整数倍放大；3D 画面经过 post.gdshader 做抖动、颗粒和暗角。

signal player_action(action: Dictionary)

const P := GameState.PLAYER
const D := GameState.DEALER
const CN_NUM := ["一", "二", "三", "四", "五"]
const LIVE := "[color=#ff5a45]实弹[/color]"
const BLANK := "[color=#6fb3ff]空包弹[/color]"
const RED := Color("e5533d")
## 玩家每回合的思考时间（秒），最后 10 秒每秒滴答一声，到点随机开一枪
## @keyword-cn 回合时限, 倒计时
## @keyword-en turn-seconds, countdown
const TURN_SECONDS := 30.0
const PIXEL_FONT := preload("res://fonts/fusion-pixel-12px-proportional-sc.woff2")
const POST_SHADER := preload("res://shaders/post.gdshader")
const FALLBACK_FONTS := [
	"Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", "WenQuanYi Zen Hei", "sans-serif",
]

var state: GameState
var ai_rng := RandomNumberGenerator.new()
var accepting_input := false
var _aiming := false
## 玩家回合还剩多少秒；_turn_timing 为 false 时不计时
var _turn_left := 0.0
var _turn_timing := false
var _fade := 0.0
var _log_lines: Array[String] = []

var scene: TableScene
var post: ShaderMaterial
var sfx: Sfx
var crt: CrtPanel
var subtitle: RichTextLabel
var hover_label: Label
var log_box: RichTextLabel
var log_panel: Panel
var aim_box: Control
var banner: Control
var banner_title: Label
var banner_sub: Label
var overlay: ColorRect
var menu_box: VBoxContainer


func _ready() -> void:
	_build_ui()
	sfx.play_music("menu")
	_show_title()


## 回合倒计时：只在等玩家操作（点道具、点枪、选开枪对象）时走，道具演出期间暂停
## @keyword-cn 倒计时更新, 超时
## @keyword-en countdown-tick, turn-timeout
func _process(delta: float) -> void:
	if not _turn_timing:
		return
	if accepting_input:
		var before := ceili(_turn_left)
		_turn_left = maxf(0.0, _turn_left - delta)
		var now := ceili(_turn_left)
		if now != before and now < 10:
			sfx.play("tick", -2.0 if now <= 3 else -8.0)
	crt.set_turn("你的回合", _turn_left, TURN_SECONDS)
	if accepting_input and _turn_left <= 0.0:
		_on_turn_timeout()


## 时间到：枪替玩家随机选一个对象开火
## @keyword-cn 超时开枪, 随机目标
## @keyword-en timeout-shot, random-target
func _on_turn_timeout() -> void:
	_turn_timing = false
	var target := P if ai_rng.randf() < 0.5 else D
	var text := "时间到！你的手不受控制地扣下了扳机——枪口对着%s。" % ("自己" if target == P else "行刑人")
	_log("[color=#e5533d]%s[/color]" % text)
	_say(text)
	player_action.emit({"type": "shoot", "target": target})


# ---------------------------------------------------------------- 界面搭建

func _build_ui() -> void:
	theme = _make_theme()
	sfx = Sfx.new()
	add_child(sfx)

	var view := SubViewportContainer.new()
	view.stretch = true
	view.mouse_filter = MOUSE_FILTER_STOP
	view.set_anchors_preset(PRESET_FULL_RECT)
	post = ShaderMaterial.new()
	post.shader = POST_SHADER
	view.material = post
	add_child(view)
	var viewport := SubViewport.new()
	viewport.physics_object_picking = true
	viewport.msaa_3d = Viewport.MSAA_DISABLED
	view.add_child(viewport)
	scene = TableScene.new()
	scene.sfx = sfx
	viewport.add_child(scene)
	scene.item_clicked.connect(_on_item_clicked)
	scene.gun_clicked.connect(_on_gun_clicked)
	scene.hover_changed.connect(func(text: String) -> void: hover_label.text = text)

	crt = CrtPanel.new()
	crt.position = Vector2(8, 8)
	crt.visible = false
	add_child(crt)

	# 记录框用普通 Panel + 固定尺寸的文本：隐藏时容器不排版，量出的文字高度会不准
	log_panel = Panel.new()
	log_panel.visible = false
	log_panel.position = Vector2(472, 8)
	log_panel.size = Vector2(160, 140)
	log_panel.mouse_filter = MOUSE_FILTER_IGNORE
	log_panel.add_theme_stylebox_override("panel", _box(Color(0, 0, 0, 0.5), Color(0.2, 0.18, 0.16, 0.8)))
	add_child(log_panel)
	log_box = RichTextLabel.new()
	log_box.bbcode_enabled = true
	log_box.scroll_active = false
	log_box.mouse_filter = MOUSE_FILTER_IGNORE
	log_box.position = Vector2(4, 4)
	log_box.size = log_panel.size - Vector2(8, 8)
	log_panel.add_child(log_box)

	hover_label = _label(Vector2(20, 284), 12, Color("e8d690"), 600)
	hover_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	subtitle = RichTextLabel.new()
	subtitle.bbcode_enabled = true
	subtitle.scroll_active = false
	subtitle.mouse_filter = MOUSE_FILTER_IGNORE
	subtitle.position = Vector2(20, 304)
	subtitle.size = Vector2(600, 48)
	add_child(subtitle)

	# 开枪选项：两个大按钮等宽并排、"放下枪"居中在下面，整组水平居中，底边贴在字幕上方
	aim_box = VBoxContainer.new()
	aim_box.mouse_filter = MOUSE_FILTER_IGNORE
	aim_box.visible = false
	aim_box.add_theme_constant_override("separation", 4)
	add_child(aim_box)
	var row := HBoxContainer.new()
	row.mouse_filter = MOUSE_FILTER_IGNORE
	row.add_theme_constant_override("separation", 8)
	aim_box.add_child(row)
	_aim_button(row, "向行刑人开枪", 24, Vector2(176, 0), _on_aim.bind(D))
	_aim_button(row, "向自己开枪", 24, Vector2(176, 0), _on_aim.bind(P))
	_aim_button(aim_box, "放下枪", 12, Vector2(96, 0), _on_aim_cancel).size_flags_horizontal = SIZE_SHRINK_CENTER
	aim_box.set_anchors_and_offsets_preset(PRESET_CENTER_BOTTOM, PRESET_MODE_MINSIZE)
	aim_box.grow_horizontal = GROW_DIRECTION_BOTH
	aim_box.grow_vertical = GROW_DIRECTION_BEGIN
	aim_box.offset_top -= 80
	aim_box.offset_bottom -= 80

	banner = Control.new()
	banner.set_anchors_preset(PRESET_FULL_RECT)
	banner.mouse_filter = MOUSE_FILTER_IGNORE
	banner.visible = false
	add_child(banner)
	var band := ColorRect.new()
	band.color = Color(0, 0, 0, 0.7)
	band.position = Vector2(0, 140)
	band.size = Vector2(640, 72)
	band.mouse_filter = MOUSE_FILTER_IGNORE
	banner.add_child(band)
	banner_title = _label(Vector2(0, 150), 24, RED, 640, banner)
	banner_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	banner_sub = _label(Vector2(0, 184), 12, Color("c9bba8"), 640, banner)
	banner_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER

	overlay = ColorRect.new()
	overlay.set_anchors_preset(PRESET_FULL_RECT)
	overlay.color = Color(0, 0, 0, 0.62)
	add_child(overlay)
	var center := CenterContainer.new()
	center.set_anchors_preset(PRESET_FULL_RECT)
	overlay.add_child(center)
	menu_box = VBoxContainer.new()
	menu_box.custom_minimum_size = Vector2(360, 0)
	menu_box.add_theme_constant_override("separation", 8)
	center.add_child(menu_box)


func _make_theme() -> Theme:
	var t := Theme.new()
	var font: FontFile = PIXEL_FONT
	var fallback := SystemFont.new()
	fallback.font_names = PackedStringArray(FALLBACK_FONTS)
	font.fallbacks = [fallback]
	t.default_font = font
	t.default_font_size = 12
	t.set_stylebox("normal", "Button", _box(Color(0, 0, 0, 0.55), Color(0.55, 0.16, 0.12)))
	t.set_stylebox("hover", "Button", _box(Color(0.35, 0.05, 0.04, 0.85), Color(0.95, 0.3, 0.22)))
	t.set_stylebox("pressed", "Button", _box(Color(0.2, 0.02, 0.02, 0.9), Color(0.95, 0.3, 0.22)))
	t.set_stylebox("focus", "Button", StyleBoxEmpty.new())
	t.set_color("font_color", "Button", Color(0.92, 0.88, 0.8))
	t.set_color("font_hover_color", "Button", Color.WHITE)
	t.set_color("font_outline_color", "Button", Color.BLACK)
	t.set_constant("outline_size", "Button", 2)
	t.set_color("font_color", "Label", Color(0.92, 0.88, 0.8))
	t.set_color("font_outline_color", "Label", Color.BLACK)
	t.set_constant("outline_size", "Label", 2)
	t.set_color("default_color", "RichTextLabel", Color(0.92, 0.88, 0.8))
	t.set_color("font_outline_color", "RichTextLabel", Color.BLACK)
	t.set_constant("outline_size", "RichTextLabel", 2)
	t.set_constant("line_separation", "RichTextLabel", 1)
	t.set_stylebox("panel", "PanelContainer", _box(Color(0, 0, 0, 0.5), Color(0.2, 0.18, 0.16, 0.8)))
	return t


func _box(bg: Color, border: Color) -> StyleBoxFlat:
	var b := StyleBoxFlat.new()
	b.bg_color = bg
	b.border_color = border
	b.set_border_width_all(1)
	b.set_content_margin_all(4)
	return b


func _label(pos: Vector2, font_size: int, color: Color, width := 0.0, parent: Node = null) -> Label:
	var l := Label.new()
	l.position = pos
	l.mouse_filter = MOUSE_FILTER_IGNORE
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	if width > 0.0:
		l.size = Vector2(width, 0)
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	(parent if parent else self).add_child(l)
	return l


## 开枪选项按钮：放进容器里由容器排版，min_size 统一宽度
## @keyword-cn 开枪按钮, 选项排版
## @keyword-en aim-button, option-layout
func _aim_button(parent: Control, text: String, font_size: int, min_size: Vector2, callback: Callable) -> Button:
	var b := Button.new()
	b.text = text
	b.custom_minimum_size = min_size
	b.add_theme_font_size_override("font_size", font_size)
	b.pressed.connect(callback)
	parent.add_child(b)
	return b


# ---------------------------------------------------------------- 菜单

func _show_menu(title: String, body: String, buttons: Array, title_size := 48,
		body_align := HORIZONTAL_ALIGNMENT_CENTER) -> void:
	for c in menu_box.get_children():
		menu_box.remove_child(c)
		c.queue_free()
	var t := Label.new()
	t.text = title
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	t.add_theme_font_size_override("font_size", title_size)
	t.add_theme_color_override("font_color", RED)
	t.add_theme_constant_override("outline_size", 4)
	menu_box.add_child(t)
	if body != "":
		var b := Label.new()
		b.text = body
		b.horizontal_alignment = body_align
		b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		b.custom_minimum_size = Vector2(360, 0)
		b.add_theme_color_override("font_color", Color("d8ccbb"))
		menu_box.add_child(b)
	for spec in buttons:
		var btn := Button.new()
		btn.text = spec[0]
		btn.custom_minimum_size = Vector2(120, 22)
		btn.size_flags_horizontal = SIZE_SHRINK_CENTER
		btn.pressed.connect(spec[1])
		menu_box.add_child(btn)
	overlay.visible = true


func _show_title() -> void:
	_show_menu("枪　毙", "一把霰弹枪，两个人。\n只有一个人能离开这张桌子。\n", [
		["开始游戏", _start_game],
		["游戏规则", _show_rules],
		["退出", get_tree().quit],
	])


func _show_rules() -> void:
	var text := "".join(PackedStringArray([
		"· 装弹时公布实弹和空包弹的数量，然后随机装进枪里。\n",
		"· 你的回合：先点道具使用（可以用多个），再点霰弹枪开枪。\n",
		"· 打自己：空包弹 → 继续行动；实弹 → 受伤，回合结束。\n",
		"· 打行刑人：无论结果如何，回合都交给对方。\n",
		"· 子弹打完重新装弹、发道具，每次装弹后你先手。\n",
		"· 你每回合有 30 秒，时间到枪会随机对着你或行刑人走火。\n",
		"· 共三局，生命和道具逐局增加。生命归零即被枪毙。\n\n",
	]))
	for id in Items.ALL:
		text += "%s：%s\n" % [Items.display_name(id), Items.description(id)]
	_show_menu("规则", text, [["返回", _show_title]], 24, HORIZONTAL_ALIGNMENT_LEFT)


## 开始一局：换成对局音乐，开始流程
## @keyword-cn 开始游戏, 对局音乐
## @keyword-en start-game, game-music
func _start_game() -> void:
	sfx.play_music("game")
	overlay.visible = false
	_run_game()


## 一局结束：结算界面，音乐恢复并换回标题曲
## @keyword-cn 游戏结束, 结算界面
## @keyword-en game-over, result-screen
func _game_over(win: bool) -> void:
	_set_player_input(false)
	crt.visible = false
	log_panel.visible = false
	hover_label.text = ""
	var s := state.stats
	var summary := "开枪 %d 次 · 道具 %d 次 · 造成伤害 %d · 承受伤害 %d\n活过 %d / %d 局" % [
		s["shots"], s["items_used"], s["damage_dealt"], s["damage_taken"],
		s["rounds_won"], GameState.ROUNDS.size()]
	var buttons := [["再来一局", _start_game], ["返回标题", _show_title]]
	sfx.muffle_music(false, 0.3)
	sfx.play_music("menu", 2.0)
	if win:
		sfx.play("win")
		_show_menu("你活下来了", "行刑人沉默片刻，把枪推到了一边。\n\n" + summary + "\n", buttons)
	else:
		sfx.play("lose")
		_show_menu("你被枪毙了", "枪声在空荡的房间里回响。\n行刑人收起枪，等待下一位客人。\n\n" + summary + "\n", buttons)


# ---------------------------------------------------------------- 游戏流程

func _run_game() -> void:
	state = GameState.new()
	state.new_game()
	ai_rng.randomize()
	_log_lines.clear()
	log_box.text = ""
	_set_fade(0.0)
	crt.visible = true
	log_panel.visible = true
	for r in GameState.ROUNDS.size():
		state.start_round(r)
		scene.reset_round()
		_refresh()
		_say("")
		_log("[color=#c9a227]—— 第%s局 ——[/color]" % CN_NUM[r])
		var sub := "双方生命 %d · 每次装弹发放 %d 件道具" % [state.max_hp, GameState.ROUNDS[r]["items"]]
		if GameState.ROUNDS[r]["items"] == 0:
			sub = "双方生命 %d · 没有道具，只有运气" % state.max_hp
		await _banner("第%s局" % CN_NUM[r], sub)
		while not state.round_over:
			if state.needs_reload():
				await _do_load()
			if state.current_turn == D:
				await _dealer_turn()
			else:
				await _player_turn()
			_refresh()
		await _wait(0.8)
		if state.round_winner == D:
			_game_over(false)
			return
		if not state.is_final_round():
			await _banner("你活过了第%s局" % CN_NUM[r], "……但这还没有结束。")
	_game_over(true)


## 装弹演出：公布实弹/空包弹数、子弹立桌上再装进枪，然后两边各自摆上新发的道具
## @keyword-cn 装弹演出, 发放道具
## @keyword-en reload-sequence, deal-items
func _do_load() -> void:
	_turn_timing = false
	crt.set_turn("装弹中……")
	var info := state.load_shells()
	_refresh()
	var shells := []
	for i in info["live"]:
		shells.append(true)
	for i in info["blank"]:
		shells.append(false)
	var msg := "%d 发%s，%d 发%s。" % [info["live"], LIVE, info["blank"], BLANK]
	_say(msg)
	_log("装弹：" + msg)
	await scene.show_shells(shells)
	await _wait(1.6)
	_say("行刑人把子弹装进枪里。顺序，没人知道。")
	await scene.load_shells()
	await scene.rack()
	var given: Array = info["given"]
	# 两边各自有上限：玩家道具满了拿不到新的，行刑人照样可能拿到，所以两边分开摆
	if not (given[P].is_empty() and given[D].is_empty()):
		_say("新的道具。")
		await scene.add_items(P, given[P])
		await scene.add_items(D, given[D])
		if not given[P].is_empty():
			_log("你得到：" + "、".join(PackedStringArray(given[P].map(func(id): return Items.display_name(id)))))
	await _wait(0.3)


## 玩家回合：每回合 TURN_SECONDS 秒（只在等玩家操作时走），用道具不换回合，开一枪结束回合
## @keyword-cn 玩家回合, 回合计时
## @keyword-en player-turn, turn-timer
func _player_turn() -> void:
	_say("你的回合。点道具使用，或者拿起霰弹枪。")
	_turn_left = TURN_SECONDS
	_turn_timing = true
	while true:
		_set_player_input(true)
		var action: Dictionary = await player_action
		_set_player_input(false)
		if action["type"] == "item":
			var index: int = action["index"]
			var res := state.use_item(P, index)
			if not res["ok"]:
				sfx.play("deny")
				_say(res["reason"])
				continue
			await _present_item(res, index)
			if state.round_over or state.needs_reload():
				return
			_say("还是你的回合。")
		else:
			await _present_shot(state.shoot(P, action["target"]))
			return


func _dealer_turn() -> void:
	_turn_timing = false
	crt.set_turn("行刑人的回合")
	_say("行刑人的回合……")
	scene.set_dealer_active(true)
	await _wait(0.9)
	for _step in GameState.MAX_ITEMS + 1:
		var action := DealerAI.decide(state, D, ai_rng)
		if action["type"] == "item":
			var index: int = action["index"]
			await _present_item(state.use_item(D, index), index)
			if state.round_over or state.needs_reload():
				break
			await _wait(0.35)
		else:
			await _present_shot(state.shoot(D, action["target"]))
			break
	scene.set_dealer_active(false)


func _set_player_input(on: bool) -> void:
	accepting_input = on
	if not on:
		_aiming = false
		aim_box.visible = false
	scene.interactive = on and not _aiming


func _on_item_clicked(index: int) -> void:
	if accepting_input and not _aiming:
		player_action.emit({"type": "item", "index": index})


func _on_gun_clicked() -> void:
	if not accepting_input or _aiming:
		return
	_aiming = true
	scene.interactive = false
	sfx.play("rack", -8.0)
	_say("向谁开枪？")
	await scene.gun_to("player_hold", 0.4)
	if _aiming:
		aim_box.visible = true


func _on_aim(target: int) -> void:
	if accepting_input and _aiming:
		aim_box.visible = false
		player_action.emit({"type": "shoot", "target": target})


func _on_aim_cancel() -> void:
	if not _aiming:
		return
	aim_box.visible = false
	_aiming = false
	_say("你把枪放回了桌上。")
	await scene.gun_to("rest", 0.35)
	scene.interactive = accepting_input


# ---------------------------------------------------------------- 演出

func _present_item(res: Dictionary, index: int) -> void:
	var actor: int = res["actor"]
	var id: String = res["item"]
	var who := _name(actor)
	var mine := actor == P
	sfx.play("item")
	await scene.animate_use(actor, index, id)
	var hold := 0.9
	var text := ""
	match id:
		Items.MAGNIFIER:
			if mine:
				scene.peek_shell(res["live"])
				text = "放大镜下，枪膛里是……%s。" % _shell(res["live"])
				hold = 1.5
			else:
				text = "行刑人凑近枪膛看了看。嗯……"
		Items.CIGARETTE:
			sfx.play("heal")
			text = "%s点了一支烟。生命 +%d。" % [who, res["heal"]]
		Items.BEER:
			text = "%s灌下啤酒，拉动枪栓——退出一发%s。" % [who, _shell(res["live"])]
			await scene.rack(1 if res["live"] else 0)
			hold = 1.2
		Items.SAW:
			sfx.play("saw")
			scene.flash_gun(Color(1, 0.8, 0.5))
			text = "%s锯短了枪管。下一发实弹伤害 ×2。" % who
		Items.HANDCUFFS:
			sfx.play("cuff")
			text = "%s给%s戴上了手铐。" % [who, _name(GameState.other(actor))]
		Items.PHONE:
			if not mine:
				text = "行刑人接起电话，听了一会儿。"
			elif res["offset"] == -1:
				text = "电话那头一片沉默……（枪里只剩最后一发）"
			else:
				text = "电话里的声音：「第 %d 发……是%s。」" % [res["offset"] + 1, _shell(res["live"])]
				hold = 1.8
		Items.INVERTER:
			scene.flash_gun(Color(0.8, 0.4, 1.0))
			text = "%s按下极性反转器。枪膛里那一发变了。" % who
		Items.MEDICINE:
			if res["heal"] >= 0:
				sfx.play("heal")
				text = "%s吞下过期药……感觉好多了。生命 +%d。" % [who, res["heal"]]
			else:
				text = "%s吞下过期药……呃！生命 -1。" % who
				_flash(Color(0.8, 0.0, 0.0, 0.5), 0.5)
				scene.shake(0.02)
	_say(text)
	_log(text)
	_refresh()
	await _wait(hold)
	if state.round_over:
		await _announce_death()


## 开枪演出：举枪、瞄准（音乐压闷）、开枪或空响（音乐放开）、拉枪栓、放下枪
## @keyword-cn 开枪流程, 紧张感
## @keyword-en shot-sequence, suspense
func _present_shot(res: Dictionary) -> void:
	var actor: int = res["actor"]
	var target: int = res["target"]
	var self_shot := actor == target
	if actor == P:
		if scene.gun_pose != "player_hold":
			await scene.gun_to("player_hold", 0.4)
		_say("你把枪口对准了%s……" % ("自己" if self_shot else "行刑人"))
		await scene.gun_to("player_at_self" if self_shot else "player_at_dealer", 0.55)
	else:
		_say("行刑人拿起了霰弹枪。")
		await scene.gun_to("dealer_hold", 0.5)
		await _wait(0.35)
		_say("行刑人把枪口对准了%s……" % ("自己" if self_shot else "你"))
		await scene.gun_to("dealer_at_self" if self_shot else "dealer_at_player", 0.6)
	# 枪口对准之后那一下：音乐压成闷声，开枪后再放开
	sfx.muffle_music(true, 0.5)
	await _wait(0.9)

	var text := ""
	if res["live"]:
		sfx.play("bang")
		scene.fire(res["sawed"])
		text = "砰！是%s。%s失去 %d 点生命。" % [LIVE, _name(target), res["damage"]]
		if target == P:
			await _player_hit_fx()
		else:
			sfx.muffle_music(false, 0.15)
			_flash(Color(1, 0.95, 0.85, 0.7), 0.35)
			scene.dealer_hit()
	else:
		sfx.play("click")
		sfx.muffle_music(false, 0.6)
		text = "咔哒——是%s。" % BLANK
		if res["extra_turn"]:
			text += "%s继续行动。" % _name(actor)
	_say(text)
	_log(text)
	_refresh()
	await _wait(1.0)
	await scene.rack(1 if res["live"] else 0)
	if state.round_over:
		await _announce_death()
	elif res["skipped"] != -1:
		var skip := "%s被手铐铐着，跳过这一回合。" % _name(res["skipped"])
		sfx.play("cuff", -6.0)
		_say(skip)
		_log(skip)
		await _wait(1.0)
	await scene.gun_to("rest", 0.5)


## 玩家中弹：白光，黑屏片刻（音乐一直闷着），再带着红色醒来、音乐慢慢回来
## @keyword-cn 玩家中弹, 黑屏醒来
## @keyword-en player-hit, blackout-wake
func _player_hit_fx() -> void:
	_flash(Color(1, 1, 1, 1), 0.12)
	scene.shake(0.06)
	await _tween_fade(1.0, 0.1)
	await _wait(0.7)
	_flash(Color(0.75, 0.0, 0.0, 0.6), 0.9)
	sfx.muffle_music(false, 1.5)
	await _tween_fade(0.0, 0.5)


func _announce_death() -> void:
	var loser := GameState.other(state.round_winner)
	var text := "[color=#ff5a45]%s倒下了。[/color]" % _name(loser)
	_say(text)
	_log(text)
	await _wait(1.0)


func _flash(color: Color, duration: float) -> void:
	var tw := create_tween()
	tw.tween_method(func(a: float) -> void: post.set_shader_parameter("flash_color", Color(color, a)),
		color.a, 0.0, duration)


func _set_fade(v: float) -> void:
	_fade = v
	post.set_shader_parameter("fade", v)


func _tween_fade(to: float, duration: float) -> Signal:
	var tw := create_tween()
	tw.tween_method(_set_fade, _fade, to, duration)
	return tw.finished


func _banner(title: String, sub: String, hold := 1.4) -> void:
	banner_title.text = title
	banner_sub.text = sub
	banner.modulate.a = 0.0
	banner.visible = true
	var tw := create_tween()
	tw.tween_property(banner, "modulate:a", 1.0, 0.35)
	tw.tween_interval(hold)
	tw.tween_property(banner, "modulate:a", 0.0, 0.4)
	await tw.finished
	banner.visible = false


func _wait(seconds: float) -> void:
	await get_tree().create_timer(seconds).timeout


# ---------------------------------------------------------------- 刷新

func _refresh() -> void:
	if state == null:
		return
	crt.show_state(state, "第%s局" % CN_NUM[state.round_index])
	scene.set_sawed(state.saw_active)
	scene.set_cuffed(D, state.cuffs[D] != GameState.CUFF_NONE)
	scene.set_cuffed(P, state.cuffs[P] != GameState.CUFF_NONE)


func _say(text: String) -> void:
	subtitle.text = "[center]%s[/center]" % text


## 记录框不滚动：从最旧的一条开始删，直到全部内容放得下，最新的一条总是完整可见
## @keyword-cn 记录框, 最新消息
## @keyword-en log-panel, latest-message
func _log(text: String) -> void:
	_log_lines.append(text)
	log_box.text = "\n".join(_log_lines)
	var room := log_box.size.y
	while _log_lines.size() > 1 and log_box.get_content_height() > room:
		_log_lines.pop_front()
		log_box.text = "\n".join(_log_lines)


func _name(actor: int) -> String:
	return "你" if actor == P else "行刑人"


func _shell(live: bool) -> String:
	return LIVE if live else BLANK
