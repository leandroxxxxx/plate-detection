"""
Script para extrair cortes de pares de caracteres de imagens de placas.

Para cada placa gerada, ele extrai retângulos de 2 em 2 caracteres.
Exemplo: placa "ABC" gera os cortes: "AB", "BC"

Uso:
    python -m src.crop_plates
    python -m src.crop_plates --input-dir generated-images --output-dir crop-output
"""

import os
import re
import sys
import json
import argparse
from PIL import Image

# Ensure the project root is in sys.path so absolute imports work
# when running this script directly with `python src/crop_plates.py`
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import CropConfig


def extract_plate_text_from_filename(filename: str) -> str | None:
    """
    Extrai o texto da placa do nome do arquivo.
    Ex: 'char2_AB_v01.jpg' -> 'AB'
    Ex: 'char3_ABC_v01.jpg' -> 'ABC'
    """
    match = re.search(r'char\d+_([A-Z0-9]+)_v\d+', filename)
    if match:
        return match.group(1)
    
    return None


def crop_character_pairs(
    image: Image.Image,
    plate_text: str,
    manual_crop_config: dict
) -> list[tuple[str, Image.Image, dict]]:
    """
    Extrai cortes manuais de pares de caracteres de uma imagem de placa.

    As coordenadas são lidas diretamente da configuração. Se o tamanho da
    imagem mudar, a configuração também deve ser atualizada.

    Retorna tuplas (par_texto, imagem_cortada, caixa_de_corte).
    """
    img_width, img_height = image.size

    crop_w = int(manual_crop_config.get("width", 24))
    crop_h = int(manual_crop_config.get("height", 17))
    crop_y = int(manual_crop_config.get("y", 16))
    x_positions = manual_crop_config.get("x_positions", [])

    if crop_w <= 0 or crop_h <= 0:
        raise ValueError("'manual_crop.width' e 'manual_crop.height' devem ser maiores que 0.")
    if not isinstance(x_positions, list):
        raise ValueError("'manual_crop.x_positions' deve ser uma lista de posições X.")

    expected_pairs = len(plate_text) - 1
    if len(x_positions) < expected_pairs:
        raise ValueError(
            "'manual_crop.x_positions' não possui posições suficientes para "
            f"{expected_pairs} pares."
        )

    crops = []

    # Itera sobre pares de caracteres: (0,1), (1,2), (2,3), ...
    for i in range(len(plate_text) - 1):
        pair_text = plate_text[i:i+2]

        left = int(x_positions[i])
        top = crop_y
        right = left + crop_w
        bottom = top + crop_h

        if left < 0 or top < 0 or right > img_width or bottom > img_height:
            raise ValueError(
                f"Corte manual fora dos limites da imagem para o par '{pair_text}': "
                f"({left}, {top}, {right}, {bottom}) em imagem {img_width}x{img_height}."
            )

        cropped = image.crop((left, top, right, bottom))
        crop_box = {
            "x": left,
            "y": top,
            "width": crop_w,
            "height": crop_h
        }
        crops.append((pair_text, cropped, crop_box))

    return crops


def process_plate_image(
    image_path: str,
    output_dir: str,
    crop_config: CropConfig,
    dry_run: bool = False,
    labels_dir: str | None = None,
    manual_crop_config: dict | None = None
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

    crops = crop_character_pairs(image, plate_text, manual_crop_config or {})
    
    # # Cria subdiretório de saída para esta placa (comentado: salva tudo na pasta crop)
    # plate_name = os.path.splitext(filename)[0]
    # plate_output_dir = os.path.join(output_dir, plate_name)
    # os.makedirs(plate_output_dir, exist_ok=True)
    
    saved_files = []
    plate_name = os.path.splitext(filename)[0]
    for pair_index, (pair_text, cropped_img, crop_box) in enumerate(crops, start=1):
        file_suffix = crop_config.file_suffix.strip("_")
        output_stem = f"{plate_name}_{file_suffix}_{pair_index:02d}_{pair_text}"
        output_filename = f"{output_stem}.jpg"
        output_path = os.path.join(output_dir, output_filename)
        cropped_img.save(output_path, 'JPEG')
        saved_files.append(output_path)
        print(
            f"    → Salvo: {output_filename} (tamanho: {cropped_img.size})"
        )

        if labels_dir is not None:
            label_path = os.path.join(labels_dir, f"{output_stem}.json")
            label = {
                "source_image": filename,
                "plate": plate_text,
                "pair": pair_text,
                "pair_index": pair_index,
                "crop_box": crop_box
            }
            with open(label_path, "w", encoding="utf-8") as label_file:
                json.dump(label, label_file, ensure_ascii=False, indent=4)
    
    return saved_files


def main():
    parser = argparse.ArgumentParser(
        description="Extrai cortes de pares de caracteres de imagens de placas."
    )
    parser.add_argument(
        '--config',
        type=str,
        default='data/inputs.json',
        help='Arquivo com ranges e seed (default: data/inputs.json)'
    )
    parser.add_argument(
        '--input-dir',
        type=str,
        default='generated-images/plates',
        help='Diretório com as imagens de placas (default: generated-images/plates)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Diretório de saída para os cortes (default: <input-dir>/crops)'
    )
    parser.add_argument(
        '--labels-dir',
        type=str,
        default=None,
        help='Diretório das labels (default: <input-dir>/../crop-labels)'
    )
    parser.add_argument(
        '--pattern',
        type=str,
        default='*.jpg',
        help='Padrão de arquivo para buscar (default: *.jpg)'
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
    
    output_dir = args.output_dir or os.path.join(os.path.dirname(input_dir), "crop")
    labels_dir = args.labels_dir or os.path.join(
        os.path.dirname(input_dir), "crop-labels"
    )

    with open(args.config, "r", encoding="utf-8") as config_file:
        inputs = json.load(config_file)
    manual_crop_config = inputs.get("manual_crop", {})
    
    # Configurações
    crop_config = CropConfig()
    
    print("=" * 60)
    print("CORTE DE PARES DE CARACTERES DE PLACAS")
    print("=" * 60)
    print(f"\nConfigurações:")
    print(f"  Diretório de entrada: {input_dir}")
    print(f"  Diretório de saída:   {output_dir}")
    print(f"  Diretório de labels:  {labels_dir}")
    print(f"  Corte manual:         {manual_crop_config}")
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
        os.makedirs(labels_dir, exist_ok=True)
    
    total_crops = 0
    for img_path in image_files:
        saved = process_plate_image(
            img_path,
            output_dir,
            crop_config,
            args.dry_run,
            labels_dir,
            manual_crop_config
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
