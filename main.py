import os
from src.config import PlateConfig
from src.plate import PlateGenerator
from src.post_process import ImageEffectProcessor

def main():
    # Configuração
    config = PlateConfig()

    # Inicializa o gerador
    generator = PlateGenerator(config)

    # Dados de entrada
    plates_data = ["ABC1D23", "XYZ9W87", "9W", "XY"]
    degradation_levels = [520, 530, 540, 550] # Lista de níveis de degradação

    # Salvamento
    output_dir = 'generated-images'
    os.makedirs(output_dir, exist_ok=True)

    for plate_text in plates_data:
        # Geração
        print(f"\n--- Processando placa: {plate_text} ---")
        final_image = generator.create_plate(plate_text)
        
        # Aplica Motion Blur (Movimento)
        print("Aplicando Motion Blur...")
        blurred_image = ImageEffectProcessor.apply_motion_blur(final_image, angle=0, intensity=8)
        
        # Aplica Sharpening (O realce artificial da câmera)
        print("Aplicando Realce de Câmera (Sharpening)...")
        sharpened_image = ImageEffectProcessor.apply_cctv_sharpening(blurred_image, percent=200)
        
        # Aplica Noise (Ruído)
        print("Aplicando Ruído...")
        noisy_image = ImageEffectProcessor.apply_noise(sharpened_image, intensity=0.10)
        
        # Salva original
        output_path = os.path.join(output_dir, f'placa_{plate_text}_h264_lvl0.jpg')
        final_image.save(output_path, 'JPEG')
        print(f"Imagem original salva em: {output_path}")

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
