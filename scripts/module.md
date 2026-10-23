# scripts 模块

## 模块名称 (Module Name)

scripts · 游戏逻辑与 3D 场景

## 概述 (Overview)

游戏本体：规则（`game_state.gd`）、行刑人 AI、道具定义、流程与界面（`main.gd`）、3D 赌桌场景与演出（`table_scene.gd`）、模型与材质入口（`props.gd`）、计分板和合成音效。模型和贴图来自 `art` 模块（`res://art/models/`、`res://art/textures/`），由 `props.gd` 加载并换上像素材质。

## 文件清单 (File List)

- `game_state.gd` — 纯规则：子弹、生命、道具、回合、手铐，不依赖节点；公开计数和实弹概率会算上被反转器翻过的子弹。
- `dealer_ai.gd` — 行刑人 AI，只用公开信息决策；按实弹概率和自己的生命决定打谁，不会在五五开或低血量时赌自己。
- `items.gd` — 道具 id、名称、说明。
- `main.gd` — 游戏流程（async/await）、像素 HUD（开枪选项、记录框）、菜单、后期特效调度。
- `table_scene.gd` — 3D 场景：房间（墙缝绿光、蜡烛灯）、吊灯（摆动、光锥、浮尘）、行刑人（触手须受击变红）、枪、子弹、道具的摆放、动画、枪口火光与硝烟、鼠标拾取。
- `props.gd` — 材质表 `MATERIALS`、触手摆动材质、按材质名给 glb 换材质的 `model()`、霰弹枪/霰弹/道具/行刑人模型入口。
- `crt_panel.gd` — 左上角荧光屏计分板，最下面一行是回合倒计时。
- `sfx.gd` — 程序合成音效；背景音乐（`art/music/` 的 CC0 曲目）的播放、交叉淡入淡出和低通压闷。

## 函数清单 (Function List)

