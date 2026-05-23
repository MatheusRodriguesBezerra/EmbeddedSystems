# Comportamento Do Firmware Arduino

Este documento define o comportamento funcional do Arduino Mega 2560 no projeto Enigma Machine. Deve ser usado em conjunto com `README.md` (hardware) e `keypads.png` (layout das teclas).

Referências de algoritmo:

- `enigma-mobile/src/services/enigmaMachine.ts`
- `enigma-raspberry/enigma/machine.py`

O Arduino deve implementar **o mesmo algoritmo** para manter cifra/decifra compatível com o app e o Raspberry Pi.

---

## Avisos Sobre A Máquina Enigma

Pontos da sua proposta que foram ajustados ou que precisam de atenção:

### 1. Modos ENC e DEC

Na Enigma real e neste projeto, **cifrar e decifrar usam a mesma operação**. Não existe um algoritmo diferente por modo.

O campo `mode` (`ENC` / `DEC`) serve para:

- orientar a interface (LCD, LEDs, teclas ativas);
- documentar a intenção do fluxo half-duplex;
- sincronizar estado com o Raspberry Pi.

O sketch pode manter dois modos de UI, mas **ao processar letras** deve usar sempre a mesma função de transformação Enigma.

### 2. Posições dos rotores: 0 a 25 (não 0 a 26)

No mobile e no Raspberry, cada rotor tem **26 posições**, indexadas de **0 a 25** (equivalente às letras A–Z).

- Incremento: `(posição + 1) % 26`
- Posição inicial acordada: `(0, 0, 0)`

A referência “0 a 26” e “ao chegar em 26 volta a 0” foi normalizada para **0 a 25**, coerente com o resto do sistema.

**Sobre “0 não faz ações”:** na Enigma deste projeto, a posição `0` é uma posição válida (primeira posição do rotor). Se quiser um estado “não configurado” apenas para ecrã, use um indicador à parte; não misturar com o índice interno da cifra.

### 3. LEDs: pinos do comportamento vs README

Neste documento de comportamento, os LEDs de modo são:

| LED | Pino | Função |
| --- | --- | --- |
| LED 1 | 48 | Modo **decifrar** (estado inicial) |
| LED 2 | 50 | Modo **cifrar** |
| LED 3 | 52 | Mensagem pronta / recebida / enviada |

O `README.md` ainda lista pinos `46`, `48`, `50`. **Atualize o README** para ficar alinhado com `48`, `50`, `52` se esta for a ligação final.

### 4. Sincronização antes de processar mensagens

Para decifrar um payload recebido do Raspberry, o Arduino precisa ter **as mesmas posições iniciais de rotores** que foram usadas para cifrar essa mensagem (ou estar sincronizado via `SYNC` imediatamente antes). Caso contrário, o texto decifrado na linha 2 do LCD ficará errado.

### 5. Half-duplex com o Raspberry

- Em **modo decifrar** (UI), o Arduino comporta-se como **RECEIVING**: espera payload cifrado.
- Em **modo cifrar** (UI), o Arduino comporta-se como **SENDING**: envia payload cifrado com `SEND`.

O Raspberry deve estar no papel oposto em cada momento.

---

## Algoritmo Enigma (igual ao mobile)

Constantes (rotores fixos I, II, III e refletor B):

```text
Rotor I:   EKMFLGDQVZNTOWYHXUSPAIBRCJ
Rotor II:  AJDKSIRUXBLHWTMCQGZNPYFVOE
Rotor III: BDFHJLCPRTXVZNYEIWGAKMUSQO
Reflector: YRUHQSLDPXNGOKMIEBFZCWVJAT
```

Ordem default dos rotores: `I`, `II`, `III` (configurável via sync).

Por cada letra `A`–`Z`:

1. Avançar o rotor da direita: `pos[2] = (pos[2] + 1) % 26`
2. Passar pelos 3 rotores (direita → esquerda), forward
3. Refletor
4. Voltar pelos 3 rotores (esquerda → direita), backward
5. Produzir letra de saída

Mensagem completa: repetir por letra, **atualizando posições após cada letra**.

