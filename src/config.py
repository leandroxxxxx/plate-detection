from dataclasses import dataclass, field
from typing import Tuple

@dataclass
class WatermarkConfig:
    text: str = "MERCOSUL BRASIL"
    # font_size: int = 15
    font_size: int = 2.6
    color: Tuple[int, int, int, int] = (180, 180, 180, 50)
    # gap_x: int = 15
    # gap_y: int = 15
    gap_x: int = 2.6 
    gap_y: int = 2.6 
    rotation: int = 45

@dataclass
class PlateConfig:
    # width: int = 520
    # height: int = 130
    width: int = 40
    height: int = 25
    bg_color: Tuple[int, int, int, int] = (200, 200, 200, 255)
    header_color: Tuple[int, int, int, int] = (0, 51, 153, 255) # Azul Mercosul
    text_color: Tuple[int, int, int, int] = (28, 28, 28, 255)
    font_path: str = "fonts/FE-Schrift.ttf"
    # font_size: int = 90
    # text_spacing: int = 9
    font_size: int = 14
    text_spacing: int = 1.44
    watermark: WatermarkConfig = field(default_factory=WatermarkConfig)

@dataclass
class CropConfig:
    """
    Configuração para o corte de pares de caracteres das imagens de placas.

    Attributes:
        width_percent: Largura do retângulo de corte em porcentagem da largura total da placa.
                       Ex: 30 significa 30% da largura da placa.
        height_percent: Altura do retângulo de corte em porcentagem da altura total da placa.
                        Ex: 100 significa 100% (altura total).
        output_subdir: Subdiretório dentro do diretório de saída para salvar os cortes.
        file_suffix: Sufixo adicionado ao nome do arquivo original para identificar cortes.
    """
    width_percent: float = 28
    height_percent: float = 100.0
    offset_x: int = 2
    output_subdir: str = "crops"
    file_suffix: str = "_pair"