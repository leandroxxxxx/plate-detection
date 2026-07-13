import os
import json
import random
from PIL import ImageOps
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


def apply_plate_border(image, border_config):
    """Adiciona uma borda à placa com tamanho percentual e cor configuráveis."""
    size_percent = border_config.get("size_percent", 0)
    color = border_config.get("color", [128, 128, 128])

    if size_percent < 0:
        raise ValueError("'plate_border.size_percent' deve ser maior ou igual a 0.")
    if not isinstance(color, list) or len(color) != 3:
        raise ValueError("'plate_border.color' deve ser uma lista RGB com 3 valores.")
    if any(not 0 <= channel <= 255 for channel in color):
        raise ValueError("Cada valor de 'plate_border.color' deve estar entre 0 e 255.")

    border_size = int(round(min(image.size) * (size_percent / 100)))
    if border_size == 0:
        return image.copy(), {
            "size_percent": size_percent,
            "size_pixels": border_size,
            "color": color
        }

    bordered_image = ImageOps.expand(
        image,
        border=border_size,
        fill=tuple(color)
    )
    return bordered_image, {
        "size_percent": size_percent,
        "size_pixels": border_size,
        "color": color
    }


def main():
    # Carrega dados de entrada do arquivo JSON
    input_path = os.path.join('data', 'inputs.json')
    with open(input_path, 'r') as f:
        inputs = json.load(f)

    num_plates = inputs.get("num_plates", 1)
    versions_per_plate = inputs.get("versions_per_plate", 1)
    seed = inputs.get("seed", None)
    effects = inputs.get("effects", {})
    plate_border_config = inputs.get("plate_border", {})
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
        final_image, plate_border = apply_plate_border(
            final_image,
            plate_border_config
        )
        
        for version in range(1, versions_per_plate + 1):
            persp_3d_cfg = effects.get("perspective_3d", {})
            pitch = random_value(
                persp_3d_cfg, "pitch", 0, effects_rng
            )
            yaw = random_value(
                persp_3d_cfg, "yaw", 0, effects_rng
            )
            roll = random_value(
                persp_3d_cfg, "roll", 0, effects_rng
            )
            focal_length = random_value(
                persp_3d_cfg, "focal_length", 1.0, effects_rng
            )

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
                f"3d(pitch={pitch:.2f}, yaw={yaw:.2f}, roll={roll:.2f}, "
                f"focal={focal_length:.2f}), "
                f"blur(angle={angle:.2f}, intensity={blur_intensity}), "
                f"sharpening={sharp_percent}, noise={noise_intensity:.4f}, "
                f"h264={degradation_level}"
            )

            # Aplica transformação 3D (pitch, yaw, roll) antes dos demais efeitos
            processed_image = ImageEffectProcessor.apply_3d_perspective(
                final_image,
                pitch=pitch,
                yaw=yaw,
                roll=roll,
                focal_length=focal_length
            )
            processed_image = ImageEffectProcessor.apply_motion_blur(
                processed_image, angle=angle, intensity=blur_intensity
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
                "plate_border": plate_border,
                "perspective_3d": {
                    "pitch": pitch,
                    "yaw": yaw,
                    "roll": roll,
                    "focal_length": focal_length
                },
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