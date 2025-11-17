
import struct
import time
import csv
import random
from typing import Optional, Dict, Tuple


class STM32Controller:
    """
    Тестовая версия.
    UART — заглушка.
    Вместо поиска реальной команды выдаются случайные zone и command_number.
    Есть шанс ошибки.
    """

    CONFIRM    = 0x00
    ERR_TX     = 0x01
    ERR_ACK    = 0x02
    ERR_ADDR   = 0x03
    ERR_STM    = 0x04
    ERR_CMD    = 0x05

    RESPONSE_TEXT = {
        CONFIRM:  "OK",
        ERR_TX:   "Arduino TX error",
        ERR_ACK:  "Arduino ACK timeout/error",
        ERR_ADDR: "Invalid Arduino address",
        ERR_STM:  "STM internal error"
    }

    # Вероятность ошибки (0.0 - 1.0)
    ERROR_PROBABILITY = 0.25

    # ---------------------------------------------------------
    def __init__(self,
                 port: str = '/dev/ttyS0',
                 baudrate: int = 115200,
                 timeout: float = 1.0,
                 file_path_to_table: str = './commands.csv'):

        self.commands = []

        # UART-заглушка
        self.ser = None
        print("🔌 ТЕСТОВЫЙ РЕЖИМ: UART заглушён")

        self._load_commands_from_csv(file_path_to_table)

    # ---------------------------------------------------------
    def _load_commands_from_csv(self, filepath: str) -> None:
        """Загрузка таблицы команд (не используется — просто лог)."""
        try:
            with open(filepath, newline='', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter='|')

                for row in reader:
                    row = [item.strip() for item in row if item.strip()]
                    if len(row) != 3:
                        continue

                    try:
                        number = int(row[0], 0)
                        name = row[1]
                        zone = int(row[2])
                    except ValueError:
                        print(f"⚠ Ошибка CSV: {row}")
                        continue

                    self.commands.append({
                        "name": name,
                        "number": number,
                        "zone": zone
                    })

            print(f"📚 Команд загружено (но не используется): {len(self.commands)}")

        except FileNotFoundError:
            print(f"❌ Файл не найден: {filepath}")

    # ---------------------------------------------------------
    def _find_command(self, name: str) -> Optional[Tuple[int, int, str]]:
        """ТЕСТОВО: возвращает случайную команду вместо поиска."""
        zone = random.randint(1, 10)
        number = random.randint(0, 255)

        print(f"🎲 Случайная команда → zone={zone}, cmd={hex(number)}")

        return zone, number, name

    # ---------------------------------------------------------
    def execute_command(self, name: str) -> Dict:
        """Выполнить команду (тестовый режим)."""

        # Генерация случайной команды
        cmd = self._find_command(name)
        if not cmd:
            return self._result(name, self.ERR_CMD, "Command not found", 0)

        zone, number, original_name = cmd
        return self._send(zone, number, original_name)

    # ---------------------------------------------------------
    def _send(self, zone: int, number: int, name: str) -> Dict:
        """
        ТЕСТОВЫЙ режим отправки.
        UART нет — просто симуляция + шанс ошибки.
        """

        start = time.time()
        time.sleep(0.05)

        # Шанс ошибки
        if random.random() < self.ERROR_PROBABILITY:
            code = random.choice([
                self.ERR_TX, self.ERR_ACK,
                self.ERR_ADDR, self.ERR_STM
            ])
            text = self.RESPONSE_TEXT.get(code, "Simulated error")
            print(f"❌ Эмулированная ошибка: {text}")
        else:
            code = self.CONFIRM
            text = "OK"
            print(f"✔ Эмулировано успешное выполнение")

        exec_time = round((time.time() - start) * 1000, 2)
        return self._result(name, code, text, exec_time)

    # ---------------------------------------------------------
    @staticmethod
    def _result(name: str, code: int, status: str, time_ms: float) -> Dict:
        return {
            "command": name,
            "error_code": code,
            "command_status": "OK" if code == 0x00 else f"Failed | {status}",
            "execution_time_ms": time_ms
        }

    # ---------------------------------------------------------
    def close(self):
        print("🔌 UART заглушка закрыта")

# Создаём контроллер (UART заглушён)
controller = STM32Controller(
    port="/dev/ttyS0",
    baudrate=115200,
    timeout=1.0,
    file_path_to_table="./commands.csv"   # можно любой CSV
)

# Выполняем несколько команд
result1 = controller.execute_command("OPEN_VALVE")
print(result1)

result2 = controller.execute_command("CLOSE_VALVE")
print(result2)

result3 = controller.execute_command("CHECK_STATUS")
print(result3)

# Закрытие (просто сообщение)
controller.close()
