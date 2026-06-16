import random
from typing import List, Optional

# Letras permitidas no padrão Mercosul (exclui I, O, Q, U para evitar confusão visual)
ALLOWED_LETTERS = "ABCDEFGHJKLMNPRSTVWXYZ"
DIGITS = "0123456789"

class RandomPlateGenerator:
    """Gera placas aleatórias no formato Mercosul LLLNLNN."""

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        if seed is not None:
            random.seed(seed)

    def generate_plate(self) -> str:
        """Gera uma única placa no formato LLLNLNN."""
        letters_part1 = "".join(random.choices(ALLOWED_LETTERS, k=3))
        digit1 = random.choice(DIGITS)
        letter2 = random.choice(ALLOWED_LETTERS)
        digits2 = "".join(random.choices(DIGITS, k=2))
        return f"{letters_part1}{digit1}{letter2}{digits2}"

    def generate_plates(self, count: int) -> List[str]:
        """Gera uma lista de placas únicas."""
        plates: set = set()
        attempts = 0
        max_attempts = count * 10  # Evita loop infinito caso o espaço seja muito pequeno

        while len(plates) < count and attempts < max_attempts:
            plates.add(self.generate_plate())
            attempts += 1

        if len(plates) < count:
            print(f"Aviso: Só foi possível gerar {len(plates)} placas únicas de {count} solicitadas.")

        return sorted(list(plates))

    @staticmethod
    def total_possible_plates() -> int:
        """Calcula o número total de combinações possíveis."""
        return len(ALLOWED_LETTERS) ** 4 * len(DIGITS) ** 3
