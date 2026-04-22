# -*- coding: utf-8 -*-
"""Testy pytest dla klasy Product.
Uruchomienie: pytest test_product_pytest.py -v
"""
import pytest
from product import Product


# --- Fixture ---
@pytest.fixture
def product():
    """Tworzy instancje Product do testow (odpowiednik setUp)."""
    return Product("Laptop", 2999.99, 10)


# --- Testy z fixture ---
def test_is_available(product):
    """Sprawdz dostepnosc produktu."""
    assert product.is_available() == True


def test_total_value(product):
    """Sprawdz wartosc calkowita."""
    assert product.total_value() == pytest.approx(29999.90)


@pytest.mark.parametrize("amount, expected_quantity", [
    (5, 15),      
    (0, 10),      
    (100, 110),   
    (1, 11),      
])
def test_add_stock_parametrized(product, amount, expected_quantity):
    """Testuje add_stock z roznymi wartosciami."""
    product.add_stock(amount)
    assert product.quantity == expected_quantity


# --- Testy bledow ---
def test_remove_stock_too_much_raises(product):
    """Sprawdz, czy proba usuniecia za duzej ilosci rzuca ValueError."""
    with pytest.raises(ValueError):
        product.remove_stock(20)


def test_add_stock_negative_raises(product):
    """Sprawdz, czy ujemna wartosc w add_stock rzuca ValueError."""
    with pytest.raises(ValueError):
        product.add_stock(-5)


@pytest.fixture
def discount_product():
    """Produkt z okragla cena 100.0 dla czytelnych testow rabatu."""
    return Product("Ksiazka", 100.0, 5)


@pytest.mark.parametrize("percent, expected_price", [
    (0, 100.0),      
    (50, 50.0),      
    (100, 0.0),      
    (25, 75.0),      
    (10, 90.0),      
])
def test_apply_discount(discount_product, percent, expected_price):
    """Sprawdza poprawne obliczenie rabatu dla roznych procentow."""
    discount_product.apply_discount(percent)
    assert discount_product.price == pytest.approx(expected_price)


@pytest.mark.parametrize("invalid_percent", [-1, -50, 101, 150])
def test_apply_discount_invalid_raises(discount_product, invalid_percent):
    """Sprawdza, czy niepoprawny procent rzuca ValueError."""
    with pytest.raises(ValueError):
        discount_product.apply_discount(invalid_percent)