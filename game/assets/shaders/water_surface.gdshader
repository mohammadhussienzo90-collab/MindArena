shader_type spatial;
render_mode blend_mix, depth_draw_always, cull_back;

// Animated wave vertex shader + transparency for Emotion Ocean realm

uniform vec4 shallow_color : source_color = vec4(0.1, 0.6, 0.8, 0.7);
uniform vec4 deep_color : source_color = vec4(0.02, 0.15, 0.35, 0.85);
uniform float wave_speed : hint_range(0.1, 3.0) = 0.8;
uniform float wave_height : hint_range(0.0, 2.0) = 0.4;
uniform float wave_frequency : hint_range(0.5, 5.0) = 1.5;
uniform float foam_threshold : hint_range(0.0, 1.0) = 0.6;
uniform float metallic_amount : hint_range(0.0, 1.0) = 0.3;
uniform float roughness_amount : hint_range(0.0, 1.0) = 0.1;

// Simplex-like hash for wave variation
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float wave(vec2 pos, float t) {
    float w1 = sin(pos.x * wave_frequency + t * wave_speed) * 0.5;
    float w2 = sin(pos.y * wave_frequency * 0.8 + t * wave_speed * 1.3) * 0.3;
    float w3 = sin((pos.x + pos.y) * wave_frequency * 0.6 + t * wave_speed * 0.7) * 0.2;
    // Small ripples
    float w4 = sin(pos.x * wave_frequency * 3.0 + t * wave_speed * 2.5) * 0.05;
    float w5 = sin(pos.y * wave_frequency * 2.8 + t * wave_speed * 2.0) * 0.05;
    return (w1 + w2 + w3 + w4 + w5) * wave_height;
}

void vertex() {
    float h = wave(VERTEX.xz, TIME);
    VERTEX.y += h;

    // Approximate normal from height differences
    float eps = 0.1;
    float hx = wave(VERTEX.xz + vec2(eps, 0.0), TIME);
    float hz = wave(VERTEX.xz + vec2(0.0, eps), TIME);
    vec3 tangent_x = vec3(eps, hx - h, 0.0);
    vec3 tangent_z = vec3(0.0, hz - h, eps);
    NORMAL = normalize(cross(tangent_z, tangent_x));
}

void fragment() {
    // Mix shallow and deep color based on viewing angle (Fresnel-like)
    float fresnel = pow(1.0 - abs(dot(NORMAL, VIEW)), 2.0);
    vec4 water_col = mix(deep_color, shallow_color, fresnel);

    // Foam at wave crests
    float h = wave(
        (MODEL_MATRIX * vec4(VERTEX, 1.0)).xz,
        TIME
    );
    float foam = smoothstep(foam_threshold * wave_height, wave_height, h);
    water_col.rgb = mix(water_col.rgb, vec3(0.9, 0.95, 1.0), foam * 0.6);

    // Bioluminescent glow in deeper areas
    float glow_pulse = sin(TIME * 1.5 + UV.x * 6.28) * 0.5 + 0.5;
    float glow_spots = smoothstep(0.7, 0.8, hash(floor(UV * 10.0)));
    vec3 bio_glow = vec3(0.0, 0.8, 1.0) * glow_spots * glow_pulse * 0.3;

    ALBEDO = water_col.rgb;
    EMISSION = bio_glow;
    ALPHA = water_col.a;
    METALLIC = metallic_amount;
    ROUGHNESS = roughness_amount + foam * 0.5;
    SPECULAR = 0.8;
}
