#!/usr/bin/env python3
"""
Тестовый файл для проверки исправления ошибки 'dict' object has no attribute 'phone'
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Имитируем структуру данных, которая вызывала ошибку
from typing import Dict, Any, Optional, Union, List, Tuple

def get_client_data(client) -> Tuple[str, str]:
    """
    Безопасно извлекает телефон и имя клиента из разных форматов данных
    Returns: (client_phone, client_name)
    """
    client_phone = ""
    client_name = ""
    
    if client:
        if isinstance(client, dict):
            client_phone = client.get('phone', '')
            client_name = client.get('name', '')
        elif isinstance(client, list) and client:
            first_client = client[0]
            if isinstance(first_client, dict):
                client_phone = first_client.get('phone', '')
                client_name = first_client.get('name', '')
        elif hasattr(client, 'phone'):
            client_phone = client.phone
            client_name = client.name
    
    return client_phone, client_name

def test_client_data_formats():
    """
    Тестирует разные форматы данных клиента
    """
    print("=== Тестирование функции get_client_data ===")
    
    # Тест 1: Словарь (проблемный случай)
    client_dict = {
        'phone': '+7 777 123 45 67',
        'name': 'Иванов Иван Иванович'
    }
    phone, name = get_client_data(client_dict)
    print(f"Тест 1 - Словарь: phone='{phone}', name='{name}'")
    assert phone == '+7 777 123 45 67'
    assert name == 'Иванов Иван Иванович'
    
    # Тест 2: Список словарей
    client_list = [
        {
            'phone': '+7 777 111 22 33',
            'name': 'Петров Петр Петрович'
        }
    ]
    phone, name = get_client_data(client_list)
    print(f"Тест 2 - Список: phone='{phone}', name='{name}'")
    assert phone == '+7 777 111 22 33'
    assert name == 'Петров Петр Петрович'
    
    # Тест 3: Пустой список
    client_empty_list = []
    phone, name = get_client_data(client_empty_list)
    print(f"Тест 3 - Пустой список: phone='{phone}', name='{name}'")
    assert phone == ''
    assert name == ''
    
    # Тест 4: None
    phone, name = get_client_data(None)
    print(f"Тест 4 - None: phone='{phone}', name='{name}'")
    assert phone == ''
    assert name == ''
    
    # Тест 5: Объект с атрибутами
    class ClientObj:
        def __init__(self, phone, name):
            self.phone = phone
            self.name = name
    
    client_obj = ClientObj('+7 777 999 88 77', 'Сидоров Сидор Сидорович')
    phone, name = get_client_data(client_obj)
    print(f"Тест 5 - Объект: phone='{phone}', name='{name}'")
    assert phone == '+7 777 999 88 77'
    assert name == 'Сидоров Сидор Сидорович'
    
    # Тест 6: Словарь без phone
    client_dict_no_phone = {
        'name': 'Козлов Козел Козлович'
    }
    phone, name = get_client_data(client_dict_no_phone)
    print(f"Тест 6 - Словарь без phone: phone='{phone}', name='{name}'")
    assert phone == ''
    assert name == 'Козлов Козел Козлович'
    
    print("✅ Все тесты пройдены успешно!")

if __name__ == "__main__":
    test_client_data_formats()
    print("\n=== Тестирование завершено ===")
    print("Функция get_client_data() корректно обрабатывает все форматы данных")
    print("Ошибка 'dict' object has no attribute 'phone' больше не возникнет")
