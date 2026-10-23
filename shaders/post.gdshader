// 后期处理：色差、分离色调、颗粒、暗角、扫描线、闪光/黑屏，最后做有序抖动 + 色阶量化。
// 挂在显示 3D 画面的 SubViewportContainer 上。
shader_type canvas_item;

uniform float levels = 14.0;
uniform float dither_strength = 1.0;
uniform float grain = 0.07;
uniform float vignette = 0.75;
uniform float scanline = 0.06;
uniform float aberration = 0.9;
uniform vec3 tint = vec3(1.0, 0.96, 0.88);
// 分离色调：暗部偏青绿，亮部保持吊灯的暖色
uniform vec3 shadow_tint = vec3(0.8, 1.0, 1.05);
uniform float shadow_tint_amount = 0.6;
uniform vec4 flash_color : source_color = vec4(1.0, 1.0, 1.0, 0.0);
uniform float fade = 0.0;

const float BAYER[16] = float[16](
	0.0, 8.0, 2.0, 10.0,
	12.0, 4.0, 14.0, 6.0,
	3.0, 11.0, 1.0, 9.0,
	15.0, 7.0, 13.0, 5.0);

// 屏幕像素坐标的伪随机数（颗粒用）
// @keyword-cn 伪随机, 颗粒噪声
// @keyword-en screen-hash, grain-noise
float hash(vec2 p) {
	return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

// 每个像素：色差 → 色调 → 颗粒 → 暗角 → 扫描线 → 闪光/黑屏 → Bayer 抖动 + 色阶量化
// @keyword-cn 后期处理, 像素抖动
// @keyword-en post-process, bayer-dither
void fragment() {
	vec2 size = vec2(textureSize(TEXTURE, 0));
	vec2 px = floor(UV * size);
	vec2 from_center = UV - 0.5;
	vec2 offset = from_center * aberration * 2.0 / size;
	vec3 col = vec3(
		texture(TEXTURE, UV + offset).r,
		texture(TEXTURE, UV).g,
		texture(TEXTURE, UV - offset).b);

	col *= tint;
	float lum = dot(col, vec3(0.299, 0.587, 0.114));
	col *= mix(vec3(1.0), shadow_tint, shadow_tint_amount * (1.0 - smoothstep(0.0, 0.45, lum)));
	col += (hash(px + floor(TIME * 24.0) * 17.0) - 0.5) * grain;
	col *= clamp(1.0 - dot(from_center, from_center) * vignette * 2.0, 0.0, 1.0);
	col *= 1.0 - scanline * mod(px.y, 2.0);
	col = mix(col, flash_color.rgb, flash_color.a);
	col *= 1.0 - fade;

	int i = int(mod(px.x, 4.0)) + int(mod(px.y, 4.0)) * 4;
	float threshold = mix(0.5, (BAYER[i] + 0.5) / 16.0, dither_strength);
	col = floor(clamp(col, 0.0, 1.0) * (levels - 1.0) + threshold) / (levels - 1.0);
	COLOR = vec4(col, 1.0);
}
