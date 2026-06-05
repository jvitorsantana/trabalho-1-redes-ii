import logging
import os
import signal
import sys

from protocolo import calcular_identidade
from metrica import throughput_mbps, Estatisticas
import transporte_tcp
import transporte_rudp

TRANSPORTES = {'tcp': transporte_tcp, 'rudp': transporte_rudp}


def _configurar_log(log_path: str):
  fmt = logging.Formatter('%(asctime)s %(message)s', datefmt='%H:%M:%S')

  stream = logging.StreamHandler(sys.stdout)
  stream.setLevel(logging.INFO)
  stream.setFormatter(fmt)

  handlers = [stream]

  if log_path:
    log_dir = os.path.dirname(log_path)
    if log_dir:
      os.makedirs(log_dir, exist_ok=True)
    arquivo = logging.FileHandler(log_path, mode='w', encoding='utf-8')
    arquivo.setLevel(logging.DEBUG)
    arquivo.setFormatter(fmt)
    handlers.append(arquivo)

  root = logging.getLogger()
  root.setLevel(logging.DEBUG)
  for h in handlers:
    root.addHandler(h)


def main():
  signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

  mode       = os.getenv('MODE', 'tcp')
  host       = os.getenv('HOST', '127.0.0.1')
  port       = int(os.getenv('PORT', 25565))
  arquivo    = os.getenv('FILE', 'joaovitor.bin')
  repeticoes = int(os.getenv('REPETICOES', 30))
  csv_saida  = os.getenv('CSV', 'resultados.csv')
  log_path   = os.getenv('LOG', '')

  _configurar_log(log_path)
  log = logging.getLogger(__name__)

  if mode not in TRANSPORTES:
    log.error(f"MODE inválido: {mode!r} (use 'tcp' ou 'rudp')")
    sys.exit(1)

  identidade = calcular_identidade()
  transporte = TRANSPORTES[mode]
  est = Estatisticas()

  try:
    for i in range(repeticoes):
      desligar = (i == repeticoes - 1)
      log.info(f'=== Execução {i + 1}/{repeticoes} (modo={mode}) ===')
      tempo, n_bytes = transporte.enviar_arquivo(
        host, port, arquivo, identidade, desligar=desligar)
      thr = throughput_mbps(n_bytes, tempo)
      est.adicionar(i + 1, tempo, thr, n_bytes)
      log.info(f'[resumo] tempo={tempo:.4f}s throughput={thr:.2f} Mbps')
  finally:
    if est.registros:
      est.salvar_csv(csv_saida)
      r = est.resumo()
      log.info('=== resumo final ===')
      log.info(
        f"execuções={r['execucoes']} | vazão min/méd/máx="
        f"{r['throughput_min']:.4f}/{r['throughput_medio']:.4f}/"
        f"{r['throughput_max']:.4f} Mbps | desvio={r['throughput_desvio']:.4f} Mbps"
        f" | tempo médio={r['tempo_medio']:.4f}s"
      )
      log.info(f'resultados salvos em {csv_saida}')
      if log_path:
        log.info(f'log salvo em {log_path}')
    logging.shutdown()


if __name__ == '__main__':
  main()
