"""Moduł z klasą Product reprezentującą produkt w sklepie internetowym."""


class Product:
    """Reprezentuje produkt w sklepie internetowym."""

    def __init__(self, name: str, price: float, quantity: int):
        if price < 0:
            raise ValueError("Cena nie może być ujemna")
        if quantity < 0:
            raise ValueError("Ilość nie może być ujemna")

        self.name = name
        self.price = price
        self.quantity = quantity

    def add_stock(self, amount: int):
        """Dodaje określoną ilość do magazynu."""
        if amount < 0:
            raise ValueError("Nie można dodać ujemnej ilości")
        self.quantity += amount

    def remove_stock(self, amount: int):
        """Usuwa określoną ilość z magazynu."""
        if amount < 0:
            raise ValueError("Nie można usunąć ujemnej ilości")
        if amount > self.quantity:
            raise ValueError(
                f"Niewystarczająca ilość w magazynie "
                f"(dostępne: {self.quantity}, żądane: {amount})"
            )
        self.quantity -= amount

    def is_available(self) -> bool:
        """Zwraca True jeśli produkt jest dostępny (quantity > 0)."""
        return self.quantity > 0

    def total_value(self) -> float:
        """Zwraca całkowitą wartość produktu (price * quantity)."""
        return self.price * self.quantity

    def __repr__(self):
        return f"Product(name={self.name!r}, price={self.price}, quantity={self.quantity})"

    def apply_discount(self, percent: float):
        """Obniża cenę o podany procent (0-100)."""
        if percent < 0 or percent > 100:
            raise ValueError(f"Procent musi być w zakresie 0-100 (podano: {percent})")
        self.price = self.price * (1 - percent / 100)