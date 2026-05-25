# Enigma Arduino

Este documento descreve a disposição física prevista para o Arduino Mega 2560 no projeto Enigma Machine. Ele deve servir como base para o desenvolvimento do sketch do Arduino e para a integração com o Raspberry Pi.

## Hardware Principal

- Arduino Mega 2560
- 2 keypads 4x4
- 3 LEDs simples de dois pinos
- LCD 20x4 com módulo I2C/IIC
- Comunicação USB Serial com o Raspberry Pi

## Mapeamento De Pinos

### Keypad 1

O Keypad 1 usa os pinos digitais `22` a `29`.

Sugestão de ligação:

| Função | Pino Arduino |
| --- | --- |
| Linha 1 | 22 |
| Linha 2 | 23 |
| Linha 3 | 24 |
| Linha 4 | 25 |
| Coluna 1 | 26 |
| Coluna 2 | 27 |
| Coluna 3 | 28 |
| Coluna 4 | 29 |

Layout das teclas:

| Coluna 1 | Coluna 2 | Coluna 3 | Coluna 4 |
| --- | --- | --- | --- |
| A | B | C | D |
| E | F | G | H |
| I | J | K | L |
| M | N | O | P |

### Keypad 2

O Keypad 2 usa os pinos digitais `30` a `37`.

Sugestão de ligação:

| Função | Pino Arduino |
| --- | --- |
| Linha 1 | 30 |
| Linha 2 | 31 |
| Linha 3 | 32 |
| Linha 4 | 33 |
| Coluna 1 | 34 |
| Coluna 2 | 35 |
| Coluna 3 | 36 |
| Coluna 4 | 37 |

Layout das teclas (ver `keypads.png`):

| Coluna 1 | Coluna 2 | Coluna 3 | Coluna 4 |
| --- | --- | --- | --- |
| Q | R | S | T |
| U | V | W | X |
| Y | Z | SEND | MODE |
| R1 | R2 | R3 | RESET/SYNC |

Conjunto completo: 26 letras + `SEND` + `RESET/SYNC` + `R1` + `R2` + `R3` + `MODE`.

## LEDs

### Porque ficam fracos sem resistor?

Ligar **LED direto** ao pino do Arduino (sem resistor) **nao e recomendado**:

1. O Mega **limita a corrente** de cada pino (~40 mA max., ~20 mA recomendado).
2. Com **varios LEDs** ligados (48, 50, 52 + L1–L5), a corrente divide-se e todos parecem **mais fracos**.
3. No fim da mensagem decifrada o firmware acende **5 LEDs ao mesmo tempo** — e o pior caso para brilho.
4. Sem resistor o LED e o pino do Arduino podem **aquecer** e degradar; o brilho fica instavel.

**Conclusao:** use sempre resistor em serie. O resistor nao “rouba” luz de forma errada — ele define uma corrente segura; com o valor certo o LED fica **mais brilhante e estavel** do que no limite estranho sem resistor.

### Ligacao correta (5 V, um LED por pino)

```text
Pino Arduino (48, 46, etc.) ----[ resistor ]----(+ LED -)---- GND
```

- **Perna longa (+)** do LED → lado do resistor que vem do pino.
- **Perna curta (-)** → **GND** comum da protoboard.
- **GND do Arduino** ligado ao trilho `-` da protoboard.

### Qual resistor usar (mais brilho, ainda seguro)

Formula: `R = (5 V - V_LED) / I`

| Cor LED (tipico) | V_LED | Resistor | Corrente aprox. | Brilho |
| --- | --- | --- | --- | --- |
| Vermelho / amarelo | ~2,0 V | **150 Ω** | ~20 mA | Forte |
| Verde | ~2,2 V | **150 Ω** | ~19 mA | Forte |
| Azul / branco | ~3,0 V | **100 Ω** | ~20 mA | Forte |
| Uso conservador | — | **220 Ω** | ~10–15 mA | Medio (seguro) |