Implementação de referência: `enigma-mobile/src/services/enigmaMachine.ts`.

---

## LCD 20x4

| Linha | Conteúdo |
| --- | --- |
| 1 | Texto **cifrado** (enviado ou recebido) |
| 2 | Texto **em claro** (antes de cifrar ou após decifrar) |
| 3 | Vazia (reservada) |
| 4 | Posições dos 3 rotores, ex.: `POS: 0, 0, 0` ou `R1:5 R2:3 R3:10` |

Limite prático de composição no modo cifrar: **20 caracteres** (largura da linha do LCD).

Atualizar linha 4 sempre que `R1`, `R2` ou `R3` alterarem posições.

---

## Estado Inicial

- Modo UI: **decifrar** (Arduino inicia neste modo)
- Posições dos rotores: `0, 0, 0`
- LED 1 (pino 48): ligado
- LED 2 (pino 50): desligado
- LED 3 (pino 52): desligado
- Linhas 1 e 2 do LCD: vazias ou apagadas conforme implementação
- Linha 4: mostra posições `0, 0, 0`
- String de composição (modo cifrar): vazia

---

## Modo Decifrar (estado inicial)

### Indicação visual

- **LED 1 (48):** ligado
- **LED 2 (50):** desligado
- **LED 3 (52):** desligado até chegar mensagem cifrada

### Teclas ativas

| Tecla | Ação |
| --- | --- |
| `R1`, `R2`, `R3` | Incrementa posição do rotor respetivo: `(pos + 1) % 26`; atualiza LCD linha 4 |
| `RESET/SYNC` | Pedido de sincronização ao Raspberry (ver secção SYNC) |
| `MODE` | Alterna para modo **cifrar** |
| Letras `A`–`Z` | **Sem função** neste modo |
| `SEND` | **Sem função** neste modo |

### Espera de mensagem cifrada (Raspberry → Arduino)

Enquanto **não** receber payload cifrado:

- LED 1 ligado
- Linhas 1 e 2 do LCD vazias (ou mensagem de espera discreta na linha 3, opcional)
- Linha 4 com posições atuais dos rotores

Quando receber payload cifrado (ex.: linha Serial `IN:<payload>` ou protocolo acordado):

1. Guardar payload na linha 1 do LCD (truncar a 20 chars se necessário)
2. Decifrar localmente com o algoritmo Enigma e posições **atuais** dos rotores **antes** de processar a primeira letra; avançar rotores letra a letra como no mobile
3. Mostrar resultado em claro na linha 2
4. Ligar **LED 3 (52)**
5. Atualizar linha 4 com posições finais após processar a mensagem

Nota: se o sync não estiver alinhado com o emissor, a linha 2 ficará incorreta — usar `RESET/SYNC` antes de receber.

---

## Modo Cifrar

Só é possível entrar/sair através da tecla **`MODE`** (toggle com modo decifrar).

### Indicação visual

- **LED 1 (48):** desligado
- **LED 2 (50):** ligado
- **LED 3 (52):** desligado até enviar; pode acender após `SEND`

### String de composição

- Variável `String` (ou buffer), inicialmente vazia
- Cada letra pressionada é acrescentada (máximo 20 caracteres, só `A`–`Z`)
- Após cada letra (ou ao atualizar o buffer completo), recalcular:
  - linha 2: texto em claro
  - linha 1: texto cifrado com Enigma a partir das posições atuais e avanço letra a letra

### Teclas ativas

| Tecla | Ação |
| --- | --- |
| Letras `A`–`Z` | Concatena à string (limite LCD); atualiza linhas 1 e 2 |
| `R1`, `R2`, `R3` | Incrementa rotor; recalcula cifra da string atual; atualiza linha 4 |
| `RESET/SYNC` | Limpa string; pedido SYNC; repõe rotores conforme resposta |
| `SEND` | Envia payload cifrado ao Raspberry; liga LED 3; ver protocolo |
| `MODE` | Volta ao modo **decifrar** |

### Tecla SEND

