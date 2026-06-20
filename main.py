import os
import json
import random
from src.config import PlateConfig
from src.plate import PlateGenerator
from src.plate_generator import RandomPlateGenerator
from src.post_process import ImageEffectProcessor


def random_value(config, key, default, rng, integer=False):
    """Sorteia um valor no ``<key>_range`` ou usa o padrão informado."""
    value_range = config.get(f"{key}_range")

    if value_range is None:
        return default
    if not isinstance(value_range, list) or len(value_range) != 2:
        raise ValueError(f"'{key}_range' deve ser uma lista com [mínimo, máximo].")

    minimum, maximum = value_range
    if minimum > maximum:
        raise ValueError(f"O mínimo de '{key}_range' não pode ser maior que o máximo.")

    if integer:
        return rng.randint(int(minimum), int(maximum))
    return rng.uniform(float(minimum), float(maximum))

def main():
    # Carrega dados de entrada do arquivo JSON
    input_path = os.path.join('data', 'inputs.json')
    with open(input_path, 'r') as f:
        inputs = json.load(f)

    num_plates = inputs.get("num_plates", 1)
    versions_per_plate = inputs.get("versions_per_plate", 1)
    seed = inputs.get("seed", None)
    effects = inputs.get("effects", {})
    base_output_dir = inputs.get("output_dir", "generated-images")
    output_dir = os.path.join(base_output_dir, "plates")
    labels_dir = os.path.join(base_output_dir, "labels")

    if not isinstance(versions_per_plate, int) or versions_per_plate < 1:
        raise ValueError("'versions_per_plate' deve ser um inteiro maior ou igual a 1.")

    # RNG separado do gerador de placas: a seed também torna os parâmetros
    # sorteados reproduzíveis entre execuções.
    effects_rng = random.Random(seed)

    # Gera placas aleatórias no formato Mercosul
    print(f"\n--- Gerando {num_plates} placas aleatórias (seed={seed}) ---")
    plate_generator = RandomPlateGenerator(seed=seed)
    plates_data = plate_generator.generate_plates(num_plates)
    print(f"Total de placas geradas: {len(plates_data)}")

    # Configuração da placa (padrão)
    config = PlateConfig()

    # Inicializa o gerador
    generator = PlateGenerator(config)

    # Salvamento
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(labels_dir, exist_ok=True)

    count = 1
    for plate_text in plates_data:
        # Geração
        print(f"\n--- Processando placa: {plate_text} ---")
        print(f"Nº: {count}")
        final_image = generator.create_plate(plate_text)
        
        for version in range(1, versions_per_plate + 1):
            mb_cfg = effects.get("motion_blur", {})
            angle = random_value(mb_cfg, "angle", 0, effects_rng)
            blur_intensity = random_value(
                mb_cfg, "intensity", 0, effects_rng, integer=True
            )

            sharp_cfg = effects.get("sharpening", {})
            sharp_percent = random_value(
                sharp_cfg, "percent", 100, effects_rng, integer=True
            )

            noise_cfg = effects.get("noise", {})
            noise_intensity = random_value(
                noise_cfg, "intensity", 0, effects_rng
            )

            h264_cfg = effects.get("h264", {})
            degradation_level = random_value(
                h264_cfg,
                "degradation_level",
                0,
                effects_rng,
                integer=True
            )
            degradation_level = max(0, degradation_level)

            print(
                f"Versão {version}/{versions_per_plate}: "
                f"blur(angle={angle:.2f}, intensity={blur_intensity}), "
                f"sharpening={sharp_percent}, noise={noise_intensity:.4f}, "
                f"h264={degradation_level}"
            )

            processed_image = ImageEffectProcessor.apply_motion_blur(
                final_image, angle=angle, intensity=blur_intensity
            )
            processed_image = ImageEffectProcessor.apply_cctv_sharpening(
                processed_image, percent=sharp_percent
            )
            processed_image = ImageEffectProcessor.apply_noise(
                processed_image, intensity=noise_intensity
            )

            h264_image = ImageEffectProcessor.apply_h264_simulation(
                processed_image, degradation_level
            )

            file_stem = f"placa_{plate_text}_v{version:02d}"
            output_image_path = os.path.join(output_dir, f"{file_stem}.jpg")
            output_label_path = os.path.join(labels_dir, f"{file_stem}.json")

            h264_image.save(output_image_path, "JPEG")

            applied_parameters = {
                "plate": plate_text,
                "version": version,
                "motion_blur": {
                    "angle": angle,
                    "intensity": blur_intensity
                },
                "sharpening": {
                    "percent": sharp_percent
                },
                "noise": {
                    "intensity": noise_intensity
                },
                "h264": {
                    "degradation_level": degradation_level
                }
            }
            with open(output_label_path, "w", encoding="utf-8") as label_file:
                json.dump(
                    applied_parameters,
                    label_file,
                    ensure_ascii=False,
                    indent=4
                )

            print(f"Imagem salva em: {output_image_path}")
            print(f"Label salvo em: {output_label_path}")
        count += 1

if __name__ == "__main__":
    main()
