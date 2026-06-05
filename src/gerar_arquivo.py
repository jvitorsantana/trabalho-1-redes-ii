import os

nome = os.environ.get('FILE', 'joaovitor.bin')
tamanho_mb = int(os.environ.get('FILE_SIZE_MB', '1'))

CHUNK = 1024 * 1024
total = tamanho_mb * CHUNK

with open(nome, 'wb') as arq:
  for _ in range(total // CHUNK):
    arq.write(os.urandom(CHUNK))

print(f'Arquivo gerado: {nome} ({total} bytes)')
