class_name GameState
extends RefCounted
## 纯游戏逻辑：子弹、生命、道具、回合。不依赖任何节点，可以在无头模式下测试。

const PLAYER := 0
const DEALER := 1
const MAX_ITEMS := 8

## 每一局的配置：生命上限、每次装弹给双方各发几件道具
const ROUNDS := [
	{"hp": 2, "items": 0},
	{"hp": 4, "items": 2},
	{"hp": 6, "items": 4},
]

## 手铐状态
const CUFF_NONE := 0
const CUFF_LOCKED := 1    # 下一次轮到时跳过
const CUFF_BREAKING := 2  # 刚跳过一回合，还没挣脱，暂时不能再被铐

var rng := RandomNumberGenerator.new()
var round_index := 0
var max_hp := 2
var hp := [2, 2]
var items := [[], []]
## true = 实弹，false = 空包弹；pos 指向枪膛里的当前这一发
var shells: Array[bool] = []
var pos := 0
var current_turn := PLAYER
var cuffs := [CUFF_NONE, CUFF_NONE]
var saw_active := false
## 每个角色已知的子弹：shells 下标 -> 是否实弹
var known := [{}, {}]
## 公开计数：还没亮出来的子弹按「装弹时的原样」算有几发实弹、几发空包弹。反转器不会改变它。
var tally_live := 0
var tally_blank := 0
## 被极性反转器翻过（奇数次）的子弹下标。用反转器是公开的，只是谁也看不到翻成了什么
var inverted := {}
var round_over := false
var round_winner := -1
var stats := {}


func new_game(seed_value: int = -1) -> void:
	if seed_value >= 0:
		rng.seed = seed_value
	else:
		rng.randomize()
	round_index = 0
	stats = {"shots": 0, "items_used": 0, "damage_taken": 0, "damage_dealt": 0, "rounds_won": 0}


func start_round(index: int) -> void:
	round_index = index
	max_hp = ROUNDS[index]["hp"]
	hp = [max_hp, max_hp]
	items = [[], []]
	shells = []
	pos = 0
	cuffs = [CUFF_NONE, CUFF_NONE]
	saw_active = false
	known = [{}, {}]
	inverted = {}
	tally_live = 0
	tally_blank = 0
	round_over = false
	round_winner = -1
	current_turn = PLAYER


func is_final_round() -> bool:
	return round_index == ROUNDS.size() - 1


static func other(actor: int) -> int:
	return 1 - actor


func remaining() -> int:
	return shells.size() - pos


func needs_reload() -> bool:
	return not round_over and remaining() == 0


