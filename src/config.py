from dataclasses import dataclass, field
from typing import Tuple

@dataclass
class WatermarkConfig:
    text: str = "MERCOSUL BRASIL"
    font_size: int = 2.6 #15
    color: Tuple[int, int, int, int] = (180, 180, 180, 50)
    gap_x: int = 2.6 #15
    gap_y: int = 2.6 #15
    rotation: int = 45

@dataclass
class PlateConfig:
    width: int = 75 #520
    height: int = 25 #130
    bg_color: Tuple[int, int, int, int] = (200, 200, 200, 255)
    font_path: str = "fonts/FE-Schrift.ttf"
    font_size: int = 14 #100
    text_spacing: int = 1.44 #100
    watermark: WatermarkConfig = field(default_factory=WatermarkConfig)
