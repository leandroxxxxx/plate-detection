from PIL import Image, ImageDraw, ImageFont
from .config import PlateConfig
from .utils import TextUtils

class PlateGenerator:
    def __init__(self, config: PlateConfig):
        self.config = config
        self.font = self._load_font()

    def _load_font(self):
        try:
            return ImageFont.truetype(self.config.font_path, self.config.font_size)
        except IOError:
            print(f"Aviso: Fonte {self.config.font_path} não encontrada. Usando padrão.")
            return ImageFont.load_default()

    def create_plate(self, text: str) -> Image.Image:
        # 1. Cria Fundo branco
        image = Image.new('RGBA', (self.config.width, self.config.height), color=self.config.bg_color)
        draw = ImageDraw.Draw(image)

        # 2. Cálculos de posicionamento do texto — centralizado no fundo inteiro
        _, char_height = TextUtils.get_char_size(self.font, "A", draw)
        total_text_width = TextUtils.get_total_text_width(self.font, text, self.config.text_spacing, draw)

        start_x = (self.config.width - total_text_width) / 2
        start_y = (self.config.height - char_height) / 2

        # 3. Desenha Texto Principal
        current_x = start_x
        for char in text:
            draw.text((current_x, start_y), char, font=self.font, fill=self.config.text_color)
            w, _ = TextUtils.get_char_size(self.font, char, draw)
            current_x += w + self.config.text_spacing

        return image.convert('RGB')