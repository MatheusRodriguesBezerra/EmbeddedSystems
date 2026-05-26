# Enigma Arduino

Este documento descreve a disposição física do Arduino Mega 2560 no projeto Enigma Machine e o comportamento que o sketch deve garantir. Ele é a base para a integração com o Raspberry Pi via USB Serial.

## Hardware Principal

- Arduino Mega 2560
- 3 keypads 4x4
- 8 LEDs (5 binários L1–L5 + DEC + ENC + MSG)
- LCD 20x4 com módulo I2C
- Comunicação USB Serial com o Raspberry Pi @ 115200 baud

## Mapeamento De Pinos

### Keypad 1 (letras A–P)

O Keypad 1 usa os pinos digitais `22` a `29`.

| Função   | Pino Arduino |
| -------- | ------------ |
| Linha 1  | 22           |
| Linha 2  | 23           |
| Linha 3  | 24           |
| Linha 4  | 25           |
| Coluna 1 | 26           |
| Coluna 2 | 27           |
| Coluna 3 | 28           |
| Coluna 4 | 29           |

Layout das teclas:

| Coluna 1 | Coluna 2 | Coluna 3 | Coluna 4 |
| -------- | -------- | -------- | -------- |
| A        | B        | C        | D        |
| E        | F        | G        | H        |
| I        | J        | K        | L        |
| M        | N        | O        | P        |

### Keypad 2 (letras Q–Z + comandos)

O Keypad 2 usa os pinos digitais `30` a `37`.

| Função   | Pino Arduino |
| -------- | ------------ |
| Linha 1  | 30           |
| Linha 2  | 31           |
| Linha 3  | 32           |
| Linha 4  | 33           |
| Coluna 1 | 34           |
| Coluna 2 | 35           |
| Coluna 3 | 36           |
| Coluna 4 | 37           |

Layout das teclas:

| Coluna 1 | Coluna 2 | Coluna 3 | Coluna 4 |
| -------- | -------- | -------- | -------- |
| Q        | R        | S        | T        |
| U        | V        | W        | X        |
| Y        | Z        | LOCK     | (vazia)  |
| SYNC     | RESET    | MODE     | SEND     |

### Keypad 3 (rotores e shifters)

O Keypad 3 usa os pinos digitais `38` a `45`.

| Função   | Pino Arduino |
| -------- | ------------ |
| Linha 1  | 38           |
| Linha 2  | 39           |
| Linha 3  | 40           |
| Linha 4  | 41           |
| Coluna 1 | 42           |
| Coluna 2 | 43           |
| Coluna 3 | 44           |
| Coluna 4 | 45           |

Layout das teclas:

| Coluna 1 | Coluna 2 | Coluna 3 | Coluna 4 |
| -------- | -------- | -------- | -------- |
| R1+      | R1       | R2+      | R2       |
| R3+      | R3       | R4+      | R4       |
| R5+      | R5       | R6+      | R6       |
| S1       | S2       | S3       | S4       |

## LEDs

### Mapa de pinos

| LED           | Pino Arduino | Função no firmware           |
| ------------- | ------------ | ---------------------------- |
| Modo decifrar | **48**       | aceso enquanto em DECIFRAR   |
| Modo cifrar   | **50**       | aceso enquanto em CIFRAR     |
| Mensagem      | **2**        | aceso durante envio/recepção |
| L1            | **46**       | bit 0 (binário)              |
| L2            | **47**       | bit 1                        |
| L3            | **49**       | bit 2                        |
| L4            | **51**       | bit 3                        |
| L5            | **3**        | bit 4                        |

### Pinos reservados

| Pinos | Uso                                |
| ----- | ---------------------------------- |
| 22–29 | Keypad 1                           |
| 30–37 | Keypad 2                           |
| 38–45 | Keypad 3                           |
| 20–21 | LCD I2C (SDA / SCL)                |
| 50–51 | LEDs ENC e L4 (também SPI MISO/MOSI no Mega — funciona pois só usamos como saída digital) |
| 2 e 3 | LEDs MSG e L5                      |

### LEDs binários L1 a L5 (valor da letra)

Codificação: `A=1`, `B=2`, `C=3` (L1+L2), … `Z=26`. Ex.: **C** acende L1 e L2.

- **Modo cifrar:** ao digitar uma letra, mostra a letra **cifrada** nos L1–L5 durante **1200 ms**.
- **Modo decifrar:** ao receber `MESSAGEFROMMOBILE:<cipher>`, mostra cada letra **decifrada** durante **1200 ms**; no fim acende todos os L1–L5 durante **5 s**.

## LCD 20x4 I2C

O LCD usa o barramento I2C do Arduino Mega 2560.

| LCD I2C | Arduino Mega 2560 |
| ------- | ----------------- |
| VCC     | 5V                |
| GND     | GND               |
| SDA     | 20                |
| SCL     | 21                |

Notas:

- No Arduino Mega, os pinos I2C principais são `SDA=20` e `SCL=21`.
- O endereço I2C comum do LCD é `0x27` ou `0x3F`. O sketch faz um scan I2C no boot e o endereço fica configurável em `config.h`.

### O que o LCD apresenta

- **Linha 1:** texto cifrado.
- **Linha 2:** texto em claro.
- **Linha 3:** alertas e mensagens curtas de estado (ex.: `SYNC OK`, `Configure rotores`, `LOCK ativo`).
- **Linha 4:** rotores ativos, na ordem e com a posição atual. Para a configuração `R1:6 R3:7 R5:14 R6:20`, o LCD apresenta:

  ```
  1:6 3:7 5:14 6:20
  ```

## Função Das Teclas

