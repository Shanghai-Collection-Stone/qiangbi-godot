class_name CrtPanel
extends Control
## 左上角的绿色荧光屏：局数、剩余子弹、双方电量（生命）、手铐和锯短枪管状态，最下面一行是回合倒计时。

const GREEN := Color(0.45, 1.0, 0.55)
const DIM := Color(0.14, 0.32, 0.18)
const RED := Color(1.0, 0.35, 0.3)
const BOLT := [
	Vector2(0.62, 0.0), Vector2(0.15, 0.55), Vector2(0.45, 0.55),
	Vector2(0.35, 1.0), Vector2(0.85, 0.4), Vector2(0.55, 0.4), Vector2(0.75, 0.0),
]

var round_text := ""
var shells_left := 0
var max_hp := 0
var hp := [0, 0]
var cuffed := [false, false]
var sawed := false
## 倒计时行：文字（谁的回合）、剩余秒数（小于 0 时不显示秒数和进度条）、总秒数
var turn_text := ""
var turn_left := -1.0
var turn_total := 1.0
var _blink := 0.0


func _init() -> void:
	mouse_filter = MOUSE_FILTER_IGNORE
	custom_minimum_size = Vector2(156, 84)
	size = custom_minimum_size


func _process(delta: float) -> void:
	_blink += delta
	if sawed or (turn_left >= 0.0 and turn_left <= 10.0):
		queue_redraw()


## 更新倒计时行；seconds_left 小于 0 表示这一行只显示文字（比如行刑人的回合）
## @keyword-cn 回合倒计时, 计时显示
## @keyword-en turn-countdown, timer-display
func set_turn(text: String, seconds_left := -1.0, total := 1.0) -> void:
	if text == turn_text and ceili(seconds_left) == ceili(turn_left) and (seconds_left < 0.0) == (turn_left < 0.0):
		turn_left = seconds_left
		return
	turn_text = text
	turn_left = seconds_left
	turn_total = total
	queue_redraw()


func show_state(state: GameState, round_name: String) -> void:
	round_text = round_name
	shells_left = state.remaining()
	max_hp = state.max_hp
	hp = state.hp.duplicate()
	cuffed = [state.cuffs[0] != GameState.CUFF_NONE, state.cuffs[1] != GameState.CUFF_NONE]
	sawed = state.saw_active
	queue_redraw()


func _draw() -> void:
	var font := get_theme_default_font()
	draw_rect(Rect2(Vector2.ZERO, size), Color(0.02, 0.05, 0.03, 0.9))
	draw_rect(Rect2(Vector2.ZERO, size), Color(0.22, 0.4, 0.26), false, 1.0)
	draw_string(font, Vector2(6, 15), round_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, GREEN)
	var right := "剩余 %d 发" % shells_left
	if sawed and fmod(_blink, 0.8) < 0.5:
		right = "伤害×2  " + right
	draw_string(font, Vector2(6, 15), right, HORIZONTAL_ALIGNMENT_RIGHT, size.x - 12, 12, RED if sawed else GREEN)
	_row(font, 22, "行刑人", GameState.DEALER)
	_row(font, 42, "你", GameState.PLAYER)
	_turn_row(font, 62)
	for y in range(0, int(size.y), 2):
		draw_line(Vector2(1, y), Vector2(size.x - 1, y), Color(0, 0, 0, 0.28))


func _row(font: Font, y: float, label: String, actor: int) -> void:
	draw_string(font, Vector2(6, y + 13), label, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, GREEN)
	for i in max_hp:
		var cell := Rect2(Vector2(48 + i * 11, y + 2), Vector2(9, 13))
		if i < hp[actor]:
			var pts := PackedVector2Array()
			for p in BOLT:
				pts.append(cell.position + p * cell.size)
			draw_colored_polygon(pts, GREEN)
		else:
			draw_rect(cell, DIM, false, 1.0)
	if cuffed[actor]:
		draw_string(font, Vector2(118, y + 13), "[铐]", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, RED)


## 倒计时行：左边是谁的回合，右边是剩余秒数，下面一条随时间缩短的进度条；最后 10 秒变红闪烁
## @keyword-cn 倒计时行, 进度条
## @keyword-en countdown-row, progress-bar
func _turn_row(font: Font, y: float) -> void:
	draw_line(Vector2(4, y - 1), Vector2(size.x - 4, y - 1), DIM)
	if turn_left < 0.0:
		draw_string(font, Vector2(6, y + 13), turn_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, GREEN)
		return
	var urgent := turn_left <= 10.0
	var color := RED if urgent else GREEN
	if urgent and fmod(_blink, 1.0) > 0.6:
		color = DIM
	draw_string(font, Vector2(6, y + 13), turn_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, color)
	draw_string(font, Vector2(6, y + 13), "%d 秒" % ceili(turn_left), HORIZONTAL_ALIGNMENT_RIGHT, size.x - 12, 12, color)
	var bar := Rect2(Vector2(6, y + 16), Vector2(size.x - 12, 3))
	draw_rect(bar, DIM)
	draw_rect(Rect2(bar.position, Vector2(bar.size.x * clampf(turn_left / turn_total, 0.0, 1.0), bar.size.y)),
		RED if urgent else GREEN)
