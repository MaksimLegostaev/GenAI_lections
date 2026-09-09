"""
Юнит-тесты для QRDecoderTool
"""

import unittest
import os
import tempfile
from PIL import Image
import qrcode
import sys

# Добавляем путь к родительской папке, чтобы импортировать наш инструмент
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from qr_decoder_tool import QRDecoderTool


class TestQRDecoderTool(unittest.TestCase):
    """Тесты для QRDecoderTool"""
    
    @classmethod
    def setUpClass(cls):
        """Подготовка тестовых данных"""
        cls.decoder = QRDecoderTool()
        
        # Создаем тестовую директорию для временных файлов
        cls.test_dir = tempfile.mkdtemp()
        
        # Создаем тестовый QR-код
        cls.test_text = "Hello, World! Тестовый QR-код"
        cls.qr_filename = os.path.join(cls.test_dir, "test_qr.png")
        
        # Генерируем QR-код
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(cls.test_text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(cls.qr_filename)
    
    @classmethod
    def tearDownClass(cls):
        """Очистка после тестов"""
        # Удаляем все файлы в test_dir
        if os.path.exists(cls.test_dir):
            for file in os.listdir(cls.test_dir):
                file_path = os.path.join(cls.test_dir, file)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            os.rmdir(cls.test_dir)
    
    def test_decode_from_path(self):
        """Тест 1: Декодирование из файла по пути"""
        results = self.decoder.decode_from_path(self.qr_filename)
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]['data'], self.test_text)
        self.assertEqual(results[0]['type'], 'QRCODE')
    
    def test_decode_from_image_object(self):
        """Тест 2: Декодирование из объекта PIL.Image"""
        image = Image.open(self.qr_filename)
        results = self.decoder.decode_from_image(image)
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]['data'], self.test_text)
        self.assertEqual(results[0]['type'], 'QRCODE')
    
    def test_decode_and_get_text(self):
        """Тест 3: Упрощенный метод получения текста"""
        text = self.decoder.decode_and_get_text(self.qr_filename, 'path')
        
        self.assertEqual(text, self.test_text)
        
        # Тест с несуществующим файлом должен вернуть None
        text_none = self.decoder.decode_and_get_text('nonexistent.png', 'path')
        self.assertIsNone(text_none)
    
    def test_cache_functionality(self):
        """Тест 4: Проверка кеширования"""
        # Первый запрос
        results1 = self.decoder.decode_from_path(self.qr_filename)
        
        # Второй запрос (должен взять из кеша)
        results2 = self.decoder.decode_from_path(self.qr_filename)
        
        self.assertEqual(results1, results2)
        
        # Очистка кеша
        self.decoder.clear_cache()
        self.assertEqual(len(self.decoder._cache), 0)
    
    def test_supported_formats(self):
        """Тест 5: Проверка получения поддерживаемых форматов"""
        formats = self.decoder.get_supported_formats()
        self.assertIsInstance(formats, list)
        self.assertIn('png', formats)
        self.assertIn('jpg', formats)
        self.assertIn('jpeg', formats)
    
    def test_use_method(self):
        """Тест 6: Метод use() для вызова из LLM-агента"""
        print("\n=== Тест метода use() ===")
        
        # Создаем QR-код с тестовыми данными
        test_data = "https://example.com/use-method-test"
        qr_filename = os.path.join(self.test_dir, "test_use_method.png")
        
        # Генерируем QR-код
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(test_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(qr_filename)
        
        try:
            # Тестируем метод use() с локальным файлом
            result = self.decoder.use(qr_filename)
            self.assertIn(test_data, result)
            print(f"✓ Метод use() с файлом работает: {result}")
            
            # Тестируем с несуществующим файлом
            result_invalid = self.decoder.use("nonexistent_file.png")
            self.assertIn("Ошибка", result_invalid)
            print(f"✓ Метод use() с несуществующим файлом корректно обрабатывает ошибку")
            
        except Exception as e:
            print(f"✗ Ошибка в тесте use(): {e}")
            raise
    
    def test_llm_agent_integration(self):
        """Тест 7: Интеграция QRDecoderTool в LLM-агент"""
        print("\n=== Тест интеграции с LLM-агентом ===")
        
        # Создаем QR-код с тестовыми данными
        test_data = "https://example.com/integration-test"
        qr_filename = os.path.join(self.test_dir, "test_integration.png")
        
        # Генерируем QR-код
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(test_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(qr_filename)
        
        try:
            # Импортируем LLM-агент
            from llm_agent.core_v2 import LLMAgent
            
            # Создаем экземпляр агента (можно в локальном режиме)
            agent = LLMAgent(local=True)
            
            # Проверяем, что инструмент зарегистрирован
            self.assertIn("qr_decoder", agent.tools)
            print(f"✓ Инструмент 'qr_decoder' зарегистрирован в агенте")
            
            # Проверяем, что инструмент работает через метод use()
            result = agent.tools["qr_decoder"].use(qr_filename)
            self.assertIn(test_data, result)
            print(f"✓ QRDecoderTool работает в составе агента: {result}")
            
            # Проверяем, что инструмент описан в системном промпте
            import inspect
            system_prompt = inspect.getsource(agent._ask_llm_for_plan)
            self.assertIn("qr_decoder", system_prompt)
            print(f"✓ Инструмент 'qr_decoder' описан в системном промпте")
            
        except Exception as e:
            print(f"✗ Ошибка в тесте интеграции: {e}")
            raise


def run_tests():
    """Запуск всех тестов"""
    # Создаем тестовый набор
    suite = unittest.TestLoader().loadTestsFromTestCase(TestQRDecoderTool)
    
    # Запускаем тесты с подробным выводом
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Возвращаем результат для CI/CD
    return result.wasSuccessful()


if __name__ == "__main__":
    # Запуск тестов
    success = run_tests()
    exit(0 if success else 1)