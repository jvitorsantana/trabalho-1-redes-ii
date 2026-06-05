import logging
import os
import socket
import time

from protocolo import TAMANHO_BLOCO, montar_mensagem, LeitorEnquadrado

log = logging.getLogger(__name__)


def enviar_arquivo(host: str, port: int, caminho_arquivo: str,
                   identidade: str, desligar: bool = False):
  nome    = os.path.basename(caminho_arquivo)
  tamanho = os.path.getsize(caminho_arquivo)

  client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  client.connect((host, port))

  inicio = time.perf_counter()

  extra = {'X-Filename': nome, 'X-Filesize': tamanho}
  if desligar:
    extra['X-Shutdown'] = 'true'

  log.debug(f'[tcp] iniciando transferencia para {host}:{port} arquivo={nome} ({tamanho} bytes)')
  client.sendall(montar_mensagem(identidade, 'init', 0, b'', extra))
  log.debug('[tcp] init enviado')

  seq = 0
  with open(caminho_arquivo, 'rb') as arq:
    while True:
      bloco = arq.read(TAMANHO_BLOCO)
      if not bloco:
        break
      seq += 1
      client.sendall(montar_mensagem(identidade, 'data', seq, bloco))
      log.debug(f'[tcp] bloco enviado seq={seq} ({len(bloco)} bytes)')

  client.sendall(montar_mensagem(identidade, 'fim', seq + 1, b''))
  log.debug(f'[tcp] fim enviado seq={seq + 1}')

  client.shutdown(socket.SHUT_WR)
  client.settimeout(3.0)
  try:
    while client.recv(4096):
      pass
  except OSError:
    log.warning('[tcp] drain encerrado por erro de socket (servidor fechou abruptamente)')

  fim = time.perf_counter()
  client.close()

  log.debug(f'[tcp] transferencia concluida: {seq} blocos enviados')
  return fim - inicio, tamanho


def iniciar_servidor(host: str, port: int, salvar_dir: str = '.'):
  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  server.bind((host, port))
  server.listen(1)
  print(f'[tcp] servidor escutando em {host}:{port}')

  while True:
    print('[tcp] aguardando conexao...')
    client, addr = server.accept()
    print(f'[tcp] cliente conectado {addr}')

    desligar = False
    try:
      leitor = LeitorEnquadrado(client)

      msg = leitor.ler_mensagem()
      if msg is None:
        print('[tcp] conexao fechou antes do init')
        continue
      campos, _ = msg
      if campos.get('X-Type') != 'init':
        print(f"[tcp] esperava 'init', veio {campos.get('X-Type')!r}")
        continue

      print(f"[tcp] X-Custom-Auth: {campos.get('X-Custom-Auth')}")
      desligar = campos.get('X-Shutdown') == 'true'

      nome    = os.path.basename(campos.get('X-Filename', 'arquivo.bin'))
      tamanho = int(campos.get('X-Filesize', 0))
      destino = os.path.join(salvar_dir, nome)

      inicio    = time.perf_counter()
      recebidos = 0
      blocos    = 0
      with open(destino, 'wb') as arq:
        while True:
          msg = leitor.ler_mensagem()
          if msg is None:
            break
          campos, payload = msg
          tipo = campos.get('X-Type')
          if tipo == 'data':
            arq.write(payload)
            recebidos += len(payload)
            blocos    += 1
          elif tipo == 'fim':
            break
      tempo = time.perf_counter() - inicio

      thr = (recebidos * 8) / (tempo * 1_000_000) if tempo > 0 else 0
      if recebidos != tamanho:
        print(f'[tcp][warn] esperado {tamanho}, recebido {recebidos}')
      print(f'[tcp] blocos={blocos} bytes={recebidos} '
            f'tempo={tempo:.6f}s throughput={thr:.2f} Mbps')

    except Exception as e:
      print(f'[tcp][error] {e}')

    finally:
      client.close()
      print('[tcp] conexao encerrada')

    if desligar:
      print('[tcp] X-Shutdown recebido — encerrando servidor')
      break

  server.close()
