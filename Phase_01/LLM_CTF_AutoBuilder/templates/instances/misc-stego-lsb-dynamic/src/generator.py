# Type: Dynamic LSB Steganography Generator
import os
import random
from PIL import Image, ImageDraw, ImageFont

# 1. 获取 Flag
FLAG = os.environ.get('FLAG', 'flag{test_dynamic_stego}')
print(f"[*] Encoding Flag: {FLAG}")

# 2. 创建一张画布 (生成随机彩色噪点图，模拟 'GitHub开源' 风格的难度)
width, height = 400, 300
img = Image.new('RGB', (width, height), color='white')
pixels = img.load()

# 给图片填充一些随机颜色，假装它是艺术画
for y in range(height):
    for x in range(width):
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        # 预处理：把所有像素的最后一位变成 0 (腾出空间)
        pixels[x, y] = (r & ~1, g & ~1, b & ~1)

# 3. 把 Flag 转换成二进制流
# 例如 'A' -> 01000001
binary_flag = ''.join(format(ord(c), '08b') for c in FLAG)
# 加上结束符 (全0的8位)，方便解密工具识别
binary_flag += '00000000'

print(f"[*] Binary length: {len(binary_flag)} bits")

# 4. LSB 隐写核心算法：把二进制位写入 R 通道的最低位
data_index = 0
data_len = len(binary_flag)

for y in range(height):
    for x in range(width):
        if data_index < data_len:
            r, g, b = pixels[x, y]

            # 取出要藏的那 1 bit (0 或 1)
            bit = int(binary_flag[data_index])

            # 修改 R 通道的最后一位
            # 如果 bit 是 1，r | 1 变奇数；如果 bit 是 0，r & ~1 变偶数
            if bit == 1:
                r = r | 1
            else:
                r = r & ~1

            pixels[x, y] = (r, g, b)
            data_index += 1
        else:
            break

# 5. 保存生成的图片
img.save("flag.png")
print("[+] Stego image generated: flag.png")

# 6. 生成一个 index.html 方便下载
with open("index.html", "w") as f:
    f.write(f"""
    <html>
    <head><title>LSB Challenge</title></head>
    <body>
        <h1>Dynamic Stego Challenge</h1>
        <p>This image was generated automatically by the server.</p>
        <p>The FLAG is hidden in the Least Significant Bit (LSB).</p>
        <img src="flag.png" width="400" />
        <br><br>
        <a href="flag.png">Download flag.png</a>
    </body>
    </html>
    """)