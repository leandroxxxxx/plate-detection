"""
Script para extrair cortes de pares de caracteres de imagens de placas.

Para cada placa gerada, ele extrai retângulos de 2 em 2 caracteres.
Exemplo: placa "AOX5G10" gera os cortes: "AO", "OX", "X5", "5G", "G1", "10"

Uso:
    python -m src.crop_plates
    python -m src.crop_plates --input-dir generated-images --output-dir crop-output
"""

import os
import re
import argparse
from PIL import Image, ImageDraw, ImageFont

from .config import PlateConfig, CropConfig
from .utils import TextUtils


def extract_plate_text_from_filename(filename: str) -> str | None:
    """
    Extrai o texto da placa do nome do arquivo.
    Ex: 'placa_AOX5G10_h264_lvl0.jpg' -> 'AOX5G10'
    """
    match = re.search(r'placa_([A-Z0-9]+)_h264', filename)
    if match:
        return match.group(1)
    
    match = re.search(r'placa_([A-Z0-9]+)\.', filename)
    if match:
        return match.group(1)
    
    return None


def get_character_positions(
    text: str,
    font_path: str,
    font_size: int,
    text_spacing: int,
    plate_width: int,
    plate_height: int
) -> list[tuple[int, int, int, int]]:
    """
    Calcula a posição (x, y, w, h) de cada caractere na placa,
    replicando a lógica de posicionamento de PlateGenerator.

    Retorna uma lista de tuplas (x, y, largura, altura) para cada caractere.
    """
    font = ImageFont.truetype(font_path, font_size)
    
    # Cria uma imagem dummy para medir
    dummy_img = Image.new('RGBA', (plate_width, plate_height), (0, 0, 0, 0))
    dummy_draw = ImageDraw.Draw(dummy_img)
    
    # Altura da faixa azul (1/4 da altura)
    header_height = plate_height // 4
    
    # Largura total do texto
    total_text_width = TextUtils.get_total_text_width(font, text, text_spacing, dummy_draw)
    
    # Posição inicial x (centralizado)
    start_x = (plate_width - total_text_width) / 2
    
    # Altura do caractere
    _, char_height = TextUtils.get_char_size(font, "A", dummy_draw)
    
    # Posição y (centralizado abaixo da faixa azul)
    start_y = header_height + (plate_height - header_height - char_height) / 2
    
    positions = []
    current_x = start_x
    
    for char in text:
        w, h = TextUtils.get_char_size(font, char, dummy_draw)
        positions.append((current_x, start_y, w, h))
        current_x += w + text_spacing
    
    return positions


def crop_character_pairs(
    image: Image.Image,
    plate_text: str,
    plate_config: PlateConfig,
    crop_config: CropConfig
) -> list[tuple[str, Image.Image]]:
    """
    Extrai cortes de pares de caracteres de uma imagem de placa.

    Para cada par de caracteres consecutivos (i, i+1) do texto da placa,
    calcula um retângulo de corte centrado no ponto médio entre os dois
    caracteres, com dimensões definidas em porcentagem no CropConfig.

    Retorna uma lista de tuplas (par_texto, imagem_cortada).
    """
    positions = get_character_positions(
        plate_text,
        plate_config.font_path,
        plate_config.font_size,
        plate_config.text_spacing,
        plate_config.width,
        plate_config.height
    )
    
    img_width, img_height = image.size
    
    # Dimensões do retângulo de corte em pixels
    crop_w = int(img_width * crop_config.width_percent / 100.0)
    crop_h = int(img_height * crop_config.height_percent / 100.0)
    
    crops = []
    
    # Itera sobre pares de caracteres: (0,1), (1,2), (2,3), ...
    for i in range(len(plate_text) - 1):
        pair_text = plate_text[i:i+2]
        
        # Centro do caractere i
        cx_i = positions[i][0] + positions[i][2] / 2.0
        # Centro do caractere i+1
        cx_j = positions[i+1][0] + positions[i+1][2] / 2.0
        # Ponto médio entre os dois caracteres
        mid_x = (cx_i + cx_j) / 2.0
        
        # Calcula centro y (altura do texto)
        cy = positions[i][1] + positions[i][3] / 2.0
        
        # Converte coordenadas relativas à imagem real
        scale_x = img_width / plate_config.width
        scale_y = img_height / plate_config.height
        
        mid_x_px = mid_x * scale_x
        cy_px = cy * scale_y
        
        # Calcula os cantos do retângulo de corte
        left = int(mid_x_px - crop_w / 2)
        top = int(cy_px - crop_h / 2)
        right = left + crop_w
        bottom = top + crop_h
        
        # Garante que não ultrapasse os limites da imagem
        left = max(0, left)
        top = max(0, top)
        right = min(img_width, right)
        bottom = min(img_height, bottom)
        
        # Ajusta para manter o crop_w/crop_h se possível
        # Se o crop encostou na borda esquerda ou direita, reposiciona
        if left == 0:
            right = min(crop_w, img_width)
        elif right == img_width:
            left = max(0, img_width - crop_w)
        
        if top == 0:
            bottom = min(crop_h, img_height)
        elif bottom == img_height:
            top = max(0, img_height - crop_h)
        
        cropped = image.crop((left, top, right, bottom))
        crops.append((pair_text, cropped))
    
    return crops


