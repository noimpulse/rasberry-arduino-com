import serial
import struct
import time


class STM32Controller:
    # Коды ошибок и подтверждений
    CONFIRM = 0x00 # Подтверждение (успешно) 
    ERR_TX = 0x01 # Ошибка передачи на Arduino 
    ERR_ACK = 0x02 # Ошибка подтверждения от Arduino 
    ERR_ADDR = 0x03 # Неверный адрес Arduino (зона вне диапазона)
    ERR_STM = 0x04 # Неверный адрес Arduino (зона вне диапазона)

    def __init__(self, port='/dev/ttyS0', baudrate=115200, timeout=1):
        """
        Инициализирует подключение к STM32 через UART.
        :param port: порт UART (например, '/dev/ttyS0')
        :param baudrate: скорость передачи (по умолчанию 115200)
        :param timeout: таймаут ожидания ответа (в секундах)
        """
        try:
            self.ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
            print(f"✅ Подключено к {port} (baudrate={baudrate})")
        except Exception as e:
            print(f"❌ Ошибка инициализации порта: {e}")
            self.ser = None

    def send_command(self, zone, command):
        """
        Отправляет STM32 сообщение (зона, команда)
        :param zone: номер зоны 1–9
        :param command: номер команды (байт)
        :return: словарь с результатом выполнения
        """
        if not self.ser or not self.ser.is_open:
            print("⚠ UART не инициализирован или закрыт.")
            return {
                "number_of_command": command,
                "error_code": self.ERR_STM,
                "command_status": "Failed",
                "execution_time_ms": 0
            }

        try:
            start_time = time.time()

            # Формируем пакет (2 байта)
            packet = struct.pack('BB', zone, command)
            self.ser.write(packet)
            print(f"📤 Отправлено STM32: зона {zone}, команда {hex(command)}")

            time.sleep(0.1)

            # Читаем ответ
            response = self.ser.read(1)
            if not response:
                print("⚠ Нет ответа от STM32")
                return {
                    "number_of_command": command,
                    "error_code": self.ERR_STM,
                    "command_status": "Failed",
                    "execution_time_ms": 0
                }

            code = response[0]
            exec_time = (time.time() - start_time) * 1000
            status = ''

            if code == self.CONFIRM:
                print("✅ Команда подтверждена STM32")
                status = "OK"
            elif code == self.ERR_TX:
                print("❌ Ошибка передачи на Arduino")
                status = "Failed"
            elif code == self.ERR_ACK:
                print("❌ Ошибка подтверждения от Arduino")
                status = "Failed"
            elif code == self.ERR_ADDR:
                print("❌ Неверный адрес Arduino")
                status = "Failed"
            else:
                print(f"⚠ Неизвестный код ответа: {hex(code)}")
                status = "Failed"

            return {
                "number_of_command": command,
                "error_code": code,
                "command_status": status,
                "execution_time_ms": exec_time
            }

        except Exception as e:
            print(f"❌ Ошибка при передаче: {e}")
            return {
                "number_of_command": command,
                "error_code": self.ERR_STM,
                "command_status": "Failed",
                "execution_time_ms": 0
            }

    def close(self):
        """Закрывает соединение."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("🔌 Соединение с STM32 закрыто.")


# Пример использования
if __name__ == "__main__":
    stm = STM32Controller()
    stm.send_command(3, 0x05)
    time.sleep(0.2)
    stm.close()
