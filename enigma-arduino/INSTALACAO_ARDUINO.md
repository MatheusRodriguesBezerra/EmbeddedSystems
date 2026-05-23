# Instalação Do Sketch No Arduino Mega

## Estrutura

Abra a pasta do sketch no Arduino IDE:

`enigma-arduino/enigma_machine/`

Ficheiros:

- `enigma_machine.ino` — programa principal
- `enigma.cpp` / `enigma.h` — algoritmo Enigma (igual ao mobile)
- `config.h` — pinos e constantes

## Bibliotecas

No Arduino IDE: **Sketch → Include Library → Manage Libraries**

Instale:

1. **Keypad** (Mark Stanley, Chris Young)
2. **LiquidCrystal I2C** (Frank de Brabander)

## Placa e porta

- Placa: **Arduino Mega 2560**
- Porta: USB ligada ao PC ou ao Raspberry Pi
- Velocidade Serial: **115200 baud** (igual ao `Serial.begin` do sketch)

## LCD I2C

Se o LCD não mostrar nada, altere o endereço em `config.h`:

```cpp
#define LCD_I2C_ADDR 0x27
```

Teste também `0x3F` se `0x27` não funcionar.

## Carregar o programa

1. Abra `enigma_machine.ino`
2. Verifique a placa e a porta
3. Clique em **Upload**

## Teste sem Raspberry Pi

1. Modo inicial: **decifrar** (LED no pino 48 ligado)
2. Abra o **Serial Monitor** a 115200 baud, fim de linha **Nova linha**
3. Envie: `IN:NCP` (exemplo) — o Arduino mostra cifrado na linha 1 e claro na linha 2, se as posições estiverem corretas
4. Carregue **MODE** no keypad para modo **cifrar** (LED pino 50)
5. Digite letras; **SEND** envia `SEND:<payload>` pela Serial

## Com Raspberry Pi

O Pi deve enviar linhas terminadas em `\n`:

| Linha | Exemplo |
| --- | --- |
| Payload recebido | `IN:OLA` |
| Posições após sync | `POS:0,0,0` |

O Arduino envia:

| Comando | Exemplo |
| --- | --- |
| Sync | `SYNC` |
| Envio | `SEND:NCP` |
| Modo | `MODE:ENC` ou `MODE:DEC` |

## Verificar se funciona

### Ao ligar o Arduino (sem carregar em nenhuma tecla)

| O que deve acontecer | Significado |
| --- | --- |
| LEDs 48, 50 e 52 piscam uma vez cada | Sketch a correr |
| LED no pino **48** fica ligado | Modo decifrar ativo |
| LCD linha 1: `Enigma iniciado` | LCD I2C OK |
| LCD linha 4: `R1:0 R2:0 R3:0` | Posicoes dos rotores |
| LCD linha 3: `Aguardando IN:...` | Espera mensagem do Pi |

Se **nada** disto acontecer, o problema é hardware ou LCD/endereco I2C, nao as teclas.

### Teclas no modo inicial (decifrar)

| Tecla | Efeito esperado |
| --- | --- |
| **R1, R2, R3** | Valores na linha 4 mudam (ex. `R1:1`) |
| **MODE** | LED 50 liga, LED 48 apaga (modo cifrar) |
| **RESET/SYNC** | Pede sync; sem Raspberry repoe `0,0,0` |
| **Letras A–Z** | **Nao fazem nada** (mensagem `DEC: letras inativas` na linha 3) |

### Modo cifrar (tecla MODE)

| Tecla | Efeito esperado |
| --- | --- |
| **Letras** | Aparecem na linha 2; linha 1 mostra cifrado |
| **SEND** | LED 52 liga; Serial envia `SEND:...` |
| **MODE** | Volta ao modo decifrar |

### Serial Monitor (115200 baud)

Deve aparecer ao ligar:

```text
ENIGMA: boot
ENIGMA: pronto (modo DEC)
```

Ao carregar numa tecla (com `DEBUG_KEYS` ativo em `config.h`):

```text
Keypad 1 tecla=0x41
```

Teste manual no modo decifrar: envie `IN:ABC` (com posicoes corretas) para simular mensagem do Raspberry.

### LCD em branco

1. Gire o potenciometro de **contraste** no modulo I2C (se existir) — LCD pode estar a funcionar mas invisivel.
2. Em `config.h`, mude `LCD_I2C_ADDR` de `0x27` para `0x3F` e volte a fazer upload.
3. Confirme: **SDA → 20**, **SCL → 21**, **5V**, **GND** (Mega 2560).
4. Use o sketch **`hardware_test/`** (pasta separada) para isolar LCD e LEDs.

### Nada funciona (LCD vazio E LEDs apagados)

Ordem de diagnostico:

1. **Placa correta?** Deve ser **Arduino Mega 2560**. Pinos 48, 50, 52 **nao existem** no Uno/Nano.
2. **Upload OK?** No IDE deve aparecer "Done uploading". Porta COM correta em Ferramentas.
3. **LED L (onboard)** no Mega: carregue `hardware_test` — deve piscar a cada segundo no `loop`.
4. Se **LED L nao pisca**: sketch nao corre (placa errada, cabo USB so alimenta, ou upload falhou).
5. Se **LED L pisca** mas externos nao: cablagem dos LEDs (pino → resistor → LED → GND).
6. Se **LEDs OK** mas LCD vazio: endereco I2C ou contraste ou fios SDA/SCL trocados.
7. O sketch principal antigo podia **bloquear no lcd.init()** antes de acender LEDs; versao atual acende LEDs **antes** do LCD.

### LEDs nunca acendem

1. Confirme: resistor em serie + LED entre pino e GND (pinos **48, 50, 52**).
2. Teste cada LED com um fio: pino → resistor → LED → GND.
3. Se so piscam no arranque e depois nada: sketch OK, verifique modo (LED 48 em decifrar).

### Keypad sem resposta

1. Confirme fios: keypad1 **22–29**, keypad2 **30–37**.
2. Abra Serial Monitor: se nao aparece `Keypad X tecla=...`, o Arduino nao deteta tecla (cablagem ou pinos trocados).
3. Troque no codigo linhas/colunas se o layout fisico for diferente.

## Documentação

- Hardware: `README.md`
- Comportamento: `COMPORTAMENTO.md`
