import csv
import statistics


def throughput_mbps(bytes_transferidos: int, tempo_s: float) -> float:
  if tempo_s <= 0:
    return 0.0
  return (bytes_transferidos * 8) / (tempo_s * 1_000_000)


class Estatisticas:
  def __init__(self):
    self.registros = []  # (execucao, tempo_s, throughput_mbps, bytes)

  def adicionar(self, execucao: int, tempo_s: float,
                thr_mbps: float, n_bytes: int):
    self.registros.append((execucao, tempo_s, thr_mbps, n_bytes))

  def resumo(self) -> dict:
    if not self.registros:
      return {}
    thrs = [r[2] for r in self.registros]
    tempos = [r[1] for r in self.registros]
    return {
      'execucoes': len(thrs),
      'throughput_min': min(thrs),
      'throughput_medio': statistics.mean(thrs),
      'throughput_max': max(thrs),
      'throughput_desvio': statistics.pstdev(thrs) if len(thrs) > 1 else 0.0,
      'tempo_medio': statistics.mean(tempos),
    }

  def salvar_csv(self, caminho: str):
    with open(caminho, 'w', newline='') as f:
      w = csv.writer(f)
      w.writerow(['execucao', 'tempo_s', 'throughput_mbps', 'bytes'])
      w.writerows(self.registros)
