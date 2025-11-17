import serial
import struct
import time
import csv
from typing import Optional, Dict, Tuple


class STM32Controller:
    """
    Простой класс для отправки команд STM32.
    Загружает команды из CSV и отправляет по UART пару (zone, command_number).
    """

    # Коды ответов STM32
    CONFIRM    = 0x00
    ERR_TX     = 0x01
    ERR_ACK    = 0x02
    ERR_ADDR   = 0x03
    ERR_STM    = 0x04
    ERR_CMD    = 0x05     # Внутренний код: команда не найдена

    RESPONSE_TEXT = {
        CONFIRM:  "OK",
        ERR_TX:   "Arduino TX error",
        ERR_ACK:  "Arduino ACK timeout/error",
        ERR_ADDR: "Invalid Arduino address",
        ERR_STM:  "STM internal error"
    }

    # -------------------------------------------------------------------------
    def __init__(self,
                 port: str = '/dev/ttyS0',
                 baudrate: int = 115200,
                 timeout: float = 1.0,
                 file_path_to_table: str = './commands.csv'):

        self.commands = []

        self._init_uart(port, baudrate, timeout)
        self._load_commands_from_csv(file_path_to_table)

    # -------------------------------------------------------------------------
    def _init_uart(self, port: str, baudrate: int, timeout: float) -> None:
        """Подключение к UART."""
        try:
            self.ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
            print(f"🔌 UART: подключено ({port}, {baudrate})")
        except Exception as e:
            print(f"❌ UART ошибка: {e}")
            self.ser = None

    # -------------------------------------------------------------------------
    def _load_commands_from_csv(self, filepath: str) -> None:
        """Загрузка таблицы команд из CSV."""
        try:
            with open(filepath, newline='', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter='|')

                for row in reader:
                    row = [item.strip() for item in row if item.strip()]
                    if len(row) != 3:
                        continue

                    try:
                        number = int(row[0], 0)  # поддержка hex
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

            print(f"📚 Команд загружено: {len(self.commands)}")

        except FileNotFoundError:
            print(f"❌ Файл не найден: {filepath}")

    # -------------------------------------------------------------------------
    def _find_command(self, name: str) -> Optional[Tuple[int, int, str]]:
        """Поиск команды по имени."""
        for cmd in self.commands:
            if cmd["name"] == name:
                return cmd["zone"], cmd["number"], cmd["name"]
        return None

    # -------------------------------------------------------------------------
    def execute_command(self, name: str) -> Dict:
        """Выполнить команду по имени."""
        cmd = self._find_command(name)

        if not cmd:
            print(f"❌ Команда '{name}' отсутствует в таблице")
            return self._result(name, self.ERR_CMD, "Command not found", 0)

        zone, number, original_name = cmd
        return self._send(zone, number, original_name)

    # -------------------------------------------------------------------------
    def _send(self, zone: int, number: int, name: str) -> Dict:
        """Отправка команды STM32."""
        if not self.ser or not self.ser.is_open:
            return self._result(name, self.ERR_STM, "UART not initialized", 0)

        start = time.time()

        try:
            # Сформировать пакет и отправить
            packet = struct.pack('BB', zone, number)
            self.ser.write(packet)
            print(f"📤 Отправлено → zone={zone}, command={hex(number)}")

            time.sleep(0.1)  # небольшая пауза

            resp = self.ser.read(1)
            exec_time = round((time.time() - start) * 1000, 2)

            if not resp:
                return self._result(name, self.ERR_STM, "No response from STM32", exec_time)

            code = resp[0]
            text = self.RESPONSE_TEXT.get(code, f"Unknown code {hex(code)}")

            if code == self.CONFIRM:
                print("✔ STM32 подтвердил выполнение")
            else:
                print(f"❌ STM32 ошибка: {text}")

            return self._result(name, code, text, exec_time)

        except Exception as e:
            return self._result(name, self.ERR_STM, f"Exception: {e}", 0)

    # -------------------------------------------------------------------------
    @staticmethod
    def _result(name: str, code: int, status: str, time_ms: float) -> Dict:
        """Формирование итогового ответа."""
        return {
            "command": name,
            "error_code": code,
            "command_status": "OK" if code == 0x00 else f"Failed | {status}",
            "execution_time_ms": time_ms
        }

    # -------------------------------------------------------------------------
    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("🔌 UART закрыт")
