import serial
import struct
import time
import csv
from typing import Optional, Tuple, Dict


class STM32Controller:
    """
    Класс для управления STM32 через UART.
    Загружает таблицу команд из CSV, ищет команду по имени
    и отправляет её в формате (zone, command_number).
    """

    # Коды ошибок и подтверждений (ответы STM32)
    CONFIRM = 0x00   # Успешно
    ERR_TX = 0x01    # Ошибка передачи на Arduino
    ERR_ACK = 0x02   # Arduino не подтвердил получение
    ERR_ADDR = 0x03  # Неверный адрес Arduino
    ERR_STM = 0x04   # Ошибка на стороне STM32
    ERR_CMD - 0x05

    def __init__(self, port='/dev/ttyS0', baudrate=115200, timeout=1,
                 file_path_to_table='./commands.csv'):
        """
        Инициализирует UART и загружает CSV с командами.
        """
        self.commands = []

        # Подключение к UART
        try:
            self.ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
            print(f"✅ Подключено к {port} (baudrate={baudrate})")
        except Exception as e:
            print(f"❌ Ошибка инициализации порта: {e}")
            self.ser = None

        # Загрузка файла команд
        self._load_csv(file_path_to_table)

    # -------------------------------------------------------------------------
    def execute_command(self, cmd_name: str) -> Optional[Dict]:
        """
        Выполняет команду по её строковому имени.
        """
        found = self._find(cmd_name)

        if not found:
            print(f"❌ Команда '{cmd_name}' не найдена в таблице.")
            return  {
                "number_of_command": 0,
                "error_code": 0x05,
                "command_status": "Not found",
                "execution_time_ms": 0
            }

        zone, cmd_num = found
        return self._send_command(zone, cmd_num)

    # -------------------------------------------------------------------------
    def _load_csv(self, filepath: str):
        """
        Загружает команды из CSV формата:
        command_number | command_name | arduino_zone | ...
        """
        try:
            with open(filepath, newline='', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter='|')

                for row in reader:

                    # Фильтруем пустые поля
                    row = [item.strip() for item in row if item.strip()]
                    if len(row) < 3:
                        continue

                    try:
                        cmd_number = int(row[0], 0)  # можно hex
                        cmd_name = row[1]
                        arduino_zone = int(row[2])
                    except ValueError:
                        print(f"⚠ Ошибка разбора строки CSV: {row}")
                        continue

                    self.commands.append({
                        "command_number": cmd_number,
                        "command_name": cmd_name,
                        "arduino_zone": arduino_zone
                    })

            print(f"📚 Загружено команд: {len(self.commands)}")

        except FileNotFoundError:
            print(f"❌ CSV файл не найден: {filepath}")
        except Exception as e:
            print(f"❌ Ошибка чтения CSV: {e}")

    # -------------------------------------------------------------------------
    def _find(self, command_name: str) -> Optional[Tuple[int, int]]:
        """
        Ищет команду по имени.
        Возвращает (arduino_zone, command_number)
        """
        for cmd in self.commands:
            if cmd["command_name"] == command_name:
                return cmd["arduino_zone"], cmd["command_number"]
        return None

    # -------------------------------------------------------------------------
    def _send_command(self, zone: int, cmd_num: int) -> Dict:
        """
        Отправляет STM32 пакет: (zone, cmd_num)
        Ожидает один байт ответа.
        """

        if not self.ser or not self.ser.is_open:
            print("⚠ UART не инициализирован.")
            return {
                "number_of_command": cmd_num,
                "error_code": self.ERR_STM,
                "command_status": "Failed | UART Error",
                "execution_time_ms": 0
            }

        try: 
            start_time = time.time()

            # Формирование пакета
            packet = struct.pack('BB', zone, cmd_num)
            self.ser.write(packet)
            print(f"📤 Отправлено: зона={zone}, команда={hex(cmd_num)}")

            # Задержка для стабильности
            time.sleep(0.1)

            # Ожидание ответа
            response = self.ser.read(1)

            if not response:
                print("⚠ Нет ответа от STM32")
                return {
                    "number_of_command": cmd_num,
                    "error_code": self.ERR_STM,
                    "command_status": "Failed | STM Error",
                    "execution_time_ms": 0
                }

            code = response[0]
            exec_time = round((time.time() - start_time) * 1000, 2)

            status = "OK" if code == self.CONFIRM else "Failed"

            messages = {
                self.CONFIRM: "Команда подтверждена STM32",
                self.ERR_TX: "Ошибка передачи на Arduino",
                self.ERR_ACK: "Arduino не подтвердил команду",
                self.ERR_ADDR: "Неверный адрес Arduino"
            }

            print("ℹ", messages.get(code, f"Неизвестный код ответа: {hex(code)}"))

            return {
                "number_of_command": cmd_num,
                "error_code": code,
                "command_status": status,
                "execution_time_ms": exec_time
            }

        except Exception as e:
            print(f"❌ Ошибка при передаче: {e}")
            return {
                "number_of_command": cmd_num,
                "error_code": self.ERR_STM,
                "command_status": "Failed | STM send error",
                "execution_time_ms": 0
            }

    # -------------------------------------------------------------------------
    def close(self):
        """Закрывает UART."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("🔌 Соединение закрыто.")


# Пример использования
if __name__ == "__main__":
    stm = STM32Controller()
    stm.execute_command("diod_on")
    time.sleep(0.2)
    stm.close()
