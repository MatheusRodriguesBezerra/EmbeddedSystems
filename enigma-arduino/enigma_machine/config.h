#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// LEDs de modo
#define PIN_LED_DECRYPT 48
#define PIN_LED_ENCRYPT 50
#define PIN_LED_MESSAGE 2

// LEDs binarios L1..L5 (valor da letra A=1 .. Z=26)
#define PIN_LED_L1 46
#define PIN_LED_L2 47
#define PIN_LED_L3 49
#define PIN_LED_L4 51
#define PIN_LED_L5 3

#define BINARY_LED_DISPLAY_MS 1200
#define DECRYPT_FINISH_ALL_MS 5000
#define SEND_MESSAGE_LED_MS 4000

// LCD I2C
#define LCD_I2C_ADDR 0x27
#define LCD_COLS 20
#define LCD_ROWS 4

// Limites
#define MAX_PLAIN_LEN 20
#define MAX_ACTIVE_ROTORS 4
#define ROTOR_POOL_SIZE 6
#define SERIAL_BAUD 115200
#define SYNC_TIMEOUT_MS 1500

// Teclas de comando
#define KEY_SEND 0x11
#define KEY_MODE 0x12
#define KEY_LOCK 0x13
#define KEY_RESET 0x16
#define KEY_SYNC 0x17
#define KEY_NONE 0x00

// Teclas de rotor / shifter
#define KEY_R1_PLUS 0x21
#define KEY_R1 0x22
#define KEY_R2_PLUS 0x23
#define KEY_R2 0x24
#define KEY_R3_PLUS 0x25
#define KEY_R3 0x26
#define KEY_R4_PLUS 0x27
#define KEY_R4 0x28
#define KEY_R5_PLUS 0x29
#define KEY_R5 0x2A
#define KEY_R6_PLUS 0x2B
#define KEY_R6 0x2C
#define KEY_S1 0x31
#define KEY_S2 0x32
#define KEY_S3 0x33
#define KEY_S4 0x34

#define DEBUG_KEYS 0
#define LCD_MIRROR_SERIAL 1

#define LED_ON  HIGH
#define LED_OFF LOW

#endif
