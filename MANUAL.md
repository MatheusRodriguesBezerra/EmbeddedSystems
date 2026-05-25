# Manual do Sistema Enigma Machine

Documento de referência do projeto **Embutidos** (Mestrado): máquina Enigma distribuída em três partes — **Arduino Mega**, **Raspberry Pi** e **app mobile** (Expo/React Native).

---

## 1. Visão geral

O sistema simula uma **máquina Enigma** para cifrar e decifrar texto (apenas letras A–Z). A cifragem é feita **localmente** no telemóvel e no Arduino. O Raspberry Pi **não cifra nem decifra**; funciona apenas como **ponte de comunicação** e guarda o **turno half-duplex** (quem pode enviar mensagem em cada momento).

```text
┌─────────────────┐         Wi-Fi HTTP          ┌──────────────────┐
│   App Mobile    │ ◄──────────────────────────► │  Raspberry Pi    │
│  (cifra/decifra)│                              │  (ponte + turno) │
└─────────────────┘                              └────────┬─────────┘
                                                            │ USB Serial
                                                            │ 115200 baud
                                                   ┌────────▼─────────┐
                                                   │  Arduino Mega    │
                                                   │  (cifra/decifra) │
                                                   │  3 keypads + LCD │
                                                   └──────────────────┘
```

### Responsabilidades

| Componente | O que faz | O que não faz |
|------------|-----------|----------------|
| **Mobile** | Interface, cifra/decifra local, envia **cipher** ao Pi | Não fala Serial com Arduino |
| **Raspberry Pi** | HTTP ↔ Serial, turno, histórico, `CFG:` no SYNC | Não executa algoritmo Enigma |
| **Arduino** | Teclados, LCD, LEDs, cifra/decifra local, Serial com Pi | Não fala Wi-Fi com o telemóvel |

---

## 2. Arquitetura de comunicação

Existem **dois canais** independentes:

1. **Wi-Fi** — App ↔ Raspberry Pi (FastAPI, porta 8000).
2. **USB Serial** — Arduino ↔ Raspberry Pi (115200 baud, texto linha a linha).

O mobile **nunca** comunica diretamente com o Arduino. Toda mensagem entre eles passa pelo Pi.

### 2.1 O que trafega em cada tipo de ligação

| Tipo | Quando | Conteúdo |
|------|--------|----------|
| **Configuração** | Explícito: botão SYNC (Arduino) ou “Salvar e sincronizar” (app) | Ordem e posições dos rotores (`CFG:` / `POST /config`) |
| **Mensagem** | Envio de texto cifrado | Apenas o **payload** (letras A–Z), sem configuração de rotores |
| **Turno** | Mudança de aba no app (`POST /role`) | Apenas `SENDING` / `RECEIVING` / `IDLE` |

Isto significa que **cada operador** (app e Arduino) pode ajustar rotores **manualmente** no seu dispositivo. Para o texto decifrar corretamente, ambos devem usar a **mesma** configuração Enigma (mesmos rotores, mesma ordem, mesmas posições iniciais). O Pi **não garante** esse alinhamento nas mensagens — só transporta o cipher.

---

## 3. Half-duplex (turno de envio)

Só **uma ponta** deve “enviar” uma mensagem de cada vez, para evitar colisões e confusão de estado.

### Papéis

| Papel | Significado |
|-------|-------------|
| `SENDING` | Esta ponta **pode enviar** uma mensagem cifrada agora |
| `RECEIVING` | Esta ponta **aguarda** receber uma mensagem |
| `IDLE` | Sem turno definido |

### Regra no Raspberry Pi (complementar ao app)

O app envia o seu papel em `POST /config` e `POST /role`. O Pi guarda o papel **oposto** (complementar):

| App mobile (aba / intenção) | Papel guardado no Pi |
|----------------------------|----------------------|
| Send → `SENDING` | `RECEIVING` |
| Receive → `RECEIVING` | `SENDING` |

### Quem pode fazer o quê no Pi

| Ação | Papel exigido no Pi |
|------|---------------------|
| Mobile envia cipher (`POST /message`) | `RECEIVING` |
| Arduino envia cipher (`SEND:` na Serial) | `SENDING` |
| App consulta `/pending` | Pi em `SENDING` (mensagem vinda do Arduino) |

Após cada mensagem relay com sucesso, o Pi **inverte** o turno (`SENDING` ↔ `RECEIVING`).

---

## 4. App mobile

### Função

- Cifrar e decifrar no telemóvel (`enigmaMachine.ts`).
- Enviar **payload já cifrado** ao Pi.
- Receber payload do Arduino via polling em `/pending`.
- Sincronizar **configuração de rotores** apenas ao guardar definições (`POST /config`).

