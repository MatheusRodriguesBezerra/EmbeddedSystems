# Enigma Raspberry

Backend Python para o Raspberry Pi do projeto Enigma Machine.

## Funcionalidades

- API HTTP local com FastAPI.
- Cifra Enigma simplificada com rotores fixos I, II e III.
- Refletor B.
- Estado half-duplex: `IDLE`, `SENDING`, `RECEIVING`.
- Sincronização de configuração por `POST /config`.
- Receção de payload cifrado por `GET /message/:payload`.
- Persistência de estado em `state/enigma_state.json`.
- Ponte Serial preparada para comandos do Arduino.
- Testes unitários mínimos.

## Rotas HTTP

- `GET /ping`
- `GET /state`
- `POST /config`
- `GET /message/{payload}`
- `GET /pending` — payload cifrado enviado pelo Arduino (app em RECEIVING)
- `POST /outgoing/{plain_text}`

## Arduino por USB Serial

O `main.py` abre automaticamente `/dev/ttyACM0` a 115200 baud e faz ponte com o firmware.

Ver **[CONEXAO_PI.md](CONEXAO_PI.md)** para ligacao completa Arduino + Pi + app mobile.

## Contrato com o app

O app deve chamar `GET /message/{payload}` apenas quando o Raspberry estiver em `RECEIVING`. O payload recebido já deve estar cifrado pela Enigma no app. O Raspberry decifra localmente, atualiza as posições dos rotores e alterna para `SENDING`.

## Execução

1. Crie um ambiente virtual Python.
2. Instale as dependências com `pip install -r requirements.txt`.
3. Execute o servidor com `python main.py`.
4. No app mobile, configure o endereço do Raspberry como `IP_DO_RASPBERRY:8000`.

## Testes

Execute `pytest` na raiz deste projeto.
