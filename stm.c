// #include "main.h"
#include <stdint.h>


#define RPI_ADDR 0x10
#define STM_ADDR 0x30

#define I2C_BASE_ADDR 0x20 // Базовый адрес ардуин 0x21–0x29
#define CONFIRM 0x00
#define ERR_TX 0x01
#define ERR_ACK 0x02
#define ERR_ADDR 0x03

// extern I2C_HandleTypeDef hi2c1;
// extern UART_HandleTypeDef huart2;

uint8_t rx_buffer[2];

void process_command(void)
{
  uint8_t zone = rx_buffer[0];
  uint8_t command = rx_buffer[1];

  if (zone < 1 || zone > 9)
  {
    uint8_t err = ERR_ADDR;
    HAL_UART_Transmit(&huart2, &err, 1, 100);
    return;
  }

  uint8_t arduino_addr = I2C_BASE_ADDR + zone;
  HAL_StatusTypeDef status = HAL_I2C_Master_Transmit(&hi2c1, arduino_addr << 1, &command, 1, 100);

  if (status != HAL_OK)
  {
    uint8_t err = ERR_TX;
    HAL_UART_Transmit(&huart2, &err, 1, 100);
    return;
  }

  uint8_t ack = 0xFF;
  if (HAL_I2C_Master_Receive(&hi2c1, arduino_addr << 1, &ack, 1, 100) != HAL_OK)
  {
    uint8_t err = ERR_ACK;
    HAL_UART_Transmit(&huart2, &err, 1, 100);
    return;
  }

  HAL_UART_Transmit(&huart2, &ack, 1, 100);
}

void loop_stm32(void)
{
  while (1)
  {
    if (HAL_UART_Receive(&huart2, rx_buffer, 2, HAL_MAX_DELAY) == HAL_OK)
    {
      process_command();
    }
  }
}
