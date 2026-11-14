"""Contact sheet: python contact.py out.jpg cols label1=path1 label2=path2 ..."""
import sys, os
from PIL import Image, ImageDraw, ImageFont, ImageOps
HERE = os.path.dirname(os.path.abspath(__file__))
out, cols = sys.argv[1], int(sys.argv[2])
items = [a.split("=", 1) for a in sys.argv[3:]]
TW, TH, PAD, CAP = 480, 270, 10, 34
rows = (len(items) + cols - 1) // cols
sheet = Image.new("RGB", (cols * (TW + PAD) + PAD, rows * (TH + CAP + PAD) + PAD), (14, 16, 18))
d = ImageDraw.Draw(sheet)
fnt = ImageFont.truetype(os.path.join(HERE, "fonts", "Inter-Bold.ttf"), 17)
for i, (lab, p) in enumerate(items):
    im = ImageOps.fit(Image.open(p).convert("RGB"), (TW, TH), Image.LANCZOS)
    x = PAD + (i % cols) * (TW + PAD); y = PAD + (i // cols) * (TH + CAP + PAD)
    sheet.paste(im, (x, y))
    d.text((x + 2, y + TH + 7), lab[:52], font=fnt, fill=(220, 220, 215))
sheet.save(out, quality=88)
print(out, sheet.size)
