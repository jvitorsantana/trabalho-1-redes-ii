import os

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

RAIZ = os.path.dirname(os.path.dirname(__file__))
SAIDA = os.path.join(RAIZ, 'graficos')
os.makedirs(SAIDA, exist_ok=True)

cenarios = ['Cenário A', 'Cenário B', 'Cenário C']
x = np.arange(len(cenarios))

tcp_tempo  = [0.1448, 0.3961, 0.7344]
rudp_tempo = [8.5985, 81.7929, 171.8716]

tcp_vazao  = [57.9299, 23.1498, 11.5661]
rudp_vazao = [0.9756, 0.1032, 0.0489]

tcp_dp  = [0.7717, 2.4799, 1.1097]
rudp_dp = [0.0006, 0.0082, 0.0023]

cor_tcp = '#b300ff'
cor_rudp = '#0068d6'
marker_tcp = 'o'
marker_rudp = 's'
lw = 2.0
ms = 7

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.spines.top'] = False
plt.rcParams['axes.spines.right'] = False
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['grid.alpha'] = 0.4
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.dpi'] = 150


def anotar(ax, valores, cor):
  for i, v in enumerate(valores):
    ax.annotate(f'{v:g}', (x[i], v), xytext=(0, 8),
                textcoords='offset points', ha='center',
                fontsize=8.5, color=cor)


def plot_grafico(tcp_vals, rudp_vals, titulo, ylabel, nome_arquivo):
  fig, ax = plt.subplots(figsize=(7, 4.5))

  ax.plot(x, tcp_vals, color=cor_tcp, marker=marker_tcp,
          linewidth=lw, markersize=ms, label='TCP', zorder=3)
  ax.plot(x, rudp_vals, color=cor_rudp, marker=marker_rudp,
          linewidth=lw, markersize=ms, label='R-UDP', zorder=3)

  anotar(ax, tcp_vals, cor_tcp)
  anotar(ax, rudp_vals, cor_rudp)

  ax.set_yscale('log')
  ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
  ax.set_xticks(x)
  ax.set_xticklabels(cenarios)
  ax.set_title(titulo, pad=10)
  ax.set_ylabel(ylabel)
  ax.legend(frameon=False)

  fig.tight_layout()
  destino = os.path.join(SAIDA, nome_arquivo)
  fig.savefig(destino, bbox_inches='tight')
  plt.close(fig)
  print(f'Salvo: {destino}')


def plot_serie(vals, titulo, ylabel, cor, marker, nome_arquivo):
  fig, ax = plt.subplots(figsize=(7, 4.5))

  ax.plot(x, vals, color=cor, marker=marker,
          linewidth=lw, markersize=ms, zorder=3)
  anotar(ax, vals, cor)

  ax.set_yscale('log')
  ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
  ax.set_xticks(x)
  ax.set_xticklabels(cenarios)
  ax.set_title(titulo, pad=10)
  ax.set_ylabel(ylabel)

  fig.tight_layout()
  destino = os.path.join(SAIDA, nome_arquivo)
  fig.savefig(destino, bbox_inches='tight')
  plt.close(fig)
  print(f'Salvo: {destino}')


plot_grafico(tcp_tempo, rudp_tempo, 'Tempo médio de transferência', 'Tempo (s)', 'grafico_tempo.png')
plot_grafico(tcp_vazao, rudp_vazao, 'Vazão média', 'Vazão (Mbps)', 'grafico_vazao.png')
plot_grafico(tcp_dp, rudp_dp, 'Desvio padrão', 'Desvio Padrão (Mbps)', 'grafico_desvio_padrao.png')

plot_serie(tcp_tempo, 'TCP - Tempo médio de transferência', 'Tempo (s)', cor_tcp, marker_tcp, 'grafico_tcp_tempo.png')
plot_serie(tcp_vazao, 'TCP - Vazão média', 'Vazão (Mbps)', cor_tcp, marker_tcp, 'grafico_tcp_vazao.png')
plot_serie(tcp_dp, 'TCP - Desvio padrão', 'Desvio Padrão (Mbps)', cor_tcp, marker_tcp, 'grafico_tcp_desvio.png')

plot_serie(rudp_tempo, 'R-UDP - Tempo médio de transferência', 'Tempo (s)', cor_rudp, marker_rudp, 'grafico_rudp_tempo.png')
plot_serie(rudp_vazao, 'R-UDP - Vazão média', 'Vazão (Mbps)', cor_rudp, marker_rudp, 'grafico_rudp_vazao.png')
plot_serie(rudp_dp, 'R-UDP - Desvio padrão', 'Desvio Padrão (Mbps)', cor_rudp, marker_rudp, 'grafico_rudp_desvio.png')
