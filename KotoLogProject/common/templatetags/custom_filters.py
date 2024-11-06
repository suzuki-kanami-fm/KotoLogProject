from django import template
import colorsys
import random
register = template.Library()


@register.filter
def generate_hsl_color(child_id):
    random.seed(child_id)
    hue = random.random()  # 色相をランダムに生成
    saturation = 0.6  # 彩度を固定
    lightness = 0.7  # 明るさを固定

    r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)
    r, g, b = int(r * 255), int(g * 255), int(b * 255)
    return f"rgb({r}, {g}, {b})"


@register.filter
def is_video(file_url):
    """ファイルが動画かどうかを判定する"""
    video_extensions = ['.mp4', '.webm', '.ogg','.mov']
    return any(file_url.endswith(ext) for ext in video_extensions)