class_name DealerAI
extends RefCounted
## 行刑人的决策。每次调用只决定一个动作：用一个道具，或者开一枪。
## 返回 {"type": "item", "index": i} 或 {"type": "shoot", "target": GameState.PLAYER/DEALER}

## 赌概率时，只有实弹概率不超过这个值才打自己（赌中空包弹能多行动一次）；再高就打对手
## @keyword-cn 自残阈值, 风险控制
## @keyword-en self-shot-threshold, risk-control
const SELF_SHOT_MAX_P := 0.34
## 自己只剩 1 点生命时更保守：几乎可以确定是空包弹才打自己，否则一枪就死
const SELF_SHOT_MAX_P_LAST_HP := 0.15
## 实弹概率落在这个区间（最拿不准）时，手里有啤酒就先退一发，看清再说
const BEER_MIN_P := 0.3
const BEER_MAX_P := 0.7


## 决定下一个动作。只用公开信息（公布的数量、亮出来的子弹、谁用过反转器）和自己看到的子弹
## @keyword-cn 行刑人决策, 概率开枪
## @keyword-en dealer-decision, odds-based-shot
static func decide(state: GameState, me: int, _rng: RandomNumberGenerator) -> Dictionary:
	var opp := GameState.other(me)
	var known := state.known_current(me)

	# 1. 先保命
	if state.hp[me] < state.max_hp:
		var cig := _usable(state, me, Items.CIGARETTE)
		if cig != -1:
			return _item(cig)
	if state.hp[me] > 1 and state.hp[me] <= state.max_hp - 2:
		var med := _usable(state, me, Items.MEDICINE)
		if med != -1:
			return _item(med)

	# 2. 不知道枪膛里是什么就先想办法知道
	if known == -1:
		var glass := _usable(state, me, Items.MAGNIFIER)
		if glass != -1:
			return _item(glass)
		if state.remaining() >= 3:
			var phone := _usable(state, me, Items.PHONE)
			if phone != -1:
				return _item(phone)

	# 3. 已知是空包弹：能反转就反转，否则打自己换回合
	if known == 0:
		var inv := _usable(state, me, Items.INVERTER)
		if inv != -1:
			return _item(inv)
		return _shoot(me)

	# 4. 已知是实弹：上手铐、锯枪管，然后打对手
	if known == 1:
		return _aggressive(state, me, opp, true)

	# 5. 只能赌概率（live_probability 已经算上了对手用过的反转器）
	var p := state.live_probability(me)
	var beer := _usable(state, me, Items.BEER)
	if beer != -1 and state.remaining() > 1 and p > BEER_MIN_P and p < BEER_MAX_P:
		return _item(beer)
	# 空包弹更可能：先反转，实弹概率就变成 1 - p，再打对手
	if p < 0.5:
		var inv := _usable(state, me, Items.INVERTER)
		if inv != -1:
			return _item(inv)
	if p >= 0.5:
		return _aggressive(state, me, opp, p >= 0.75)
	# 打自己只在空包弹把握很大时才做，生命只剩 1 点时更保守；五五开或拿不准时一律打对手
	var limit := SELF_SHOT_MAX_P if state.hp[me] > 1 else SELF_SHOT_MAX_P_LAST_HP
	return _shoot(me if p <= limit else opp)


static func _aggressive(state: GameState, me: int, opp: int, confident: bool) -> Dictionary:
	if state.remaining() > 1:
		var cuffs := _usable(state, me, Items.HANDCUFFS)
		if cuffs != -1:
			return _item(cuffs)
	if confident:
		var saw := _usable(state, me, Items.SAW)
		if saw != -1:
			return _item(saw)
	return _shoot(opp)


## 找到一件当前可以使用的道具，返回下标；没有则 -1
static func _usable(state: GameState, me: int, id: String) -> int:
	for i in state.items[me].size():
		if state.items[me][i] == id and state.item_block_reason(me, i) == "":
			return i
	return -1


static func _item(index: int) -> Dictionary:
	return {"type": "item", "index": index}


static func _shoot(target: int) -> Dictionary:
	return {"type": "shoot", "target": target}
