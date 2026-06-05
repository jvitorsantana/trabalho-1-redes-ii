import logging
import os
import socket
import time
import zlib

from protocolo import (FIM_HEADER, TAMANHO_BLOCO, montar_mensagem,
                       parsear_campos, calcular_identidade)

TIMEOUT    = 1.0
TIMEOUT_RX = 5.0
BUFSIZE    = 65507

IDENTIDADE = calcular_identidade()

log = logging.getLogger(__name__)


def _checksum(dados: bytes) -> str:
  return format(zlib.crc32(dados), '08x')

def _parse(raw: bytes):
  sep = raw.find(FIM_HEADER)
  if sep < 0:
    return None, b''
  return parsear_campos(raw[:sep + len(FIM_HEADER)]), raw[sep + len(FIM_HEADER):]

def _enviar_ack(sock, seq: int, addr):
  sock.sendto(montar_mensagem(IDENTIDADE, 'ack', seq, b''), addr)

def _enviar_com_ack(sock, datagrama: bytes, seq: int, addr, tipo: str = 'pkt') -> None:
  tentativa = 0
  while True:
    if tentativa == 0:
      log.debug(f'[rudp] {tipo} enviado seq={seq} ({len(datagrama)} bytes)')
    else:
      log.debug(f'[rudp] RETRANSMISSAO {tipo} seq={seq} tentativa={tentativa}')
    sock.sendto(datagrama, addr)
    sock.settimeout(TIMEOUT)
    try:
      raw, _ = sock.recvfrom(BUFSIZE)
    except socket.timeout:
      tentativa += 1
      log.debug(f'[rudp] TIMEOUT seq={seq} sem ACK (tentativa {tentativa})')
      continue
    campos, _ = _parse(raw)
    if (campos
        and campos.get('X-Type') == 'ack'
        and int(campos.get('X-Seq', -1)) == seq):
      log.debug(f'[rudp] ACK recebido seq={seq}')
      return


def iniciar_servidor(host: str, port: int, salvar_dir: str = '.'):
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  sock.bind((host, port))
  print(f'[rudp] servidor escutando em {host}:{port}')

  while True:
    print('[rudp] aguardando init...')
    sock.settimeout(None)

    while True:
      raw, addr = sock.recvfrom(BUFSIZE)
      campos, _ = _parse(raw)
      if campos is None:
        continue
      tipo = campos.get('X-Type')
      if tipo == 'init':
        break
      if tipo == 'fim':
        _enviar_ack(sock, int(campos.get('X-Seq', 0)), addr)

    print(f'[rudp] init de {addr}')
    print(f'[rudp] X-Custom-Auth: {campos.get("X-Custom-Auth")}')

    desligar = campos.get('X-Shutdown') == 'true'
    nome = os.path.basename(campos.get('X-Filename', 'arquivo.bin'))
    tamanho = int(campos.get('X-Filesize', 0))
    destino = os.path.join(salvar_dir, nome)

    _enviar_ack(sock, 0, addr)
    sock.settimeout(TIMEOUT_RX)

    seq_esperado = 1
    recebidos = 0
    blocos = 0
    inicio = time.perf_counter()

    try:
      with open(destino, 'wb') as arq:
        while True:
          try:
            raw, _ = sock.recvfrom(BUFSIZE)
          except socket.timeout:
            print('[rudp][warn] timeout aguardando bloco')
            break

          campos, payload = _parse(raw)
          if campos is None:
            continue

          tipo = campos.get('X-Type')
          seq  = int(campos.get('X-Seq', -1))

          if tipo == 'init':
            _enviar_ack(sock, 0, addr)
            continue

          if tipo == 'data':
            if campos.get('X-Checksum', '') != _checksum(payload):
              print(f'[rudp][warn] checksum invalido seq={seq}')
              continue

            if seq == seq_esperado:
              arq.write(payload)
              recebidos    += len(payload)
              blocos       += 1
              seq_esperado += 1

            _enviar_ack(sock, seq, addr)

          elif tipo == 'fim':
            _enviar_ack(sock, seq, addr)
            break

    except Exception as e:
      print(f'[rudp][error] {e}')

    tempo = time.perf_counter() - inicio
    thr   = (recebidos * 8) / (tempo * 1_000_000) if tempo > 0 else 0

    if recebidos != tamanho:
      print(f'[rudp][warn] esperado {tamanho}, recebido {recebidos}')
    print(f'[rudp] blocos={blocos} bytes={recebidos} '
          f'tempo={tempo:.6f}s throughput={thr:.2f} Mbps')

    if desligar:
      print('[rudp] X-Shutdown recebido — encerrando servidor')
      break

  sock.close()

def enviar_arquivo(host: str, port: int, caminho_arquivo: str,
                   identidade: str, desligar: bool = False):
  nome    = os.path.basename(caminho_arquivo)
  tamanho = os.path.getsize(caminho_arquivo)
  addr    = (host, port)

  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

  try:
    extra = {'X-Filename': nome, 'X-Filesize': tamanho}
    if desligar:
      extra['X-Shutdown'] = 'true'

    inicio = time.perf_counter()

    log.debug(f'[rudp] iniciando transferencia para {addr} arquivo={nome} ({tamanho} bytes)')
    _enviar_com_ack(
      sock,
      montar_mensagem(identidade, 'init', 0, b'', extra),
      0, addr, tipo='init',
    )

    seq = 0
    with open(caminho_arquivo, 'rb') as arq:
      while True:
        bloco = arq.read(TAMANHO_BLOCO)
        if not bloco:
          break
        seq += 1
        _enviar_com_ack(
          sock,
          montar_mensagem(identidade, 'data', seq, bloco, {'X-Checksum': _checksum(bloco)}),
          seq, addr, tipo='data',
        )

    seq_fim = seq + 1
    _enviar_com_ack(
      sock,
      montar_mensagem(identidade, 'fim', seq_fim, b''),
      seq_fim, addr, tipo='fim',
    )

    fim = time.perf_counter()

  finally:
    sock.close()

  log.info(f'[rudp] transferencia concluida: {seq} blocos enviados')
  return fim - inicio, tamanho
