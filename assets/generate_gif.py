import math
import os
import shutil
from PIL import Image, ImageDraw

def render_scene(frame_idx, total_frames=36, scale=4, target_size=200, transparent=False):
    S = scale
    W = target_size * S
    H = target_size * S
    
    # Background
    if transparent:
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    else:
        # App theme canvas: #faf9f5
        img = Image.new("RGBA", (W, H), (250, 249, 245, 255))
    
    draw = ImageDraw.Draw(img)
    
    # Palette
    INK = (34, 32, 28, 255)         # #22201c
    LIQUID = (194, 96, 60, 230)     # #c2603c terracotta
    LIQUID_DEEP = (169, 79, 47, 240)
    LIQUID_SURF = (214, 114, 78, 255)
    BISCUIT_FILL = (235, 205, 155, 255)
    BISCUIT_EDGE = (212, 176, 120, 255)
    BISCUIT_DOT = (160, 125, 75, 255)
    TICK_COLOR = (140, 134, 124, 200)
    HIGHLIGHT = (255, 255, 255, 130)
    
    # Center & Geometry (at 200px base scale, multiplied by S)
    cx = 100 * S
    flask_bottom_y = 175 * S
    flask_shoulder_y = 105 * S
    flask_neck_top_y = 60 * S
    neck_w = 18 * S                  # Neck half-width: 18 -> full width 36px
    base_w = 60 * S                  # Base half-width: 60 -> full width 120px
    lip_w = 23 * S                   # Lip half-width: 23 -> 46px
    liquid_rest_y = 142 * S          # Normal liquid surface level
    
    # Stroke widths
    ST_MAIN = 3 * S
    ST_THIN = 2 * S
    
    # Impact timing:
    # 0 -> 12: Biscuit falls from y=-30 to y=142
    # 13: Hits liquid surface
    # 14 -> 24: Splashes, sinks into liquid, dissolves
    # 25 -> 35: Surface settles, ripples dissipate, bubbles rise
    
    impact_frame = 13
    sink_end_frame = 23
    
    # Calculate wave displacement on liquid surface
    time_since_impact = frame_idx - impact_frame
    wave_amplitude = 0
    wave_phase = 0
    if 0 <= time_since_impact <= 22:
        decay = math.exp(-time_since_impact * 0.18)
        wave_amplitude = 6 * S * decay
        wave_phase = time_since_impact * 0.8
    else:
        # Subtle idle breathing wave
        wave_amplitude = 1.2 * S * math.sin(frame_idx * (2 * math.pi / total_frames))
        wave_phase = frame_idx * 0.3
        
    liquid_y = liquid_rest_y
    if 0 <= time_since_impact <= 8:
        # Slight level rise on entry
        liquid_y -= (3 * S) * math.sin(time_since_impact * math.pi / 8)
        
    # --- 1. DRAW LIQUID (inside flask polygon) ---
    # Construct conical liquid polygon
    # At y=liquid_y, calculate flask half-width by linear interpolation
    t_liq = (liquid_y - flask_shoulder_y) / (flask_bottom_y - flask_shoulder_y)
    liq_half_w = neck_w + t_liq * (base_w - neck_w) - (2 * S)
    
    # Liquid points
    liq_pts = []
    # Surface wave points (left to right)
    num_surf_pts = 20
    for i in range(num_surf_pts + 1):
        frac = i / num_surf_pts
        px = (cx - liq_half_w) + frac * (2 * liq_half_w)
        # Sine wave modulated by parabolic envelope so edges stay attached
        env = 4 * frac * (1 - frac)
        py = liquid_y + wave_amplitude * math.sin(frac * math.pi * 3 + wave_phase) * env
        liq_pts.append((px, py))
        
    # Right wall down to rounded bottom-right
    r_bottom_x = cx + base_w - (3 * S)
    liq_pts.append((r_bottom_x, flask_bottom_y - (4 * S)))
    # Bottom curve
    liq_pts.append((cx + base_w * 0.6, flask_bottom_y - (1 * S)))
    liq_pts.append((cx - base_w * 0.6, flask_bottom_y - (1 * S)))
    # Left wall
    l_bottom_x = cx - base_w + (3 * S)
    liq_pts.append((l_bottom_x, flask_bottom_y - (4 * S)))
    
    # Fill liquid
    draw.polygon(liq_pts, fill=LIQUID)
    
    # Darker depth layer near the bottom
    depth_pts = [
        (cx - base_w * 0.85, flask_bottom_y - (16 * S)),
        (cx + base_w * 0.85, flask_bottom_y - (16 * S)),
        (r_bottom_x, flask_bottom_y - (4 * S)),
        (cx + base_w * 0.6, flask_bottom_y - (1 * S)),
        (cx - base_w * 0.6, flask_bottom_y - (1 * S)),
        (l_bottom_x, flask_bottom_y - (4 * S)),
    ]
    draw.polygon(depth_pts, fill=LIQUID_DEEP)
    
    # Liquid surface meniscus line
    surf_pts = [(p[0], p[1]) for p in liq_pts[:num_surf_pts + 1]]
    draw.line(surf_pts, fill=LIQUID_SURF, width=max(1, int(2.5 * S)))

    # --- 2. BUBBLES IN LIQUID ---
    # Persistent rising bubbles
    bubble_seeds = [
        (0.2, 0.4, 3.2 * S, 0.0),
        (0.6, 0.7, 2.5 * S, 0.3),
        (0.4, 0.2, 2.0 * S, 0.6),
        (0.75, 0.5, 3.0 * S, 0.8),
    ]
    for bx_ratio, by_ratio, b_rad, b_offset in bubble_seeds:
        # progress 0 to 1 as it rises
        b_prog = ((frame_idx / total_frames) + b_offset) % 1.0
        by = (flask_bottom_y - (8 * S)) - b_prog * ((flask_bottom_y - liquid_rest_y) + (5 * S))
        # slight sway
        bx = (cx - base_w * 0.5) + bx_ratio * (base_w * 1.0) + (3 * S) * math.sin(b_prog * 6 + b_offset * 10)
        
        # Only draw if below current liquid surface
        if by > liquid_y + (4 * S):
            draw.ellipse([bx - b_rad, by - b_rad, bx + b_rad, by + b_rad], outline=HIGHLIGHT, fill=(255, 255, 255, 70), width=max(1, S))
            
    # Splash droplets when biscuit hits (frames 13 -> 20)
    if 0 <= time_since_impact <= 8:
        t_sp = time_since_impact / 8.0
        # Left splash drop
        sp1_x = cx - (12 * S) - (10 * S) * t_sp
        sp1_y = liquid_y - (14 * S) * math.sin(t_sp * math.pi)
        sp1_r = (2.2 * S) * (1 - t_sp * 0.4)
        if sp1_y < liquid_y:
            draw.ellipse([sp1_x - sp1_r, sp1_y - sp1_r, sp1_x + sp1_r, sp1_y + sp1_r], fill=LIQUID_SURF)
            
        # Right splash drop
        sp2_x = cx + (14 * S) + (12 * S) * t_sp
        sp2_y = liquid_y - (18 * S) * math.sin(t_sp * math.pi)
        sp2_r = (2.6 * S) * (1 - t_sp * 0.4)
        if sp2_y < liquid_y:
            draw.ellipse([sp2_x - sp2_r, sp2_y - sp2_r, sp2_x + sp2_r, sp2_y + sp2_r], fill=LIQUID_SURF)

    # --- 3. BISCUIT MOTION ---
    # Falling trajectory
    biscuit_rad = 12 * S
    if frame_idx < impact_frame:
        # Falling through the air into the neck
        t_fall = frame_idx / impact_frame
        # Ease in (gravity acceleration)
        b_y = (-20 * S) + (liquid_rest_y + (20 * S)) * (t_fall ** 1.8)
        # Slight rotation as it falls
        b_angle = math.radians(-15 + 22 * t_fall)
        b_alpha = 255
        b_scale = 1.0
    elif frame_idx <= sink_end_frame:
        # Sinking and dissolving in liquid
        t_sink = (frame_idx - impact_frame) / (sink_end_frame - impact_frame)
        b_y = liquid_rest_y + (flask_bottom_y - liquid_rest_y - (12 * S)) * (t_sink ** 0.8)
        b_angle = math.radians(7 + 10 * t_sink)
        b_alpha = int(255 * (1.0 - t_sink ** 1.5))
        b_scale = 1.0 - (0.4 * t_sink)
    else:
        # Dissolved, waiting for next cycle
        b_alpha = 0
        b_y = flask_bottom_y
        b_angle = 0
        b_scale = 0

    if b_alpha > 0 and b_scale > 0:
        # Create separate layer for rotated biscuit
        b_dim = int(biscuit_rad * 3)
        b_img = Image.new("RGBA", (b_dim, b_dim), (0, 0, 0, 0))
        b_draw = ImageDraw.Draw(b_img)
        bc = b_dim / 2
        br = biscuit_rad * b_scale
        
        # Biscuit base
        b_draw.ellipse([bc - br, bc - br, bc + br, bc + br], fill=BISCUIT_FILL, outline=INK, width=max(1, int(2.5 * S)))
        # Inner baked rim
        b_draw.ellipse([bc - br * 0.85, bc - br * 0.85, bc + br * 0.85, bc + br * 0.85], outline=BISCUIT_EDGE, width=max(1, int(1.2 * S)))
        
        # 5 Docking prick dots (classic biscuit texture)
        dot_r = max(1, 1.2 * S * b_scale)
        dots = [
            (0, 0),
            (-br * 0.45, -br * 0.2),
            (br * 0.45, -br * 0.2),
            (-br * 0.25, br * 0.4),
            (br * 0.25, br * 0.4),
        ]
        for dx, dy in dots:
            b_draw.ellipse([bc + dx - dot_r, bc + dy - dot_r, bc + dx + dot_r, bc + dy + dot_r], fill=BISCUIT_DOT)
            
        # Rotate
        b_rot = b_img.rotate(math.degrees(b_angle), resample=Image.Resampling.BICUBIC)
        
        # Apply alpha fade if sinking
        if b_alpha < 255:
            r_ch, g_ch, b_ch, a_ch = b_rot.split()
            a_ch = a_ch.point(lambda p: int(p * (b_alpha / 255.0)))
            b_rot = Image.merge("RGBA", (r_ch, g_ch, b_ch, a_ch))
            
        # Paste onto main image
        img.paste(b_rot, (int(cx - bc), int(b_y - bc)), b_rot)

    # --- 4. FLASK GLASS OUTLINE & DETAILS ---
    # Lip at top
    lip_rect = [cx - lip_w, flask_neck_top_y - (2 * S), cx + lip_w, flask_neck_top_y + (3 * S)]
    draw.rounded_rectangle(lip_rect, radius=int(2.5 * S), fill=None, outline=INK, width=ST_MAIN)
    
    # Flask body path
    # Left lip corner -> neck down -> shoulder -> bottom-left corner -> bottom edge -> bottom-right corner -> shoulder -> neck up -> right lip corner
    corner_r = 14 * S
    flask_outline = [
        (cx - neck_w, flask_neck_top_y + (3 * S)),
        (cx - neck_w, flask_shoulder_y),
        (cx - base_w, flask_bottom_y - corner_r),
    ]
    # Draw Left neck and shoulder
    draw.line(flask_outline[:2], fill=INK, width=ST_MAIN)
    draw.line(flask_outline[1:3], fill=INK, width=ST_MAIN)
    
    # Left rounded bottom corner
    draw.arc([cx - base_w, flask_bottom_y - corner_r * 2, cx - base_w + corner_r * 2, flask_bottom_y], 
             start=90, end=180, fill=INK, width=ST_MAIN)
    
    # Bottom line
    draw.line([(cx - base_w + corner_r, flask_bottom_y), (cx + base_w - corner_r, flask_bottom_y)], fill=INK, width=ST_MAIN)
    
    # Right rounded bottom corner
    draw.arc([cx + base_w - corner_r * 2, flask_bottom_y - corner_r * 2, cx + base_w, flask_bottom_y], 
             start=0, end=90, fill=INK, width=ST_MAIN)
    
    # Right shoulder & neck
    draw.line([(cx + base_w, flask_bottom_y - corner_r), (cx + neck_w, flask_shoulder_y)], fill=INK, width=ST_MAIN)
    draw.line([(cx + neck_w, flask_shoulder_y), (cx + neck_w, flask_neck_top_y + (3 * S))], fill=INK, width=ST_MAIN)

    # Measurement markings on right side of conical body
    for y_mark, mark_len in [(160 * S, 10 * S), (145 * S, 14 * S), (130 * S, 10 * S), (115 * S, 8 * S)]:
        # Interpolate x on right edge
        t_m = (y_mark - flask_shoulder_y) / (flask_bottom_y - flask_shoulder_y)
        edge_x = cx + neck_w + t_m * (base_w - neck_w) - (4 * S)
        draw.line([(edge_x - mark_len, y_mark), (edge_x, y_mark)], fill=TICK_COLOR, width=ST_THIN)

    # Left glass highlight / reflection line
    hl_pts = [
        (cx - neck_w + (4 * S), flask_neck_top_y + (10 * S)),
        (cx - neck_w + (4 * S), flask_shoulder_y - (4 * S)),
        (cx - base_w + (12 * S), flask_bottom_y - corner_r - (6 * S)),
    ]
    draw.line(hl_pts[:2], fill=HIGHLIGHT, width=int(2 * S))
    draw.line(hl_pts[1:], fill=HIGHLIGHT, width=int(2.5 * S))

    # Downsample with high quality Lanczos antialiasing
    final_img = img.resize((target_size, target_size), resample=Image.Resampling.LANCZOS)
    return final_img

