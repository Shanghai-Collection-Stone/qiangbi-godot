extends SceneTree
## 无头测试：godot --headless --path . -s tests/run_tests.gd

const P := GameState.PLAYER
const D := GameState.DEALER

var _failures := 0
var _checks := 0


func _init() -> void:
	test_load_shells()
	test_blank_on_self_keeps_turn()
	test_live_on_opponent_passes_turn()
	test_saw_doubles_damage_once()
	test_handcuffs_skip_one_turn()
	test_beer_ejects_and_updates_tally()
	test_magnifier_and_probability()
	test_phone_reveals_future_shell()
	test_inverter_flips_current()
	test_inverter_flips_probability()
	test_ai_avoids_bad_self_shots()
	test_round_ends_at_zero_hp()
	test_item_block_reasons()
	test_ai_self_play()
	print("%d checks, %d failures" % [_checks, _failures])
	quit(1 if _failures > 0 else 0)


func check(cond: bool, msg: String) -> void:
	_checks += 1
	if not cond:
		_failures += 1
		printerr("FAIL: " + msg)


## 构造一局，枪里装好指定的子弹
func make_state(shells: Array, round_index := 1) -> GameState:
	var s := GameState.new()
	s.new_game(1)
	s.start_round(round_index)
	s.shells.assign(shells)
	s.pos = 0
	s.tally_live = shells.count(true)
	s.tally_blank = shells.count(false)
	return s


func test_load_shells() -> void:
	var s := GameState.new()
	for seed_value in 300:
		s.new_game(seed_value)
		s.start_round(2)
		var info := s.load_shells()
		check(info["total"] >= 2 and info["total"] <= 8, "total in range")
		check(info["live"] >= 1 and info["blank"] >= 1, "at least one of each")
		check(s.shells.count(true) == info["live"], "live count matches")
		check(s.items[P].size() == 4 and s.items[D].size() == 4, "items given in round 3")
		check(s.current_turn == P, "player starts each load")


func test_blank_on_self_keeps_turn() -> void:
	var s := make_state([false, true])
	var r := s.shoot(P, P)
	check(not r["live"] and r["extra_turn"], "blank on self gives extra turn")
	check(s.current_turn == P, "turn stays with player")
	check(s.hp[P] == 4, "no damage from blank")


func test_live_on_opponent_passes_turn() -> void:
	var s := make_state([true, false])
	var r := s.shoot(P, D)
	check(r["damage"] == 1 and s.hp[D] == 3, "live deals 1")
	check(s.current_turn == D, "turn passes to dealer")


func test_saw_doubles_damage_once() -> void:
	var s := make_state([true, true, false])
	s.items[P] = [Items.SAW]
	check(s.use_item(P, 0)["ok"], "saw usable")
	s.shoot(P, D)
	check(s.hp[D] == 2, "sawed shot deals 2")
	check(not s.saw_active, "saw resets after shot")
	s.shoot(D, P)
	check(s.hp[P] == 3, "next shot deals 1")


func test_handcuffs_skip_one_turn() -> void:
	var s := make_state([false, false, false, false])
	s.items[P] = [Items.HANDCUFFS, Items.HANDCUFFS]
	s.use_item(P, 0)
	var r := s.shoot(P, D)
	check(r["skipped"] == D and s.current_turn == P, "cuffed dealer is skipped")
	check(s.use_item(P, 0)["ok"] == false, "cannot re-cuff while breaking free")
	r = s.shoot(P, D)
	check(r["skipped"] == -1 and s.current_turn == D, "dealer gets turn after skip")
	check(s.cuffs[D] == GameState.CUFF_NONE, "cuffs removed")


func test_beer_ejects_and_updates_tally() -> void:
	var s := make_state([true, false, false])
	s.items[P] = [Items.BEER]
	var r := s.use_item(P, 0)
	check(r["live"] == true and s.pos == 1, "beer ejects current shell")
	check(s.tally_live == 0 and s.tally_blank == 2, "tally updated")
	check(s.current_turn == P, "beer does not pass the turn")


func test_magnifier_and_probability() -> void:
	var s := make_state([false, true, true, false])
	check(is_equal_approx(s.live_probability(D), 0.5), "2 of 4 live")
	s.items[D] = [Items.MAGNIFIER]
	var r := s.use_item(D, 0)
	check(r["live"] == false, "magnifier shows blank")
	check(s.known_current(D) == 0 and s.known_current(P) == -1, "only user learns")
	check(s.live_probability(D) == 0.0, "known blank -> 0")
	s.shoot(D, D)
	check(is_equal_approx(s.live_probability(D), 2.0 / 3.0), "after blank: 2 of 3 live")


func test_phone_reveals_future_shell() -> void:
	var s := make_state([false, true, false])
	s.items[P] = [Items.PHONE]
	var r := s.use_item(P, 0)
	check(r["offset"] >= 1 and r["offset"] <= 2, "phone points to a future shell")
	check(r["live"] == s.shells[r["offset"]], "phone tells the truth")
	var single := make_state([true])
	single.items[P] = [Items.PHONE]
	check(single.use_item(P, 0)["offset"] == -1, "phone has nothing to say on last shell")


