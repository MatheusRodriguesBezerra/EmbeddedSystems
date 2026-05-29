# Enigma Mobile

App mobile em React Native (Expo + TypeScript) para o projeto Enigma Machine.

## Funcionalidades

- App Expo com TypeScript.
- React Navigation (uma única tela Home com tabs internas).
- Estado global com Zustand.
- Cifra e decifra **locais** no app, usando até 4 rotores entre 6 possíveis (R1–R6).
- 2 modos: `CIFRAR` (envia) e `DECIFRAR` (recebe).
- Comunicação HTTP com o Raspberry Pi:
  - `GET /ping` para testar conectividade.
  - `POST /config` para enviar a configuração atual dos rotores ao Raspberry.
  - `GET /message/:cipher` para transportar o payload já cifrado.
  - `GET /has-message` (polling a cada **4 s** no modo DECIFRAR) para receber cifras do Arduino.

## Como executar

1. Instale as dependências: `npm install`.
2. Inicie o Expo: `npm start`.
3. Abra no Android com Expo Go ou `npm run android`.
4. Nas configurações (ícone ⚙), defina o IP/porta do Raspberry Pi, por exemplo `192.168.1.100:8000`.

## Contrato HTTP esperado

### `GET /ping`

```json
{
  "status": "ok",
  "connectedArduino": true
}
```

### `POST /config`

O app envia a configuração atual dos rotores ao Raspberry.

Payload:

```json
{
  "rotors": [
    { "id": 1, "position": 5 },
    { "id": 3, "position": 3 },
    { "id": 4, "position": 10 }
  ]
}
```

### `GET /message/:cipher`

O app envia esta rota quando está em `CIFRAR` (modo enviar). O valor já vem cifrado pela Enigma local.

```json
{
  "status": "received",
  "cipher": "XYZ"
}
```

### `GET /has-message`

O app consulta esta rota a cada **4 s** quando está em `DECIFRAR` (modo receber). Se o Raspberry tiver uma cifra do Arduino, devolve-a no campo `cipher`; caso contrário, devolve `null`.

Resposta com mensagem:

```json
{
  "cipher": "QWE"
}
```

Resposta vazia:

```json
{
  "cipher": null
}
```

## Funcionamento

### Configuração dos rotores

No painel de configurações é possível:

1. Selecionar até **4 rotores** entre R1–R6.
2. Incrementar a posição de cada rotor (0–25, rotativo).
3. Trocar a ordem com os shifters S1–S4 (cada shifter troca dois slots adjacentes).
4. Salvar — o app envia automaticamente `POST /config` para o Raspberry com a configuração nova.

### Modo CIFRAR

O utilizador escreve uma string; o app cifra localmente com a configuração atual de rotores, mostra o texto cifrado e envia via `GET /message/:cipher` para o Raspberry. O Raspberry encaminha ao Arduino.

### Modo DECIFRAR

O app fica em polling `GET /has-message` a cada 4 s. Quando o Raspberry devolve um `cipher` não nulo, o app decifra localmente e mostra a mensagem em claro ao utilizador.
