#ifndef CONFIG_H
#define CONFIG_H

// LEDs
#define PIN_LED_DECRYPT 48
#define PIN_LED_ENCRYPT 50
#define PIN_LED_MESSAGE 52

// LCD I2C (ajuste o endereco se necessario: 0x27 ou 0x3F)
#define LCD_I2C_ADDR 0x27
#define LCD_COLS 20
#define LCD_ROWS 4

#define MAX_PLAIN_LEN 20
#define SERIAL_BAUD 115200
#define SYNC_TIMEOUT_MS 1500

// Teclas especiais no keypad 2 (bytes privados)
#define KEY_SEND 0x11
#define KEY_MODE 0x12
#define KEY_R1 0x13
#define KEY_R2 0x14
#define KEY_R3 0x15
#define KEY_RESET_SYNC 0x16

// 1 = espelha linhas do LCD na Serial (util se LCD I2C falhar)
#define LCD_MIRROR_SERIAL 1

// HIGH = LED acende com digitalWrite(HIGH). Se usar logica invertida, mude para LOW.
#define LED_ON  HIGH
#define LED_OFF LOW

#endif