def build_gif():
    total_frames = 36
    frames = []
    frames_trans = []
    
    print("Generating frames...")
    for f in range(total_frames):
        # Canvas-colored matte GIF (crispest in Streamlit canvas)
        fr = render_scene(f, total_frames=total_frames, scale=4, target_size=180, transparent=False)
        frames.append(fr.convert("P", palette=Image.Palette.ADAPTIVE))
        
        # Transparent version
        fr_t = render_scene(f, total_frames=total_frames, scale=4, target_size=180, transparent=True)
        frames_trans.append(fr_t)
        
    out_path = "assets/loading_biscuit_flask.gif"
    out_trans_path = "assets/loading_biscuit_flask_trans.gif"
    
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=50,
        loop=0,
        optimize=True,
    )
    print(f"Saved {out_path} ({os.path.getsize(out_path)} bytes)")
    
    # Transparent GIF
    frames_trans[0].save(
        out_trans_path,
        save_all=True,
        append_images=frames_trans[1:],
        duration=50,
        loop=0,
        transparency=0,
        disposal=2,
    )
    print(f"Saved {out_trans_path} ({os.path.getsize(out_trans_path)} bytes)")

    # Also copy to artifacts directory for direct user viewing
    artifact_dir = r"C:\Users\ht934\.gemini\antigravity\brain\ed41213d-31c9-46f3-84c5-88e41d35eeda"
    art_path = os.path.join(artifact_dir, "loading_biscuit_flask.gif")
    shutil.copy2(out_path, art_path)
    print(f"Copied to artifact dir: {art_path}")

if __name__ == "__main__":
    build_gif()
