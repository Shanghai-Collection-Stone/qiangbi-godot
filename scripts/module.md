# scripts 模块

## 模块名称 (Module Name)

scripts · 游戏逻辑与 3D 场景

## 概述 (Overview)

游戏本体：规则（`game_state.gd`）、行刑人 AI、道具定义、流程与界面（`main.gd`）、3D 赌桌场景与演出（`table_scene.gd`）、模型与材质入口（`props.gd`）、计分板和合成音效。模型和贴图来自 `art` 模块（`res://art/models/`、`res://art/textures/`），由 `props.gd` 加载并换上像素材质。

## 文件清单 (File List)

- `game_state.gd` — 纯规则：子弹、生命、道具、回合、手铐，不依赖节点；公开计数和实弹概率会算上被反转器翻过的子弹。
- `dealer_ai.gd` — 行刑人 AI，只用公开信息决策；按实弹概率和自己的生命决定打谁，不会在五五开或低血量时赌自己。
- `items.gd` — 道具 id、名称、说明。
- `main.gd` — 游戏流程（async/await）、像素 HUD（开枪选项、记录框）、菜单、后期特效调度；局与局之间行刑人变身，受击时的顿帧、色差、屏幕溅血和低血量泛红。
- `table_scene.gd` — 3D 场景：房间（墙缝绿光、蜡烛灯）、吊灯（摆动、光锥、浮尘）、行刑人（三个形态、绕髋部前后仰的上身、受击喷血/后仰/触手抽搐/伤口、倒下与变身演出）、枪、子弹、道具的摆放、动画、枪口火光与硝烟、鼠标拾取、玩家中弹时镜头歪斜。
- `props.gd` — 材质表 `MATERIALS`、触手摆动材质、按材质名给 glb 换材质的 `model()`、霰弹枪/霰弹/道具/行刑人模型入口。
- `crt_panel.gd` — 左上角荧光屏计分板，最下面一行是回合倒计时。
- `sfx.gd` — 程序合成音效（含行刑人三个形态的嘶叫、变身的地鸣/碎裂/湿黏声、玩家中弹的耳鸣和心跳）；背景音乐（`art/music/` 的 CC0 曲目）的播放、交叉淡入淡出和低通压闷。
- `blood_overlay.gd` — 玩家中弹时糊在镜头上的像素血（`shaders/blood_overlay.gdshader`）：每次中弹现画遮罩，血斑多在画面四周，血痕往下淌，几秒后淡掉。

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
- `props.blood_splat_texture()` — 溅血贴图（白色，用材质颜色染色）：一团不规则的血斑、往外甩的尖刺和四周的小血点（程序生成，48×48） | keywords: blood-splat, splatter-texture, 溅血贴图, 血斑
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
- `table_scene._lean_transform()` — 躯干前后仰的变换：绕髋部支点 HIP_PIVOT 转 _lean | keywords: lean-transform, torso-pivot, 躯干变换, 后仰变换
- `table_scene._place_dealer_parts(lean)` — 跟着躯干前后仰的部件，胸口之眼一直盯着镜头；正在长出来（或缩回去）的形态部件按 _grow 缩放 | keywords: place-torso-parts, part-growth, 摆放躯干部件, 部件生长
- `table_scene._build_blood()` — 行刑人中弹喷出来的血滴和一团血雾（颜色按形态在喷之前设置） | keywords: blood-particles, blood-droplets, 血雾粒子, 血滴粒子
- `table_scene.set_dealer_form(form)` — 切换到某个形态：只显示这个形态的部件（立刻切换，不演出；演出见 transform_to） | keywords: set-form, show-parts, 切换形态, 显示部件
- `table_scene.reset_game()` — 新开一盘：回到第一形态，扶正身体、点亮灯，清掉桌上的碎片 | keywords: reset-game, reset-dealer, 新开一盘, 重置行刑人
- `table_scene.dealer_hit(damage)` — 行刑人中弹：头往后一甩、整个上身后仰再弹回来、皮肤和触手泛红、触手剧烈抽搐、瞳孔一亮、 | keywords: dealer-hit, hit-reaction, 行刑人受击, 受击反应
- `table_scene._spray_blood(at, heavy)` — 头上喷出血滴和血雾：颜色按形态，第三形态的体液发光（不受光照、亮度超过 1 会带柔光） | keywords: spray-blood, ichor-color, 喷血, 体液颜色
- `table_scene._splat_behind(heavy)` — 椅背上、行刑人身后溅一片血（留到这条命结束） | keywords: splat-behind, blood-decal, 椅背溅血, 血迹
- `table_scene._add_wound()` — 头上留一个伤口：第一形态打在面具上（瓷面上一个黑洞），之后打在皮肉上（暗色的血窟窿） | keywords: head-wound, damage-mark, 伤口, 受伤痕迹
- `table_scene._face_z(x, y)` — 头部基本形正面 (x, y) 处的 z（头部局部坐标）：和 art/blender/build_dealer.py 的 head_base 是同一个公式 | keywords: face-depth, head-base-shape, 脸面深度, 头部基本形
- `table_scene.player_hit(damage)` — 玩家中弹：镜头被打得往上一仰、歪向一边，然后晕乎乎地慢慢晃回来 | keywords: player-hit-camera, camera-knock, 玩家受击镜头, 镜头歪斜
- `table_scene.dealer_die()` — 这条命没了：触手一阵抽搐，上身往前栽、头垂下来、瞳孔熄灭 | keywords: dealer-die, life-lost, 行刑人倒下, 一条命结束
- `table_scene.transform_to(form)` — 换成下一个形态（下一条命）：吊灯闪几下灭掉，墙缝里的绿光涌出来；黑暗里旧形态的面具碎成片掉在桌上、 | keywords: transform-sequence, next-form, 变身演出, 下一形态
- `table_scene.dealer_final_death()` — 最后一条命也没了：倒下以后背后的触手、长触手须和胸口之眼枯萎缩回去，发光的血管熄灭，上身再往下栽 | keywords: final-death, wither, 最终死亡, 触手枯萎
- `table_scene._flicker_lamp(levels, step)` — 吊灯按 levels 依次跳到这些亮度，每一下停 step 秒（灯泡接触不良那种闪） | keywords: lamp-flicker, light-stutter, 吊灯闪烁, 灯光明灭
- `table_scene._drop_hat()` — 礼帽从头上飞走，翻着跟头落到椅子后面 | keywords: hat-flies-off, drop-hat, 礼帽飞走, 掉帽子
- `table_scene._shatter_mask(node_name, count)` — 面具碎成 count 片：从脸上迸开，翻滚着落到行刑人面前的桌上，一直留到这盘游戏结束 | keywords: mask-shards, shatter, 面具碎片, 碎裂
- `main._process(delta)` — 回合倒计时：只在等玩家操作（点道具、点枪、选开枪对象）时走，道具演出期间暂停 | keywords: countdown-tick, turn-timeout, 倒计时更新, 超时
- `main._on_turn_timeout()` — 时间到：枪替玩家随机选一个对象开火 | keywords: timeout-shot, random-target, 超时开枪, 随机目标
- `main._aim_button(parent, text, font_size, min_size, callback)` — 开枪选项按钮：放进容器里由容器排版，min_size 统一宽度 | keywords: aim-button, option-layout, 开枪按钮, 选项排版
- `main._start_game()` — 开始一局：换成对局音乐，开始流程 | keywords: start-game, game-music, 开始游戏, 对局音乐
- `main._game_over(win)` — 一局结束：结算界面，音乐恢复并换回标题曲 | keywords: game-over, result-screen, 游戏结束, 结算界面
- `main._do_load()` — 装弹演出：公布实弹/空包弹数、子弹立桌上再装进枪，然后两边各自摆上新发的道具 | keywords: reload-sequence, deal-items, 装弹演出, 发放道具
- `main._player_turn()` — 玩家回合：每回合 TURN_SECONDS 秒（只在等玩家操作时走），用道具不换回合，开一枪结束回合 | keywords: player-turn, turn-timer, 玩家回合, 回合计时
- `main._present_shot(res)` — 开枪演出：举枪、瞄准（音乐压闷）、开枪或空响（音乐放开）、拉枪栓、放下枪 | keywords: shot-sequence, suspense, 开枪流程, 紧张感
- `main._player_hit_fx(damage)` — 玩家中弹：顿帧、白光，镜头被打得一仰一歪，血糊上镜头，耳鸣；黑屏片刻里只听得见心跳（音乐一直闷着）， | keywords: player-hit, blackout-wake, 玩家中弹, 黑屏醒来
- `main._log(text)` — 记录框不滚动：从最旧的一条开始删，直到全部内容放得下，最新的一条总是完整可见 | keywords: log-panel, latest-message, 记录框, 最新消息
- `sfx._exit_tree()` — 退出时停掉音乐、放掉曲子，否则正在播放的 OGG 会在退出时报资源未释放 | keywords: stop-music, exit-cleanup, 停止音乐, 退出清理
- `sfx._build_music_bus()` — Music 总线（带低通滤波器）和音乐播放器 | keywords: music-bus, lowpass-filter, 音乐总线, 低通滤波器
- `sfx.play_music(track, fade)` — 换背景音乐：旧的淡出、新的从头淡入，循环播放；已经在放同一首就不动 | keywords: play-music, crossfade, 播放音乐, 交叉淡入淡出
- `sfx.muffle_music(on, duration)` — 把音乐压低成闷声（低通 + 降音量），用在扣扳机前那一下的紧张感；on 为 false 时恢复 | keywords: muffle-music, lowpass-duck, 音乐压低, 低通滤波
- `sfx._set_cutoff(t, from_hz, to_hz)` — 低通截止频率按对数插值，听起来扫得均匀 | keywords: cutoff-sweep, log-interpolation, 截止频率, 对数插值
- `sfx._tick()` — 倒计时最后 10 秒的滴答：很短的高频咔嗒 + 一点木头共鸣 | keywords: tick-sound, clock-sound, 倒计时滴答, 钟表声
- `sfx._splat()` — 打进肉里的闷响：低频一撞加一团湿漉漉的噪声 | keywords: flesh-impact, splat-sound, 血肉闷响, 中弹声
- `sfx._creature(seconds, f_from, f_to, rough, lp)` — 怪物的嘶叫：锯齿波从 f_from 滑到 f_to，带颤音、粗糙的随机抖动（rough）和气声， | keywords: creature-shriek, roar, 怪物嘶叫, 咆哮
- `sfx._rumble()` — 变身前的地鸣：很低的隆隆声慢慢涌上来再退下去 | keywords: rumble, low-drone, 地鸣, 低频隆隆
- `sfx._shatter()` — 白瓷碎裂：几下错开的清脆噪声和高频的叮当 | keywords: porcelain-shatter, break-sound, 瓷器碎裂, 碎片声
- `sfx._squelch()` — 触手长出来的湿黏声：被低频随机起伏调制的闷噪声 | keywords: squelch, tentacle-grow, 湿黏声, 触手生长
- `sfx._ring()` — 中弹后的耳鸣：一声细细的高频，两个频率差一点点所以有轻微的拍音，慢慢消失 | keywords: tinnitus, ear-ring, 耳鸣, 高频鸣响
- `sfx._heartbeat()` — 心跳：咚——咚两下 | keywords: heartbeat, pulse, 心跳, 心跳声
- `crt_panel.set_turn(text, seconds_left, total)` — 更新倒计时行；seconds_left 小于 0 表示这一行只显示文字（比如行刑人的回合） | keywords: turn-countdown, timer-display, 回合倒计时, 计时显示
- `crt_panel._turn_row(font, y)` — 倒计时行：左边是谁的回合，右边是剩余秒数，下面一条随时间缩短的进度条；最后 10 秒变红闪烁 | keywords: countdown-row, progress-bar, 倒计时行, 进度条
- `game_state.live_probability(actor)` — 站在 actor 的角度，当前这一发是实弹的概率。先按公开计数（装弹时的原样）和自己知道的子弹算， | keywords: live-probability, inverter-aware, 实弹概率, 反转器
- `game_state._reveal(live, index)` — 一发子弹被亮出来（开枪或退膛），更新公开计数。被反转过的子弹亮出来的是翻过之后的样子， | keywords: public-tally, reveal-shell, 公开计数, 亮弹
- `dealer_ai.decide(state, me, _rng)` — 决定下一个动作。只用公开信息（公布的数量、亮出来的子弹、谁用过反转器）和自己看到的子弹 | keywords: dealer-decision, odds-based-shot, 行刑人决策, 概率开枪
- `blood_overlay.splash(damage)` — 溅一脸血：damage 越大血斑越多越大；血痕 2.6 秒淌完，2 秒后开始淡出 | keywords: splash-blood, hit-splash, 溅血, 中弹溅血
- `blood_overlay.clear()` — 立刻擦干净（新开一盘时） | keywords: clear-blood, wipe, 擦掉血, 清屏
- `blood_overlay._paint(damage)` — 画遮罩：R = 血斑，G = 血痕流到这里的时刻（0..1），B = 明暗 | keywords: paint-mask, drip-lines, 画血斑, 血痕
- `blood_overlay._edge_point()` — 画面四周随机一点：上下各 30 像素、左右各 50 像素的边带 | keywords: edge-point, border-band, 边缘取点, 四周
- `blood_overlay._blob(img, center, r)` — 一团边缘起伏的血斑，左上一侧亮一点像湿的高光 | keywords: blood-blob, wet-highlight, 屏幕血斑, 湿润高光
- `blood_overlay._drip(img, start, length)` — 一道往下淌的血痕：每个像素记下血流到这里的时刻 | keywords: drip-line, arrival-time, 血痕下淌, 流淌时刻

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
| 躯干变换 | lean-transform |
| 后仰变换 | torso-pivot |
| 摆放躯干部件 | place-torso-parts |
| 部件生长 | part-growth |
| 血雾粒子 | blood-particles |
| 血滴粒子 | blood-droplets |
| 切换形态 | set-form |
| 显示部件 | show-parts |
| 新开一盘 | reset-game |
| 重置行刑人 | reset-dealer |
| 行刑人受击 | dealer-hit |
| 受击反应 | hit-reaction |
| 喷血 | spray-blood |
| 体液颜色 | ichor-color |
| 椅背溅血 | splat-behind |
| 血迹 | blood-decal |
| 伤口 | head-wound |
| 受伤痕迹 | damage-mark |
| 脸面深度 | face-depth |
| 头部基本形 | head-base-shape |
| 玩家受击镜头 | player-hit-camera |
| 镜头歪斜 | camera-knock |
| 行刑人倒下 | dealer-die |
| 一条命结束 | life-lost |
| 变身演出 | transform-sequence |
| 下一形态 | next-form |
| 最终死亡 | final-death |
| 触手枯萎 | wither |
| 吊灯闪烁 | lamp-flicker |
| 灯光明灭 | light-stutter |
| 礼帽飞走 | hat-flies-off |
| 掉帽子 | drop-hat |
| 面具碎片 | mask-shards |
| 碎裂 | shatter |
| 行刑人变身 | dealer-transform |
| 换形态 | next-life |
| 行刑人中弹 | dealer-hit-fx |
| 受击演出 | impact-feedback |
| 顿帧 | hit-stop |
| 打击停顿 | impact-freeze |
| 色差抖动 | aberration-kick |
| 冲击感 | impact-distortion |
| 血肉闷响 | flesh-impact |
| 中弹声 | splat-sound |
| 怪物嘶叫 | creature-shriek |
| 咆哮 | roar |
| 地鸣 | rumble |
| 低频隆隆 | low-drone |
| 瓷器碎裂 | porcelain-shatter |
| 碎片声 | break-sound |
| 湿黏声 | squelch |
| 触手生长 | tentacle-grow |
| 耳鸣 | tinnitus |
| 高频鸣响 | ear-ring |
| 心跳 | heartbeat |
| 心跳声 | pulse |
| 溅血贴图 | blood-splat |
| 血斑 | splatter-texture |
| 溅血 | splash-blood |
| 中弹溅血 | hit-splash |
| 擦掉血 | clear-blood |
| 清屏 | wipe |
| 画血斑 | paint-mask |
| 血痕 | drip-lines |
| 边缘取点 | edge-point |
| 四周 | border-band |
| 屏幕血斑 | blood-blob |
| 湿润高光 | wet-highlight |
| 血痕下淌 | drip-line |
| 流淌时刻 | arrival-time |