- `props.part(parent, mesh, material, pos, rot, scl, node_name)` — 生成一个网格节点挂到 parent 下 | keywords: mesh-part, add-mesh, 网格节点, 拼装部件
- `props.mat(color, roughness, metallic, texture)` — 新建一个最近邻采样的标准材质 | keywords: new-material, pixel-material, 新建材质, 像素材质
- `props.glow(color, energy)` — 不受光照影响的发光材质 | keywords: glow-material, emissive, 发光材质, 自发光
- `props.material(key)` — 按 key 取材质表里的材质，按名字缓存共享 | keywords: material-table, material-cache, 材质表, 材质缓存
- `props.tentacle_material()` — 触手材质（shaders/tentacle.gdshader，顶点摆动 + 吸盘贴图），所有触手共享 | keywords: tentacle-material, sway-shader, 触手材质, 摆动着色器
- `props.hull_material(live, glowing)` — 弹壳塑料壳材质：同一张灰色贴图染成实弹红或空包弹蓝；glowing 时自发光（放大镜亮弹） | keywords: shell-hull-material, live-blank-color, 弹壳材质, 实弹颜色
- `props.pixel_texture(tex_name)` — 加载 art/textures/ 下的像素贴图 | keywords: load-texture, pixel-texture, 加载贴图, 像素贴图
- `props._slot_texture()` — 道具格：半透明深色底、浅色描边、四角加亮（程序生成，32×32） | keywords: item-slot, slot-texture, 道具格, 格子贴图
- `props.model(path, overrides)` — 实例化 art/models/<path>.glb，并把每个面的占位材质按名字换成材质表里的材质 | keywords: load-model, material-override, 加载模型, 替换材质
- `props._apply_materials(node, overrides)` — 递归替换节点树里所有网格的面材质（model() 的实现） | keywords: apply-materials, surface-override, 递归换材质, 面材质
- `props.shotgun()` — 霰弹枪：子节点 Body / BarrelFront / Sight / Pump，外加枪口标记 Muzzle | keywords: shotgun, gun-model, 霰弹枪, 枪模型
- `props.shell(live, glowing)` — 一发霰弹：实弹红、空包弹蓝；glowing 时自发光 | keywords: shotgun-shell, shell-model, 霰弹, 子弹模型
- `props.item(id)` — 道具模型，id 见 Items | keywords: item-model, table-item, 道具模型, 桌面道具
- `props.dealer(skin, pupil, tentacle)` — 行刑人：椅子、身体、头（Head，带瞳孔 Pupil*、触手须）、两只手（HandL/HandR）和两条袖子（ArmL/ArmR，由场景每帧摆放） | keywords: dealer, dealer-model, 行刑人, 庄家模型
- `table_scene._process(delta)` — 每帧：吊灯闪烁与摆动、光锥跟着闪、行刑人头部和手臂、镜头晃动 | keywords: frame-update, lamp-swing, 每帧更新, 吊灯摆动
- `table_scene._build_environment()` — 黑色背景、偏青的环境光、距离雾，自发光物体带柔光 | keywords: world-environment, glow-bloom, 环境设置, 柔光
- `table_scene._build_room()` — 房间模型（地砖、墙、管道、门、音箱、海报、木箱、墙缝触手、排水口触手、蜡烛、血字），门上红灯、冷色补光、墙缝绿光和蜡烛灯 | keywords: room-model, fill-light, 房间模型, 补光
- `table_scene._build_table()` — 赌桌模型和两边各 8 个道具格 | keywords: table-model, item-slots, 赌桌模型, 道具格
- `table_scene._build_lamp()` — 吊灯挂在天花板的挂点上，灯、光锥和主光源一起摆动 | keywords: pendant-lamp, light-cone, 吊灯, 光锥
- `table_scene._build_dust()` — 吊灯光里慢慢飘的灰尘 | keywords: dust-particles, floating-dust, 灰尘粒子, 浮尘
- `table_scene._build_muzzle_flash()` — 枪口火光：一张朝镜头的星形火光 + 两张沿枪管十字交叉的长条火焰；硝烟是世界空间的粒子 | keywords: muzzle-flash, gun-smoke, 枪口火光, 硝烟
- `table_scene._solve_arm(i, wrist)` — 两段手臂 IK：肩固定，手腕到 wrist，肘按 ELBOW_POLES 往下往外弯；够不着时整条手臂沿直线拉长 | keywords: arm-ik, elbow-solve, 手臂IK, 肘部求解
- `table_scene._place_segment(segment, from, to)` — 把沿本地 Y 轴长 1 米、原点居中的手臂段拉伸摆到两点之间 | keywords: arm-segment, place-between, 手臂段, 两点摆放
- `table_scene._grip_transform(i, where)` — 握拳手在枪上某个握持点的变换：杆的轴向 = 本地 X，手腕（本地 -Y）尽量朝向肩膀 | keywords: gun-grip-pose, grip-anchor, 握枪手势, 握持点
- `table_scene._show_fists(on)` — 握枪时显示握拳手、隐藏张开的手（反之亦然） | keywords: toggle-fist, hand-swap, 切换手型, 握拳手
- `table_scene._grab_gun()` — 行刑人伸手去拿桌上的枪：张开的手先伸到握把和护木上方，再换成握拳 | keywords: grab-gun, reach, 拿起枪, 伸手
- `table_scene._release_gun()` — 枪放回桌上后松手，两只手收回桌边（被铐着就收到一起） | keywords: release-gun, let-go, 放下枪, 松手
- `table_scene._make_pickable(model)` — 道具的点击范围：贴着模型网格的包围盒（四周留 1 厘米） | keywords: pick-shape, item-picking, 点击范围, 道具拾取
- `table_scene.pose_transform(pose)` — 枪在各个姿势下的变换（rest 平放桌上；player_* 玩家持枪/瞄准；dealer_* 行刑人持枪/瞄准） | keywords: gun-pose, aim-pose, 持枪姿势, 瞄准姿势
- `table_scene._tucked(butt, target)` — 托底板放在 butt、枪口朝 target 的枪变换 | keywords: butt-placement, shouldered-aim, 枪托定位, 持枪瞄准
- `table_scene.gun_to(pose, duration)` — 枪换到某个姿势。行刑人的姿势：先伸手握住枪再一起动，换姿势时两只手在握持点之间平滑换手； | keywords: move-gun, hold-animation, 移动枪, 握枪动画
- `table_scene.fire(sawed)` — 开枪演出：火光、枪口灯、硝烟、吊灯被震得摆起来、镜头震动和后坐 | keywords: fire-effects, recoil, 开枪演出, 后坐
- `main._process(delta)` — 回合倒计时：只在等玩家操作（点道具、点枪、选开枪对象）时走，道具演出期间暂停 | keywords: countdown-tick, turn-timeout, 倒计时更新, 超时
- `main._on_turn_timeout()` — 时间到：枪替玩家随机选一个对象开火 | keywords: timeout-shot, random-target, 超时开枪, 随机目标
- `main._aim_button(parent, text, font_size, min_size, callback)` — 开枪选项按钮：放进容器里由容器排版，min_size 统一宽度 | keywords: aim-button, option-layout, 开枪按钮, 选项排版
- `main._start_game()` — 开始一局：换成对局音乐，开始流程 | keywords: start-game, game-music, 开始游戏, 对局音乐
- `main._game_over(win)` — 一局结束：结算界面，音乐恢复并换回标题曲 | keywords: game-over, result-screen, 游戏结束, 结算界面
- `main._do_load()` — 装弹演出：公布实弹/空包弹数、子弹立桌上再装进枪，然后两边各自摆上新发的道具 | keywords: reload-sequence, deal-items, 装弹演出, 发放道具
- `main._player_turn()` — 玩家回合：每回合 TURN_SECONDS 秒（只在等玩家操作时走），用道具不换回合，开一枪结束回合 | keywords: player-turn, turn-timer, 玩家回合, 回合计时
- `main._present_shot(res)` — 开枪演出：举枪、瞄准（音乐压闷）、开枪或空响（音乐放开）、拉枪栓、放下枪 | keywords: shot-sequence, suspense, 开枪流程, 紧张感
- `main._player_hit_fx()` — 玩家中弹：白光，黑屏片刻（音乐一直闷着），再带着红色醒来、音乐慢慢回来 | keywords: player-hit, blackout-wake, 玩家中弹, 黑屏醒来
- `main._log(text)` — 记录框不滚动：从最旧的一条开始删，直到全部内容放得下，最新的一条总是完整可见 | keywords: log-panel, latest-message, 记录框, 最新消息
- `sfx._exit_tree()` — 退出时停掉音乐、放掉曲子，否则正在播放的 OGG 会在退出时报资源未释放 | keywords: stop-music, exit-cleanup, 停止音乐, 退出清理
- `sfx._build_music_bus()` — Music 总线（带低通滤波器）和音乐播放器 | keywords: music-bus, lowpass-filter, 音乐总线, 低通滤波器
- `sfx.play_music(track, fade)` — 换背景音乐：旧的淡出、新的从头淡入，循环播放；已经在放同一首就不动 | keywords: play-music, crossfade, 播放音乐, 交叉淡入淡出
- `sfx.muffle_music(on, duration)` — 把音乐压低成闷声（低通 + 降音量），用在扣扳机前那一下的紧张感；on 为 false 时恢复 | keywords: muffle-music, lowpass-duck, 音乐压低, 低通滤波
- `sfx._set_cutoff(t, from_hz, to_hz)` — 低通截止频率按对数插值，听起来扫得均匀 | keywords: cutoff-sweep, log-interpolation, 截止频率, 对数插值
- `sfx._tick()` — 倒计时最后 10 秒的滴答：很短的高频咔嗒 + 一点木头共鸣 | keywords: tick-sound, clock-sound, 倒计时滴答, 钟表声
- `crt_panel.set_turn(text, seconds_left, total)` — 更新倒计时行；seconds_left 小于 0 表示这一行只显示文字（比如行刑人的回合） | keywords: turn-countdown, timer-display, 回合倒计时, 计时显示
- `crt_panel._turn_row(font, y)` — 倒计时行：左边是谁的回合，右边是剩余秒数，下面一条随时间缩短的进度条；最后 10 秒变红闪烁 | keywords: countdown-row, progress-bar, 倒计时行, 进度条
- `game_state.live_probability(actor)` — 站在 actor 的角度，当前这一发是实弹的概率。先按公开计数（装弹时的原样）和自己知道的子弹算， | keywords: live-probability, inverter-aware, 实弹概率, 反转器
- `game_state._reveal(live, index)` — 一发子弹被亮出来（开枪或退膛），更新公开计数。被反转过的子弹亮出来的是翻过之后的样子， | keywords: public-tally, reveal-shell, 公开计数, 亮弹
- `dealer_ai.decide(state, me, _rng)` — 决定下一个动作。只用公开信息（公布的数量、亮出来的子弹、谁用过反转器）和自己看到的子弹 | keywords: dealer-decision, odds-based-shot, 行刑人决策, 概率开枪

