"""Печатные карточки-наклейки с QR-кодом визитки салона «Шегги».

Запуск: python make_qr_card.py

Результат:
  qr-shaggi-card.png       — обложка перекрашена в градиентные полутона
  qr-shaggi-card-plain.png — без фото: «ШЕГГИ» типографикой на общем градиенте

Размер 1240x1748 — A6 при 300 dpi.
"""
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageFilter
import qrcode

URL = "https://painhahub.github.io/shaggi/"
OUT_COVER = "qr-shaggi-card.png"
OUT_PLAIN = "qr-shaggi-card-plain.png"

W, H = 1240, 1748

BG = (20, 10, 16)
SURFACE = (36, 16, 27)
EDGE = (56, 32, 46)
ACCENT = (230, 41, 135)
WINE = (156, 32, 93)
MUTED = (183, 152, 168)
INK = (247, 235, 241)

# Полутона для фона обложки: сверху насыщенный малиновый, книзу глухой бордовый.
COVER_TOP = (166, 30, 95)
COVER_BOTTOM = (72, 15, 40)

# Палитра типографской шапки второго варианта
PLAIN_TOP = (62, 15, 36)

FONTS = "C:/Windows/Fonts/"


def load_font(name, size):
    return ImageFont.truetype(FONTS + name, size)


f_label = load_font("segoeuib.ttf", 26)
f_addr = load_font("segoeui.ttf", 26)
f_hint = load_font("segoeuib.ttf", 34)
f_sub = load_font("segoeui.ttf", 24)
f_phone = load_font("segoeuib.ttf", 38)
f_tiny = load_font("segoeui.ttf", 21)
f_brand = load_font("georgiab.ttf", 152)


def rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255
    )
    return mask


def paste_rounded(base, img, xy, radius):
    base.paste(img, xy, rounded_mask(img.size, radius))


def vertical_gradient(size, top, bottom):
    """Плавный вертикальный градиент: одна строка растягивается на всю высоту."""
    width, height = size
    strip = Image.new("RGB", (1, height))
    px = strip.load()

    for y in range(height):
        t = y / max(height - 1, 1)
        px[0, y] = tuple(
            int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)
        )

    return strip.resize((width, height), Image.BILINEAR)


def recolor_cover(size):
    """Заменяет розовый фон обложки на градиент полутонов.

    Меняется только фон — насыщенный розовый по цвету. Белые мазки надписи
    и чёрная графика остаются исходными, поэтому «ШЕГГИ» сохраняет свой цвет
    и не превращается в цветной силуэт.
    """
    img = Image.open("assets/cover-source.jpg").convert("RGB").resize(size, Image.LANCZOS)
    _, sat, val = img.convert("HSV").split()

    # Маска фона: розовый любой насыщенности выше слабого оттенка — так в градиент
    # уходят и полупрозрачные ореолы вокруг мазков. Белое (низкая насыщенность)
    # и чёрное (низкая яркость) в маску не попадают.
    mask = ImageChops.multiply(
        sat.point(lambda x: 255 if x > 85 else 0),
        val.point(lambda x: 255 if x > 95 else 0),
    )
    mask = mask.filter(ImageFilter.GaussianBlur(1.6))

    grad = vertical_gradient(size, COVER_TOP, COVER_BOTTOM)
    return Image.composite(grad, img, mask)


def tear_mask(size, top_fade=28, bottom_share=0.8):
    """Маска растворения обложки в фоне карточки."""
    width, height = size
    mask = Image.new("L", (width, height), 255)
    painter = ImageDraw.Draw(mask)

    for y in range(top_fade):
        painter.line(
            [(0, y), (width, y)],
            fill=int(255 * (y / top_fade) ** 1.2),
        )

    bottom_start = int(height * bottom_share)
    for y in range(bottom_start, height):
        progress = (y - bottom_start) / (height - bottom_start)
        painter.line(
            [(0, y), (width, y)],
            fill=int(255 * (1 - progress) ** 1.4),
        )

    return mask.filter(ImageFilter.GaussianBlur(10))


