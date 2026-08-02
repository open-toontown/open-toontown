#version 120

// Water fragment shader with reflection, refraction, and Fresnel effect

uniform vec4 waterColor;
uniform float time;
uniform float waveHeight;
uniform float clarity;
uniform float reflectivity;
uniform sampler2D reflectionTex;
uniform sampler2D p3d_Texture0;

varying vec3 normal;
varying vec3 worldPos;
varying vec2 texcoord;
varying float depth;

// Fresnel reflectance approximation
float fresnel(vec3 incident, vec3 normal, float power) {
    float cosine = dot(-incident, normal);
    cosine = clamp(cosine, 0.0, 1.0);
    return pow(1.0 - cosine, power);
}

// Simple noise for water caustics
float hash(float n) {
    return fract(sin(n) * 43758.5453);
}

float noise(vec2 x) {
    vec2 p = floor(x);
    vec2 f = fract(x);
    f = f * f * (3.0 - 2.0 * f);
    float n = p.x + p.y * 57.0;
    return mix(mix(hash(n + 0.0), hash(n + 1.0), f.x),
               mix(hash(n + 57.0), hash(n + 58.0), f.x), f.y);
}

float fbm(vec2 p) {
    float f = 0.0;
    f += 0.5000 * noise(p); p *= 2.02;
    f += 0.2500 * noise(p); p *= 2.03;
    f += 0.1250 * noise(p); p *= 2.01;
    f += 0.0625 * noise(p);
    return f / 0.9375;
}

void main() {
    // Calculate reflection coordinates
    vec3 viewDir = normalize(-worldPos);
    vec3 reflectDir = reflect(viewDir, normal);
    
    // Convert reflection direction to texture coordinates
    vec2 reflCoord = 0.5 * reflectDir.xy / reflectDir.z + 0.5;
    reflCoord = clamp(reflCoord, 0.0, 1.0);
    
    // Sample reflection texture
    vec4 reflection = texture2D(reflectionTex, reflCoord);
    
    // Calculate Fresnel term
    float fresnelTerm = fresnel(viewDir, normal, 5.0);
    fresnelTerm = mix(0.02, 0.8, fresnelTerm);
    
    // Base water color with depth attenuation
    vec4 baseColor = waterColor;
    float depthFactor = clamp(1.0 - depth * 0.5, 0.1, 1.0);
    baseColor.a *= depthFactor * clarity;
    
    // Generate caustics pattern
    vec2 causticUV = worldPos.xz * 0.1 + time * 0.05;
    float caustics = fbm(causticUV) * 0.3 + 0.7;
    
    // Combine reflection and base color
    vec4 finalColor = mix(baseColor, reflection, fresnelTerm * reflectivity);
    
    // Apply caustics to underwater areas
    finalColor.rgb *= mix(1.0, caustics, 1.0 - fresnelTerm);
    
    // Add wave foam based on slope
    float slope = 1.0 - abs(normal.y);
    float foam = smoothstep(0.3, 0.5, slope * waveHeight * 10.0);
    
    // Foam noise
    vec2 foamUV = worldPos.xz * 0.5 + time * 0.2;
    float foamNoise = fbm(foamUV);
    foam *= foamNoise;
    
    // Add white foam
    finalColor.rgb = mix(finalColor.rgb, vec3(1.0), foam * 0.3);
    
    // Final alpha based on depth and clarity
    finalColor.a = mix(baseColor.a, 1.0, fresnelTerm * 0.5);
    
    gl_FragColor = finalColor;
}