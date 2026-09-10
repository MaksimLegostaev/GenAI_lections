# main_qr.py
from llm_agent.core_v2 import LLMAgent
import qrcode
import os

def create_test_qr():
    """Создаёт тестовый QR-код"""
    test_data = "https://example.com/test-qr-code"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(test_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img.save("test_qr.png")
    print(f"✅ QR-код создан с данными: {test_data}")
    return "test_qr.png"

def main():
    """Основная функция для запуска агента с QR-кодом."""
    print("Проверка работы QRDecoderTool в LLM-агенте")
    print("-" * 70)

    # Создаём тестовый QR-код
    qr_file = create_test_qr()

    # Создаём агента
    agent = LLMAgent(local=True, ollama_model="qwen3.5:2b")

    # Запрос с QR-кодом
    query = f"Разбери QR-код из файла {qr_file} и скажи, что в нём закодировано"

    print(f"Ваш запрос: {query}")
    print("-" * 70)

    response = agent.process_query(query)

    print("\n" + "=" * 70)
    print("Финальный ответ агента:\n")
    print(response)
    print("=" * 70)

    # Удаляем тестовый файл
    if os.path.exists(qr_file):
        os.unlink(qr_file)

if __name__ == "__main__":
    main()