## 关键词索引 (Keyword Index)

| 中文 | English |
|---|---|
| 网格节点 | mesh-part |
| 拼装部件 | add-mesh |
| 新建材质 | new-material |
| 像素材质 | pixel-material |
| 发光材质 | glow-material |
| 自发光 | emissive |
| 材质表 | material-table |
| 材质缓存 | material-cache |
| 触手材质 | tentacle-material |
| 摆动着色器 | sway-shader |
| 弹壳材质 | shell-hull-material |
| 实弹颜色 | live-blank-color |
| 加载贴图 | load-texture |
| 像素贴图 | pixel-texture |
| 道具格 | item-slot |
| 格子贴图 | slot-texture |
| 加载模型 | load-model |
| 替换材质 | material-override |
| 递归换材质 | apply-materials |
| 面材质 | surface-override |
| 霰弹枪 | shotgun |
| 枪模型 | gun-model |
| 霰弹 | shotgun-shell |
| 子弹模型 | shell-model |
| 道具模型 | item-model |
| 桌面道具 | table-item |
| 行刑人 | dealer |
| 庄家模型 | dealer-model |
| 每帧更新 | frame-update |
| 吊灯摆动 | lamp-swing |
| 环境设置 | world-environment |
| 柔光 | glow-bloom |
| 房间模型 | room-model |
| 补光 | fill-light |
| 赌桌模型 | table-model |
| 道具格 | item-slots |
| 吊灯 | pendant-lamp |
| 光锥 | light-cone |
| 灰尘粒子 | dust-particles |
| 浮尘 | floating-dust |
| 枪口火光 | muzzle-flash |
| 硝烟 | gun-smoke |
| 手臂IK | arm-ik |
| 肘部求解 | elbow-solve |
| 手臂段 | arm-segment |
| 两点摆放 | place-between |
| 握枪手势 | gun-grip-pose |
| 握持点 | grip-anchor |
| 切换手型 | toggle-fist |
| 握拳手 | hand-swap |
| 拿起枪 | grab-gun |
| 伸手 | reach |
| 放下枪 | release-gun |
| 松手 | let-go |
| 点击范围 | pick-shape |
| 道具拾取 | item-picking |
| 持枪姿势 | gun-pose |
| 瞄准姿势 | aim-pose |
| 枪托定位 | butt-placement |
| 持枪瞄准 | shouldered-aim |
| 移动枪 | move-gun |
| 握枪动画 | hold-animation |
| 开枪演出 | fire-effects |
| 后坐 | recoil |
| 倒计时更新 | countdown-tick |
| 超时 | turn-timeout |
| 超时开枪 | timeout-shot |
| 随机目标 | random-target |
| 开枪按钮 | aim-button |
| 选项排版 | option-layout |
| 开始游戏 | start-game |
| 对局音乐 | game-music |
| 游戏结束 | game-over |
| 结算界面 | result-screen |
| 装弹演出 | reload-sequence |
| 发放道具 | deal-items |
| 玩家回合 | player-turn |
| 回合计时 | turn-timer |
| 开枪流程 | shot-sequence |
| 紧张感 | suspense |
| 玩家中弹 | player-hit |
| 黑屏醒来 | blackout-wake |
| 记录框 | log-panel |
| 最新消息 | latest-message |
| 停止音乐 | stop-music |
| 退出清理 | exit-cleanup |
| 音乐总线 | music-bus |
| 低通滤波器 | lowpass-filter |
| 播放音乐 | play-music |
| 交叉淡入淡出 | crossfade |
| 音乐压低 | muffle-music |
| 低通滤波 | lowpass-duck |
| 截止频率 | cutoff-sweep |
| 对数插值 | log-interpolation |
| 倒计时滴答 | tick-sound |
| 钟表声 | clock-sound |
| 回合倒计时 | turn-countdown |
| 计时显示 | timer-display |
| 倒计时行 | countdown-row |
| 进度条 | progress-bar |
| 实弹概率 | live-probability |
| 反转器 | inverter-aware |
| 公开计数 | public-tally |
| 亮弹 | reveal-shell |
| 行刑人决策 | dealer-decision |
| 概率开枪 | odds-based-shot |
| 资源目录 | asset-dir |
| 模型目录 | model-dir |
| 材质规格 | material-spec |
| 材质键 | material-key |
| 触手着色器 | tentacle-shader |
| 顶点动画 | vertex-animation |
| 挂点 | lamp-pivot |
| 体积光 | fake-volumetric |
| 蜡烛灯光 | candle-lights |
| 墙缝绿光 | crack-glow |
| 手臂长度 | arm-length |
| 肘部方向 | elbow-pole |
| 枪托位置 | gun-butt |
| 握把位置 | grip-point |
| 背景音乐 | background-music |
| 曲目表 | track-list |
| 回合时限 | turn-seconds |
| 倒计时 | countdown |
| 自残阈值 | self-shot-threshold |
| 风险控制 | risk-control |

