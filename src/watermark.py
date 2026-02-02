from PIL import Image, ImageDraw, ImageFont
import math
from .config import WatermarkConfig
from .utils import TextUtils

class WatermarkRenderer:
    def __init__(self, config: WatermarkConfig, font_path: str):
        self.config = config
        self.font = self._load_font(font_path)

    def _load_font(self, font_path: str):
        try:
            return ImageFont.truetype(font_path, self.config.font_size)
        except IOError:
            return ImageFont.load_default()

    def generate_overlay(self, target_width: int, target_height: int) -> Image.Image:
        """Gera uma imagem RGBA transparente com o texto repetido e rotacionado."""
        
        # Cria um canvas temporário para medição
        temp_img = Image.new('RGBA', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        
        wm_w, wm_h = TextUtils.get_char_size(self.font, self.config.text, temp_draw)
        
        # Canvas gigante para garantir cobertura após rotação
        diagonal = int(math.sqrt(target_width**2 + target_height**2))
        canvas_size = diagonal * 3
        
        layer = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        
        step_x = int(wm_w + self.config.gap_x)
        step_y = int(wm_h + self.config.gap_y)
        
        # Desenha o padrão repetido
        for i in range(0, canvas_size, step_x):
            for j in range(0, canvas_size, step_y):
                draw.text((i, j), self.config.text, font=self.font, fill=self.config.color)
        
        # Rotaciona
        rotated = layer.rotate(self.config.rotation, resample=Image.BICUBIC)
        
        # Recorta para o tamanho alvo centralizado
        left = (canvas_size - target_width) // 2
        top = (canvas_size - target_height) // 2
        right = left + target_width
        bottom = top + target_height
        
        return rotated.crop((left, top, right, bottom))