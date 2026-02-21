shader_type spatial;
render_mode blend_mix, depth_draw_always, cull_back;

// Pulsing emission crystal shader for Logic Fortress & Knowledge Peaks

uniform vec4 crystal_color : source_color = vec4(0.3, 0.6, 1.0, 0.85);
uniform vec4 inner_glow_color : source_color = vec4(0.5, 0.8, 1.0, 1.0);
uniform float pulse_speed : hint_range(0.1, 5.0) = 1.2;
uniform float pulse_intensity : hint_range(0.0, 5.0) = 2.0;
uniform float base_emission : hint_range(0.0, 3.0) = 0.5;
uniform float refraction_strength : hint_range(0.0, 1.0) = 0.3;
uniform float facet_scale : hint_range(1.0, 20.0) = 8.0;

// Hash for facet pattern
float hash(vec3 p) {
    p = fract(p * vec3(443.897, 441.423, 437.195));
    p += dot(p, p.yzx + 19.19);
    return fract((p.x + p.y) * p.z);
}

// Voronoi distance for crystal facets
float voronoi(vec3 p) {
    vec3 i = floor(p);
    vec3 f = fract(p);
    float min_dist = 1.0;
    for (int x = -1; x <= 1; x++) {
        for (int y = -1; y <= 1; y++) {
            for (int z = -1; z <= 1; z++) {
                vec3 neighbor = vec3(float(x), float(y), float(z));
                vec3 point = neighbor + hash(i + neighbor) * 0.5 + 0.25;
                float dist = length(f - point);
                min_dist = min(min_dist, dist);
            }
        }
    }
    return min_dist;
}

void fragment() {
    // Crystal facets from Voronoi
    vec3 world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
    float facets = voronoi(world_pos * facet_scale);
    float facet_edge = smoothstep(0.0, 0.15, facets);

    // Pulse animation
    float pulse = sin(TIME * pulse_speed + world_pos.y * 2.0) * 0.5 + 0.5;
    float secondary_pulse = sin(TIME * pulse_speed * 0.7 + world_pos.x * 1.5) * 0.5 + 0.5;
    float combined_pulse = mix(pulse, secondary_pulse, 0.3);

    // Internal glow - stronger near center (using normal as proxy)
    float center_glow = pow(max(0.0, dot(NORMAL, VIEW)), 1.5);

    // Color
    vec3 surface_color = crystal_color.rgb * facet_edge;
    vec3 glow = inner_glow_color.rgb * center_glow;

    // Emission intensity based on pulse
    float emission_strength = base_emission + combined_pulse * pulse_intensity;
    emission_strength *= mix(0.7, 1.0, facet_edge);

    // Edge highlight (rim lighting)
    float rim = pow(1.0 - abs(dot(NORMAL, VIEW)), 3.0);
    vec3 rim_color = inner_glow_color.rgb * rim * 1.5;

    ALBEDO = surface_color;
    EMISSION = (glow + rim_color) * emission_strength;
    ALPHA = crystal_color.a + rim * 0.15;
    METALLIC = 0.6;
    ROUGHNESS = 0.05 + (1.0 - facet_edge) * 0.2;
    SPECULAR = 0.9;
}
