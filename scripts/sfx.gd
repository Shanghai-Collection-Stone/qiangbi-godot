class_name Sfx
extends Node
## 音效是程序合成的；背景音乐来自 art/music/（OpenGameArt 上的 CC0 曲目）。
## 音乐走单独的 Music 总线，总线上挂一个低通滤波器，紧张的时候把音乐压得像隔着水听。

const RATE := 22050
## 背景音乐：标题/结算用阴冷的氛围曲，对局中用工业节拍
## @keyword-cn 背景音乐, 曲目表
## @keyword-en background-music, track-list
const MUSIC := {
	"menu": preload("res://art/music/bleak_terminal.ogg"),
	"game": preload("res://art/music/omen.ogg"),
}
## 两首曲子的响度不一样（omen 很响），各自的播放音量让它们听起来差不多大，并且压在音效下面
const MUSIC_DB := {"menu": -8.0, "game": -15.0}
const MUSIC_BUS := "Music"
const OPEN_HZ := 20000.0
const MUFFLED_HZ := 450.0
const SILENT_DB := -40.0

var _rng := RandomNumberGenerator.new()
var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _music_player: AudioStreamPlayer
var _music := ""
var _music_tween: Tween
var _lowpass: AudioEffectLowPassFilter
## 压低时额外降低的音量
var _duck_db := 0.0


func _ready() -> void:
	_rng.seed = 1337
	_streams["bang"] = _to_stream(_bang())
	_streams["click"] = _to_stream(_click())
	_streams["rack"] = _to_stream(_rack())
	_streams["insert"] = _to_stream(_insert())
	_streams["item"] = _to_stream(_item())
	_streams["heal"] = _to_stream(_heal())
	_streams["deny"] = _to_stream(_deny())
	_streams["saw"] = _to_stream(_saw())
	_streams["cuff"] = _to_stream(_cuff())
	_streams["win"] = _to_stream(_win())
	_streams["lose"] = _to_stream(_lose())
	_streams["thud"] = _to_stream(_thud())
	_streams["tick"] = _to_stream(_tick())
	_build_music_bus()
	for i in 6:
		var p := AudioStreamPlayer.new()
		add_child(p)
		_players.append(p)


func play(sound: String, volume_db := 0.0) -> void:
	var player := _players[0]
	for p in _players:
		if not p.playing:
			player = p
			break
	player.stream = _streams[sound]
	player.volume_db = volume_db
	player.play()


## 退出时停掉音乐、放掉曲子，否则正在播放的 OGG 会在退出时报资源未释放
## @keyword-cn 停止音乐, 退出清理
## @keyword-en stop-music, exit-cleanup
func _exit_tree() -> void:
	_music_player.stop()
	_music_player.stream = null


## Music 总线（带低通滤波器）和音乐播放器
## @keyword-cn 音乐总线, 低通滤波器
## @keyword-en music-bus, lowpass-filter
func _build_music_bus() -> void:
	var bus := AudioServer.get_bus_index(MUSIC_BUS)
	if bus == -1:
		bus = AudioServer.bus_count
		AudioServer.add_bus(bus)
		AudioServer.set_bus_name(bus, MUSIC_BUS)
		AudioServer.set_bus_send(bus, "Master")
		AudioServer.add_bus_effect(bus, AudioEffectLowPassFilter.new())
	_lowpass = AudioServer.get_bus_effect(bus, 0)
	_lowpass.cutoff_hz = OPEN_HZ
	for track in MUSIC.values():
		(track as AudioStreamOggVorbis).loop = true
	_music_player = AudioStreamPlayer.new()
	_music_player.bus = MUSIC_BUS
	_music_player.volume_db = SILENT_DB
	add_child(_music_player)


## 换背景音乐：旧的淡出、新的从头淡入，循环播放；已经在放同一首就不动
## @keyword-cn 播放音乐, 交叉淡入淡出
## @keyword-en play-music, crossfade
func play_music(track: String, fade := 1.2) -> void:
	if track == _music:
		return
	_music = track
	if _music_tween:
		_music_tween.kill()
	_music_tween = create_tween()
	if _music_player.playing:
		_music_tween.tween_property(_music_player, "volume_db", SILENT_DB, fade * 0.5)
	_music_tween.tween_callback(func() -> void:
		_music_player.stream = MUSIC[track]
		_music_player.play())
	_music_tween.tween_property(_music_player, "volume_db", MUSIC_DB[track] + _duck_db, fade)


## 把音乐压低成闷声（低通 + 降音量），用在扣扳机前那一下的紧张感；on 为 false 时恢复
## @keyword-cn 音乐压低, 低通滤波
## @keyword-en muffle-music, lowpass-duck
func muffle_music(on: bool, duration := 0.5) -> void:
	_duck_db = -5.0 if on else 0.0
	var to_hz := MUFFLED_HZ if on else OPEN_HZ
	var tw := create_tween().set_parallel()
	tw.tween_method(_set_cutoff.bind(_lowpass.cutoff_hz, to_hz), 0.0, 1.0, duration)
	if _music != "" and (not _music_tween or not _music_tween.is_running()):
		tw.tween_property(_music_player, "volume_db", MUSIC_DB[_music] + _duck_db, duration)


## 低通截止频率按对数插值，听起来扫得均匀
## @keyword-cn 截止频率, 对数插值
## @keyword-en cutoff-sweep, log-interpolation
func _set_cutoff(t: float, from_hz: float, to_hz: float) -> void:
	_lowpass.cutoff_hz = exp(lerpf(log(from_hz), log(to_hz), t))