def draw_qr(canvas, draw, tile_y, tile=720):
    """Плитка со стеклянной тенью, QR и логотипом в центре."""
    tile_x = (W - tile) // 2

    shadow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(shadow).rounded_rectangle(
        [tile_x - 6, tile_y + 10, tile_x + tile + 6, tile_y + tile + 18],
        radius=46,
        fill=135,
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(32))
    canvas.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0), shadow)

    draw.rounded_rectangle(
        [tile_x, tile_y, tile_x + tile, tile_y + tile],
        radius=40,
        fill=SURFACE,
        outline=EDGE,
        width=2,
    )

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, border=4)
    qr.add_data(URL)
    qr.make(fit=True)
    qr.box_size = max(6, 600 // (qr.modules_count + 8))
    qr_img = qr.make_image(
        fill_color=(20, 10, 16), back_color=(255, 255, 255)
    ).convert("RGB")

    plate = 640
    plate_x = tile_x + (tile - plate) // 2
    plate_y = tile_y + (tile - plate) // 2
    paste_rounded(canvas, Image.new("RGB", (plate, plate), (255, 255, 255)),
                  (plate_x, plate_y), 26)

    canvas.paste(
        qr_img,
        (
            plate_x + (plate - qr_img.width) // 2,
            plate_y + (plate - qr_img.height) // 2,
        ),
    )

    # Логотип в центре: 120 px при H-коррекции (30%) сканирование сохраняется
    center_x = plate_x + plate // 2
    center_y = plate_y + plate // 2
    logoS = 120
    ring = logoS + 18

    paste_rounded(
        canvas,
        Image.new("RGB", (ring, ring), (255, 255, 255)),
        (center_x - ring // 2, center_y - ring // 2),
        ring // 2,
    )
    paste_rounded(
        canvas,
        Image.open("assets/logo.jpg").convert("RGB").resize(
            (logoS, logoS), Image.LANCZOS
        ),
        (center_x - logoS // 2, center_y - logoS // 2),
        logoS // 2,
    )


def draw_contacts(canvas_draw, start_y):
    """Призыв, телефон и строка мессенджеров."""
    y = start_y
    centered(canvas_draw, "Наведите камеру телефона", y, f_hint, INK)
    y += 44
    centered(canvas_draw, "меню услуг и запись онлайн", y, f_sub, MUTED)
    y += 76
    centered(canvas_draw, "+7 930 246-36-60", y, f_phone, ACCENT)
    y += 50
    tracked(canvas_draw, "АВИТО · ВКОНТАКТЕ · MAX", y, f_tiny, MUTED, 3)


def centered(canvas_draw, text, y, font, fill):
    canvas_draw.text((W // 2, y), text, font=font, fill=fill, anchor="mm")


def tracked(canvas_draw, text, y, font, fill, spacing):
    widths = [canvas_draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x = W / 2 - total / 2

    for ch, width in zip(text, widths):
        canvas_draw.text((x, y), ch, font=font, fill=fill, anchor="lm")
        x += width + spacing


def new_canvas():
    """Фон карточки: общий градиент плюс мягкое винное свечение."""
    canvas = Image.new("RGB", (W, H), BG)

    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse([-300, 120, W + 300, 980], fill=58)
    glow = glow.filter(ImageFilter.GaussianBlur(200))
    canvas.paste(Image.new("RGB", (W, H), WINE), (0, 0), glow)

    return canvas


def build_cover_card():
    """Вариант 1: обложка перекрашена в градиентные полутона."""
    canvas = new_canvas()
    draw = ImageDraw.Draw(canvas)

    cover_size = (W, round(W * 480 / 1200))
    cover = recolor_cover(cover_size)
    canvas.paste(cover, (0, 0), tear_mask(cover_size))

    y = cover_size[1] + 66
    tracked(draw, "САЛОН КРАСОТЫ", y, f_label, ACCENT, 7)
    y += 46
    centered(draw, "Нижний Новгород · ул. Страж Революции, 2", y, f_addr, MUTED)

    tile_y = y + 84
    draw_qr(canvas, draw, tile_y)
    draw_contacts(draw, tile_y + 720 + 64)

    return canvas


def build_plain_card():
    """Вариант 2: без фото — «ШЕГГИ» типографикой на общем градиенте."""
    canvas = new_canvas()

    # Шапка: тот же общий градиент, без отдельной плитки и без фото
    head_h = 520
    head = vertical_gradient((W, head_h), PLAIN_TOP, BG)
    canvas.paste(head, (0, 0), tear_mask((W, head_h), top_fade=0, bottom_share=0.62))

    draw = ImageDraw.Draw(canvas)

    centered(draw, "ШЕГГИ", 236, f_brand, INK)
    tracked(draw, "САЛОН КРАСОТЫ", 344, f_label, ACCENT, 7)

    y = head_h + 70
    centered(draw, "Нижний Новгород · ул. Страж Революции, 2", y, f_addr, MUTED)

    tile_y = y + 84
    draw_qr(canvas, draw, tile_y)
    draw_contacts(draw, tile_y + 720 + 64)

    return canvas


def save(canvas, path):
    try:
        canvas.save(path, "PNG")
        print("saved", path, canvas.size)
    except OSError:
        # Файл может быть открыт в просмотрщике — пишем рядом
        fallback = path.replace(".png", "-v2.png")
        canvas.save(fallback, "PNG")
        print("saved", fallback, canvas.size, "(основной файл занят)")


save(build_cover_card(), OUT_COVER)
save(build_plain_card(), OUT_PLAIN)

# Обложка для шапки сайта — тот же перекрас и тот же градиент, что на карточке
site_cover = recolor_cover((1200, 480))
site_cover.save("assets/cover.jpg", "JPEG", quality=86, optimize=True)
print("saved assets/cover.jpg", site_cover.size)
