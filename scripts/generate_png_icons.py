import os
import sys
import subprocess

# Ensure PIL (Pillow) is installed
try:
    from PIL import Image, ImageDraw
except ImportError:
    print("[*] Installing Pillow for image generation...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
        from PIL import Image, ImageDraw
    except Exception as e:
        print(f"[!] Failed to install Pillow: {e}")
        print("[*] Drawing mockup icons using basic methods...")
        sys.exit(1)

def create_icon(size, filename):
    # Base dark canvas (#0e0f19)
    img = Image.new('RGBA', (size, size), (14, 15, 25, 255))
    draw = ImageDraw.Draw(img)
    
    # Center and scale references
    c = size // 2
    r_outer = int(size * 0.35)
    
    # 1. Radial ambient glow (Purple -> Transparent)
    for r in range(r_outer, 0, -2):
        alpha = int(45 * (1 - r / r_outer))
        draw.ellipse([c-r, c-r, c+r, c+r], fill=(139, 92, 246, alpha))
        
    # Scale width for strokes
    stand_w = max(4, int(size * 0.018))
    
    # 2. Mic stand base
    draw.line([c - int(size*0.08), c + int(size*0.26), c + int(size*0.08), c + int(size*0.26)], fill=(236, 72, 153), width=stand_w)
    draw.line([c, c + int(size*0.26), c, c + int(size*0.16)], fill=(236, 72, 153), width=stand_w)
    
    # 3. Stand U-shape
    u_rect = [c - int(size*0.11), c + int(size*0.02), c + int(size*0.11), c + int(size*0.18)]
    draw.arc(u_rect, 0, 180, fill=(139, 92, 246), width=stand_w)
    
    # 4. Microphone lower body
    body_rect = [c - int(size*0.06), c - int(size*0.02), c + int(size*0.06), c + int(size*0.12)]
    draw.rounded_rectangle(body_rect, radius=max(2, int(size*0.015)), fill=(14, 15, 25), outline=(139, 92, 246), width=stand_w)
    
    # 5. Microphone capsule (Grille)
    grille_rect = [c - int(size*0.06), c - int(size*0.15), c + int(size*0.06), c - int(size*0.02)]
    draw.rounded_rectangle(grille_rect, radius=int(size*0.06), fill=(139, 92, 246), outline=(6, 182, 212), width=stand_w)
    
    # 6. Windscreen band
    band_rect = [c - int(size*0.07), c - int(size*0.03), c + int(size*0.07), c - int(size*0.01)]
    draw.rounded_rectangle(band_rect, radius=2, fill=(5, 5, 10))
    draw.rounded_rectangle(band_rect, radius=2, outline=(139, 92, 246), width=max(1, stand_w//2))
    
    # 7. Status light dot
    dot_r = max(2, int(size * 0.015))
    draw.ellipse([c - dot_r, c - int(size*0.08) - dot_r, c + dot_r, c - int(size*0.08) + dot_r], fill=(6, 182, 212))

    # Save to disk
    img.save(filename, 'PNG')
    print(f"[OK] Generated {filename}")

if __name__ == "__main__":
    # Script is in scripts/generate_png_icons.py, get root/frontend/public directory
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(scripts_dir)
    public_dir = os.path.join(root_dir, "frontend", "public")
    
    # Create public folder if it doesn't exist
    os.makedirs(public_dir, exist_ok=True)
    
    create_icon(192, os.path.join(public_dir, "icon-192.png"))
    create_icon(512, os.path.join(public_dir, "icon-512.png"))
    create_icon(180, os.path.join(public_dir, "apple-touch-icon.png"))
    print("[OK] All PNG fallback icons generated successfully in frontend/public.")
