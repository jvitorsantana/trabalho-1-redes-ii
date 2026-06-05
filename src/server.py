import os
import sys

import transporte_tcp
import transporte_rudp

TRANSPORTES = {'tcp': transporte_tcp, 'rudp': transporte_rudp}


def main():
  mode     = os.getenv('MODE', 'tcp')
  host     = os.getenv('HOST', '0.0.0.0')
  port     = int(os.getenv('PORT', 25565))
  save_dir = os.getenv('SAVE_DIR', '.')
  cenario  = os.getenv('CENARIO', 'A')

  if mode not in TRANSPORTES:
    sys.exit(1)

  print(f'[server] modo={mode} | host={host}:{port} | cenario={cenario}')
  TRANSPORTES[mode].iniciar_servidor(host, port, save_dir)


if __name__ == '__main__':
  main()
