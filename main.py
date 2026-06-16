import os
import json
from src.config import PlateConfig
from src.plate import PlateGenerator
from src.plate_generator import RandomPlateGenerator
from src.post_process import ImageEffectProcessor

def main():
    # Carrega dados de entrada do arquivo JSON
    input_path = os.path.join('data', 'inputs.json')
    with open(input_path, 'r') as f:
        inputs = json.load(f)

    num_plates = inputs.get("num_plates", 1)
    seed = inputs.get("seed", None)
    degradation_levels = inputs.get("degradation_levels", [])
    effects = inputs.get("effects", {})
    base_output_dir = inputs.get("output_dir", "generated-images")
    output_dir = os.path.join(base_output_dir, "plates")

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

    for plate_text in plates_data:
        # Geração
        print(f"\n--- Processando placa: {plate_text} ---")
        final_image = generator.create_plate(plate_text)
        
        # Aplica Motion Blur (Movimento)
        mb_cfg = effects.get("motion_blur", {})
        print("Aplicando Motion Blur...")
        blurred_image = ImageEffectProcessor.apply_motion_blur(
            final_image,
            angle=mb_cfg.get("angle", 0),
            intensity=mb_cfg.get("intensity", 0)
        )
        
        # Aplica Sharpening (O realce artificial da câmera)
        sharp_cfg = effects.get("sharpening", {})
        print("Aplicando Realce de Câmera (Sharpening)...")
        sharpened_image = ImageEffectProcessor.apply_cctv_sharpening(blurred_image, percent=sharp_cfg.get("percent", 100))
        
        # Aplica Noise (Ruído)
        noise_cfg = effects.get("noise", {})
        print("Aplicando Ruído...")
        noisy_image = ImageEffectProcessor.apply_noise(sharpened_image, intensity=noise_cfg.get("intensity", 0))
        
        # # Salva original (comentado: apenas versões com degradação são geradas)
        # output_path = os.path.join(output_dir, f'placa_{plate_text}_h264_lvl0.jpg')
        # final_image.save(output_path, 'JPEG')
        # print(f"Imagem original salva em: {output_path}")

        # Itera sobre os níveis de degradação
        for level in degradation_levels:
            # Aplica simulação de H.264 (Degradação)
            print(f"Gerando versão H.264 (Nível {level})...")
            h264_image = ImageEffectProcessor.apply_h264_simulation(noisy_image, level)
            
            # resized_image = ImageEffectProcessor.resize_image(h264_image, [128,32])

            # Salva modificada com o nível no nome do arquivo
            output_h264_path = os.path.join(output_dir, f'placa_{plate_text}_h264_lvl{level}.jpg')
            h264_image.save(output_h264_path, 'JPEG')
            print(f"Imagem H.264 (Nível {level}) salva em: {output_h264_path}")

if __name__ == "__main__":
    main()
