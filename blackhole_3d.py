import os
import sys
import numpy as np
import pygame

pygame.init()
W, H = 1100, 720
CX, CY = W // 2, H // 2
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("3D Black Hole Simulation")
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 14)
rng = np.random.default_rng(11)


def rx(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def ry(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rz(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def gradient(t, stops):
    pos = [p for p, _ in stops]
    out = np.zeros((len(t), 3), dtype=np.float32)
    for c in range(3):
        out[:, c] = np.interp(t, pos, [col[c] for _, col in stops])
    return out


HOT = [(0.0, (175, 205, 255)), (0.15, (255, 245, 210)), (0.5, (255, 160, 45)),
       (1.0, (190, 45, 10))]


def noise_layer(scale):
    gw, gh = W // scale + 2, H // scale + 2
    small = (rng.random((gw, gh)) * 255).astype(np.uint8)
    surf = pygame.surfarray.make_surface(np.stack([small] * 3, axis=2))
    big = pygame.transform.smoothscale(surf, (W, H))
    return pygame.surfarray.array3d(big)[:, :, 0].astype(np.float32) / 255.0


def fbm(scales, weights):
    total = sum(weights)
    return sum(w * noise_layer(sc) for sc, w in zip(scales, weights)) / total


def build_background():
    a = fbm((300, 150, 70, 28, 12), (0.40, 0.28, 0.18, 0.09, 0.05))
    b = fbm((260, 130, 60, 24), (0.45, 0.30, 0.15, 0.10))
    c = fbm((90, 40, 18), (0.5, 0.3, 0.2))
    a = np.clip((a - 0.40) * 2.6, 0, 1) ** 1.3
    b = np.clip((b - 0.42) * 2.6, 0, 1) ** 1.3
    xs = np.linspace(0, 1, W, dtype=np.float32)[:, None]
    ys = np.linspace(0, 1, H, dtype=np.float32)[None, :]

    def blob(cx, cy, sx, sy):
        return np.exp(-(((xs - cx) ** 2) / sx + ((ys - cy) ** 2) / sy))

    warm = blob(0.45, 0.50, 0.09, 0.16)
    purple = 0.30 + 0.75 * blob(0.12, 0.18, 0.10, 0.10) + 0.6 * blob(0.92, 0.88, 0.08, 0.10)
    teal = blob(0.84, 0.18, 0.10, 0.10) + 0.7 * blob(0.18, 0.88, 0.10, 0.08)
    lane = np.clip(1 - np.abs(c - 0.5) * 9, 0, 1)
    dark = 1 - 0.55 * lane * (0.35 + a)

    r = 4 + a * (purple * 105 + warm * 140) + b * teal * 20
    g = 5 + a * (purple * 28 + warm * 68) + b * teal * 115
    bl = 10 + a * (purple * 145 + warm * 16) + b * teal * 135
    arrf = np.stack([r, g, bl], axis=2) * dark[:, :, None]

    tvals = rng.random(4200)
    off = rng.normal(0, 70, 4200)
    bx = tvals * W + off * 0.45
    by = H * (0.82 - 0.62 * tvals) + off
    bxi, byi = bx.astype(np.int32), by.astype(np.int32)
    okb = (bxi >= 0) & (bxi < W) & (byi >= 0) & (byi < H)
    bright = (40 + 170 * rng.random(4200) ** 2)[:, None]
    tints = np.array([[200, 215, 255], [255, 240, 225], [255, 205, 160]], dtype=np.float32)
    tint = tints[rng.integers(0, 3, 4200)]
    arrf[bxi[okb], byi[okb]] += (tint * bright / 255.0)[okb]

    sxi = rng.integers(0, W, 900)
    syi = rng.integers(0, H, 900)
    sb = (60 + 190 * rng.random(900) ** 2)[:, None]
    arrf[sxi, syi] += tints[rng.integers(0, 3, 900)] * sb / 255.0

    arr = np.clip(arrf, 0, 255).astype(np.uint8)
    bg = pygame.surfarray.make_surface(arr)

    layer = pygame.Surface((W, H), pygame.SRCALPHA)
    palette = [(255, 255, 255), (190, 215, 255), (255, 225, 190), (255, 170, 210), (170, 255, 240)]
    for _ in range(190):
        x, y = int(rng.integers(0, W)), int(rng.integers(0, H))
        size = int(rng.choice([1, 1, 1, 2, 2, 3]))
        tint_c = palette[int(rng.integers(0, len(palette)))]
        pygame.draw.circle(layer, tint_c + (255,), (x, y), size)
        if size >= 2:
            L = int(rng.integers(12, 34)) if size == 3 else int(rng.integers(5, 12))
            for k in range(1, L):
                al = int(215 * (1 - k / L) ** 1.6)
                for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
                    if 0 <= x + dx < W and 0 <= y + dy < H:
                        layer.set_at((x + dx, y + dy), tint_c + (al,))
    for _ in range(9):
        x, y = int(rng.integers(40, W - 40)), int(rng.integers(40, H - 40))
        tint_c = palette[int(rng.integers(1, len(palette)))]
        pygame.draw.circle(layer, tint_c + (255,), (x, y), 3)
        for k in range(1, 46):
            al = int(230 * (1 - k / 46) ** 1.8)
            for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
                if 0 <= x + dx < W and 0 <= y + dy < H:
                    layer.set_at((x + dx, y + dy), tint_c + (al,))
            for dx, dy in ((k // 2, k // 2), (-k // 2, k // 2), (k // 2, -k // 2), (-k // 2, -k // 2)):
                if 0 <= x + dx < W and 0 <= y + dy < H:
                    layer.set_at((x + dx, y + dy), tint_c + (al // 3,))
    bg.blit(layer, (0, 0))
    return bg.convert()


R_RING = 330.0

N_DISC = 50000
u = rng.random(N_DISC)
d_r = 22 + (R_RING - 22) * u ** 1.3
arm = rng.random(N_DISC) < 0.55
d_th = rng.random(N_DISC) * 2 * np.pi
spiral = 2.3 * np.log(d_r / 20.0) + rng.choice([0.0, np.pi], N_DISC) + rng.normal(0, 0.32, N_DISC)
d_th = np.where(arm, spiral, d_th)
d_z = rng.normal(0, 2.2, N_DISC) + rng.normal(0, 1, N_DISC) * d_r * 0.014
d_omega = 1.0 / (d_r / 110.0)
t = d_r / R_RING
d_col = gradient(np.clip(t * 1.15, 0, 1), HOT)
d_w = 1.3 * (9 + 20 * (1 - t) ** 1.6) * (0.35 + 0.95 * rng.random(N_DISC)) * np.where(arm, 1.4, 0.9)
d_sp = np.clip(np.sqrt(150.0 / d_r), 0.35, 1.0)

N_RING = 10000
g_th = np.linspace(0, 2 * np.pi, N_RING) + rng.normal(0, 0.002, N_RING)
g_r = R_RING + rng.normal(0, 0.9, N_RING)
g_x, g_y = np.cos(g_th) * g_r, np.sin(g_th) * g_r
g_z = rng.normal(0, 0.9, N_RING)
g_col = gradient(rng.random(N_RING) * 0.5, [(0.0, (255, 205, 100)), (0.5, (255, 245, 205))])
g_w = 9 + 22 * rng.random(N_RING)
g_w[rng.random(N_RING) < 0.10] = 120

N_R2 = 4500
h_th = rng.random(N_R2) * 2 * np.pi
h_r = R_RING + 18 + rng.normal(0, 1.0, N_R2)
h_x, h_y = np.cos(h_th) * h_r, np.sin(h_th) * h_r
h_z = rng.normal(0, 1.0, N_R2)
h_col = np.tile(np.array([[255, 180, 80]], dtype=np.float32), (N_R2, 1))
h_w = 16 + 24 * rng.random(N_R2)

N_R3 = 3000
k_th = rng.random(N_R3) * 2 * np.pi
k_r = 190 + rng.normal(0, 0.7, N_R3)
k_x, k_y = np.cos(k_th) * k_r, np.sin(k_th) * k_r
k_z = rng.normal(0, 0.8, N_R3)
k_col = np.tile(np.array([[255, 215, 150]], dtype=np.float32), (N_R3, 1))
k_w = 10 + 16 * rng.random(N_R3)

N_JET = 16000
JET_L = 600.0
j_z = JET_L * rng.random(N_JET) ** 1.5 * rng.choice([-1, 1], N_JET)
j_abs = np.abs(j_z)
j_f = j_abs / JET_L
wob = 4.0 * j_f * np.sin(j_abs * 0.035)
j_x = rng.normal(0, 1, N_JET) * (0.6 + 3.2 * j_f) + wob
j_y = rng.normal(0, 1, N_JET) * (0.6 + 3.2 * j_f) + wob * 0.6
j_col = gradient(np.clip(j_f * 1.3, 0, 1), [(0.0, (210, 230, 255)), (0.25, (255, 235, 190)),
                                            (1.0, (255, 135, 40))])
j_w0 = 60 * (1 - j_f) ** 2 + 4

N_EMB = 2200
e_th = rng.random(N_EMB) * 2 * np.pi
e_r = 360 + rng.random(N_EMB) ** 1.5 * 420
e_x, e_y = np.cos(e_th) * e_r, np.sin(e_th) * e_r
e_z = rng.normal(0, 55, N_EMB)
e_col = gradient(rng.random(N_EMB), [(0.0, (255, 190, 100)), (1.0, (255, 100, 30))])
e_w = 22 + 60 * rng.random(N_EMB)

N_STAR = 1000
sv = rng.normal(0, 1, (N_STAR, 3))
sv /= np.linalg.norm(sv, axis=1, keepdims=True)
sv *= (650 + rng.random(N_STAR) * 500)[:, None]
st_col = gradient(rng.random(N_STAR), [(0.0, (190, 210, 255)), (0.6, (255, 255, 255)),
                                       (1.0, (255, 210, 160))])
st_w0 = 55 + 200 * rng.random(N_STAR) ** 2
st_ph = rng.random(N_STAR) * 6.28
st_sp = 1 + 3 * rng.random(N_STAR)

N_HALO = 4500
ha = rng.random(N_HALO) * 2 * np.pi
hr = 58 + rng.normal(0, 1.3, N_HALO)
N_ARC = 7000
aa = rng.normal(0, 0.5, N_ARC) + np.where(rng.random(N_ARC) < 0.5, 0.0, np.pi)
ar = 58 + np.abs(rng.normal(0, 12, N_ARC)) * np.where(rng.random(N_ARC) < 0.3, 1.8, 1.0)
halo_r = np.concatenate([hr, ar])
halo_a0 = np.concatenate([ha, aa])
halo_col = gradient(rng.random(N_HALO + N_ARC) * 0.6,
                    [(0.0, (255, 245, 215)), (0.6, (255, 170, 60))])
halo_w0 = np.concatenate([5 + 9 * rng.random(N_HALO), 1.5 + 6 * rng.random(N_ARC)])

O_X = np.concatenate([g_x, h_x, k_x, j_x, e_x, sv[:, 0]])
O_Y = np.concatenate([g_y, h_y, k_y, j_y, e_y, sv[:, 1]])
O_Z = np.concatenate([g_z, h_z, k_z, j_z, e_z, sv[:, 2]])
O_TX = np.concatenate([-np.sin(g_th), -np.sin(h_th), -np.sin(k_th),
                       np.zeros(N_JET + N_EMB + N_STAR)])
O_TY = np.concatenate([np.cos(g_th), np.cos(h_th), np.cos(k_th),
                       np.zeros(N_JET + N_EMB + N_STAR)])
O_SP = np.concatenate([np.ones(N_RING + N_R2 + N_R3), np.zeros(N_JET + N_EMB + N_STAR)])

ALL_COL = np.concatenate([d_col, g_col, h_col, k_col, j_col, e_col, st_col, halo_col]).astype(np.float32)

TONE = (255 * (1 - np.exp(-np.arange(4096) / 165.0))).astype(np.uint8)


def make_core_sprite(size=520):
    ax = np.linspace(-1, 1, size, dtype=np.float32)
    xx, yy = np.meshgrid(ax, ax, indexing="ij")
    d = np.sqrt(xx ** 2 + yy ** 2)
    a = (np.exp(-(d * 7.0) ** 2) * 1.2 + np.exp(-(d * 3.0) ** 2) * 0.55 +
         np.exp(-(d * 1.3) ** 2) * 0.16)
    a = a * np.clip(1.0 - d, 0, 1) ** 2
    r = np.clip(a * 255, 0, 255)
    g = np.clip(a * 195, 0, 255)
    b = np.clip(a * 105 - 8, 0, 255)
    return pygame.surfarray.make_surface(np.stack([r, g, b], axis=2).astype(np.uint8))


def make_streak(width=1500, height=40):
    x = np.linspace(-1, 1, width, dtype=np.float32)[:, None]
    y = np.linspace(-1, 1, height, dtype=np.float32)[None, :]
    a = np.exp(-np.abs(x) * 5.5) * np.exp(-(y * 7.0) ** 2) * 0.9
    r = np.clip(a * 255, 0, 255)
    g = np.clip(a * 185, 0, 255)
    b = np.clip(a * 120, 0, 255)
    return pygame.surfarray.make_surface(np.stack([r, g, b], axis=2).astype(np.uint8))


def make_vignette():
    xs = np.linspace(-1, 1, W, dtype=np.float32)[:, None]
    ys = np.linspace(-1, 1, H, dtype=np.float32)[None, :]
    d2 = xs ** 2 * 0.8 + ys ** 2
    v = np.clip(1.0 - 0.5 * d2 ** 1.3, 0.25, 1.0)
    arr = (np.stack([v, v, v], axis=2) * 255).astype(np.uint8)
    return pygame.surfarray.make_surface(arr)


core_sprite = make_core_sprite()
streak_sprite = make_streak()
vignette = make_vignette()
background = build_background()
base_surf = pygame.Surface((W, H)).convert()


def initial_matrix():
    return rz(-0.62) @ rx(1.22)


M = initial_matrix()
zoom = 1.0
auto_rotate = True
orbit_motion = True
dragging = False
show_hint = True
disc_phase = 0.0
tm = 0.0
FOCAL = 1400.0


def render(M, zoom, phase, tm):
    th = d_th + phase * d_omega
    cs, sn = np.cos(th), np.sin(th)
    dx, dy = cs * d_r, sn * d_r
    vz_d = M[2, 0] * (-sn) + M[2, 1] * cs
    beam_d = np.clip(1 - 0.45 * d_sp * vz_d, 0.6, 1.5)
    vz_o = M[2, 0] * O_TX + M[2, 1] * O_TY
    beam_o = np.clip(1 - 0.5 * O_SP * vz_o, 0.55, 1.6)

    jw = j_w0 * (0.6 + 0.4 * np.sin(j_abs * 0.05 - tm * 5.0))
    sw = st_w0 * (0.55 + 0.45 * np.sin(tm * st_sp + st_ph))
    o_w = np.concatenate([g_w, h_w, k_w, jw, e_w, sw]) * beam_o ** 2

    pts = np.stack([np.concatenate([dx, O_X]), np.concatenate([dy, O_Y]),
                    np.concatenate([d_z, O_Z])], axis=1) @ M.T
    x, y, z = pts[:, 0], pts[:, 1], pts[:, 2]
    s = FOCAL / (FOCAL + z)
    sx3 = CX + x * s * zoom
    sy3 = CY + y * s * zoom
    w3 = np.concatenate([d_w * beam_d ** 2, o_w]) * np.clip(s, 0.4, 1.5) ** 2
    valid3 = z > -0.85 * FOCAL

    phi = np.arctan2(M[1, 2], M[0, 2])
    edge = 1.0 - abs(M[2, 2])
    ang = halo_a0.copy()
    ang[N_HALO:] += phi
    sxh = CX + np.cos(ang) * halo_r * zoom
    syh = CY + np.sin(ang) * halo_r * zoom
    pulse = 1.0 + 0.12 * np.sin(tm * 2.2)
    hw = halo_w0.copy() * pulse
    hw[N_HALO:] *= 0.4 + 1.4 * edge

    sx = np.concatenate([sx3, sxh]).astype(np.int32)
    sy = np.concatenate([sy3, syh]).astype(np.int32)
    w = np.concatenate([w3, hw])
    ok = (sx >= 0) & (sx < W) & (sy >= 0) & (sy < H) & np.concatenate([valid3, np.ones(len(sxh), bool)])
    idx = sx[ok] * H + sy[ok]
    wk = w[ok]
    col = ALL_COL[ok]
    out = np.empty((W, H, 3), dtype=np.uint8)
    for c in range(3):
        acc = np.bincount(idx, weights=col[:, c] * (1 / 255.0) * wk, minlength=W * H)
        out[:, :, c] = TONE[np.minimum(acc, 4095).astype(np.int32)].reshape(W, H)
    return out


def draw_frame():
    pygame.surfarray.blit_array(base_surf, render(M, zoom, disc_phase, tm))
    screen.blit(background, (0, 0))
    screen.blit(base_surf, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

    s1 = pygame.transform.smoothscale(base_surf, (W // 3, H // 3))
    g1 = pygame.transform.smoothscale(s1, (W, H))
    s2 = pygame.transform.smoothscale(s1, (W // 8, H // 8))
    g2 = pygame.transform.smoothscale(s2, (W, H))
    s3 = pygame.transform.smoothscale(s2, (W // 24, H // 24))
    g3 = pygame.transform.smoothscale(s3, (W, H))
    for _ in range(2):
        screen.blit(g1, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    for _ in range(4):
        screen.blit(g2, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    for _ in range(3):
        screen.blit(g3, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

    pulse = 1.0 + 0.05 * np.sin(tm * 2.2)
    size = int(520 * zoom * pulse)
    spr = pygame.transform.smoothscale(core_sprite, (size, size))
    screen.blit(spr, (CX - size // 2, CY - size // 2), special_flags=pygame.BLEND_RGB_ADD)

    sw_ = int(1500 * zoom * (1.0 + 0.04 * np.sin(tm * 1.3)))
    sh_ = max(4, int(40 * zoom))
    st = pygame.transform.smoothscale(streak_sprite, (sw_, sh_))
    screen.blit(st, (CX - sw_ // 2, CY - sh_ // 2), special_flags=pygame.BLEND_RGB_ADD)

    pygame.draw.circle(screen, (255, 252, 240), (CX, CY), max(2, int(5 * zoom)))
    screen.blit(vignette, (0, 0), special_flags=pygame.BLEND_RGB_MULT)


shot_mode = os.environ.get("BH_SHOT")
frame = 0
running = True
while running:
    dt = clock.tick(60) / 1000.0
    tm += dt
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_a:
                auto_rotate = not auto_rotate
            elif event.key == pygame.K_SPACE:
                orbit_motion = not orbit_motion
            elif event.key == pygame.K_h:
                show_hint = not show_hint
            elif event.key == pygame.K_r:
                M = initial_matrix()
                zoom = 1.0
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                dragging = True
                pygame.mouse.get_rel()
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                dragging = False
        elif event.type == pygame.MOUSEWHEEL:
            zoom = float(np.clip(zoom * (1.1 ** event.y), 0.3, 3.0))

    if dragging:
        mdx, mdy = pygame.mouse.get_rel()
        M = rx(mdy * 0.008) @ ry(-mdx * 0.008) @ M

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        M = ry(0.03) @ M
    if keys[pygame.K_RIGHT]:
        M = ry(-0.03) @ M
    if keys[pygame.K_UP]:
        M = rx(-0.03) @ M
    if keys[pygame.K_DOWN]:
        M = rx(0.03) @ M

    if auto_rotate and not dragging:
        M = ry(-0.0028) @ M
    if orbit_motion:
        disc_phase += 0.38 * dt

    draw_frame()
    if show_hint:
        hint = font.render("Drag: rotate | Wheel: zoom | A: auto | SPACE: orbit | H: hide | R: reset",
                           True, (170, 170, 170))
        screen.blit(hint, (10, H - 22))
    pygame.display.flip()

    frame += 1
    if shot_mode and frame >= 3:
        pygame.image.save(screen, shot_mode)
        running = False

pygame.quit()
sys.exit()
sys.exit()