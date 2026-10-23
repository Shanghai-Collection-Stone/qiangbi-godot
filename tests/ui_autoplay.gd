extends SceneTree
## 用真实场景自动打几整局（玩家一方也交给 AI），检查流程不会卡死或报错。
## 至少打 3 局；如果还没有哪一局用到过道具（第二局起才发道具），就继续打，最多 12 局。
##   godot --headless --path . -s tests/ui_autoplay.gd
## 在有显示的环境下加 `-- --shots=<目录>` 会以正常速度运行并定时截图。

const MIN_GAMES := 3
const MAX_GAMES := 12
const TIMEOUT_MSEC := 400000

var main: Control
var rng := RandomNumberGenerator.new()
var games_done := 0
var items_seen := false
var in_game := false
var shots_dir := ""
var next_shot := 0.0
var elapsed := 0.0
var started_at := 0


func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--shots="):
			shots_dir = arg.substr(8)
	Engine.time_scale = 1.0 if shots_dir != "" else 25.0
	rng.seed = 7
	started_at = Time.get_ticks_msec()
	main = load("res://scenes/main.tscn").instantiate()
	root.add_child(main)


func _process(delta: float) -> bool:
	elapsed += delta
	if shots_dir != "" and elapsed >= next_shot:
		_screenshot()
		next_shot += 1.5
	if Time.get_ticks_msec() - started_at > TIMEOUT_MSEC:
		printerr("FAIL: autoplay timed out")
		quit(1)
		return false

	if main.overlay.visible:
		if in_game:
			in_game = false
			games_done += 1
			var s: Dictionary = main.state.stats
			print("game %d over: rounds won %d, shots %d, items %d" % [
				games_done, s["rounds_won"], s["shots"], s["items_used"]])
			items_seen = items_seen or s["items_used"] > 0
			if shots_dir != "" or (games_done >= MIN_GAMES and items_seen):
				quit(0)
				return false
			if games_done >= MAX_GAMES:
				printerr("FAIL: no game reached the rounds with items")
				quit(1)
				return false
		if elapsed > 1.0:
			in_game = true
			main._start_game()
	elif main.accepting_input:
		main.player_action.emit(DealerAI.decide(main.state, GameState.PLAYER, rng))
	return false


func _screenshot() -> void:
	var img := root.get_texture().get_image()
	if img == null:
		return
	img.resize(img.get_width() * 2, img.get_height() * 2, Image.INTERPOLATE_NEAREST)
	DirAccess.make_dir_recursive_absolute(shots_dir)
	img.save_png("%s/shot_%03d.png" % [shots_dir, int(elapsed * 10)])
