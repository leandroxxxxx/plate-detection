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
    plate_text = "ABC1D23"

    # Geração
    print(f"Gerando placa: {plate_text}...")
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
    
    # Aplica simulação de H.264 (Degradação)
    degradation_level = 520
    print(f"Gerando versão H.264 (Nível {degradation_level})...")
    h264_image = ImageEffectProcessor.apply_h264_simulation(noisy_image, degradation_level)
    
    # Salvamento
    output_dir = 'generated-images'
    os.makedirs(output_dir, exist_ok=True)

    # Salva original
    output_path = os.path.join(output_dir, 'placa.jpg')
    final_image.save(output_path, 'JPEG')
    print(f"Imagem original salva em: {output_path}")

    # Salva modificada
    output_h264_path = os.path.join(output_dir, 'placa_h264.jpg')
    h264_image.save(output_h264_path, 'JPEG')
    print(f"Imagem H.264 salva em: {output_h264_path}")

if __name__ == "__main__":
    main()
