import io
import os
import math
from PIL import Image, ImageFilter
from typing import Tuple

class ImageEffectProcessor:
    """
    Classe responsável por aplicar filtros e degradações em imagens
    para simular cenários reais de captura de vídeo.
    """

    @staticmethod
    def resize_image(image: Image.Image, size: Tuple[int, int]) -> Image.Image:
        """
        Redimensiona a imagem para o tamanho especificado.

        :param image: Imagem original.
        :param size: Tupla (largura, altura).
        :return: Imagem redimensionada.
        """
        # Usa LANCZOS para manter a qualidade no redimensionamento (antigo ANTIALIAS)
        return image.resize(size, resample=Image.LANCZOS)

    @staticmethod
    def apply_motion_blur(image: Image.Image, angle: float, intensity: int) -> Image.Image:
        """
        Aplica Desfoque de Movimento (Motion Blur).
        Cria um kernel de convolução linear na direção especificada.

        :param image: Imagem original.
        :param angle: Ângulo do movimento em graus (0 = Horizontal, 90 = Vertical).
        :param intensity: Intensidade do borrão (tamanho do kernel em pixels).
                          Agora aceita valores altos (ex: 15, 30, 50).
        :return: Imagem com motion blur.
        """
        if intensity <= 1:
            return image

        # Converte para RGBA para garantir que o blending funcione perfeitamente
        original_mode = image.mode
        img_rgba = image.convert('RGBA')

        # Cria uma imagem base para acumular os deslocamentos
        canvas = Image.new('RGBA', img_rgba.size, (0, 0, 0, 0))

        # Vetor de direção
        dx = math.cos(math.radians(angle))
        dy = math.sin(math.radians(angle))

        # Sobrepõe a imagem n vezes com deslocamentos incrementais
        for i in range(intensity):
            offset_x = int(round(i * dx))
            offset_y = int(round(i * dy))

            # Alpha dinâmico para criar uma média aritmética das imagens
            # A primeira imagem tem peso 1, a segunda 1/2, a terceira 1/3...
            alpha = 1.0 / (i + 1)

            # Cria um frame deslocado
            frame = Image.new('RGBA', img_rgba.size, (0, 0, 0, 0))
            frame.paste(img_rgba, (offset_x, offset_y))

            # Mescla com o acumulado
            canvas = Image.blend(canvas, frame, alpha)

        return canvas.convert(original_mode)

    @staticmethod
    def apply_cctv_sharpening(image: Image.Image, percent: int = 150) -> Image.Image:
        """
        Simula o 'Sharpening' agressivo de câmeras de segurança.
        Isso cria halos e artefatos ao redor das bordas dos caracteres.
        """
        # UnsharpMask ajuda a criar aquele aspecto de bordas realçadas artificialmente
        # radius: raio do efeito, percent: força, threshold: sensibilidade
        return image.filter(ImageFilter.UnsharpMask(radius=2, percent=percent, threshold=3))

    @staticmethod
    def apply_low_dynamic_range(image: Image.Image, contrast: float = 0.8) -> Image.Image:
        """Simula a perda de detalhe em sombras e luzes (contraste de sensor barato)."""
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(contrast)
        return image

    @staticmethod
    def apply_noise(image: Image.Image, intensity: float) -> Image.Image:
        """
        Aplica ruído aleatório (simulação de ISO/Grão).

        :param image: Imagem original.
        :param intensity: Intensidade da mistura (0.0 a 1.0).
        :return: Imagem com ruído.
        """
        if intensity <= 0:
            return image

        # Gera uma "imagem" de ruído RGB puro a partir de bytes aleatórios
        w, h = image.size
        noise_data = os.urandom(w * h * 3) # 3 bytes por pixel (RGB)
        noise_image = Image.frombytes('RGB', (w, h), noise_data)

        # Mistura a imagem original com o ruído baseado na intensidade
        return Image.blend(image, noise_image, alpha=intensity)

    @staticmethod
    def apply_h264_simulation(image: Image.Image, degradation_level: int) -> Image.Image:
        """
        Simula artefatos de compressão H.264/MPEG.
        
        :param image: Imagem original (PIL Image).
        :param degradation_level: Inteiro >= 0.
                                  0-100: Artefatos de compressão JPEG/DCT.
                                  >100: Artefatos severos + Perda de resolução (Macroblocking).
        :return: Nova imagem com o efeito aplicado.
        """
        level = max(0, degradation_level)
        
        if level == 0:
            return image

        # 1. Define a Qualidade JPEG (1 a 95)
        # Se o nível for alto, a qualidade trava no mínimo (1)
        quality = max(1, int(95 - level))

        # 2. Define o Fator de Escala (Simulação de Macroblocos)
        # Se o nível > 50, começamos a diminuir a resolução interna
        # Nível 100 = 50% do tamanho original
        # Nível 200 = 25% do tamanho original
        scale_factor = 1.0
        if level > 50:
            scale_factor = max(0.01, 50 / float(level))

        original_w, original_h = image.size
        
        # Aplica o downscale se necessário (pixelização)
        processed_img = image
        if scale_factor < 1.0:
            new_w = max(1, int(original_w * scale_factor))
            new_h = max(1, int(original_h * scale_factor))
            # Resize down
            processed_img = processed_img.resize((new_w, new_h), resample=Image.NEAREST)

        # Buffer em memória para simular o processo de encoding/decoding
        buffer = io.BytesIO()

        # O formato JPEG usa compressão DCT, muito similar aos I-frames do H.264.
        # subsampling=2 força o subsampling de croma 4:2:0 (comum em vídeo)
        processed_img.convert("RGB").save(buffer, format="JPEG", quality=quality, subsampling=2)
        
        buffer.seek(0)
        loaded_img = Image.open(buffer)

        # --- O SEGREDO ESTÁ AQUI ---
        # Se houve redução, usamos BILINEAR para esticar de volta.
        # Isso remove os quadrados e cria manchas/borrões orgânicos.
        if scale_factor < 1.0:
            return loaded_img.resize((original_w, original_h), resample=Image.BILINEAR)
            
        return loaded_img