func _to_stream(samples: PackedFloat32Array) -> AudioStreamWAV:
	var peak := 0.0001
	for v in samples:
		peak = maxf(peak, absf(v))
	var data := PackedByteArray()
	data.resize(samples.size() * 2)
	for i in samples.size():
		data.encode_s16(i * 2, int(samples[i] / peak * 0.9 * 32767.0))
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = RATE
	stream.stereo = false
	stream.data = data
	return stream


func _buffer(seconds: float) -> PackedFloat32Array:
	var out := PackedFloat32Array()
	out.resize(int(seconds * RATE))
	return out


func _noise() -> float:
	return _rng.randf_range(-1.0, 1.0)


## 金属撞击声：一小段噪声加一个快速衰减的音调
func _clack(t: float, freq: float) -> float:
	if t < 0.0:
		return 0.0
	return _noise() * exp(-t * 260.0) * 0.7 + sin(TAU * freq * t) * exp(-t * 60.0) * 0.35


func _bang() -> PackedFloat32Array:
	var out := _buffer(1.0)
	var lp := 0.0
	for i in out.size():
		var t := float(i) / RATE
		var n := _noise()
		lp += lerpf(0.9, 0.03, minf(t * 4.0, 1.0)) * (n - lp)
		var thump := sin(TAU * (70.0 - 30.0 * t) * t) * exp(-t * 8.0)
		out[i] = 0.9 * lp * exp(-t * 4.5) + 0.8 * thump + 0.6 * n * exp(-t * 120.0)
	return out


func _click() -> PackedFloat32Array:
	var out := _buffer(0.15)
	for i in out.size():
		var t := float(i) / RATE
		out[i] = _clack(t, 2400.0) + sin(TAU * 900.0 * t) * exp(-t * 50.0) * 0.2
	return out


func _rack() -> PackedFloat32Array:
	var out := _buffer(0.35)
	var lp := 0.0
	for i in out.size():
		var t := float(i) / RATE
		var n := _noise()
		lp += 0.2 * (n - lp)
		var slide := (n - lp) * 0.12 if t > 0.03 and t < 0.15 else 0.0
		out[i] = _clack(t, 1300.0) + _clack(t - 0.17, 1000.0) + slide
	return out


func _insert() -> PackedFloat32Array:
	var out := _buffer(0.09)
	for i in out.size():
		out[i] = _clack(float(i) / RATE, 1800.0)
	return out


func _item() -> PackedFloat32Array:
	var out := _buffer(0.2)
	for i in out.size():
		var t := float(i) / RATE
		var f := 520.0 if t < 0.07 else 780.0
		out[i] = sin(TAU * f * t) * exp(-t * 14.0)
	return out


func _heal() -> PackedFloat32Array:
	var out := _buffer(0.4)
	for i in out.size():
		var t := float(i) / RATE
		out[i] = sin(TAU * (400.0 + 600.0 * t) * t) * sin(PI * t / 0.4)
	return out


func _deny() -> PackedFloat32Array:
	var out := _buffer(0.2)
	for i in out.size():
		var t := float(i) / RATE
		out[i] = signf(sin(TAU * 140.0 * t)) * 0.5 * exp(-t * 8.0)
	return out


func _saw() -> PackedFloat32Array:
	var out := _buffer(0.6)
	var lp := 0.0
	for i in out.size():
		var t := float(i) / RATE
		var n := _noise()
		lp += 0.3 * (n - lp)
		out[i] = (n - lp) * maxf(0.0, sin(TAU * 5.0 * t))
	return out


func _cuff() -> PackedFloat32Array:
	var out := _buffer(0.45)
	for i in out.size():
		var t := float(i) / RATE
		var ring := sin(TAU * 1800.0 * t) + 0.6 * sin(TAU * 2710.0 * t) + 0.4 * sin(TAU * 3930.0 * t)
		out[i] = ring * exp(-t * 14.0) * 0.4 + _clack(t, 2200.0)
	return out


func _win() -> PackedFloat32Array:
	var out := _buffer(0.9)
	var notes := [330.0, 415.3, 493.9]
	for i in out.size():
		var t := float(i) / RATE
		var k := mini(int(t / 0.22), notes.size() - 1)
		var lt := t - k * 0.22
		out[i] = sin(TAU * notes[k] * t) * exp(-lt * 5.0)
	return out


func _lose() -> PackedFloat32Array:
	var out := _buffer(1.6)
	for i in out.size():
		var t := float(i) / RATE
		out[i] = (sin(TAU * 55.0 * t) + sin(TAU * 58.0 * t) + 0.3 * sin(TAU * 110.0 * t)) * sin(PI * t / 1.6)
	return out


func _thud() -> PackedFloat32Array:
	var out := _buffer(0.18)
	for i in out.size():
		var t := float(i) / RATE
		out[i] = sin(TAU * (140.0 - 200.0 * t) * t) * exp(-t * 30.0) + _noise() * exp(-t * 200.0) * 0.4
	return out


## 倒计时最后 10 秒的滴答：很短的高频咔嗒 + 一点木头共鸣
## @keyword-cn 倒计时滴答, 钟表声
## @keyword-en tick-sound, clock-sound
func _tick() -> PackedFloat32Array:
	var out := _buffer(0.08)
	for i in out.size():
		var t := float(i) / RATE
		out[i] = _clack(t, 3200.0) * 0.6 + sin(TAU * 1100.0 * t) * exp(-t * 90.0) * 0.5
	return out
