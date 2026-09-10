"""
QRDecoderTool - декодирование QR-кода из изображения
Использование библиотеки pyzbar для чтения QR-кодов
"""

import os
import base64
from io import BytesIO
from typing import Union, Optional, List, Dict
from PIL import Image
from pyzbar.pyzbar import decode as qr_decode
import requests
from urllib.parse import urlparse
import tempfile


class QRDecoderTool:
    """
    Инструмент для декодирования QR-кодов из изображений.
    Поддерживает: путь к файлу, URL, base64-строку, объект PIL.Image
    """
    name = "qr_decoder"
    description = (
        "Декодирует QR-коды из изображений. "
        "Принимает путь к файлу, URL или base64-строку."
    )

    def __init__(self):
        """Инициализация инструмента"""
        self.supported_formats = ['png', 'jpg', 'jpeg', 'bmp', 'gif', 'webp']
        self._cache = {}  # Простой кеш для результатов

    def use(self, source: str) -> str:
        """
        Универсальный метод для вызова из LLM-агента.
        Принимает строку (путь, URL или base64) и возвращает результат.
        Умеет извлекать путь из текстового описания.
        """
        try:
            print(f"> QRDecoderTool: обрабатываю '{source}'")

            cleaned_source = source.strip()

            # 1. Если это URL — используем как есть
            if cleaned_source.startswith(('http://', 'https://')):
                results = self.decode_from_url(cleaned_source)

            # 2. Если это base64
            elif cleaned_source.startswith('data:image'):
                results = self.decode_from_base64(cleaned_source)

            # 3. Если это существующий файл — используем как есть
            elif os.path.exists(cleaned_source):
                results = self.decode_from_path(cleaned_source)

            # 4. Пытаемся извлечь путь к файлу из текста
            else:
                import re
                pattern = r'[a-zA-Z]:\\[^\s]*?\.(?:png|jpg|jpeg|bmp|gif|webp)|[^\s]+\.(?:png|jpg|jpeg|bmp|gif|webp)'
                matches = re.findall(pattern, cleaned_source, re.IGNORECASE)

                if matches:
                    file_path = matches[0]
                    print(f"> QRDecoderTool: извлёк путь из текста: '{file_path}'")
                    if os.path.exists(file_path):
                        results = self.decode_from_path(file_path)
                    else:
                        return f"Ошибка: файл '{file_path}' не найден"
                else:
                    return f"Ошибка: не могу определить тип источника '{source}'. Укажите путь к файлу, URL или base64."

            if results:
                return f"QR-код содержит: {results[0]['data']}"
            return "QR-код не найден в изображении"
        except Exception as e:
            return f"Ошибка при декодировании QR-кода: {str(e)}"

    def decode_from_path(self, image_path: str) -> List[Dict[str, Union[str, bytes]]]:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Файл не найден: {image_path}")

        ext = os.path.splitext(image_path)[1].lower()[1:]
        if ext not in self.supported_formats:
            raise ValueError(f"Неподдерживаемый формат: {ext}. Поддерживаемые: {self.supported_formats}")

        if image_path in self._cache:
            return self._cache[image_path]

        try:
            image = Image.open(image_path)
            result = self.decode_from_image(image)
            self._cache[image_path] = result
            return result
        except Exception as e:
            raise RuntimeError(f"Ошибка при декодировании QR-кода: {str(e)}")

    def decode_from_url(self, image_url: str, timeout: int = 10) -> List[Dict[str, Union[str, bytes]]]:
        parsed = urlparse(image_url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Неверный URL: {image_url}")

        try:
            response = requests.get(image_url, timeout=timeout)
            response.raise_for_status()

            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                tmp_file.write(response.content)
                tmp_path = tmp_file.name

            try:
                result = self.decode_from_path(tmp_path)
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

            return result
        except requests.RequestException as e:
            raise RuntimeError(f"Ошибка загрузки изображения: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Ошибка при декодировании QR-кода: {str(e)}")

    def decode_from_base64(self, base64_string: str) -> List[Dict[str, Union[str, bytes]]]:
        try:
            if ',' in base64_string:
                base64_string = base64_string.split(',', 1)[1]

            image_data = base64.b64decode(base64_string)
            image = Image.open(BytesIO(image_data))
            return self.decode_from_image(image)
        except Exception as e:
            raise RuntimeError(f"Ошибка декодирования base64: {str(e)}")

    def decode_from_image(self, image: Image.Image) -> List[Dict[str, Union[str, bytes]]]:
        if not isinstance(image, Image.Image):
            raise TypeError("Ожидается объект PIL.Image")

        try:
            if image.mode != 'RGB':
                image = image.convert('RGB')

            decoded_objects = qr_decode(image)

            if not decoded_objects:
                return []

            result = []
            for obj in decoded_objects:
                try:
                    data = obj.data.decode('utf-8')
                except UnicodeDecodeError:
                    data = obj.data.decode('latin-1')

                result.append({
                    'data': data,
                    'type': obj.type,
                    'rect': {
                        'left': obj.rect.left,
                        'top': obj.rect.top,
                        'width': obj.rect.width,
                        'height': obj.rect.height
                    },
                    'points': [(p.x, p.y) for p in obj.polygon] if obj.polygon else []
                })

            return result
        except Exception as e:
            raise RuntimeError(f"Ошибка при декодировании: {str(e)}")

    def decode_and_get_text(self, source: Union[str, Image.Image],
                           source_type: str = 'path') -> Optional[str]:
        try:
            if source_type == 'path':
                results = self.decode_from_path(source)
            elif source_type == 'url':
                results = self.decode_from_url(source)
            elif source_type == 'base64':
                results = self.decode_from_base64(source)
            elif source_type == 'image':
                results = self.decode_from_image(source)
            else:
                raise ValueError(f"Неизвестный тип источника: {source_type}")

            if results:
                return results[0]['data']
            return None
        except Exception:
            return None

    def clear_cache(self):
        """Очистка кеша"""
        self._cache.clear()

    def get_supported_formats(self) -> List[str]:
        """Получить список поддерживаемых форматов"""
        return self.supported_formats.copy()