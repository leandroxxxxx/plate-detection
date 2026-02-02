from PIL import ImageDraw, ImageFont

class TextUtils:
    @staticmethod
    def get_char_size(font: ImageFont.FreeTypeFont, char: str, dummy_draw: ImageDraw.Draw):
        """Calcula largura e altura de um único caractere."""
        try:
            left, top, right, bottom = dummy_draw.textbbox((0, 0), char, font=font)
            return right - left, bottom - top
        except AttributeError:
            # Fallback para versões antigas do Pillow
            return dummy_draw.textsize(char, font=font)

    @staticmethod
    def get_total_text_width(font: ImageFont.FreeTypeFont, text: str, spacing: int, dummy_draw: ImageDraw.Draw):
        """Calcula a largura total do texto somando letras + espaçamentos."""
        total_width = 0
        for char in text:
            w, _ = TextUtils.get_char_size(font, char, dummy_draw)
            total_width += w
        
        if len(text) > 1:
            total_width += (len(text) - 1) * spacing
        return total_width