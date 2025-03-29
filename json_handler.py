import json
import pandas as pd
import numpy as np

def custom_serializer(obj):
    """Кастомный сериализатор для обработки несериализуемых типов."""
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()  # Преобразуем Timestamp в строку ISO
    elif isinstance(obj, (np.integer, np.floating)):
        return obj.item()  # Преобразуем numpy числа в стандартные Python числа
    elif isinstance(obj, np.ndarray):
        return obj.tolist()  # Преобразуем numpy массивы в списки
    elif pd.isna(obj):
        return None  # Преобразуем NaN в None
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

def dumps(data):
    """Обёртка для json.dumps с обработкой ошибок и кастомным сериализатором."""
    try:
        return json.dumps(data, default=custom_serializer)
    except Exception as e:
        raise Exception(f"Ошибка при сериализации JSON: {str(e)}")

def loads(data):
    """Обёртка для json.loads с обработкой ошибок."""
    try:
        return json.loads(data)
    except Exception as e:
        raise Exception(f"Ошибка при десериализации JSON: {str(e)}")

__all__ = ['dumps', 'loads']