## 类型导出 (Type Exports)

- `Props`（class_name）— `MODEL_DIR` / `TEXTURE_DIR`（资源目录，keywords: asset-dir, model-dir, 资源目录, 模型目录）、`TENTACLE_SHADER`（keywords: tentacle-shader, vertex-animation, 触手着色器, 顶点动画）、`MATERIALS`（材质 key → [颜色, 粗糙度, 金属度, 贴图名, 自发光强度]，keywords: material-spec, material-key, 材质规格, 材质键）。
- `TableScene`（class_name）— 信号 `item_clicked(index)`、`gun_clicked`、`hover_changed(text)`；常量 `LAMP_POS` / `LAMP_PIVOT`（keywords: lamp-position, lamp-pivot, 吊灯位置, 挂点）、`LIGHT_CONE_SHADER`（keywords: light-cone-shader, fake-volumetric, 光锥着色器, 体积光）、`CANDLE_LIGHTS` / `CRACK_LIGHT_POS`（keywords: candle-lights, crack-glow, 蜡烛灯光, 墙缝绿光）、`UPPER_ARM` / `FOREARM` / `ELBOW_POLES`（keywords: arm-length, elbow-pole, 手臂长度, 肘部方向）、`BUTT` / `PISTOL_GRIP` / `PISTOL_GRIP_AXIS` / `BARREL_GRIP`（keywords: gun-butt, grip-point, 枪托位置, 握把位置）、`DEALER_GRIPS`（每个行刑人持枪姿势两只手握哪里）。
- `Sfx`（class_name）— 常量 `MUSIC`（曲目表：menu = Bleak Terminal，game = Omen；keywords: background-music, track-list, 背景音乐, 曲目表）、`MUSIC_DB`（各曲播放音量）、`MUSIC_BUS`（运行时创建的 Music 总线，带一个低通滤波器）。
- `DealerAI`（class_name）— 常量 `SELF_SHOT_MAX_P` / `SELF_SHOT_MAX_P_LAST_HP`（打自己的实弹概率上限，生命只剩 1 点时更低；keywords: self-shot-threshold, risk-control, 自残阈值, 风险控制）、`BEER_MIN_P` / `BEER_MAX_P`（最拿不准时先用啤酒退一发）。
- `GameState`（class_name）— 新增 `inverted`（被反转器翻过的子弹下标，公开信息）。
- `main.gd` 常量 `TURN_SECONDS`（玩家每回合思考时间 30 秒；keywords: turn-seconds, countdown, 回合时限, 倒计时）。
- `Items`、`CrtPanel`（class_name）。

