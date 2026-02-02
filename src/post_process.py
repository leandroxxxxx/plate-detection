import io
from PIL import Image
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
    def apply_h264_simulation(image: Image.Image, degradation_level: int) -> Image.Image:
        """
        Simula artefatos de compressão H.264/MPEG.
        Agora suporta níveis extremos (>100) criando macroblocos (pixelização).

        :param image: Imagem original (PIL Image).
        :param degradation_level: Inteiro >= 0.
                                  0-100: Artefatos de compressão JPEG/DCT.
                                  >100: Artefatos severos + Perda de resolução (Macroblocking).
        :return: Nova imagem com o efeito aplicado.
        """
        level = max(0, degradation_level)
        
        if level == 0:
            return image.copy()

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
            # Resize down (reduz informação)
            processed_img = processed_img.resize((new_w, new_h), resample=Image.NEAREST)

        # Buffer em memória para simular o processo de encoding/decoding
        buffer = io.BytesIO()

        # O formato JPEG usa compressão DCT, muito similar aos I-frames do H.264.
        # subsampling=2 força o subsampling de croma 4:2:0 (comum em vídeo)
        processed_img.convert("RGB").save(buffer, format="JPEG", quality=quality, subsampling=2)
        
        buffer.seek(0)
        loaded_img = Image.open(buffer)

        # Se houve redução de tamanho, estica de volta para o tamanho original
        # Usamos NEAREST ou BOX para manter os "quadrados" (macroblocos) visíveis
        if scale_factor < 1.0:
            return loaded_img.resize((original_w, original_h), resample=Image.NEAREST)
            
        return loaded_img.copy()