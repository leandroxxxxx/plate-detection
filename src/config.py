from dataclasses import dataclass
from typing import Tuple

@dataclass
class PlateConfig:
    width: int = 100
    height: int = 100
    bg_color: Tuple[int, int, int, int] = (200, 200, 200, 255)
    text_color: Tuple[int, int, int, int] = (28, 28, 28, 255)
    font_path: str = "fonts/FE-Schrift.ttf"
    font_size: int = 20
    text_spacing: int = 2

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