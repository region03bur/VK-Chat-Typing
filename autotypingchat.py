import requests
import time
import logging
from datetime import datetime, timedelta
import os
import threading

# ==================== НАСТРОЙКА ====================
VK_TOKEN = 'ТОКЕН СЮДА'
CHAT_ID = 129
PEER_ID = 2000000000 + CHAT_ID
INTERVAL = 3
# ===================================================

# Статистика
typing_count = 0
error_count = 0
start_time = datetime.now()
running = True
last_error_msg = "-"

# Цвета (ANSI) — работают в современных терминалах Windows 10+/Linux/macOS
class C:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'

# Включаем ANSI на Windows
if os.name == 'nt':
    os.system('')

os.system('cls' if os.name == 'nt' else 'clear')

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(message)s', datefmt='%H:%M:%S')

W = 62  # ширина рамки

def line(text: str = "", color: str = "") -> None:
    """Печать строки, обрезанной/дополненной до ширины рамки"""
    # Учитываем только видимые символы
    visible = text
    # Обрезаем если слишком длинно
    if len(visible) > W - 2:
        visible = visible[:W - 5] + "..."
    pad = W - 2 - len(visible)
    print(f"{C.CYAN}║{C.RESET} {color}{visible}{C.RESET}{' ' * pad}{C.CYAN}║{C.RESET}")

def top() -> None:
    print(f"{C.CYAN}╔{'═' * (W - 2)}╗{C.RESET}")

def mid() -> None:
    print(f"{C.CYAN}╠{'═' * (W - 2)}╣{C.RESET}")

def bottom() -> None:
    print(f"{C.CYAN}╚{'═' * (W - 2)}╝{C.RESET}")

def header(title: str) -> None:
    top()
    line(title.center(W - 2), C.BOLD + C.MAGENTA)
    mid()

def log(msg: str, color: str = "") -> None:
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"{C.GRAY}[{ts}]{C.RESET} {color}{msg}{C.RESET}")

def send_typing() -> bool:
    """Отправка статуса 'печатает'"""
    global typing_count, error_count, last_error_msg

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
            err = data['error']
            last_error_msg = f"API {err.get('error_code')}: {err.get('error_msg')}"
            log(last_error_msg, C.RED)
            return False

        typing_count += 1
        last_error_msg = "-"
        return True

    except requests.exceptions.Timeout:
        error_count += 1
        last_error_msg = "Таймаут запроса"
        log(last_error_msg, C.RED)
        return False
    except requests.exceptions.ConnectionError:
        error_count += 1
        last_error_msg = "Ошибка соединения"
        log(last_error_msg, C.RED)
        return False
    except Exception as e:
        error_count += 1
        last_error_msg = f"Исключение: {e}"
        log(last_error_msg, C.RED)
        return False

def uptime_str() -> str:
    up = datetime.now() - start_time
    h = up.seconds // 3600
    m = (up.seconds % 3600) // 60
    s = up.seconds % 60
    return f"{up.days}д {h:02d}ч {m:02d}м {s:02d}с"

def success_rate() -> float:
    total = typing_count + error_count
    return (typing_count / total * 100) if total > 0 else 0.0

def print_hourly_stats() -> None:
    """Вывод статистики каждый час"""
    global running

    while running:
        try:
            now = datetime.now()
            next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            sleep_seconds = (next_hour - now).total_seconds()

            for _ in range(int(sleep_seconds)):
                if not running:
                    return
                time.sleep(1)

            if not running:
                return

            total = typing_count + error_count
            rate = success_rate()
            rate_color = C.GREEN if rate >= 95 else C.YELLOW if rate >= 80 else C.RED

            print()
            header("📊  ЧАСОВАЯ СТАТИСТИКА  📊")
            line(f"⏱  Аптайм:        {uptime_str()}", C.WHITE)
            line(f"✍️  Отправлено:    {typing_count}", C.GREEN)
            line(f"❌  Ошибок:        {error_count}", C.RED if error_count else C.GRAY)
            line(f"📨  Всего операций:{total}", C.WHITE)
            line(f"📈  Успешность:    {rate:.1f}%", rate_color)
            line(f"🕒  Время:         {datetime.now().strftime('%H:%M:%S')}", C.GRAY)
            bottom()
            print()

        except Exception as e:
            logging.error(f"Ошибка в потоке статистики: {e}")
            time.sleep(60)

def print_final_stats() -> None:
    """Вывод финальной статистики"""
    total = typing_count + error_count
    rate = success_rate()
    rate_color = C.GREEN if rate >= 95 else C.YELLOW if rate >= 80 else C.RED

    print()
    header("👋  РАБОТА ЗАВЕРШЕНА  👋")
    line(f"⏱  Время работы:  {uptime_str()}", C.WHITE)
    line(f"✍️  Отправлено:    {typing_count}", C.GREEN)
    line(f"❌  Ошибок:        {error_count}", C.RED if error_count else C.GRAY)
    line(f"📨  Всего операций:{total}", C.WHITE)
    line(f"📈  Успешность:    {rate:.1f}%", rate_color)
    line(f"📅  Завершено:     {datetime.now().strftime('%H:%M:%S')}", C.GRAY)
    bottom()

def main() -> None:
    """Основная функция"""
    global running
    fail_count = 0
    max_fails = 5
    fail_sleep = 30

    # Стартовая панель
    print()
    header("🚀  АВТО ТАЙПИНГ ДЛЯ ЧАТА  🚀")
    line(f"💬  Чат ID:      {CHAT_ID}", C.CYAN)
    line(f"🔗  Peer ID:     {PEER_ID}", C.CYAN)
    line(f"⏱  Интервал:    {INTERVAL} сек", C.CYAN)
    line(f"🕒  Запуск:      {start_time.strftime('%H:%M:%S')}", C.CYAN)
    line(f"📊  Статистика:  каждый час", C.CYAN)
    bottom()
    print()

    # Поток часовой статистики
    stats_thread = threading.Thread(target=print_hourly_stats, daemon=True)
    stats_thread.start()

    log("Начинаю отправку статусов...", C.GREEN)
    log("Для остановки нажмите Ctrl+C", C.YELLOW)
    print()

    try:
        while running:
            if not send_typing():
                fail_count += 1
                if fail_count >= max_fails:
                    log(f"Подряд {max_fails} ошибок, пауза {fail_sleep}с...", C.YELLOW)
                    time.sleep(fail_sleep)
                    fail_count = 0
            else:
                fail_count = 0

            time.sleep(INTERVAL)

    except KeyboardInterrupt:
        running = False
        log("Завершение работы...", C.YELLOW)
        time.sleep(1)
        print_final_stats()
        return
    except Exception as e:
        running = False
        log(f"Критическая ошибка: {e}", C.RED)
        print_final_stats()
        return

if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        pass
