from PIL import Image, ImageDraw, ImageFont
from .config import PlateConfig
from .utils import TextUtils
from .watermark import WatermarkRenderer

class PlateGenerator:
    def __init__(self, config: PlateConfig):
        self.config = config
        self.font = self._load_font()
        self.watermark_renderer = WatermarkRenderer(config.watermark, config.font_path)

    def _load_font(self):
        try:
            return ImageFont.truetype(self.config.font_path, self.config.font_size)
        except IOError:
            print(f"Aviso: Fonte {self.config.font_path} não encontrada. Usando padrão.")
            return ImageFont.load_default()

    def create_plate(self, text: str) -> Image.Image:
        # 1. Cria Fundo
        image = Image.new('RGBA', (self.config.width, self.config.height), color=self.config.bg_color)
        draw = ImageDraw.Draw(image)

        # 2. Cálculos de posicionamento
        _, char_height = TextUtils.get_char_size(self.font, "A", draw)
        total_text_width = TextUtils.get_total_text_width(self.font, text, self.config.text_spacing, draw)

        start_x = (self.config.width - total_text_width) / 2
        start_y = (self.config.height - char_height) / 2

        # 3. Desenha Texto Principal
        current_x = start_x
        for char in text:
            draw.text((current_x, start_y), char, font=self.font, fill='black')
            w, _ = TextUtils.get_char_size(self.font, char, draw)
            current_x += w + self.config.text_spacing

        # 4. Gera e aplica Marca D'água
        watermark_layer = self.watermark_renderer.generate_overlay(self.config.width, self.config.height)
        image.alpha_composite(watermark_layer)

        return image.convert('RGB')