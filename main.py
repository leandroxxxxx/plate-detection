import os
from src.config import PlateConfig
from src.plate import PlateGenerator

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

    # Salvamento
    output_dir = 'generated-images'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'placa.jpg')

    final_image.save(output_path, 'JPEG')
    print(f"Imagem salva em: {output_path}")

if __name__ == "__main__":
    main()
