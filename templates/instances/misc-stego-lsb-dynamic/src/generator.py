# Type: Dynamic LSB Steganography Generator
# Difficulty: Easy
import os
import random
from PIL import Image

FLAG = os.environ.get('FLAG', 'FLAG_PLACEHOLDER')
print(f"[*] Encoding Flag: {FLAG}")

width, height = 400, 300
img    = Image.new('RGB', (width, height), color='white')
pixels = img.load()

for y in range(height):
    for x in range(width):
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        pixels[x, y] = (r & ~1, g & ~1, b & ~1)

# FLAG 转二进制 + 结束符
binary_flag = ''.join(format(ord(c), '08b') for c in FLAG) + '00000000'
print(f"[*] Binary length: {len(binary_flag)} bits")

# LSB 写入 R 通道
data_index = 0
for y in range(height):
    for x in range(width):
        if data_index < len(binary_flag):
            r, g, b = pixels[x, y]
            bit = int(binary_flag[data_index])
            r   = (r | 1) if bit == 1 else (r & ~1)
            pixels[x, y] = (r, g, b)
            data_index  += 1

img.save("flag.png")
print("[+] Stego image saved: flag.png")

with open("index.html", "w") as f:
    f.write("""<!DOCTYPE html>
<html lang="zh">
<head><meta charset="UTF-8"><title>LSB Stego Challenge</title></head>
<body style="font-family:sans-serif;text-align:center;padding:40px">
  <h2>🖼️ LSB 隐写挑战</h2>
  <p>图片由服务器动态生成，FLAG 藏在图片像素的最低位（LSB）中。</p>
  <img src="flag.png" width="400"><br><br>
  <a href="flag.png">📥 下载 flag.png</a>
  <p style="color:#888;font-size:13px">提示：尝试 zsteg / stegsolve / 手写脚本提取 R 通道 LSB</p>
</body>
</html>""")