### Letras A–Z

Entrada de texto da máquina Enigma.

- **Modo CIFRAR:** com o `LOCK` ativo, cada letra digitada é cifrada com a posição atual dos rotores e mostrada nos LEDs binários por 1200 ms; o LCD acumula o texto cifrado (linha 1) e o texto em claro (linha 2). Limite de **20 caracteres** por mensagem.
- **Modo DECIFRAR:** as letras estão inativas; o Arduino apenas aguarda `MESSAGEFROMMOBILE:` do Raspberry Pi.

### LOCK

Sinaliza que o Arduino está com os rotores preparados — tanto para criar uma cifra como para receber uma. Enquanto `LOCK` não estiver ativo, as letras ficam inativas mesmo em CIFRAR. Qualquer alteração de rotores (seleção, incremento, shift) automaticamente sai do estado LOCK e exige novo bloqueio.

### MODE

Alterna entre `CIFRAR` ↔ `DECIFRAR`. **O estado inicial após o boot é CIFRAR.**

### RESET

Limpa o texto do LCD, remove a configuração de rotores, sai do estado LOCK e volta ao estado inicial do modo atual.

### SYNC

Envia o comando `SYNC` ao Raspberry Pi para obter a configuração de rotores que o app mobile gravou. A resposta esperada do Raspberry é `POS:<r1,pos>,<r2,pos>,...` (até 4 pares). Se não houver resposta em 1500 ms, o LCD mostra `SYNC: sem resposta`.

### SEND

Envia a mensagem cifrada para o Raspberry Pi quando estiver no modo CIFRAR e com `LOCK` ativo. Comportamento:

1. Envia `MESSAGEFROMARDUINO:<cipher>` pela Serial.
2. Acende o LED `Mensagem` durante 4 s.
3. Após o envio age como `RESET` (limpa texto, rotores e LOCK).

### R1, R2, R3, R4, R5, R6

Selecionam quais rotores estão ativos. Máximo de **4 rotores** ativos. Pressionar uma tecla R já selecionada remove-o do banco.

### R1+, R2+, R3+, R4+, R5+, R6+

Incrementam a posição do respetivo rotor em +1 (rotativo: depois de 25 volta a 0).

### S1, S2, S3, S4 (Shifters)

Trocam dois rotores adjacentes no banco. `S1` troca os slots 0 e 1, `S2` os slots 1 e 2 e assim por diante. Servem para ordenar os rotores selecionados.

## Comunicação Com O Raspberry Pi

USB Serial @ 115200 baud, linhas terminadas em `\n`.

### Arduino → Raspberry Pi

| Comando                       | Significado                                                     |
| ----------------------------- | --------------------------------------------------------------- |
| `MESSAGEFROMARDUINO:<cipher>` | Envia a cifra para o Raspberry Pi ao se clicar em `SEND`        |
| `SYNC`                        | Solicita a configuração de rotores armazenada no Raspberry      |
| `STATUS`                      | Solicita estado atual do Raspberry                              |

### Raspberry Pi → Arduino

| Resposta / Comando            | Significado                                                                     |
| ----------------------------- | ------------------------------------------------------------------------------- |
| `POS:<r1,pos>,<r2,pos>,...`   | Resposta ao `SYNC`. Lista os rotores ativos no Raspberry, na ordem e posição.   |
| `STATUS:OK`                   | Resposta ao `STATUS`                                                            |
| `MESSAGEFROMMOBILE:<cipher>`  | Cifra recebida do app mobile a ser decifrada pelo Arduino                       |

## Funcionamento do Arduino

O Arduino pode estar em 2 modos: `CIFRAR` ou `DECIFRAR`. **Estado inicial após boot: `CIFRAR`.**

### Modo CIFRAR

LED 50 aceso enquanto o modo estiver ativo.

1. Configurar os rotores:
   - **Via SYNC:** pressionar `SYNC` para buscar a configuração que o app mobile gravou.
   - **Manualmente:**
     1. Escolher até 4 rotores com `R1`–`R6`.
     2. Incrementar as posições com `R1+`–`R6+`.
     3. Ordenar com `S1`–`S4`.
2. Pressionar `LOCK` (a partir deste momento, as letras ficam ativas).
3. Escrever a mensagem (de A a Z, máximo 20 caracteres). Para cada letra:
   - LEDs binários L1–L5 acendem com a letra **cifrada** por 1200 ms.
   - Linha 1 do LCD acumula o texto cifrado.
   - Linha 2 do LCD acumula o texto em claro.
4. Pressionar `SEND`:
   - LED `Mensagem` acende por 4 s.
   - Envia `MESSAGEFROMARDUINO:<cipher>` ao Raspberry.
   - Age como `RESET` (limpa LCD, rotores e LOCK).

`RESET` clicado em qualquer momento antes do `SEND` apaga a mensagem em construção e os rotores, voltando ao estado inicial.

### Modo DECIFRAR

LED 48 aceso enquanto o modo estiver ativo.

1. Configurar os rotores (via `SYNC` ou manualmente como no modo CIFRAR).
2. Pressionar `LOCK` (a partir deste momento o Arduino está preparado para receber uma cifra).
3. Aguardar `MESSAGEFROMMOBILE:<cipher>` do Raspberry.
   - LED `Mensagem` acende.
   - Linha 1 do LCD mostra a mensagem cifrada; linha 2 mostra a mensagem decifrada.
   - Cada letra decifrada é mostrada nos L1–L5 por 1200 ms.
   - No fim, todos os L1–L5 ficam acesos durante 5 s.
4. O modo só reinicia se o utilizador clicar em `RESET`.
