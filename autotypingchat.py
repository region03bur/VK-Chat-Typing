import requests
import time
import logging
from datetime import datetime, timedelta
import os
import sys
import threading
from typing import NoReturn
# Настройка
VK_TOKEN = 'ТОКЕН СЮДА'
CHAT_ID = 113 # заменить на свой айди чата
PEER_ID = 2000000000 + CHAT_ID
INTERVAL = 3  # Интервал отправки статуса (секунд)

# Статистика
typing_count = 0
error_count = 0
start_time = datetime.now()
running = True  # Флаг для управления потоками

# Очистка консоли и приветствие
os.system('cls' if os.name == 'nt' else 'clear')

print("╔" + "═" * 58 + "╗")
print("║                    🚀 АВТО ТАЙПИНГ ДЛЯ ЧАТА 🚀                  ║")
print("╠" + "═" * 58 + "╣")
print(f"║   Чат ID: {CHAT_ID:<47} ║")
print(f"║   Интервал: {INTERVAL} сек{' ' * 38} ║")
print(f"║   Запуск: {start_time.strftime('%H:%M:%S')}{' ' * 39} ║")
print(f"║   Статистика: каждый час{' ' * 34} ║")
print("╚" + "═" * 58 + "╝")
print()

# Настройка логирования (только для критических ошибок)
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(message)s', datefmt='%H:%M:%S')

def send_typing() -> bool:
    """Отправка статуса 'печатает'"""
    global typing_count, error_count

    url = 'https://api.vk.com/method/messages.setActivity'
    params = {
        'access_token': VK_TOKEN,
        'peer_id': PEER_ID,
        'type': 'typing',
        'v': '5.199'
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        if 'error' in data:
            error_count += 1
            return False

        typing_count += 1
        return True

    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        error_count += 1
        return False
    except Exception as e:
        error_count += 1
        return False

def print_hourly_stats() -> None:
    """Вывод полной статистики каждый час"""
    global running

    while running:
        try:
            # Ждем до следующего часа
            now = datetime.now()
            next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            sleep_seconds = (next_hour - now).total_seconds()

            # Проверяем каждую секунду, не пора ли остановиться
            for _ in range(int(sleep_seconds)):
                if not running:
                    return
                time.sleep(1)

            if not running:
                return

            uptime = datetime.now() - start_time
            hours = uptime.seconds // 3600
            minutes = (uptime.seconds % 3600) // 60
            seconds = uptime.seconds % 60

            total_ops = typing_count + error_count
            success_rate = (typing_count / total_ops * 100) if total_ops > 0 else 0

            print()
            print("╔" + "═" * 58 + "╗")
            print("║                  📊 ЧАСОВАЯ СТАТИСТИКА 📊                  ║")
            print("╠" + "═" * 58 + "╣")
            print(f"║  ⏱ Время работы: {uptime.days}д {hours:02d}ч {minutes:02d}м {seconds:02d}с{' ' * 27} ║")
            print(f"║  ✍️ Отправлено статусов: {typing_count:<38} ║")
            print(f"║  ❌ Ошибок: {error_count:<44} ║")
            print(f"║  📈 Успешность: {success_rate:.1f}%{' ' * 40} ║")
            print(f"║  📨 Всего операций: {total_ops:<38} ║")
            print(f"║  🕒 {datetime.now().strftime('%H:%M:%S')}{' ' * 45} ║")
            print("╚" + "═" * 58 + "╝")
            print()

        except Exception as e:
            # Логируем ошибку, но продолжаем работу
            logging.error(f"Ошибка в потоке статистики: {e}")
            time.sleep(60)  # Пауза перед следующей попыткой

def print_final_stats() -> None:
    """Вывод финальной статистики при завершении"""
    uptime = datetime.now() - start_time
    hours = uptime.seconds // 3600
    minutes = (uptime.seconds % 3600) // 60
    seconds = uptime.seconds % 60
    total_ops = typing_count + error_count
    success_rate = (typing_count / total_ops * 100) if total_ops > 0 else 0

    print("\n" + "╔" + "═" * 58 + "╗")
    print("║                    👋 РАБОТА ЗАВЕРШЕНА 👋                  ║")
    print("╠" + "═" * 58 + "╣")
    print(f"║  ⏱ Всего работал: {uptime.days}д {hours:02d}ч {minutes:02d}м {seconds:02d}с{' ' * 26} ║")
    print(f"║  ✍️ Всего отправлено: {typing_count:<38} ║")
    print(f"║  ❌ Всего ошибок: {error_count:<41} ║")
    print(f"║  📈 Успешность: {success_rate:.1f}%{' ' * 40} ║")
    print(f"║  📨 Всего операций: {total_ops:<38} ║")
    print(f"║  📅 Завершен: {datetime.now().strftime('%H:%M:%S')}{' ' * 38} ║")
    print("╚" + "═" * 58 + "╝")

def main() -> None:
    """Основная функция"""
    global running
    fail_count = 0
    max_fails = 5  # Максимальное количество ошибок подряд
    fail_sleep = 30  # Секунд паузы при ошибках

    # Запускаем поток для часовой статистики
    stats_thread = threading.Thread(target=print_hourly_stats, daemon=True)
    stats_thread.start()

    print("🔄 Начинаю отправку статусов...")
    print("⏹ Для остановки нажмите Ctrl+C")
    print()

    try:
        while running:
            if not send_typing():
                fail_count += 1
                if fail_count >= max_fails:
                    print(f"⚠️ Слишком много ошибок ({max_fails}), пауза {fail_sleep} сек...")
                    time.sleep(fail_sleep)
                    fail_count = 0
            else:
                fail_count = 0  # Сбрасываем счетчик при успешной отправке

            time.sleep(INTERVAL)

    except KeyboardInterrupt:
        running = False  # Останавливаем поток статистики
        print("\n\n⏳ Завершение работы...")
        time.sleep(1)  # Даем время потоку статистики завершиться
        print_final_stats()
        # Просто выходим, без sys.exit()
        return
    except Exception as e:
        running = False
        print(f"\n❌ Критическая ошибка: {e}")
        print_final_stats()
        # При критической ошибке все равно выходим без sys.exit()
        return

if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        # Ловим SystemExit на всякий случай
        pass