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
    
    # Redimensiona (Resize)
    target_size = (145, 48)
    print(f"Redimensionando para {target_size}...")
    resized_image = ImageEffectProcessor.resize_image(final_image, target_size)
    
    # Aplica simulação de H.264 (Degradação)
    degradation_level = 150
    print(f"Gerando versão H.264 (Nível {degradation_level})...")
    h264_image = ImageEffectProcessor.apply_h264_simulation(resized_image, degradation_level)
    
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