def process_plate_image(
    image_path: str,
    output_dir: str,
    plate_config: PlateConfig,
    crop_config: CropConfig,
    dry_run: bool = False
) -> list[str]:
    """
    Processa uma única imagem de placa: extrai os pares e salva os cortes.

    Retorna uma lista com os caminhos dos arquivos gerados.
    """
    filename = os.path.basename(image_path)
    plate_text = extract_plate_text_from_filename(filename)
    
    if plate_text is None:
        print(f"  ⚠  Não foi possível extrair o texto da placa de: {filename}")
        return []
    
    print(f"\n  Placa: {plate_text}")
    print(f"  Pares: ", end="")
    for i in range(len(plate_text) - 1):
        print(f"'{plate_text[i:i+2]}'", end=" ")
    print()
    
    if dry_run:
        return []
    
    image = Image.open(image_path).convert('RGB')
    
    crops = crop_character_pairs(image, plate_text, plate_config, crop_config)
    
    # Cria subdiretório de saída para esta placa
    plate_name = os.path.splitext(filename)[0]
    plate_output_dir = os.path.join(output_dir, plate_name)
    os.makedirs(plate_output_dir, exist_ok=True)
    
    saved_files = []
    for pair_text, cropped_img in crops:
        output_filename = f"{plate_name}_{crop_config.file_suffix}_{pair_text}.jpg"
        output_path = os.path.join(plate_output_dir, output_filename)
        cropped_img.save(output_path, 'JPEG')
        saved_files.append(output_path)
        print(f"    → Salvo: {output_filename} (tamanho: {cropped_img.size})")
    
    return saved_files


def main():
    parser = argparse.ArgumentParser(
        description="Extrai cortes de pares de caracteres de imagens de placas."
    )
    parser.add_argument(
        '--input-dir',
        type=str,
        default='generated-images',
        help='Diretório com as imagens de placas (default: generated-images)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Diretório de saída para os cortes (default: <input-dir>/crops)'
    )
    parser.add_argument(
        '--pattern',
        type=str,
        default='*.jpg',
        help='Padrão de arquivo para buscar (default: *.jpg)'
    )
    parser.add_argument(
        '--width-percent',
        type=float,
        default=None,
        help='Sobrescreve a largura do corte em porcentagem da largura da placa'
    )
    parser.add_argument(
        '--height-percent',
        type=float,
        default=None,
        help='Sobrescreve a altura do corte em porcentagem da altura da placa'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Apenas lista os pares sem gerar os cortes'
    )
    
    args = parser.parse_args()
    
    input_dir = args.input_dir
    if not os.path.isdir(input_dir):
        print(f"Erro: Diretório '{input_dir}' não encontrado.")
        return
    
    output_dir = args.output_dir or os.path.join(input_dir, "crops")
    
    # Configurações
    plate_config = PlateConfig()
    crop_config = CropConfig()
    
    if args.width_percent is not None:
        crop_config.width_percent = args.width_percent
    if args.height_percent is not None:
        crop_config.height_percent = args.height_percent
    
    print("=" * 60)
    print("CORTE DE PARES DE CARACTERES DE PLACAS")
    print("=" * 60)
    print(f"\nConfigurações:")
    print(f"  Diretório de entrada: {input_dir}")
    print(f"  Diretório de saída:   {output_dir}")
    print(f"  Largura do corte:     {crop_config.width_percent}% da placa")
    print(f"  Altura do corte:      {crop_config.height_percent}% da placa")
    print(f"  Tamanho da placa:     {plate_config.width}x{plate_config.height}")
    print(f"  Dry-run:              {'Sim' if args.dry_run else 'Não'}")
    
    # Busca arquivos de imagem
    import glob
    search_pattern = os.path.join(input_dir, args.pattern)
    image_files = sorted(glob.glob(search_pattern))
    
    if not image_files:
        print(f"\nNenhuma imagem encontrada em '{input_dir}' com padrão '{args.pattern}'.")
        return
    
    print(f"\nImagens encontradas: {len(image_files)}")
    
    if not args.dry_run:
        os.makedirs(output_dir, exist_ok=True)
    
    total_crops = 0
    for img_path in image_files:
        saved = process_plate_image(
            img_path,
            output_dir,
            plate_config,
            crop_config,
            args.dry_run
        )
        total_crops += len(saved)
    
    print("\n" + "=" * 60)
    if args.dry_run:
        print(f"Dry-run concluído. {len(image_files)} imagem(ns) analisada(s).")
    else:
        print(f"Processamento concluído!")
        print(f"  Imagens processadas: {len(image_files)}")
        print(f"  Total de cortes gerados: {total_crops}")
        print(f"  Cortes salvos em: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()