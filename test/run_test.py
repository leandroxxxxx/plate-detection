import os
import sys
from PIL import Image

# Configuração de caminhos absolutos
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'src'))
sys.path.append(SRC_DIR)

try:
    from post_process import ImageEffectProcessor
except ImportError:
    print("Erro: Não foi possível importar 'post_process' da pasta 'src'.")
    sys.exit(1)

def main():
    # Nomes de arquivos baseados no seu diretório 'test/'
    input_path = os.path.join(SCRIPT_DIR, "original.jpg")
    output_path = os.path.join(SCRIPT_DIR, "test_processed.jpg")

    if not os.path.exists(input_path):
        print(f"Erro: Arquivo '{input_path}' não encontrado.")
        return

    try:
        print(f"Processando imagem: {input_path}")
        img = Image.open(input_path)

        # Aplicação dos filtros de degradação
        img = ImageEffectProcessor.apply_motion_blur(img, angle=15.0, intensity=5)
        img = ImageEffectProcessor.apply_cctv_sharpening(img, percent=180)
        img = ImageEffectProcessor.apply_low_dynamic_range(img, contrast=0.75)
        img = ImageEffectProcessor.apply_noise(img, intensity=0.05)
        img = ImageEffectProcessor.apply_h264_simulation(img, degradation_level=80)

        # Salva o resultado
        img.save(output_path, quality=90)
        print(f"Sucesso! Resultado salvo em: {output_path}")

    except Exception as e:
        print(f"Ocorreu um erro: {e}")

if __name__ == "__main__":
    main()