Para o projeto academico, **150 Ω** (vermelho/verde) ou **100 Ω** (azul/branco) costuma resolver “LED fraco”. **220 Ω** e mais suave.

Compre um kit **150 Ω + 220 Ω**; custo baixo e evita queimar pinos.

### Limites do Arduino Mega

- Por pino: evite passar de **20 mA** continuos.
- **Total** de todos os pinos: nao ultrapassar ~**200 mA** somados.
- Com 8 LEDs a ~15 mA cada, se **todos** estiverem ON ao mesmo tempo (~120 mA), ainda e aceitavel **com resistor em cada um**.

Se precisar de muito brilho com muitos LEDs ON juntos, use **transistor** (ex. 2N2222) ou modulo a 5 V externo — fora do escopo minimo do projeto.

Mapeamento definido (ver `COMPORTAMENTO.md` para funções de firmware):

| LED | Pino Arduino | Função no firmware |
| --- | --- | --- |
| Modo decifrar | **48** | Estado inicial / modo DEC |
| Modo cifrar | **50** | Modo ENC |
| Mensagem | **54** (A0) | Mensagem recebida ou enviada |
| L1 | **46** | bit 0 (binario) |
| L2 | **47** | bit 1 |
| L3 | **49** | bit 2 |
| L4 | **51** | bit 3 |
| L5 | **55** (A1) | bit 4 |

### Pinos reservados e SPI (Mega 2560)

| Pinos | Uso |
| --- | --- |
| 22–29 | Keypad 1 |
| 30–37 | Keypad 2 |
| **38–45** | Keypad 3 (futuro) |
| 20–21 | LCD I2C (SDA/SCL) |
| 50–51 | SPI MISO/MOSI — **ENC e L4** (funcionam na sua montagem) |
| **52–53** | SPI SCK/SS — **evitar**; MSG e L5 usam **54 (A0)** e **55 (A1)** |

### LEDs binarios L1 a L5 (valor da letra)

**Um resistor por LED** (mesma regra acima). L1 e o bit menos significativo (LSB).

| LED | Pino | Bit |
| --- | --- | --- |
| L1 | 46 | 0 |
| L2 | 47 | 1 |
| L3 | 49 | 2 |
| L4 | 51 | 3 |
| L5 | 55 (A1) | 4 |

Codificacao: `A=1`, `B=2`, `C=3` (L1+L2), ... `Z=26`. Ex.: **C** acende L1 e L2.

- **Modo cifrar:** ao digitar, mostra a letra **cifrada** nos L1-L5 durante 2 s.
- **Modo decifrar:** ao receber `IN:<payload>`, mostra cada letra **decifrada** 2 s; no fim todos os L1-L5 acesos 5 s.

### Checklist se o LED continua fraco

1. Confirmar **polaridade** (perna longa no resistor vindo do pino).
2. **GND comum** entre Arduino e todos os LEDs.
3. Colocar **150 Ω** (ou 100 Ω em LED azul/branco) em **cada** LED.
4. Testar **um LED so** no pino 46: se ficar forte, o problema era corrente partilhada / varios sem resistor.
5. No Serial Monitor (115200), no boot deve aparecer o teste dos LEDs modo e L1-L5.

Ligação recomendada (resumo):

| Elemento | Ligação |
| --- | --- |
| Pino digital | Uma ponta do resistor |
| Outra ponta do resistor | Perna maior do LED |
| Perna menor do LED | GND |

Exemplo lógico:

| LED | Caminho |
| --- | --- |
| Modo DEC | Pino 48 -> resistor -> LED -> GND |
| Modo ENC | Pino 50 -> resistor -> LED -> GND |
| Mensagem | Pino 54 (A0) -> resistor -> LED -> GND |
| L1–L5 | Pinos 46, 47, 49, 51, 55 -> resistor -> LED -> GND |

## LCD 20x4 I2C

O LCD usa o barramento I2C do Arduino Mega 2560.

| LCD I2C | Arduino Mega 2560 |
| --- | --- |
| VCC | 5V |
| GND | GND |
| SDA | 20 |
| SCL | 21 |