func test_inverter_flips_current() -> void:
	var s := make_state([false, true])
	s.items[P] = [Items.MAGNIFIER, Items.INVERTER]
	s.use_item(P, 0)
	s.use_item(P, 0)
	check(s.shells[0] == true, "inverter flipped blank to live")
	check(s.known_current(P) == 1, "knowledge flipped too")
	check(s.tally_live == 1, "public tally unchanged")
	s.shoot(P, D)
	check(s.tally_live + s.tally_blank == s.remaining(), "tally stays consistent")
	# 打出去的是被翻过的那一发（原来是空包弹），剩下的那发实弹要算对
	check(s.tally_live == 1 and s.tally_blank == 0, "inverted shell counted as its original kind")
	check(s.live_probability(D) == 1.0, "dealer knows the last shell is live")


## 对手用了反转器（结果看不到），当前这一发的实弹概率要翻成 1 - p
func test_inverter_flips_probability() -> void:
	var s := make_state([true, false, false])
	check(is_equal_approx(s.live_probability(D), 1.0 / 3.0), "1 of 3 live")
	s.items[P] = [Items.INVERTER]
	s.use_item(P, 0)
	check(is_equal_approx(s.live_probability(D), 2.0 / 3.0), "after public inversion: 2 of 3")
	s.use_item(P, -1)
	s.items[P] = [Items.INVERTER]
	s.use_item(P, 0)
	check(is_equal_approx(s.live_probability(D), 1.0 / 3.0), "inverted twice: back to 1 of 3")


## 行刑人不会在不划算的时候打自己
func test_ai_avoids_bad_self_shots() -> void:
	var rng := RandomNumberGenerator.new()
	var s := make_state([true, false])
	s.current_turn = D
	check(DealerAI.decide(s, D, rng) == {"type": "shoot", "target": P}, "50/50 -> shoot the player, never a coin flip")
	s = make_state([true, true, false, false, false])
	s.current_turn = D
	check(DealerAI.decide(s, D, rng)["target"] == P, "40% live -> shoot the player")
	s = make_state([true, false, false, false])
	s.current_turn = D
	check(DealerAI.decide(s, D, rng)["target"] == D, "25% live with hp to spare -> self for the extra turn")
	s.hp[D] = 1
	check(DealerAI.decide(s, D, rng)["target"] == P, "25% live at 1 hp -> too risky, shoot the player")
	# 原来的 bug：玩家把空包弹翻成实弹打行刑人，剩下最后一发实弹，旧逻辑以为剩的是空包弹而打自己
	s = make_state([false, true], 2)
	s.items[P] = [Items.INVERTER]
	s.use_item(P, 0)
	s.shoot(P, D)
	check(s.current_turn == D, "dealer's turn")
	check(DealerAI.decide(s, D, rng)["target"] == P, "last shell is live after an inverted shot -> dealer shoots the player")
	s = make_state([true, false, false, false])
	s.current_turn = D
	s.items[D] = [Items.INVERTER]
	check(DealerAI.decide(s, D, rng) == {"type": "item", "index": 0}, "blank likely -> invert first")


func test_round_ends_at_zero_hp() -> void:
	var s := make_state([true, true, true], 0)
	s.shoot(P, D)
	check(not s.round_over, "dealer still alive at 1 hp")
	s.shoot(D, D)
	check(s.round_over and s.round_winner == P, "player wins when dealer hits 0")
	check(s.stats["rounds_won"] == 1, "round counted")


func test_item_block_reasons() -> void:
	var s := make_state([true, false])
	s.items[P] = [Items.CIGARETTE, Items.SAW, Items.SAW]
	check(s.item_block_reason(P, 0) != "", "no smoking at full hp")
	s.use_item(P, 1)
	check(s.item_block_reason(P, 1) != "", "cannot saw twice")
	check(s.item_block_reason(P, 5) != "", "bad index blocked")


## 双方都用 AI 打完整局，确保不会卡死、不会出错
func test_ai_self_play() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 42
	var wins := [0, 0]
	for game in 400:
		var s := GameState.new()
		s.new_game(game)
		for r in GameState.ROUNDS.size():
			s.start_round(r)
			var steps := 0
			while not s.round_over and steps < 2000:
				steps += 1
				if s.needs_reload():
					s.load_shells()
				var actor := s.current_turn
				var action := DealerAI.decide(s, actor, rng)
				if action["type"] == "item":
					check(s.use_item(actor, action["index"])["ok"], "AI only picks usable items")
				else:
					s.shoot(actor, action["target"])
				check(s.hp[P] >= 0 and s.hp[D] >= 0 and s.hp[P] <= s.max_hp, "hp in bounds")
				check(s.tally_live + s.tally_blank == s.remaining(), "tally consistent")
			check(s.round_over, "round terminates")
			wins[s.round_winner] += 1
	print("AI vs AI round wins (first player / second player): %s" % [wins])
	check(wins[0] > 0 and wins[1] > 0, "both sides can win")
