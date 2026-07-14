import random
from typing import List, Optional

# Letras permitidas no padrão Mercosul (exclui I, O, Q, U para evitar confusão visual)
ALLOWED_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DIGITS = "0123456789"

# Caracteres permitidos
ALLOWED_CHARS = ALLOWED_LETTERS + DIGITS


class RandomPlateGenerator:
    """Gera strings de caracteres (1, 2, 3+ caracteres) para placas Mercosul."""

    def __init__(self, seed: Optional[int] = None, num_chars: int = 2):
        self.seed = seed
        self.num_chars = num_chars
        if seed is not None:
            random.seed(seed)

    def generate_string(self) -> str:
        """Gera uma string aleatória com ``num_chars`` caracteres."""
        return "".join(random.choice(ALLOWED_CHARS) for _ in range(self.num_chars))

    def generate_plate(self) -> str:
        """Mantido por compatibilidade: gera uma única string."""
        return self.generate_string()

    def generate_plates(self, count: int) -> List[str]:
        """Gera uma lista de strings únicas."""
        strings: set = set()
        attempts = 0
        max_attempts = count * 10  # Evita loop infinito caso o espaço seja muito pequeno

        while len(strings) < count and attempts < max_attempts:
            strings.add(self.generate_string())
            attempts += 1

        if len(strings) < count:
            print(f"Aviso: Só foi possível gerar {len(strings)} strings únicas de {count} solicitadas.")

        return sorted(list(strings))

    @staticmethod
    def total_possible_strings(num_chars: int) -> int:
        """Calcula o número total de combinações possíveis para N caracteres."""
        return len(ALLOWED_CHARS) ** num_chars