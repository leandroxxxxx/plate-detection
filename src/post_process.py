import io
import os
import math
from PIL import Image, ImageFilter, ImageEnhance
from typing import List, Sequence, Tuple


class ImageEffectProcessor:
    """
    Classe responsável por aplicar filtros e degradações em imagens
    para simular cenários reais de captura de vídeo.
    """

    @staticmethod
    def _solve_linear_system(matrix: List[List[float]]) -> List[float]:
        """Resolve um sistema linear por eliminação de Gauss com pivoteamento."""
        size = len(matrix)
        for column in range(size):
            pivot = max(range(column, size), key=lambda row: abs(matrix[row][column]))
            if abs(matrix[pivot][column]) < 1e-12:
                raise ValueError("Não foi possível calcular a transformação de perspectiva.")
            matrix[column], matrix[pivot] = matrix[pivot], matrix[column]

            divisor = matrix[column][column]
            matrix[column] = [value / divisor for value in matrix[column]]

            for row in range(size):
                if row == column:
                    continue
                factor = matrix[row][column]
                matrix[row] = [
                    current - factor * reference
                    for current, reference in zip(matrix[row], matrix[column])
                ]

        return [matrix[row][-1] for row in range(size)]

    @staticmethod
    def _perspective_coefficients(
        source: Sequence[Tuple[float, float]],
        destination: Sequence[Tuple[float, float]]
    ) -> List[float]:
        """Calcula os coeficientes que mapeiam o destino de volta à origem."""
        matrix = []
        for (source_x, source_y), (dest_x, dest_y) in zip(source, destination):
            matrix.append([
                dest_x, dest_y, 1, 0, 0, 0,
                -source_x * dest_x, -source_x * dest_y, source_x
            ])
            matrix.append([
                0, 0, 0, dest_x, dest_y, 1,
                -source_y * dest_x, -source_y * dest_y, source_y
            ])
        return ImageEffectProcessor._solve_linear_system(matrix)

    @staticmethod
    def apply_perspective_distortion(
        image: Image.Image,
        camera_elevation: float,
        horizontal_angle: float = 0.0
    ) -> Image.Image:
        """
        Simula uma placa observada por uma câmera instalada acima do veículo.

        ``camera_elevation`` representa a inclinação vertical da câmera em graus.
        ``horizontal_angle`` adiciona uma pequena visão lateral, também em graus.
        O tamanho final da imagem é preservado.
        """
        elevation = max(0.0, min(75.0, float(camera_elevation)))
        horizontal = max(-45.0, min(45.0, float(horizontal_angle)))
        if elevation == 0 and horizontal == 0:
            return image.copy()

        width, height = image.size
        max_x = float(width - 1)
        max_y = float(height - 1)

        elevation_factor = math.sin(math.radians(elevation))
        horizontal_factor = math.sin(math.radians(horizontal))

        # A vista superior comprime a placa verticalmente. O trapézio deixa a
        # borda superior ligeiramente maior, pois ela está mais perto da câmera.
        vertical_scale = 1.0 - (0.35 * elevation_factor)
        transformed_height = max_y * vertical_scale
        top_y = (max_y - transformed_height) / 2.0
        bottom_y = top_y + transformed_height

        outer_margin = max_x * 0.025
        bottom_taper = max_x * (0.035 + 0.075 * elevation_factor)
        horizontal_shift = max_x * 0.08 * horizontal_factor
        vertical_skew = max_y * 0.12 * horizontal_factor

        destination = [
            (outer_margin + horizontal_shift, top_y - vertical_skew),
            (max_x - outer_margin + horizontal_shift, top_y + vertical_skew),
            (
                max_x - outer_margin - bottom_taper - horizontal_shift,
                bottom_y + vertical_skew
            ),
            (
                outer_margin + bottom_taper - horizontal_shift,
                bottom_y - vertical_skew
            )
        ]
        source = [
            (0.0, 0.0),
            (max_x, 0.0),
            (max_x, max_y),
            (0.0, max_y)
        ]
        coefficients = ImageEffectProcessor._perspective_coefficients(
            source, destination
        )
        fill_color = image.getpixel((0, height - 1))

        return image.transform(
            image.size,
            Image.Transform.PERSPECTIVE,
            coefficients,
            resample=Image.Resampling.BICUBIC,
            fillcolor=fill_color
        )

    @staticmethod
    def apply_rotation(image: Image.Image, angle: float) -> Image.Image:
        """Aplica uma pequena rotação óptica preservando o tamanho da imagem."""
        if angle == 0:
            return image.copy()
        return image.rotate(
            angle,
            resample=Image.Resampling.BICUBIC,
            expand=False,
            fillcolor=image.getpixel((0, image.height - 1))
        )

    @staticmethod
    def apply_3d_perspective(
        image: Image.Image,
        pitch: float = 0.0,
        yaw: float = 0.0,
        roll: float = 0.0,
        focal_length: float = 1.0
    ) -> Image.Image:
        """
        Aplica transformação 3D completa (pitch, yaw, roll) com projeção
        perspectiva, substituindo a antiga perspectiva 2D + rotação.

        Parâmetros:
            pitch   : Rotação em torno do eixo X (inclinação para frente/trás) em graus.
            yaw     : Rotação em torno do eixo Y (giro lateral) em graus.
            roll    : Rotação em torno do eixo Z (rotação no plano) em graus.
            focal_length : Distância focal relativa (1.0 = natural, >1 = teleobjectiva,
                           <1 = grande angular).
        """
        if pitch == 0.0 and yaw == 0.0 and roll == 0.0:
            return image.copy()

        width, height = image.size
        half_w = width / 2.0
        half_h = height / 2.0

        # Cantos da imagem original
        src = [(0, 0), (width, 0), (width, height), (0, height)]

        # Cantos em 3D centrados na origem
        corners_3d = [
            (-half_w, -half_h, 0.0),
            ( half_w, -half_h, 0.0),
            ( half_w,  half_h, 0.0),
            (-half_w,  half_h, 0.0),
        ]

        # Matriz de rotação combinada: R = Rz(roll) @ Ry(yaw) @ Rx(pitch)
        pitch_r = math.radians(pitch)
        yaw_r = math.radians(yaw)
        roll_r = math.radians(roll)

        cp, sp = math.cos(pitch_r), math.sin(pitch_r)
        cy, sy = math.cos(yaw_r),   math.sin(yaw_r)
        cr, sr = math.cos(roll_r),  math.sin(roll_r)

        # pylint: disable=line-too-long
        # R = [[cy*cr + sp*sy*sr,  -cy*sr + sp*sy*cr,  cp*sy],
        #      [cp*sr,             cp*cr,              -sp   ],
        #      [-sy*cr + sp*cy*sr, sy*sr + sp*cy*cr,   cp*cy ]]
        # pylint: enable=line-too-long

        # Aplicando Rz @ Ry @ Rx
        R11 = cy * cr + sp * sy * sr
        R12 = -cy * sr + sp * sy * cr
        R13 = cp * sy
        R21 = cp * sr
        R22 = cp * cr
        R23 = -sp
        R31 = -sy * cr + sp * cy * sr
        R32 = sy * sr + sp * cy * cr
        R33 = cp * cy

        # Projeta cada canto 3D para 2D usando o modelo de câmera pinhole
        distance = max(width, height) * focal_length

        dst = []
        for p in corners_3d:
            xr = R11 * p[0] + R12 * p[1] + R13 * p[2]
            yr = R21 * p[0] + R22 * p[1] + R23 * p[2]
            zr = R31 * p[0] + R32 * p[1] + R33 * p[2]

            zc = zr + distance
            if zc <= 0:
                zc = 0.001

            x_proj = distance * xr / zc + half_w
            y_proj = distance * yr / zc + half_h
            dst.append((x_proj, y_proj))

        # Encontra a bounding box dos pontos projetados
        xs = [p[0] for p in dst]
        ys = [p[1] for p in dst]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        # Escala os pontos projetados para preencher a imagem de saída
        bbox_w = max_x - min_x
        bbox_h = max_y - min_y
        scale_x = (width - 1) / bbox_w if bbox_w > 0 else 1.0
        scale_y = (height - 1) / bbox_h if bbox_h > 0 else 1.0

        dst_scaled = [
            ((p[0] - min_x) * scale_x, (p[1] - min_y) * scale_y)
            for p in dst
        ]

        # Calcula os coeficientes da transformação perspectiva
        coeffs = ImageEffectProcessor._perspective_coefficients(src, dst_scaled)

        # Cor de preenchimento (cantos inferior esquerdo)
        fill_color = image.getpixel((0, height - 1))

        return image.transform(
            image.size,
            Image.Transform.PERSPECTIVE,
            coeffs,
            resample=Image.Resampling.BICUBIC,
            fillcolor=fill_color
        )

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