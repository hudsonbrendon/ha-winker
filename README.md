# Winker (Beelive) — Home Assistant

Integração não-oficial para a plataforma **Winker** (apps white-label como o **Beelive**),
usada por condomínios no Brasil. Expõe os dados da sua conta como sensores.

Derivada por engenharia reversa do app `br.com.winker.wl.beelive` + API ao vivo.

## Sensores
- **Boletos em aberto** — quantidade; atributos com referência, vencimento, valor, linha digitável e PDF.
- **Próximo vencimento** — timestamp do boleto aberto mais próximo (atributo `valor`).
- **Avisos** — total de comunicados; últimos 10 nos atributos.
- **Reservas** — reservas ativas.
- **Encomendas a retirar** — pacotes pendentes na portaria.

## Instalação
1. Copie `custom_components/winker` para o `config/custom_components` do seu HA.
2. Reinicie o Home Assistant.
3. Ajustes → Dispositivos e Serviços → Adicionar Integração → **Winker (Beelive)**.
4. Informe o **mesmo e-mail e senha do app**. Se tiver mais de um condomínio, escolha qual.

## API (resumo)
`https://api.winker.com.br/v1` · login `POST /auth/login {username,password,key}` ·
header `Authorization: <token>` (JWT cru) · endpoints por `?id_portal=`.