### Abas

| Aba | Papel local | Efeito no Pi (`POST /role`) |
|-----|-------------|------------------------------|
| **Send** | `SENDING` | Pi → `RECEIVING` |
| **Receive** | `RECEIVING` | Pi → `SENDING` |

### Rotores no app

- Até **4 rotores ativos**, escolhidos entre **R1–R6** (wirings históricos I–VI).
- Ordem e posições configuráveis no modal de definições.
- Botões **S1–S4** equivalentes ao Arduino: trocam ordem (shift right).

### Fluxo: enviar mensagem (mobile → Arduino)

1. Utilizador na aba **Send**, com rotores configurados.
2. App cifra localmente: `OLA` → `LXMPQGB` (exemplo).
3. App chama `POST /role` com `SENDING` (Pi fica `RECEIVING`).
4. App chama `POST /message` com `{ "payload": "LXMPQGB" }`.
5. Pi encaminha `IN:LXMPQGB` ao Arduino (sem `CFG:`).
6. Pi inverte turno; app passa a `RECEIVING`.
7. Arduino, em modo **decifrar**, processa `IN:` e mostra texto claro no LCD.

### Fluxo: receber mensagem (Arduino → mobile)

1. Utilizador na aba **Receive`.
2. App faz polling `GET /pending` a cada ~2 s.
3. Quando há mensagem, app decifra localmente com **os seus** rotores configurados.
4. App atualiza posições localmente após decifrar.

### API HTTP (resumo)

| Método | Rota | Uso |
|--------|------|-----|
| `GET` | `/ping` | Testar ligação |
| `GET` | `/state` | Estado do Pi + pending |
| `POST` | `/config` | **Sincronização explícita** de rotores + modo |
| `POST` | `/role` | Apenas turno |
| `POST` | `/message` | Enviar cipher (corpo JSON) |
| `GET` | `/message/{payload}` | Mesmo relay (compatibilidade) |
| `GET` | `/pending` | Receber cipher do Arduino |

---

## 5. Raspberry Pi

### Função

- Servidor **FastAPI** na porta **8000**.
- Ponte **Serial** ↔ **HTTP**.
- Persistência em `state/enigma_state.json`.
- Envio de `CFG:` ao Arduino quando:
  - App faz `POST /config`, ou
  - Arduino pede `SYNC`.

### Protocolo Serial (Arduino → Pi)

| Linha enviada pelo Arduino | Significado |
|--------------------------|-------------|
| `SYNC` | Pedir configuração guardada no Pi |
| `SEND:ABC` | Enviar payload cifrado (Arduino cifrou localmente) |
| `MODE:ENC` / `MODE:DEC` | Informar modo UI (estado no Pi) |
| `STATUS` | Pedir estado (resposta com CFG e role) |

| Linha enviada pelo Pi → Arduino | Significado |
|--------------------------------|-------------|
| `CFG:2,10,1,2,5,15,3,16` | Configuração de rotores (pares `id,pos`) |
| `CFG:` | Sem rotores selecionados |
| `IN:ABC` | Payload cifrado para decifrar no LCD |
| `ACK:uuid` | Mensagem aceite |
| `ERR:...` | Erro (ex. `NOT_SENDING`, `PAYLOAD_VAZIO`) |

**Importante:** nas mensagens, o Pi envia **apenas** `IN:...`, sem `CFG:` antes ou depois. A configuração dos rotores no Arduino é responsabilidade do operador ou do botão **SYNC**.

### Fluxo: mobile → Arduino (via Pi)

```text
App POST /message { payload }
    → Pi (role RECEIVING) aceita
    → Serial: IN:payload
    → Arduino decifra em modo DEC
    → Pi role → SENDING
```

### Fluxo: Arduino → mobile (via Pi)

```text
Arduino SEND:payload
    → Pi (role SENDING) guarda em pending
    → App GET /pending
    → App decifra localmente
    → Pi role → RECEIVING
