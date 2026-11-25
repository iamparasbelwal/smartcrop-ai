import math
import os
import shutil
from PIL import Image, ImageDraw


def render_scene(frame_idx, total_frames=36, scale=4, target_size=144):
    S = scale
    W = target_size * S
    H = target_size * S

    # Transparent background canvas
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Palette matching SmartCrop.AI editorial UI
    INK = (34, 32, 28, 255)          # #22201c
    GLASS_FILL = (255, 255, 255, 195)
    LIQUID = (194, 96, 60, 240)      # #c2603c terracotta
    LIQUID_DEEP = (169, 79, 47, 250)
    LIQUID_SURF = (218, 122, 86, 255)
    BISCUIT_FILL = (235, 202, 144, 255)
    BISCUIT_EDGE = (206, 166, 102, 255)
    BISCUIT_DOT = (146, 108, 58, 255)
    TICK_COLOR = (128, 122, 112, 225)
    HIGHLIGHT = (255, 255, 255, 165)

    # Proportions scaled to 144px base so it stays crisp even at 24px inline size
    k = target_size / 200.0
    cx = 100 * k * S
    flask_bottom_y = 176 * k * S
    flask_shoulder_y = 104 * k * S
    flask_neck_top_y = 56 * k * S
    neck_w = 20 * k * S
    base_w = 64 * k * S
    lip_w = 26 * k * S
    liquid_rest_y = 140 * k * S

    ST_MAIN = max(2, int(round(4.6 * k * S)))
    ST_THIN = max(1, int(round(2.4 * k * S)))

    impact_frame = 13
    sink_end_frame = 23

    time_since_impact = frame_idx - impact_frame
    if 0 <= time_since_impact <= 22:
        decay = math.exp(-time_since_impact * 0.18)
        wave_amplitude = 7.0 * k * S * decay
        wave_phase = time_since_impact * 0.85
    else:
        wave_amplitude = 1.4 * k * S * math.sin(frame_idx * (2 * math.pi / total_frames))
        wave_phase = frame_idx * 0.3

    liquid_y = liquid_rest_y
    if 0 <= time_since_impact <= 8:
        liquid_y -= (3.5 * k * S) * math.sin(time_since_impact * math.pi / 8)

    corner_r = 15 * k * S

    # --- 1. SUBTLE FROSTED GLASS INTERIOR SO LIQUID & BISCUIT READ OVER ANY BG ---
    glass_poly = [
        (cx - neck_w + ST_MAIN * 0.3, flask_neck_top_y + 3 * k * S),
        (cx + neck_w - ST_MAIN * 0.3, flask_neck_top_y + 3 * k * S),
        (cx + neck_w - ST_MAIN * 0.3, flask_shoulder_y),
        (cx + base_w - 2 * k * S, flask_bottom_y - corner_r * 0.5),
        (cx + base_w * 0.65, flask_bottom_y - 1 * k * S),
        (cx - base_w * 0.65, flask_bottom_y - 1 * k * S),
        (cx - base_w + 2 * k * S, flask_bottom_y - corner_r * 0.5),
        (cx - neck_w + ST_MAIN * 0.3, flask_shoulder_y),
    ]
    draw.polygon(glass_poly, fill=GLASS_FILL)

    # --- 2. LIQUID INSIDE FLASK ---
    t_liq = (liquid_y - flask_shoulder_y) / (flask_bottom_y - flask_shoulder_y)
    liq_half_w = neck_w + t_liq * (base_w - neck_w) - (2 * k * S)

    liq_pts = []
    num_surf_pts = 20
    for i in range(num_surf_pts + 1):
        frac = i / num_surf_pts
        px = (cx - liq_half_w) + frac * (2 * liq_half_w)
        env = 4 * frac * (1 - frac)
        py = liquid_y + wave_amplitude * math.sin(frac * math.pi * 3 + wave_phase) * env
        liq_pts.append((px, py))

    r_bottom_x = cx + base_w - (3 * k * S)
    l_bottom_x = cx - base_w + (3 * k * S)
    liq_pts.extend([
        (r_bottom_x, flask_bottom_y - (4 * k * S)),
        (cx + base_w * 0.65, flask_bottom_y - (1 * k * S)),
        (cx - base_w * 0.65, flask_bottom_y - (1 * k * S)),
        (l_bottom_x, flask_bottom_y - (4 * k * S)),
    ])
    draw.polygon(liq_pts, fill=LIQUID)

    depth_pts = [
        (cx - base_w * 0.85, flask_bottom_y - (16 * k * S)),
        (cx + base_w * 0.85, flask_bottom_y - (16 * k * S)),
        (r_bottom_x, flask_bottom_y - (4 * k * S)),
        (cx + base_w * 0.65, flask_bottom_y - (1 * k * S)),
        (cx - base_w * 0.65, flask_bottom_y - (1 * k * S)),
        (l_bottom_x, flask_bottom_y - (4 * k * S)),
    ]
    draw.polygon(depth_pts, fill=LIQUID_DEEP)

    surf_pts = liq_pts[: num_surf_pts + 1]
    draw.line(surf_pts, fill=LIQUID_SURF, width=max(2, int(round(3.0 * k * S))))

    # Rising micro-bubbles
    bubble_seeds = [
        (0.22, 3.6 * k * S, 0.0),
        (0.60, 2.8 * k * S, 0.3),
        (0.42, 2.3 * k * S, 0.6),
        (0.74, 3.2 * k * S, 0.8),
    ]
    for bx_ratio, b_rad, b_offset in bubble_seeds:
        b_prog = ((frame_idx / total_frames) + b_offset) % 1.0
        by = (flask_bottom_y - (8 * k * S)) - b_prog * ((flask_bottom_y - liquid_rest_y) + (4 * k * S))
        bx = (cx - base_w * 0.5) + bx_ratio * base_w + (3 * k * S) * math.sin(b_prog * 6 + b_offset * 10)
        if by > liquid_y + (4 * k * S):
            draw.ellipse(
                [bx - b_rad, by - b_rad, bx + b_rad, by + b_rad],
                outline=HIGHLIGHT,
                fill=(255, 255, 255, 85),
                width=max(1, int(round(1.2 * k * S))),
            )

    # Splash droplets
    if 0 <= time_since_impact <= 8:
        t_sp = time_since_impact / 8.0
        sp1_x = cx - (13 * k * S) - (11 * k * S) * t_sp
        sp1_y = liquid_y - (16 * k * S) * math.sin(t_sp * math.pi)
        sp1_r = (2.8 * k * S) * (1 - t_sp * 0.35)
        if sp1_y < liquid_y:
            draw.ellipse([sp1_x - sp1_r, sp1_y - sp1_r, sp1_x + sp1_r, sp1_y + sp1_r], fill=LIQUID_SURF)

        sp2_x = cx + (15 * k * S) + (13 * k * S) * t_sp
        sp2_y = liquid_y - (20 * k * S) * math.sin(t_sp * math.pi)
        sp2_r = (3.2 * k * S) * (1 - t_sp * 0.35)
        if sp2_y < liquid_y:
            draw.ellipse([sp2_x - sp2_r, sp2_y - sp2_r, sp2_x + sp2_r, sp2_y + sp2_r], fill=LIQUID_SURF)

    # --- 3. FALLING BISCUIT ---
    biscuit_rad = 14.5 * k * S
    if frame_idx < impact_frame:
        t_fall = frame_idx / impact_frame
        b_y = (-18 * k * S) + (liquid_rest_y + (18 * k * S)) * (t_fall ** 1.75)
        b_angle = math.radians(-16 + 24 * t_fall)
        b_alpha = 255
        b_scale = 1.0
    elif frame_idx <= sink_end_frame:
        t_sink = (frame_idx - impact_frame) / (sink_end_frame - impact_frame)
        b_y = liquid_rest_y + (flask_bottom_y - liquid_rest_y - (12 * k * S)) * (t_sink ** 0.8)
        b_angle = math.radians(8 + 10 * t_sink)
        b_alpha = int(255 * (1.0 - t_sink ** 1.45))
        b_scale = 1.0 - (0.38 * t_sink)
    else:
        b_alpha = 0
        b_y = flask_bottom_y
        b_angle = 0
        b_scale = 0

    if b_alpha > 0 and b_scale > 0:
        b_dim = int(biscuit_rad * 3.2)
        b_img = Image.new("RGBA", (b_dim, b_dim), (0, 0, 0, 0))
        b_draw = ImageDraw.Draw(b_img)
        bc = b_dim / 2
        br = biscuit_rad * b_scale

        b_draw.ellipse(
            [bc - br, bc - br, bc + br, bc + br],
            fill=BISCUIT_FILL,
            outline=INK,
            width=max(2, int(round(3.2 * k * S))),
        )
        b_draw.ellipse(
            [bc - br * 0.82, bc - br * 0.82, bc + br * 0.82, bc + br * 0.82],
            outline=BISCUIT_EDGE,
            width=max(1, int(round(1.5 * k * S))),
        )

        dot_r = max(1.5, 1.5 * k * S * b_scale)
        dots = [
            (0, 0),
            (-br * 0.44, -br * 0.2),
            (br * 0.44, -br * 0.2),
            (-br * 0.24, br * 0.4),
            (br * 0.24, br * 0.4),
        ]
        for dx, dy in dots:
            b_draw.ellipse([bc + dx - dot_r, bc + dy - dot_r, bc + dx + dot_r, bc + dy + dot_r], fill=BISCUIT_DOT)

        b_rot = b_img.rotate(math.degrees(b_angle), resample=Image.Resampling.BICUBIC)
        if b_alpha < 255:
            r_ch, g_ch, b_ch, a_ch = b_rot.split()
            a_ch = a_ch.point(lambda p: int(p * (b_alpha / 255.0)))
            b_rot = Image.merge("RGBA", (r_ch, g_ch, b_ch, a_ch))
        img.paste(b_rot, (int(cx - bc), int(b_y - bc)), b_rot)

    # --- 4. FLASK GLASS OUTLINE ---
    lip_rect = [cx - lip_w, flask_neck_top_y - (3 * k * S), cx + lip_w, flask_neck_top_y + (4 * k * S)]
    draw.rounded_rectangle(lip_rect, radius=max(2, int(round(3 * k * S))), fill=GLASS_FILL, outline=INK, width=ST_MAIN)

    draw.line([(cx - neck_w, flask_neck_top_y + (4 * k * S)), (cx - neck_w, flask_shoulder_y)], fill=INK, width=ST_MAIN)
    draw.line([(cx - neck_w, flask_shoulder_y), (cx - base_w, flask_bottom_y - corner_r)], fill=INK, width=ST_MAIN)
    draw.arc(
        [cx - base_w, flask_bottom_y - corner_r * 2, cx - base_w + corner_r * 2, flask_bottom_y],
        start=90,
        end=180,
        fill=INK,
        width=ST_MAIN,
    )
    draw.line([(cx - base_w + corner_r, flask_bottom_y), (cx + base_w - corner_r, flask_bottom_y)], fill=INK, width=ST_MAIN)
    draw.arc(
        [cx + base_w - corner_r * 2, flask_bottom_y - corner_r * 2, cx + base_w, flask_bottom_y],
        start=0,
        end=90,
        fill=INK,
        width=ST_MAIN,
    )
    draw.line([(cx + base_w, flask_bottom_y - corner_r), (cx + neck_w, flask_shoulder_y)], fill=INK, width=ST_MAIN)
    draw.line([(cx + neck_w, flask_shoulder_y), (cx + neck_w, flask_neck_top_y + (4 * k * S))], fill=INK, width=ST_MAIN)

    for y_mark, mark_len in [(160 * k * S, 11 * k * S), (144 * k * S, 15 * k * S), (128 * k * S, 11 * k * S)]:
        t_m = (y_mark - flask_shoulder_y) / (flask_bottom_y - flask_shoulder_y)
        edge_x = cx + neck_w + t_m * (base_w - neck_w) - (5 * k * S)
        draw.line([(edge_x - mark_len, y_mark), (edge_x, y_mark)], fill=TICK_COLOR, width=ST_THIN)

    hl_pts = [
        (cx - neck_w + (5 * k * S), flask_neck_top_y + (12 * k * S)),
        (cx - neck_w + (5 * k * S), flask_shoulder_y - (3 * k * S)),
        (cx - base_w + (13 * k * S), flask_bottom_y - corner_r - (6 * k * S)),
    ]
    draw.line(hl_pts[:2], fill=HIGHLIGHT, width=max(1, int(round(2.5 * k * S))))
    draw.line(hl_pts[1:], fill=HIGHLIGHT, width=max(1, int(round(3.0 * k * S))))

    return img.resize((target_size, target_size), resample=Image.Resampling.LANCZOS)