## 模块功能描述 (Module Description)

- **材质替换**：`Props.model(path, overrides)` 实例化 `res://art/models/<path>.glb`，遍历所有网格面，按 glb 材质名取材质：`overrides` 优先（行刑人传入自己的 `skin` 受击变红、`pupil` 回合变色、`tentacle` 受击变红）；材质名 `tentacle` 用 `Props.tentacle_material()`（摆动着色器）；其余在 `MATERIALS` 里取（像素贴图 + 最近邻采样）。`slot`、`sigil`、`scrawl` 是半透明贴花。材质表里没有的名字会 `push_warning` 并保留 glb 原材质。
- **节点约定**：`table_scene.gd` 按名字取模型节点——枪的 `Pump`/`BarrelFront`/`Sight`，行刑人的 `Head`/`HandL`/`HandR`/`ArmL`/`ArmR`；枪口 `Muzzle` 是 `Props.shotgun()` 加的 `Marker3D`。这些名字和原点由 `art/blender/build_*.py` 保证。
- **皮肤顶点色**：`skin` 材质开启 `vertex_color_use_as_albedo`，行刑人头部的眼窝、额眼、口腔、缝线明暗来自 glb 顶点色；手、身体的顶点色是白色。
- **场景效果**：吊灯是绕天花板挂点的阻尼单摆，开枪时 `fire()` 给它一下冲量，主光源和光锥跟着摆，影子会晃；光锥用 `shaders/light_cone.gdshader` 加色混合；浮尘是只在灯柱里生成的加色粒子；枪口火光是朝镜头的星形贴片 + 两张十字交叉的火焰贴片，硝烟是世界空间的一次性粒子；环境开了柔光（glow）。房间里有左后角冷色补光、后墙裂缝里一明一暗的绿光（`CRACK_LIGHT_POS`）、两组蜡烛各一盏闪烁的暖光（`CANDLE_LIGHTS`，和 `build_room.py` 里蜡烛的位置对齐）。
- **行刑人握枪**：手臂是上臂 + 前臂两段，每帧用解析两段 IK（`_solve_arm`）从肩膀解到手腕，肘部朝 `ELBOW_POLES`（往下往外）弯。拿枪时（`gun_to` 进入 dealer_* 姿势）先 `_grab_gun`：张开的手伸到握把和护木上，换成握拳手 `GripL/R`；之后每帧按 `DEALER_GRIPS` 把握拳手贴在枪的握持点上（`_grip_transform`：杆的轴向对齐、手腕朝肩膀），所以枪移动、后坐、拉枪栓（左手跟着 Pump 节点）时手都跟着；换姿势时两只手在旧/新握持点之间用 `_grip_blend` 平滑过渡。画面左边那只手（行刑人的右手）握手枪握把，右边那只托护木，两臂不交叉。枪放回桌面后 `_release_gun` 松手收回。枪的姿势用 `_tucked(枪托位置, 瞄准点)` 定：端着时枪托夹在右胸前，瞄玩家时枪托顶在胸口正中，瞄自己时枪托搭在桌上、双手握前段把枪口拉到下巴底下。
- **背景音乐**：标题和结算放 Bleak Terminal（阴冷氛围），对局放 Omen（工业节拍），`play_music` 交叉淡入淡出、循环播放。枪口对准之后到扣扳机前，`muffle_music(true)` 把音乐的低通截止频率扫到 450Hz、音量降 5dB，像隔着水听；开枪/空响后放开。玩家中弹黑屏时一直闷着，醒来时慢慢恢复。音乐走单独的 Music 总线，音效不受影响。
- **回合倒计时**：玩家每回合 30 秒，只在等玩家操作（点道具、点枪、选开枪对象）时走，道具演出期间暂停；计分板最下面一行显示秒数和进度条，最后 10 秒变红闪烁、每秒滴答一声（最后 3 秒更响）。时间到 `_on_turn_timeout` 随机选自己或行刑人开一枪。装弹、行刑人的回合时这一行只显示文字。
- **行刑人 AI**：先保命（烟、药），再想办法看清当前这一发（放大镜、手机）；知道是空包弹就反转或打自己，知道是实弹就上手铐、锯枪管、打玩家。只能赌时：实弹概率在 0.3~0.7 之间且有啤酒就先退一发；概率小于 0.5 且有反转器就先反转；概率 ≥ 0.5 打玩家；只有概率 ≤ 0.34（自己只剩 1 点生命时 ≤ 0.15）才打自己，其余一律打玩家，不再掷硬币。概率由 `GameState.live_probability` 算，已经算上对手用过的反转器（公开计数按子弹被翻之前的样子记，当前这一发被翻过就取 1 - p）。
- **道具点击范围**：`_make_pickable` 用模型网格的包围盒（四周留 1 厘米）做点击盒，不再用统一的高盒子；否则近排的高盒子在屏幕上挡住远排道具的下半截，鼠标指着远排道具却选不中。
- **界面**：开枪选项是居中的 VBox（两个等宽大按钮并排 + 下面居中的"放下枪"），底边固定在字幕上方。右上角记录框不滚动：每来一条新记录就从最旧的删起，直到内容放得下，最新一条总是完整可见。
- **函数清单范围**：只收录带 `@keyword` 文档的函数（`props.gd` 全部、`table_scene.gd` 和 `main.gd` 中新增或改动过的）；其余脚本的函数尚未建索引，按 R9 回退到源码搜索。