Notas:

- No Arduino Mega, os pinos I2C principais são `SDA 20` e `SCL 21`.
- O endereço I2C comum do LCD é `0x27` ou `0x3F`.
- O sketch deve permitir ajustar o endereço caso o módulo use outro valor.

## Função Das Teclas

### Letras

As teclas `A` a `Z` representam a entrada de texto da máquina Enigma.

Ao pressionar uma letra, o Arduino deve enviar ao Raspberry Pi um comando Serial:

| Evento | Comando Serial |
| --- | --- |
| Letra pressionada | `KEY:<letra>` |

Exemplo:

```text
KEY:A
```

### SEND

Tecla usada para indicar envio/conclusão da mensagem atual.

Comando Serial sugerido:

```text
SEND
```

### RESET/SYNC

Tecla física única com duas funções lógicas, conforme `keypads.png`:

| Função | Comportamento sugerido | Comando Serial |
| --- | --- | --- |
| **RESET** | Limpa a mensagem em composição, reinicia entrada local ou pede reset de estado ao Raspberry | `RESET` |
| **SYNC** | Solicita sincronização de configuração e estado com o Raspberry Pi (rotores, posições, modo, turno) | `SYNC` |

Sugestão de implementação no sketch:

- **toque curto**: envia `RESET`
- **toque longo** (ex.: > 1 s): envia `SYNC`

Alternativa: alternar a função ativa no LCD e confirmar com um único toque. O importante é que a mesma tecla física dispare um dos dois comandos, nunca ambos ao mesmo tempo.

Exemplos:

```text
RESET
SYNC
```

### R1, R2, R3

Teclas usadas para selecionar ou ajustar os rotores físicos/lógicos.

Uso sugerido:

- `R1`: selecionar rotor 1
- `R2`: selecionar rotor 2
- `R3`: selecionar rotor 3

Os LEDs `48`, `50` e `52` indicam modo e estado da mensagem (ver `COMPORTAMENTO.md`).

Comando Serial sugerido para alteração de posição:

```text
ROTOR:<indice>:<delta>
```

Exemplo:

```text
ROTOR:1:1
```

### MODE

Tecla usada para alternar entre modo de cifra e decifra.

Comandos Serial sugeridos:

```text
MODE:ENC
MODE:DEC
```

## Comunicação Com O Raspberry Pi

O Arduino comunica com o Raspberry Pi por USB Serial.

Comandos previstos do Arduino para o Raspberry:

| Comando | Significado |
| --- | --- |
| `KEY:<letra>` | Envia uma letra pressionada |
| `ROTOR:<indice>:<delta>` | Altera posição de um rotor |
| `MODE:<ENC\|DEC>` | Altera modo lógico |
| `SEND` | Finaliza/envia mensagem atual |
| `RESET` | Solicita limpeza ou reset local/remoto |
| `SYNC` | Solicita sincronização de configuração e estado com o Raspberry |
| `STATUS` | Solicita estado atual |

Respostas previstas do Raspberry para o Arduino:

| Resposta | Significado |
| --- | --- |
| `OUT:<letra>` | Letra cifrada/decifrada resultante |
| `POS:<r1>,<r2>,<r3>` | Posições atuais dos rotores |
| `STATUS:<mensagem>` | Estado ou informação geral |

## Observações De Desenvolvimento

- Os pinos `22` a `37` ficam reservados exclusivamente para os dois keypads.
- Os pinos `20` e `21` ficam reservados ao LCD I2C.
- Os pinos `48`, `50` e `52` ficam reservados aos LEDs.
- Especificação completa de comportamento: `COMPORTAMENTO.md`.
- Sketch para instalar: pasta `enigma_machine/` (ver `INSTALACAO_ARDUINO.md`).
- Cada LED deve usar resistor em série.
- Se as teclas aparecerem trocadas durante os testes, ajuste a ordem dos arrays de linhas e colunas no sketch.
- A imagem `keypads.png` representa o layout físico pretendido das teclas.
