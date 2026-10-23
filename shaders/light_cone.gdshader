// 吊灯下的光锥：加色混合的半透明圆锥，正对视线处最亮、轮廓和底部渐隐，假装有体积光。
// GL Compatibility 没有体积雾，用它代替。挂在 table_scene.gd 的吊灯下面。
shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, shadows_disabled;

uniform vec3 color : source_color = vec3(1.0, 0.78, 0.5);
uniform float strength = 0.14;
// 跟着吊灯闪烁，由脚本每帧写入
uniform float flicker = 1.0;

// 视线正对处最亮、上浓下淡，乘上吊灯闪烁
// @keyword-cn 光锥着色, 体积光
// @keyword-en light-cone-shading, fake-volumetric
void fragment() {
	float facing = abs(dot(normalize(NORMAL), normalize(VIEW)));
	// CylinderMesh 的 UV.y 从顶端 0 到底端 1：顶端浓、往下淡
	float fall = smoothstep(1.0, 0.1, UV.y) * smoothstep(0.0, 0.08, UV.y);
	ALBEDO = color * strength * facing * facing * fall * flicker;
}
