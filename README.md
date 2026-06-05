# Análise de Desempenho e Confiabilidade: TCP vs. R-UDP

> **Aluno:** João Vitor Santana Lima<br>
> **Matrícula:** 20249006849<br>
> **Link do Vídeo: https://www.youtube.com/watch?v=13jUMfOo2Oo**

Trabalho da disciplina de Redes de Computadores II. O projeto implementa e compara dois
sistemas de transferência de arquivos escritos em Python: um usando o protocolo TCP
nativo e outro usando o UDP com uma camada de confiabilidade desenvolvida do zero, o
R-UDP. Os testes rodam em contêineres Docker, com simulação de redes ruins via
`tc qdisc netem`, e o tráfego é capturado com `tcpdump` para validação cruzada no
Wireshark.

## Tecnologias

- Python 3.12 (uv 0.11.15)
- Docker
- `tc` para simular atraso e perda de pacotes
- `tcpdump` para captura de tráfego
- matplotlib e numpy para os gráficos

## O que foi implementado

### Protocolo de aplicação

Cabeçalho em texto, no estilo HTTP, comum aos dois modos. Cada mensagem tem os campos:

- `X-Custom-Auth`: hash SHA-256 da matrícula somada ao nome do aluno, identifica a origem do tráfego
- `X-Type`: tipo da mensagem (`init`, `data`, `ack`, `fim`)
- `X-Seq`: número de sequência do bloco
- `X-Length`: tamanho do corpo da mensagem
- `X-Checksum`: CRC-32 do bloco, presente apenas nas mensagens de dados
- `X-Filename` e `X-Filesize`: metadados do arquivo, presentes apenas no `init`

### Modo TCP

Cliente abre uma conexão por transferência, envia os blocos com `sendall` e mede o tempo
de entrega real usando `shutdown(SHUT_WR)` seguido da drenagem do socket, garantindo que
o cronômetro pare somente quando o servidor processou tudo.

### Modo R-UDP

Confiabilidade implementada na camada de aplicação sobre UDP, com:

- Mecanismo Stop-and-Wait (envia um bloco e espera o ACK antes do próximo)
- Números de sequência e confirmações (ACKs)
- Timeout de 1 segundo com retransmissão sem limite de tentativas
- Verificação de integridade por CRC-32 em cada bloco
- Blocos de 1300 bytes, escolhidos para não ultrapassar a MTU de 1500 e evitar fragmentação IP

### Cenários de rede

Aplicados com `tc qdisc netem` na saída do servidor:

| Cenário | Atraso | Perda |
|---------|--------|-------|
| A | 10 ms | 0% |
| B | 50 ms | 5% |
| C | 100 ms | 10% |

## Estrutura do projeto

```
.
├── src/
│   ├── protocolo.py          Cabeçalhos, parsing, identidade SHA-256 e TAMANHO_BLOCO
│   ├── transporte_tcp.py     Cliente e servidor no modo TCP
│   ├── transporte_rudp.py    Cliente e servidor no modo R-UDP (Stop-and-Wait)
│   ├── client.py             Ponto de entrada do cliente
│   ├── server.py             Ponto de entrada do servidor
│   ├── metrica.py            Cálculo de throughput e geração do CSV
│   ├── gerar_arquivo.py      Gera o arquivo de teste com bytes aleatórios
│   ├── gerar_graficos.py     Gera os gráficos a partir dos resultados
│   ├── entrypoint-server.sh  Aplica o tc, inicia o tcpdump e sobe o servidor
│   ├── Dockerfile.server
│   └── Dockerfile.client
├── docker-compose.yml        Sobe servidor e cliente, com healthcheck
├── pyproject.toml            Dependências do projeto (matplotlib, numpy, pandas)
├── uv.lock                   Versões travadas das dependências (uv)
├── .python-version           Versão do Python usada (3.12)
├── resultados/               CSVs com as métricas de cada cenário (tcp_A.csv ... rudp_C.csv)
├── logs/                     Logs detalhados do cliente, um por cenário
├── capturas/                 Arquivos .pcap por cenário (TCP_A.pcap ... RUDP_C.pcap)
├── graficos/                 Imagens PNG geradas
├── relatorio/
│   └── relatorio.pdf         Relatório final no modelo SBC
├── trabalho.pdf              Enunciado do trabalho
└── README.md
```

## Como executar

A porta usada é a 25565. As variáveis de ambiente selecionam o protocolo, o cenário e os
nomes dos arquivos de saída.

### Construir as imagens

```powershell
docker compose build
```

### Rodar um cenário

Os comandos abaixo são para PowerShell. Ajuste `MODE`, `CENARIO` e os nomes dos arquivos
a cada rodada.

Terminal 1 (servidor):

```powershell
$env:MODE="rudp"; $env:CENARIO="A"
docker compose up server
```

Terminal 2 (cliente), depois que o servidor ficar saudável:

```powershell
$env:MODE="rudp"; $env:CENARIO="A"; $env:CSV="/resultados/rudp_A.csv"; $env:LOG="/logs/rudp_A.log"
docker compose up --no-deps client
```

Combinações de `MODE` e `CENARIO` a executar:

| MODE | CENARIO | CSV |
|------|---------|-----|
| tcp  | A | `/resultados/tcp_A.csv` |
| tcp  | B | `/resultados/tcp_B.csv` |
| tcp  | C | `/resultados/tcp_C.csv` |
| rudp | A | `/resultados/rudp_A.csv` |
| rudp | B | `/resultados/rudp_B.csv` |
| rudp | C | `/resultados/rudp_C.csv` |

Por padrão são 30 execuções de um arquivo de 1 MiB. Para mudar, use as variáveis
`REPETICOES` e `FILE_SIZE_MB`.

## Saídas geradas

- `resultados/`: CSV com tempo, throughput e bytes de cada execução, mais o resumo com vazão mínima, média, máxima e desvio padrão
- `logs/`: log detalhado do cliente, incluindo cada bloco enviado e cada retransmissão
- `capturas/`: um arquivo `.pcap` por cenário, nomeado automaticamente como `PROTOCOLO_CENARIO.pcap`

## Gerar os gráficos

Depois de ter os CSV em `resultados/`, gere os gráficos com:

```powershell
python src/gerar_graficos.py
```

As imagens são salvas em `graficos/`, com comparativos entre TCP e R-UDP e gráficos
individuais por protocolo.

## Relatório

O relatório está em `relatorio/relatorio.pdf`, seguindo o modelo da SBC, com a análise
comparativa, a validação cruzada com o Wireshark e as respostas às perguntas obrigatórias.

## Autor

João Vitor Santana Lima
