import serial
import struct
import time

# Инициализация UART
ser = serial.Serial('/dev/ttyS0', baudrate=115200, timeout=1)

# Адреса и коды ошибок
CONFIRM = 0x00
ERR_TX = 0x01
ERR_ACK = 0x02
ERR_ADDR = 0x03
ERR_STM = 0x04


# Отправка команды
def send_command_to_stm32(zone, command):
    """
    Отправляет STM32 сообщение (зона, команда)
    :param zone: номер зоны 1–9
    :param command: номер команды (байт)
    """
    try:

        start_time = time.time()
        # Формируем пакет (2 байта)
        packet = struct.pack('BB', zone, command)
        ser.write(packet)
        print(f"Отправлено STM32: зона {zone}, команда {hex(command)}")
         # Читаем подтверждение
        time.sleep(0.1)
        # Ожидаем ответ
        response = ser.read(1)
        if not response:
            print("⚠ Нет ответа от STM32")
            return {
              "number_of_command": command,
              "error_code": ERR_STM,
              "command_status ": "Failed", 
              "execution_time_ms": 0
            }

        code = response[0]
        if code == CONFIRM:
            print("✅ Команда подтверждена STM32")
            return {
              "number_of_command": command,
              "error_code": CONFIRM,
              "command_status ": "OK", 
              "execution_time_ms": (time.time() - start_time) * 1000
            }
        elif code == ERR_TX:
            print("❌ Ошибка передачи на Arduino")
        elif code == ERR_ACK:
            print("❌ Ошибка подтверждения от Arduino")
        elif code == ERR_ADDR:
            print("❌ Неверный адрес Arduino")
        else:
            print(f"⚠ Неизвестный код ответа: {hex(code)}")
        return {
          "number_of_command": command,
          "error_code": code,
          "command_status ": "Failed", 
          "execution_time_ms": (time.time() - start_time) * 1000
        }

    except Exception as e:
        print(f"Ошибка при передаче: {e}")
        return {
          "number_of_command": command,
          "error_code": ERR_STM,
          "command_status ": "Failed", 
          "execution_time_ms": 0
        }

# Пример использования
if __name__ == "__main__":
        send_command_to_stm32(3, 0x05)
        time.sleep(0.2)
