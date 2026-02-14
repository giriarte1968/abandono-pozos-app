from PIL import Image, ImageDraw, ImageFilter
import os
import random

def add_noise(image, intensity=10):
    """Adds subtle noise to simulate photo grain."""
    pixels = image.load()
    for i in range(image.size[0]):
        for j in range(image.size[1]):
            r, g, b = pixels[i, j]
            noise = random.randint(-intensity, intensity)
            pixels[i, j] = (max(0, min(255, r + noise)), 
                            max(0, min(255, g + noise)), 
                            max(0, min(255, b + noise)))

def draw_industrial_background(draw, size, theme="desert"):
    width, height = size
    if theme == "desert":
        # Sky Gradient
        for y in range(int(height * 0.7)):
            r = int(180 - (y / height) * 50)
            g = int(210 - (y / height) * 40)
            b = int(240 - (y / height) * 30)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        # Ground
        draw.rectangle([0, int(height * 0.7), width, height], fill=(160, 130, 90))
    elif theme == "incident":
        # Neutral industrial gray/dirt
        draw.rectangle([0, 0, width, height], fill=(90, 80, 70))
    elif theme == "restored":
        # Restored wasteland/sparse grass
        draw.rectangle([0, 0, width, height], fill=(100, 110, 80))

def create_x123_site():
    img = Image.new('RGB', (800, 600))
    draw = ImageDraw.Draw(img)
    draw_industrial_background(draw, (800, 600), "desert")
    
    # Draw a more realistic pump jack
    # Main A-Frame
    draw.polygon([(350, 440), (400, 180), (450, 440)], fill=(40, 40, 40), outline=(20, 20, 20))
    # Beam
    draw.line([(250, 210), (550, 210)], fill=(60, 60, 60), width=18)
    # Horse head (Nodding head)
    draw.chord([200, 160, 300, 260], 90, 270, fill=(30, 30, 30))
    # Cables
    draw.line([(250, 260), (250, 440)], fill=(20, 20, 20), width=3)
    
    add_noise(img, 15)
    img.save("storage/evidence/X-123_pre_work_site.jpg")

def create_z789_leakage():
    img = Image.new('RGB', (800, 600))
    draw = ImageDraw.Draw(img)
    draw_industrial_background(draw, (800, 600), "incident")
    
    # Wellhead base (cellar)
    draw.ellipse([300, 250, 500, 350], fill=(50, 50, 50), outline=(30, 30, 30))
    # Metallic pipes
    draw.rectangle([380, 280, 420, 350], fill=(70, 70, 70))
    # LEAKAGE: Irregular dark blob
    # Create a separate layer for the spill to add blur
    spill = Image.new('RGBA', (800, 600), (0, 0, 0, 0))
    spill_draw = ImageDraw.Draw(spill)
    # Main puddle
    spill_draw.ellipse([320, 310, 550, 420], fill=(10, 10, 10, 220))
    # Seepage fingers
    spill_draw.ellipse([450, 350, 600, 450], fill=(15, 15, 15, 180))
    spill = spill.filter(ImageFilter.GaussianBlur(5))
    img.paste(spill, (0, 0), spill)
    
    add_noise(img, 20)
    img.save("storage/evidence/Z-789_leakage_cellar.jpg")

def create_m555_capped():
    img = Image.new('RGB', (800, 600))
    draw = ImageDraw.Draw(img)
    draw_industrial_background(draw, (800, 600), "restored")
    
    # Capped Well (Cut below surface or just above)
    # Cylindrical wellhead cap (Green, standard in many regions)
    draw.rectangle([350, 320, 450, 480], fill=(40, 80, 40), outline=(20, 40, 20))
    # Top lid (flange)
    draw.ellipse([345, 305, 455, 335], fill=(50, 100, 50), outline=(20, 50, 20))
    # Bolts on lid
    for i in range(8):
        import math
        angle = i * (math.pi / 4)
        bx = 400 + 45 * math.cos(angle)
        by = 320 + 10 * math.sin(angle)
        draw.point((bx, by), fill=(150, 150, 150))
    
    add_noise(img, 12)
    img.save("storage/evidence/M-555_capped_wellhead.jpg")

if __name__ == "__main__":
    os.makedirs("storage/evidence", exist_ok=True)
    create_x123_site()
    create_z789_leakage()
    create_m555_capped()
    print("High-fidelity procedural industrial images generated.")