## 类型导出 (Type Exports)

- `Props`（class_name）— `MODEL_DIR` / `TEXTURE_DIR`（资源目录，keywords: asset-dir, model-dir, 资源目录, 模型目录）、`TENTACLE_SHADER`（keywords: tentacle-shader, vertex-animation, 触手着色器, 顶点动画）、`MATERIALS`（材质 key → [颜色, 粗糙度, 金属度, 贴图名, 自发光强度]，keywords: material-spec, material-key, 材质规格, 材质键）。
- `TableScene`（class_name）— 信号 `item_clicked(index)`、`gun_clicked`、`hover_changed(text)`；常量 `LAMP_POS` / `LAMP_PIVOT`（keywords: lamp-position, lamp-pivot, 吊灯位置, 挂点）、`LIGHT_CONE_SHADER`（keywords: light-cone-shader, fake-volumetric, 光锥着色器, 体积光）、`CANDLE_LIGHTS` / `CRACK_LIGHT_POS`（keywords: candle-lights, crack-glow, 蜡烛灯光, 墙缝绿光）、`UPPER_ARM` / `FOREARM` / `ELBOW_POLES`（keywords: arm-length, elbow-pole, 手臂长度, 肘部方向）、`BUTT` / `PISTOL_GRIP` / `PISTOL_GRIP_AXIS` / `BARREL_GRIP`（keywords: gun-butt, grip-point, 枪托位置, 握把位置）、`DEALER_GRIPS`（每个行刑人持枪姿势两只手握哪里）、`FORM_NODES`（每个形态显示哪些形态部件，和 `build_dealer.py` 一致；keywords: dealer-forms, form-parts, 行刑人形态, 形态部件）、`FORM_STYLE`（每个形态的名字、瞳孔颜色、血色和发光；keywords: form-style, blood-color, 形态样式, 血色）、`TORSO_NODES` / `HEAD_FORM_NODES`（跟着躯干后仰的节点、挂在头上随形态长出的节点）、`HIP_PIVOT`（躯干前后仰的支点；keywords: hip-pivot, torso-lean, 躯干支点, 后仰）；属性 `dealer_form`（当前形态）。
- `Sfx`（class_name）— 常量 `MUSIC`（曲目表：menu = Bleak Terminal，game = Omen；keywords: background-music, track-list, 背景音乐, 曲目表）、`MUSIC_DB`（各曲播放音量）、`MUSIC_BUS`（运行时创建的 Music 总线，带一个低通滤波器）。
- `DealerAI`（class_name）— 常量 `SELF_SHOT_MAX_P` / `SELF_SHOT_MAX_P_LAST_HP`（打自己的实弹概率上限，生命只剩 1 点时更低；keywords: self-shot-threshold, risk-control, 自残阈值, 风险控制）、`BEER_MIN_P` / `BEER_MAX_P`（最拿不准时先用啤酒退一发）。
- `GameState`（class_name）— 新增 `inverted`（被反转器翻过的子弹下标，公开信息）。
- `main.gd` 常量 `TURN_SECONDS`（玩家每回合思考时间 30 秒；keywords: turn-seconds, countdown, 回合时限, 倒计时）。
- `main._transform_dealer(form)` — 行刑人这条命没了，换成下一个形态：音乐压闷，灯灭、变身，灯亮时按新形态的颜色闪一下，再加一声嘶吼 | keywords: dealer-transform, next-life, 行刑人变身, 换形态
- `main._dealer_hit_fx(damage)` — 行刑人中弹：顿帧、闪白、色差猛地一抖；场景里喷血、后仰、触手抽搐，加上血肉闷响和这个形态的嘶叫 | keywords: dealer-hit-fx, impact-feedback, 行刑人中弹, 受击演出
- `main._hit_stop(seconds)` — 顿帧：中弹那一下整个世界放慢到 5%，按真实时间过 seconds 秒后恢复（恢复成原来的倍率，测试里的加速不受影响） | keywords: hit-stop, impact-freeze, 顿帧, 打击停顿
- `main._aberration_kick(strength)` — 色差猛地一抖再回到平时的 0.9 | keywords: aberration-kick, impact-distortion, 色差抖动, 冲击感
- `BloodOverlay`（class_name，`TextureRect`）— 常量 `SIZE`（遮罩分辨率 320×180；keywords: blood-mask, mask-size, 溅血遮罩, 遮罩尺寸）、`SHADER`；方法 `splash(damage)`、`clear()`。
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
- **行刑人的三条命**：每一局是行刑人的一条命，一条命一个形态（`TableScene.FORM_NODES` / `FORM_STYLE`）：第一局「白面」——白瓷面具（画着黑眼线、泪痕、腮红和缝着线的笑）、高礼帽、怀表链；第二局「裂面」——面具碎得只剩半张，露出咧嘴尖牙，下巴的触手须垂下来，背后长出两根大触手，额头三只小眼睁开；第三局「深渊」——头顶骨刺和两根大骨角、脸上发光的绿血管、更长的触手须、背后六根像光环一样张开的触手、西装胸口裂开一道带牙的肉缝，里面一只发光的眼睛一直盯着玩家转（`_place_dealer_parts` 每帧让 `ChestEye` 朝向镜头）。形态部件是 `dealer.glb` 里的独立节点，`set_dealer_form` 只切显示；`_grow` 记录每个部件长出来的程度（变身时从 0 补间到 1）。
- **倒下与变身**：行刑人一条命没了（`main._announce_death` → `dealer_die`）：触手一阵抽搐，上身绕髋部 `HIP_PIVOT` 往前栽、头垂下来、瞳孔熄灭。下一局开始前 `main._transform_dealer` → `transform_to(form)`：音乐压闷、吊灯闪几下灭掉、墙缝绿光涌出来；黑暗里面具碎成片（`_shatter_mask`，碎片落在桌上一直留到这盘结束）、礼帽飞走（`_drop_hat`），新部件一边抽搐一边从 0 长出来；然后灯亮、行刑人直起身红着眼睛嘶吼，画面按新形态的颜色闪一下。最后一局赢了以后 `dealer_final_death`：背后触手、长触手须、胸口之眼枯萎缩回去，血管熄灭。新开一盘 `reset_game` 回到第一形态。
- **上身前后仰**：头、肩膀（IK 的起点 `_shoulders`）、`Body`、背后触手、胸口之眼都按 `_lean_transform()` 绕髋部转；手留在桌上，手臂 IK 自然跟着弯。受击时 `_lean` 先往后甩再弹性回正，倒下时往前栽。
- **行刑人受击**（`main._dealer_hit_fx` + `table_scene.dealer_hit`）：顿帧（`_hit_stop` 把 `Engine.time_scale` 临时乘 0.05，按真实时间恢复，不覆盖测试的加速倍率）、淡淡的闪白、色差猛抖；头往后一甩、上身后仰、镜头视野一缩；皮肤和触手泛红、触手着色器 `thrash` 剧烈乱甩、瞳孔一亮、两只手在桌上一抽；头上喷出血滴和血雾（`FORM_STYLE` 的血色：白面暗红、裂面黑红、深渊发光的绿色体液），椅背和他面前的桌上溅血，头上留下伤口（白面时是面具上的黑洞，`_face_z` 按 `head_base` 同一公式算位置），这些都留到这条命结束；配上血肉闷响和这个形态的嘶叫（`shriek1..3`，一个比一个低沉）。锯短枪管的 2 点伤害反应更重。
- **玩家受击**（`main._player_hit_fx`）：顿帧、白光、色差，`table_scene.player_hit` 让镜头往上一仰、歪向一边再慢慢晃回来，`BloodOverlay.splash` 把像素血糊在屏幕四周、血痕往下淌，耳鸣；黑屏那一下只听得见心跳。生命只剩最后一点时（且上限大于 1），`post.gdshader` 的 `hurt` 让画面四周随心跳泛红、颜色变淡。
- **函数清单范围**：只收录带 `@keyword` 文档的函数（`props.gd`、`blood_overlay.gd` 全部，`table_scene.gd`、`main.gd`、`sfx.gd` 中新增或改动过的）；其余脚本的函数尚未建索引，按 R9 回退到源码搜索。