def rgba_to_transparent_p(rgba_img: Image.Image, matte=(255, 255, 255)) -> Image.Image:
    """Convert RGBA frame to crisp 256-color palette GIF frame with index 0 = transparent.

    Premultiplies semi-transparent foreground pixels against a light warm matte to eliminate
    dark fringes around curved strokes.
    """
    rgba = rgba_img.convert("RGBA")
    alpha = rgba.getchannel("A")
    # Threshold mask: any pixel with alpha >= 80 stays opaque; < 80 becomes transparent (index 0)
    mask = alpha.point(lambda a: 255 if a >= 80 else 0)

    # Composite foreground onto clean matte so anti-aliased edge pixels have zero black halo
    bg = Image.new("RGB", rgba.size, matte)
    bg.paste(rgba.convert("RGB"), mask=alpha)

    # Quantize to 255 colors, leaving index 255 free, then shift to keep index 0 as transparent
    q = bg.quantize(colors=255, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    old_pal = q.getpalette() or [0] * (256 * 3)
    new_pal = [0, 0, 0] + old_pal[: 255 * 3]

    out = Image.new("P", rgba.size, 0)
    out.putpalette(new_pal)

    src_data = q.getdata()
    m_data = mask.getdata()
    out_data = [pix + 1 if m else 0 for pix, m in zip(src_data, m_data)]
    out.putdata(out_data)
    out.info["transparency"] = 0
    return out


def build_gif():
    total_frames = 36
    frames_trans = []

    print("Generating transparent frames...")
    for f in range(total_frames):
        fr_rgba = render_scene(f, total_frames=total_frames, scale=4, target_size=144)
        frames_trans.append(rgba_to_transparent_p(fr_rgba, matte=(255, 255, 255)))

    out_path = "assets/loading_biscuit_flask.gif"
    frames_trans[0].save(
        out_path,
        save_all=True,
        append_images=frames_trans[1:],
        duration=48,
        loop=0,
        transparency=0,
        disposal=2,
        optimize=False,
    )
    print(f"Saved {out_path} ({os.path.getsize(out_path)} bytes)")

    artifact_dir = r"C:\Users\ht934\.gemini\antigravity\brain\ed41213d-31c9-46f3-84c5-88e41d35eeda"
    art_path = os.path.join(artifact_dir, "loading_biscuit_flask.gif")
    shutil.copy2(out_path, art_path)
    print(f"Copied to artifact dir: {art_path}")


if __name__ == "__main__":
    build_gif()
