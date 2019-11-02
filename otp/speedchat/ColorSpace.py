import math

def rgb2hsv(r, g, b):
    _min = float(min(r, g, b))
    _max = float(max(r, g, b))
    v = _max
    delta = _max - _min
    if delta != 0.0:
        s = delta / _max
    else:
        s = 0.0
        h = -1.0
        return (h, s, v)
    if r == _max:
        h = (g - b) / delta
    elif g == _max:
        h = 2.0 + (b - r) / delta
    else:
        h = 4.0 + (r - g) / delta
    h *= 60.0
    if h < 0.0:
        h += 360.0
    return (h, s, v)


def hsv2rgb(h, s, v):
    if s == 0.0:
        return (v, v, v)
    h %= 360.0
    h /= 60.0
    i = int(math.floor(h))
    f = h - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    if i == 0:
        return (v, t, p)
    elif i == 1:
        return (q, v, p)
    elif i == 2:
        return (p, v, t)
    elif i == 3:
        return (p, q, v)
    elif i == 4:
        return (t, p, v)
    else:
        return (v, p, q)


def rgb2yuv(r, g, b):
    y = 0.299 * r + 0.587 * g + 0.114 * b
    u = -.169 * r - 0.331 * g + 0.5 * b + 0.5
    v = 0.5 * r - 0.419 * g - 0.081 * b + 0.5
    return tuple(map(lambda x: min(max(x, 0), 1), (y, u, v)))


def yuv2rgb(y, u, v):
    r = y - 0.0009267 * (u - 0.5) + 1.4016868 * (v - 0.5)
    g = y - 0.3436954 * (u - 0.5) - 0.714169 * (v - 0.5)
    b = y + 1.7721604 * (u - 0.5) + 0.0009902 * (v - 0.5)
    return tuple(map(lambda x: min(max(x, 0), 1), (r, g, b)))
