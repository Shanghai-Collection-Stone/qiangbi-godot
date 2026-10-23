class_name Items
extends RefCounted
## 道具定义：名称、说明。逻辑在 GameState.use_item 中实现，模型在 Props.item 中。

const MAGNIFIER := "magnifier"
const CIGARETTE := "cigarette"
const BEER := "beer"
const SAW := "saw"
const HANDCUFFS := "handcuffs"
const PHONE := "phone"
const INVERTER := "inverter"
const MEDICINE := "medicine"

const ALL := [MAGNIFIER, CIGARETTE, BEER, SAW, HANDCUFFS, PHONE, INVERTER, MEDICINE]

const INFO := {
	MAGNIFIER: {"name": "放大镜", "desc": "查看枪膛里当前这一发是实弹还是空包弹。"},
	CIGARETTE: {"name": "香烟", "desc": "恢复 1 点生命（不超过上限）。"},
	BEER: {"name": "啤酒", "desc": "拉动枪栓，退出当前这一发（所有人都能看到它是什么）。"},
	SAW: {"name": "手锯", "desc": "锯短枪管：下一发实弹造成 2 点伤害。"},
	HANDCUFFS: {"name": "手铐", "desc": "铐住对手，让对手跳过下一个回合。"},
	PHONE: {"name": "一次性手机", "desc": "神秘来电：告诉你之后某一发子弹的类型。"},
	INVERTER: {"name": "极性反转器", "desc": "把当前这一发反转：实弹变空包弹，空包弹变实弹。"},
	MEDICINE: {"name": "过期药", "desc": "50% 恢复 2 点生命，50% 失去 1 点生命。"},
}


static func display_name(id: String) -> String:
	return INFO[id]["name"]


static func description(id: String) -> String:
	return INFO[id]["desc"]
