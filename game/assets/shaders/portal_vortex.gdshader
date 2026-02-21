shader_type spatial;
render_mode unshaded, cull_disabled, blend_mix, depth_draw_opaque;

// Swirling energy vortex for realm portals
uniform vec3 portal_color : source_color = vec3(0.2, 0.4, 1.0);
uniform vec3 secondary_color : source_color = vec3(0.1, 0.2, 0.5);
uniform float time_scale : hint_range(0.1, 5.0) = 1.5;
uniform float swirl_arms : hint_range(1.0, 8.0) = 4.0;
uniform float intensity : hint_range(0.5, 5.0) = 2.5;
uniform float pulse_speed : hint_range(0.0, 3.0) = 0.8;
uniform float edge_glow : hint_range(0.0, 3.0) = 1.5;

// Simplex-like noise
float noise(vec2 p) {
	return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

float smooth_noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);

	float a = noise(i);
	float b = noise(i + vec2(1.0, 0.0));
	float c = noise(i + vec2(0.0, 1.0));
	float d = noise(i + vec2(1.0, 1.0));

	return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

void fragment() {
	vec2 uv = UV * 2.0 - 1.0;
	float dist = length(uv);
	float angle = atan(uv.y, uv.x);

	// Swirling vortex pattern
	float swirl = sin(angle * swirl_arms + TIME * time_scale * 2.0 - dist * 8.0) * 0.5 + 0.5;
	float swirl2 = cos(angle * (swirl_arms - 1.0) + TIME * time_scale * 1.3 + dist * 5.0) * 0.5 + 0.5;

	// Noise distortion for organic feel
	float n = smooth_noise(uv * 4.0 + TIME * 0.3);

	// Combine swirls
	float pattern = mix(swirl, swirl2, 0.4) + n * 0.2;

	// Radial masks
	float inner_mask = 1.0 - smoothstep(0.0, 0.85, dist);    // Fade toward edge
	float ring_glow = smoothstep(0.7, 0.85, dist) * (1.0 - smoothstep(0.85, 1.0, dist));
	float center_bright = (1.0 - smoothstep(0.0, 0.3, dist)) * 0.5;

	// Pulse
	float pulse = 1.0 + sin(TIME * pulse_speed) * 0.15;

	// Color mixing
	float color_blend = swirl * inner_mask;
	vec3 base_color = mix(secondary_color, portal_color, color_blend);

	// Final composition
	float brightness = (pattern * inner_mask + center_bright + ring_glow * edge_glow) * intensity * pulse;

	ALBEDO = base_color;
	EMISSION = base_color * brightness;
	ALPHA = inner_mask * 0.85 + ring_glow * 0.5;
	ALPHA = clamp(ALPHA, 0.0, 0.95);
}
