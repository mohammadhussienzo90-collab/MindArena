shader_type spatial;
render_mode cull_back, diffuse_burley, specular_schlick_ggx;

// Height-based color blending for floating island terrain
uniform vec3 color_top : source_color = vec3(0.18, 0.42, 0.22);       // Lush grass
uniform vec3 color_mid : source_color = vec3(0.35, 0.25, 0.15);       // Brown earth
uniform vec3 color_bottom : source_color = vec3(0.12, 0.10, 0.08);    // Dark stone
uniform vec3 color_cliff : source_color = vec3(0.08, 0.06, 0.12);     // Purple-tinged cliff face
uniform float height_range = 4.0;
uniform float cliff_threshold = -0.5;
uniform float detail_scale = 25.0;
uniform float glow_intensity : hint_range(0.0, 2.0) = 0.15;
uniform vec3 glow_color : source_color = vec3(0.2, 0.5, 1.0);

// Procedural Voronoi noise for surface variation
float voronoi(vec2 uv) {
	vec2 cell = floor(uv);
	vec2 frac_part = fract(uv);
	float min_dist = 1.0;
	for (int y = -1; y <= 1; y++) {
		for (int x = -1; x <= 1; x++) {
			vec2 neighbor = vec2(float(x), float(y));
			vec2 point = fract(sin(vec2(
				dot(cell + neighbor, vec2(127.1, 311.7)),
				dot(cell + neighbor, vec2(269.5, 183.3))
			)) * 43758.5453);
			float d = length(neighbor + point - frac_part);
			min_dist = min(min_dist, d);
		}
	}
	return min_dist;
}

// Simple hash for variation
float hash(vec2 p) {
	return fract(sin(dot(p, vec2(41.1, 289.7))) * 45758.5453);
}

void fragment() {
	float h = VERTEX.y / height_range;

	// Base color from height
	vec3 color = mix(color_bottom, color_mid, smoothstep(-1.0, -0.1, h));
	color = mix(color, color_top, smoothstep(-0.1, 0.6, h));

	// Cliff faces: steep normals get cliff color
	float steepness = 1.0 - abs(dot(NORMAL, vec3(0.0, 1.0, 0.0)));
	color = mix(color, color_cliff, smoothstep(0.4, 0.8, steepness));

	// Voronoi detail for ground texture
	float detail = voronoi(UV * detail_scale) * 0.12;
	float fine_detail = voronoi(UV * detail_scale * 3.0) * 0.05;
	color += detail + fine_detail;

	// Subtle color variation per cell
	float variation = hash(floor(UV * detail_scale)) * 0.06 - 0.03;
	color += variation;

	// Edge glow for floating island mystical feel
	float edge_factor = smoothstep(cliff_threshold - 0.5, cliff_threshold, h);
	vec3 edge_glow = glow_color * (1.0 - edge_factor) * glow_intensity;

	ALBEDO = color;
	EMISSION = edge_glow;
	ROUGHNESS = mix(0.95, 0.75, smoothstep(-0.5, 0.5, h));
	METALLIC = 0.0;
	SPECULAR = 0.2;
}