1. Obter texto cifrado atual (linha 1 / resultado do algoritmo)
2. Ligar **LED 3 (52)**
3. Enviar ao Raspberry Pi, por exemplo: `SEND:<payload>` ou encaminhar para HTTP via bridge no Pi
4. Manter LED 3 até o utilizador carregar `RESET/SYNC` para estado inicial (limpar string, desligar LED 3, restaurar UI de espera em decifrar se voltar ao modo decifrar)

### Tecla RESET/SYNC (modo cifrar)

1. **Reset:** string de composição = vazia; linhas 1 e 2 limpas
2. **Sync:** pedir estado ao Raspberry

---

## Tecla RESET/SYNC (ambos os modos)

Comportamento unificado sugerido para a tecla física `RESET/SYNC`:

| Ação | Efeito |
| --- | --- |
| Sync | Enviar `SYNC` ou `STATUS` ao Raspberry por Serial |
| Sem resposta válida | Posições dos rotores := `0, 0, 0`; atualizar linha 4 |
| Com resposta | Aplicar posições recebidas, ex.: `POS:5,3,10` → `(5, 3, 10)` |

Resposta esperada do Raspberry:

```text
POS:<r1>,<r2>,<r3>
```

Opcionalmente incluir ordem de rotores e modo na mesma mensagem ou em `STATUS:...`.

---

## Protocolo Serial (Arduino ↔ Raspberry)

### Arduino → Raspberry

| Comando | Quando |
| --- | --- |
| `SYNC` | Tecla RESET/SYNC |
| `SEND:<payload>` | Tecla SEND no modo cifrar (payload já cifrado) |
| `MODE:ENC` / `MODE:DEC` | Alternância de modo UI (opcional, para o Pi alinhar turno) |
| `STATUS` | Pedido de estado |

Os comandos `KEY:<letra>` por letra **não são necessários** no fluxo descrito (composição local + envio em bloco). Podem manter-se como extensão.

### Raspberry → Arduino

| Resposta | Significado |
| --- | --- |
| `POS:<r1>,<r2>,<r3>` | Posições dos rotores após sync |
| `IN:<payload>` | Payload cifrado para o Arduino decifrar no modo decifrar |
| `ACK:<messageId>` | Confirmação de receção de `SEND` |
| `ERR:<mensagem>` | Erro de sync, turno ou payload |

---

## Diagrama De Estados (resumo)

```text
                    [INÍCIO: modo decifrar]
                    LED1 ON, LED2 OFF
                    Espera IN:<payload>
                           |
              +------------+------------+
              |                         |
        (recebe payload)            (MODE)
              |                         |
        LED3 ON, L1=cifrado      [modo cifrar]
        L2=decifrado            LED2 ON, LED1 OFF
              |                 composição + cifra local
         (RESET/SYNC)                |
              |                 (SEND) -> Pi
              v                 LED3 ON
         sync / reset              |
              |                 (RESET/SYNC)
              +--------+---------+
                       |
                  (MODE) volta
                  a decifrar
```

---

## Checklist De Implementação

- [ ] Biblioteca Keypad (2x 4x4) pinos 22–29 e 30–37
- [ ] LCD I2C 20x4 (SDA 20, SCL 21)
- [ ] LEDs nos pinos 48, 50, 52 com resistores
- [ ] Módulo `enigma.cpp` / `enigma.h` com mesmo algoritmo que `enigmaMachine.ts`
- [ ] Parser Serial para `IN:`, `POS:`, `ACK:`
- [ ] Toggle MODE entre modos UI
- [ ] Limite de 20 caracteres na composição
- [ ] Sync antes de decifrar mensagem recebida quando o projeto exigir alinhamento estrito

---

## Diferenças Em Relação Ao README.md Antigo

| Tópico | README antigo | Este documento |
| --- | --- | --- |
| LEDs de modo | 46, 48, 50 genéricos | 48=decifrar, 50=cifrar, 52=evento |
| Fluxo de letras | `KEY:` por tecla ao Pi | Composição local + `SEND:<cipher>` |
| Modo DEC | Não detalhado | Espera `IN:<payload>`, decifra local |
| Posições | Não especificado | 0–25, início 0,0,0 |

Recomenda-se atualizar `README.md` para apontar para este ficheiro como especificação de firmware.