```

---

## 6. Arduino Mega

### Hardware

- **3 keypads** 4×4 (pinos 22–45).
- **LCD** 20×4 I2C (SDA 20, SCL 21).
- **LEDs** de modo (DEC, ENC, MSG) e **5 LEDs binários** (valor da letra A=1 … Z=26).
- **USB Serial** para o Pi.

### Keypads (layout atual — ver `enigma-arduino/keypads.png`)

**Keypad 1** (22–29): letras **A–P**.

**Keypad 2** (30–37):

| | | | |
|--|--|--|--|
| Q | R | S | T |
| U | V | W | X |
| Y | Z | — | — |
| MODE | RESET | SYNC | SEND |

**Keypad 3** (38–45) — rotores dinâmicos:

| | | | |
|--|--|--|--|
| R1+ | R1 | R2+ | R2 |
| R3+ | R3 | R4+ | R4 |
| R5+ | R5 | R6+ | R6 |
| S1 | S2 | S3 | S4 |

| Tecla | Função |
|-------|--------|
| **R1…R6** | Seleciona/deseleciona rotor (máx. 4) |
| **R1+…R6+** | Incrementa posição desse rotor |
| **S1…S4** | Troca ordem (shift right na posição N) |
| **RESET** | Limpa todos os rotores selecionados |
| **SYNC** | Pede `CFG:` ao Pi (config guardada pelo app) |
| **MODE** | Alterna modo cifrar / decifrar |
| **SEND** | Envia cipher ao Pi (modo cifrar) |

### LCD (linhas)

| Linha | Conteúdo |
|-------|----------|
| 0 | Texto **cifrado** |
| 1 | Texto **em claro** |
| 2 | Mensagens de estado / erro |
| 3 | Rotores ativos, ex.: `2:10 1:2 5:15 3:16` |

### Modos de interface

| Modo | LED DEC | LED ENC | Teclas de letras |
|------|---------|---------|------------------|
| **Decifrar** | ON | off | Inativas (espera `IN:` do Pi) |
| **Cifrar** | off | ON | Ativas; compõe texto e mostra cipher |

### Rotores no firmware

- **6 tipos** de rotor (R1–R6), wirings da Enigma histórica I–VI.
- **0 a 4** rotores ativos na cadeia.
- Início **sem rotores**; utilizador escolhe com **R1…R6**.
- Cifra/decifra só funciona com pelo menos 1 rotor selecionado.

### Algoritmo (resumo)

Por cada letra A–Z:

1. Avança o rotor **mais à direita** (`posição + 1 mod 26`).
2. Passa pelos rotores ativos da **direita para a esquerda** (forward).
3. **Refletor B** fixo.
4. Volta da **esquerda para a direita** (backward).
5. Emite letra de saída.

Cifrar e decifrar usam a **mesma** operação (Enigma simétrica).

---

## 7. Rotores disponíveis (R1–R6)

| ID | Nome histórico | Wiring (excerpt) |
|----|----------------|------------------|
| R1 | I | EKMFLGDQVZNTOWYHXUSPAIBRCJ |
| R2 | II | AJDKSIRUXBLHWTMCQGZNPYFVOE |
| R3 | III | BDFHJLCPRTXVZNYEIWGAKMUSQO |
| R4 | IV | ESLPYHKWRDAVZFXNGMJCQIOBUT |
| R5 | V | VZBRGRIYWATUKQCMLHPFDJNCXESO |
| R6 | VI | JVMUBRFXDYZNTQEWHGLKOCPISA |

Refletor fixo: **B** — `YRUHQSLDPXNGOKMIEBFZCWVJAT`.

Posições: **0 a 25** (26 posições por rotor, correspondendo a deslocamento no alfabeto).

---

## 8. Semelhança com a Enigma real

### O que este projeto reproduz bem

| Aspeto | Enigma militar (simplificado) | Este projeto |
|--------|------------------------------|--------------|
| Rotores substituíveis | Conjunto maior (5–8 tipos), 3–4 ativos | 6 tipos (R1–R6), até 4 ativos |
| Ordem dos rotores | Operador escolhe ordem na máquina | Teclas **S1–S4** / UI no app |
| Posição inicial | Anéis / posição de cada rotor | **R+** / picker no app |
| Refletor | Fixo ou intercambiável | **Refletor B** fixo |
| Simetria | Cifrar = decifrar com mesma config | Igual |
| Half-duplex operacional | Operador humano numa máquina | Duas “máquinas” (app + Arduino) com turno via Pi |

A ideia de **escolher até 4 rotores de um conjunto maior** aproxima-se mais da Enigma **M3/M4** (vários rotores no armário, subset ativo na máquina) do que um trio fixo I–II–III.

### Simplificações deste projeto (diferenças da máquina real)

| Aspeto real | Este projeto |
|-------------|--------------|
| **Duplo passo** (notches, rotores vizinhos avançam juntos) | Não implementado — só o rotor da direita avança |
| **Plugboard** (Steckerbrett) | Não existe |
| **Refletor** intercambiável (B/C/D) | Apenas refletor B |
| **Entrada** por teclas luminosas com circuito complexo | Keypads + app |
| **U-boat 4. rotor**, etc. | Não modelado |
| Chaveamento rápido de rotores em combate | Config manual ou SYNC explícito |

Conclusão: o projeto é pedagogicamente fiel ao **princípio** da Enigma (rotores + refletor + avanço + simetria), mas é uma **versão didática simplificada**, não uma réplica criptográfica completa da máquina de campo.

---

## 9. Procedimentos operacionais recomendados

### 9.1 Primeira utilização

1. Ligar Arduino ao Pi por USB; arrancar `python main.py` no Pi (venv).
2. No app: definir IP do Pi (`IP:8000`), configurar rotores, **Salvar e sincronizar**.
3. No Arduino: **SYNC** — LCD deve mostrar a mesma ordem/posições (via `CFG:`).
4. Alinhar modo: app aba Send, Arduino **MODE** para cifrar (ou o fluxo inverso para teste).

### 9.2 Enviar do telemóvel para o Arduino

1. App: aba **Send**, mesmos rotores/posições que o Arduino (após SYNC ou config manual idêntica).
2. Escrever texto, **Cifrar e enviar**.
3. Arduino: modo **decifrar**; deve receber `IN:` e mostrar texto claro na linha 2.

### 9.3 Enviar do Arduino para o telemóvel

1. Arduino: modo **cifrar**, rotores configurados, escrever texto, **SEND**.
2. App: aba **Receive** (polling).
3. App decifra com a **sua** config — deve coincidir com a do Arduino no envio.

### 9.4 Só alterar configuração quando necessário

| Ação | Quando |
|------|--------|
| `POST /config` (app) | Mudou rotores/ordem/posições no telemóvel e quer copiar ao Pi/Arduino |
| **SYNC** (Arduino) | Quer copiar a config guardada no Pi para o hardware |
| Teclas **R / S / RESET** | Ajuste local sem envolver o Pi |

---

## 10. Erros comuns e resolução

| Sintoma | Causa provável | O que fazer |
|---------|----------------|-------------|
| `409 Raspberry nao esta em RECEIVING` | App enviou mensagem com Pi no turno errado | Aba **Send** (faz `POST /role`), reiniciar Pi, repetir |
| `409 NOT_SENDING` no Arduino | Arduino fez SEND com Pi em `RECEIVING` | Arduino deve enviar quando Pi está em `SENDING` (app na aba Receive) |
| Texto decifrado errado | Config diferente entre app e Arduino | SYNC + mesma ordem/posições, ou configurar manualmente igual |
| `404` em `/message/...` | Pi com código antigo | Atualizar `enigma-raspberry` e reiniciar servidor |
| LCD Arduino vazio após envio | Modo errado ou sem `IN:` | Arduino em modo **decifrar** |
| Sem rotores | Nenhum R1–R6 selecionado | Selecionar até 4 rotores antes de cifrar |

---

## 11. Estrutura do repositório

| Pasta | Conteúdo |
|-------|----------|
| `enigma-arduino/` | Firmware Mega, `keypads.png`, `COMPORTAMENTO.md` |
| `enigma-raspberry/` | FastAPI, ponte Serial, `CONEXAO_PI.md` |
| `enigma-mobile/` | App Expo, `enigmaMachine.ts` |
| `MANUAL.md` | Este documento |

---

## 12. Referências rápidas de implementação

| Tema | Ficheiro |
|------|----------|
| Algoritmo mobile | `enigma-mobile/src/services/enigmaMachine.ts` |
| Algoritmo Arduino | `enigma-arduino/enigma_machine/enigma.cpp` |
| Ponte / turno Pi | `enigma-raspberry/comm/protocol.py` |
| API HTTP | `enigma-raspberry/comm/mobile_server.py` |
| Serial Arduino | `enigma-raspberry/comm/arduino_handler.py` |
| UI mobile | `enigma-mobile/src/screens/HomeScreen.tsx` |

---

## 13. Glossário

| Termo | Significado |
|-------|-------------|
| **Payload** | Texto só com letras A–Z (normalmente já cifrado) |
| **Cipher** | Texto cifrado pela Enigma |
| **CFG** | Linha Serial com configuração de rotores do Pi |
| **Relay** | Pi reencaminha mensagem sem alterar o conteúdo cifrado |
| **Slot** | Posição na cadeia (1.º a 4.º rotor ativo) |
| **Wiring** | Permutação interna fixa de cada rotor |
| **Refletor** | Permutação fixa que devolve o sinal pelos rotores em sentido inverso |

---

*Última atualização alinhada ao firmware e backend com rotores dinâmicos (R1–R6), três keypads, Pi apenas como ponte e mensagens sem configuração embutida.*
