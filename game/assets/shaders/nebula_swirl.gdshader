shader_type spatial;
render_mode unshaded, cull_disabled, blend_mix;

// Rotating color-shift nebula shader for Creativity Nebula realm

uniform vec4 color_a : source_color = vec4(0.8, 0.2, 0.9, 1.0);  // Purple
uniform vec4 color_b : source_color = vec4(0.2, 0.6, 1.0, 1.0);  // Cyan
uniform vec4 color_c : source_color = vec4(1.0, 0.4, 0.2, 1.0);  // Orange
uniform float rotation_speed : hint_range(0.0, 2.0) = 0.3;
uniform float swirl_intensity : hint_range(0.0, 10.0) = 4.0;
uniform float noise_scale : hint_range(0.5, 10.0) = 3.0;
uniform float brightness : hint_range(0.0, 5.0) = 1.5;
uniform float alpha_base : hint_range(0.0, 1.0) = 0.8;

// Smooth noise function
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);  // Smoothstep

    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));

    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p) {
    float value = 0.0;
    float amplitude = 0.5;
    for (int i = 0; i < 5; i++) {
        value += amplitude * noise(p);
        p *= 2.0;
        amplitude *= 0.5;
    }
    return value;
}

vec2 rotate2d(vec2 p, float angle) {
    float c = cos(angle);
    float s = sin(angle);
    return vec2(p.x * c - p.y * s, p.x * s + p.y * c);
}

void fragment() {
    vec2 uv = UV * 2.0 - 1.0;  // Center UVs (-1 to 1)

    // Rotation
    float angle = TIME * rotation_speed;
    vec2 rotated_uv = rotate2d(uv, angle);

    // Swirl distortion
    float dist = length(uv);
    float swirl_angle = dist * swirl_intensity - TIME * rotation_speed * 2.0;
    vec2 swirled_uv = rotate2d(rotated_uv, swirl_angle);

    // Layered noise for nebula structure
    float n1 = fbm(swirled_uv * noise_scale + TIME * 0.1);
    float n2 = fbm(swirled_uv * noise_scale * 1.5 - TIME * 0.15 + 5.0);
    float n3 = fbm(rotated_uv * noise_scale * 0.7 + TIME * 0.05 + 10.0);

    // Color cycling — each noise layer drives a different color
    float cycle = TIME * 0.2;
    float t1 = fract(n1 + cycle);
    float t2 = fract(n2 + cycle + 0.33);
    float t3 = fract(n3 + cycle + 0.66);

    vec3 col = vec3(0.0);
    col += color_a.rgb * smoothstep(0.3, 0.7, t1) * n1;
    col += color_b.rgb * smoothstep(0.3, 0.7, t2) * n2;
    col += color_c.rgb * smoothstep(0.3, 0.7, t3) * n3;

    // Stars / sparkle
    float star_field = noise(swirled_uv * 30.0 + TIME * 0.5);
    float stars = smoothstep(0.92, 0.95, star_field);
    col += vec3(1.0) * stars * 2.0;

    // Bright center core
    float core = smoothstep(0.5, 0.0, dist);
    col += mix(color_a.rgb, color_b.rgb, sin(TIME * 0.5) * 0.5 + 0.5) * core * 0.5;

    // Edge fade
    float edge_fade = smoothstep(1.0, 0.3, dist);

    ALBEDO = col * brightness;
    ALPHA = alpha_base * edge_fade * (0.5 + (n1 + n2) * 0.25);
}
