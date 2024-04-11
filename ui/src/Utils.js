export function toTitleCase(str) {
    return str.replaceAll("_", " ").replace(
        /\w\S*/g,
        function (txt) {
            return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
        }
    );
}

export function stringToColor(str, alpha = 1) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const charCode = str.charCodeAt(i);
        hash = (hash * 31) + charCode;
    }

    const h = Math.abs(hash) % 360; // Hue (0-359)
    const s = 0.7; // Saturation (0-1)
    const l = 0.5; // Lightness (0-1)

    function hueToRgb(p, q, t) {
        if (t < 0) t += 1;
        if (t > 1) t -= 1;
        if (t < 1 / 6) return p + (q - p) * 6 * t;
        if (t < 1 / 2) return q;
        if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
        return p;
    }

    const r = hueToRgb(l + (1 - l) * Math.cos((h + 45) / 60), l + (1 - l) * Math.cos(h / 60), h / 60);
    const g = hueToRgb(l + (1 - l) * Math.cos((h - 15) / 60), l + (1 - l) * Math.cos(h / 60), (h - 15) / 60);
    const b = hueToRgb(l + (1 - l) * Math.cos((h + 195) / 60), l + (1 - l) * Math.cos(h / 60), (h + 195) / 60);

    const rgb = `rgba(${Math.round(r * 255)}, ${Math.round(g * 255)}, ${Math.round(b * 255)}, ${alpha})`;
    return rgb;
}