## 装弹并发放道具。每次装弹后都由玩家先手。
func load_shells() -> Dictionary:
	var total := rng.randi_range(2, 8)
	var live := clampi(roundi(total * rng.randf_range(0.35, 0.65)), 1, total - 1)
	shells = []
	for i in total:
		shells.append(i < live)
	for i in range(total - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var t := shells[i]
		shells[i] = shells[j]
		shells[j] = t
	pos = 0
	tally_live = live
	tally_blank = total - live
	inverted = {}
	known = [{}, {}]
	saw_active = false
	cuffs = [CUFF_NONE, CUFF_NONE]
	current_turn = PLAYER

	var given := [[], []]
	var count: int = ROUNDS[round_index]["items"]
	for actor in [PLAYER, DEALER]:
		for k in count:
			if items[actor].size() >= MAX_ITEMS:
				break
			var id: String = Items.ALL[rng.randi_range(0, Items.ALL.size() - 1)]
			items[actor].append(id)
			given[actor].append(id)
	return {"live": live, "blank": total - live, "total": total, "given": given}


## 当前这一发对 actor 来说：-1 未知，0 空包弹，1 实弹
func known_current(actor: int) -> int:
	if remaining() == 0 or not known[actor].has(pos):
		return -1
	return 1 if known[actor][pos] else 0


## 站在 actor 的角度，当前这一发是实弹的概率。先按公开计数（装弹时的原样）和自己知道的子弹算，
## 当前这一发如果被反转器翻过，实弹概率就是 1 - p
## @keyword-cn 实弹概率, 反转器
## @keyword-en live-probability, inverter-aware
func live_probability(actor: int) -> float:
	if remaining() <= 0:
		return 0.0
	var k := known_current(actor)
	if k != -1:
		return float(k)
	var unknown_live := tally_live
	var unknown_count := remaining()
	for idx in known[actor]:
		if idx > pos:
			unknown_count -= 1
			if known[actor][idx]:
				unknown_live -= 1
	if unknown_count <= 0:
		return 0.5
	var p := clampf(float(unknown_live) / unknown_count, 0.0, 1.0)
	return 1.0 - p if inverted.has(pos) else p


## 返回不能使用该道具的原因；可以使用时返回空字符串
func item_block_reason(actor: int, index: int) -> String:
	if round_over or remaining() == 0:
		return "现在不能使用道具"
	if index < 0 or index >= items[actor].size():
		return "没有这个道具"
	match items[actor][index]:
		Items.SAW:
			if saw_active:
				return "枪管已经锯短了"
		Items.HANDCUFFS:
			if cuffs[other(actor)] != CUFF_NONE:
				return "对手手上已经有手铐了"
		Items.CIGARETTE:
			if hp[actor] >= max_hp:
				return "生命已满"
	return ""


func use_item(actor: int, index: int) -> Dictionary:
	var reason := item_block_reason(actor, index)
	if reason != "":
		return {"ok": false, "reason": reason}
	var id: String = items[actor][index]
	items[actor].remove_at(index)
	if actor == PLAYER:
		stats["items_used"] += 1
	var res := {"ok": true, "actor": actor, "item": id}
	match id:
		Items.MAGNIFIER:
			known[actor][pos] = shells[pos]
			res["live"] = shells[pos]
		Items.CIGARETTE:
			res["heal"] = _heal(actor, 1)
		Items.BEER:
			var ejected := shells[pos]
			_reveal(ejected, pos)
			pos += 1
			res["live"] = ejected
		Items.SAW:
			saw_active = true
		Items.HANDCUFFS:
			cuffs[other(actor)] = CUFF_LOCKED
		Items.PHONE:
			if remaining() <= 1:
				res["offset"] = -1
			else:
				var idx := rng.randi_range(pos + 1, shells.size() - 1)
				known[actor][idx] = shells[idx]
				res["offset"] = idx - pos
				res["live"] = shells[idx]
		Items.INVERTER:
			shells[pos] = not shells[pos]
			if inverted.has(pos):
				inverted.erase(pos)
			else:
				inverted[pos] = true
			for a in [PLAYER, DEALER]:
				if known[a].has(pos):
					known[a][pos] = shells[pos]
		Items.MEDICINE:
			if rng.randf() < 0.5:
				res["heal"] = _heal(actor, 2)
			else:
				res["heal"] = -1
				_damage(actor, 1)
	return res


func shoot(actor: int, target: int) -> Dictionary:
	assert(remaining() > 0 and not round_over)
	var live := shells[pos]
	_reveal(live, pos)
	pos += 1
	var damage := (2 if saw_active else 1) if live else 0
	var res := {
		"actor": actor, "target": target, "live": live, "damage": damage,
		"sawed": saw_active, "extra_turn": false, "skipped": -1,
	}
	saw_active = false
	if actor == PLAYER:
		stats["shots"] += 1
	if damage > 0:
		_damage(target, damage)
	if round_over:
		return res
	if target == actor and not live:
		res["extra_turn"] = true
	else:
		res["skipped"] = _pass_turn(actor)
	return res


## 把回合交给对手；如果对手被铐住则跳过他，返回被跳过的角色（没有则 -1）
func _pass_turn(from_actor: int) -> int:
	var nxt := other(from_actor)
	if cuffs[nxt] == CUFF_LOCKED:
		cuffs[nxt] = CUFF_BREAKING
		current_turn = from_actor
		return nxt
	if cuffs[nxt] == CUFF_BREAKING:
		cuffs[nxt] = CUFF_NONE
	current_turn = nxt
	return -1


func _heal(actor: int, amount: int) -> int:
	var before: int = hp[actor]
	hp[actor] = mini(max_hp, before + amount)
	return hp[actor] - before


func _damage(actor: int, amount: int) -> void:
	hp[actor] = maxi(0, hp[actor] - amount)
	if actor == PLAYER:
		stats["damage_taken"] += amount
	else:
		stats["damage_dealt"] += amount
	if hp[actor] == 0:
		round_over = true
		round_winner = other(actor)
		if round_winner == PLAYER:
			stats["rounds_won"] += 1


## 一发子弹被亮出来（开枪或退膛），更新公开计数。被反转过的子弹亮出来的是翻过之后的样子，
## 但公开计数记的是装弹时的原样，所以要按「翻之前」那一类减
## @keyword-cn 公开计数, 亮弹
## @keyword-en public-tally, reveal-shell
func _reveal(live: bool, index: int) -> void:
	var original := live != inverted.has(index)
	if (original and tally_live > 0) or tally_blank == 0:
		tally_live = maxi(0, tally_live - 1)
	else:
		tally_blank -= 1
