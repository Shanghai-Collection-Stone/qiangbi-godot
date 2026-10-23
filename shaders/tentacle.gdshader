// 触手：顶点沿长度做缓慢的正弦摆动，根部不动、越往尖端摆得越厉害。
// 网格约定（art/blender/kit.py 的 tentacle()）：UV.x 绕一圈 0..1，UV.y 从根 0 到尖 1；
// 顶点色 R = 摆动相位，G = 尖端摆幅（米 × 10），B = 触手长度（米 ÷ 2）。
shader_type spatial;

uniform sampler2D albedo_tex : source_color, filter_nearest_mipmap, repeat_enable;
// 行刑人中弹时由脚本改成红色
uniform vec4 tint : source_color = vec4(1.0);
// 受击抽搐：0 = 平静，1 = 剧烈地快速乱甩（脚本补间回 0）
uniform float thrash = 0.0;
uniform float speed = 1.1;
// 沿长度方向每隔多少米重复一次吸盘贴图
uniform float tile_length = 0.12;

// 摆动：两个方向上频率不同的正弦叠加，按 UV.y² 加权，根部固定
// @keyword-cn 触手摆动, 顶点动画
// @keyword-en tentacle-sway, vertex-animation
void vertex() {
	float w = UV.y * UV.y;
	float phase = COLOR.r * 6.2832;
	float amp = COLOR.g * 0.1;
	vec3 sway = vec3(
		sin(TIME * speed + phase + UV.y * 5.0),
		0.35 * sin(TIME * speed * 0.7 + phase * 1.7 + UV.y * 3.0),
		cos(TIME * speed * 0.8 + phase + UV.y * 4.0));
	// 抽搐是叠加上去的高频乱甩，不去改主摆动的频率（改频率会让相位跳变）
	vec3 jerk = vec3(
		sin(TIME * 17.0 + phase * 3.0 + UV.y * 11.0),
		sin(TIME * 13.0 + phase * 2.0 + UV.y * 7.0),
		cos(TIME * 19.0 + phase + UV.y * 9.0));
	VERTEX += (sway * amp * (1.0 + thrash * 2.0) + jerk * thrash * (0.02 + amp * 0.6)) * w;
}

// 吸盘贴图按真实长度平铺，湿滑的高光
// @keyword-cn 触手着色, 吸盘贴图
// @keyword-en tentacle-shading, sucker-texture
void fragment() {
	vec2 uv = vec2(UV.x, UV.y * COLOR.b * 2.0 / tile_length);
	ALBEDO = texture(albedo_tex, uv).rgb * tint.rgb;
	ROUGHNESS = 0.3;
	SPECULAR = 0.7;
}
