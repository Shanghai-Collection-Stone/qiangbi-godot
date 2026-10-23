// 玩家中弹时糊在镜头上的血：一张 320×180 的遮罩贴图（最近邻放大，和画面的像素一样大）。
// R = 血斑，G = 往下流的血痕「流到这里的时刻」（0 = 没有，越大越晚流到），B = 明暗变化。
// 脚本把 drip 从 0 补间到 1 让血慢慢往下淌，再把 amount 补间到 0 让整片淡掉。挂在 main.gd 的 BloodOverlay 上。
shader_type canvas_item;

uniform float amount = 0.0;
uniform float drip = 0.0;
uniform vec4 blood_color : source_color = vec4(0.42, 0.0, 0.02, 1.0);

// 血斑或已经流到的血痕处不透明，颜色带一点明暗和湿润的高光
// @keyword-cn 屏幕溅血, 血痕下流
// @keyword-en screen-blood, drip-reveal
void fragment() {
	vec4 m = texture(TEXTURE, UV);
	float run = (m.g > 0.0 && m.g <= drip) ? 1.0 : 0.0;
	float a = max(m.r, run) * amount * blood_color.a;
	vec3 c = blood_color.rgb * (0.7 + 0.6 * m.b);
	COLOR = vec4(c, a);
}
