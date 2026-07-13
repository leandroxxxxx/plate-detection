import random
from typing import List, Optional

# Letras permitidas no padrão Mercosul (exclui I, O, Q, U para evitar confusão visual)
ALLOWED_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DIGITS = "0123456789"

# Caracteres permitidos para os pares: letras e dígitos
ALLOWED_CHARS = ALLOWED_LETTERS + DIGITS


class RandomPlateGenerator:
    """Gera pares de caracteres (combinações de 2 caracteres) para placas Mercosul."""

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        if seed is not None:
            random.seed(seed)

    def generate_pair(self) -> str:
        """Gera um par aleatório de 2 caracteres (letra+letra, letra+dígito, dígito+letra ou dígito+dígito)."""
        c1 = random.choice(ALLOWED_CHARS)
        c2 = random.choice(ALLOWED_CHARS)
        return f"{c1}{c2}"

    def generate_plate(self) -> str:
        """Mantido por compatibilidade: gera um único par de 2 caracteres."""
        return self.generate_pair()

    def generate_plates(self, count: int) -> List[str]:
        """Gera uma lista de pares únicos."""
        pairs: set = set()
        attempts = 0
        max_attempts = count * 10  # Evita loop infinito caso o espaço seja muito pequeno

        while len(pairs) < count and attempts < max_attempts:
            pairs.add(self.generate_pair())
            attempts += 1

        if len(pairs) < count:
            print(f"Aviso: Só foi possível gerar {len(pairs)} pares únicos de {count} solicitados.")

        return sorted(list(pairs))

    @staticmethod
    def total_possible_pairs() -> int:
        """Calcula o número total de combinações possíveis de pares."""
        return len(ALLOWED_CHARS) ** 2