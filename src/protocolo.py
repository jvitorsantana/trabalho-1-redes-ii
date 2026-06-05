import hashlib

NOME = 'João Vitor Santana Lima'
MATRICULA = '20249006849'

FIM_HEADER = b'\r\n\r\n'
TAMANHO_BLOCO = 1300


def calcular_identidade(matricula: str = MATRICULA, nome: str = NOME) -> str:
  return hashlib.sha256(f'{matricula}{nome}'.encode()).hexdigest()


def montar_mensagem(identidade: str, tipo: str, seq: int, payload: bytes = b'', extra: dict | None = None) -> bytes:
  campos = [
    f'X-Custom-Auth: {identidade}',
    f'X-Type: {tipo}',
    f'X-Seq: {seq}',
    f'X-Length: {len(payload)}',
  ]
  if extra:
    for chave, valor in extra.items():
      campos.append(f'{chave}: {valor}')
  cabecalho = '\r\n'.join(campos).encode() + FIM_HEADER
  return cabecalho + payload


def parsear_campos(raw: bytes) -> dict:
  texto = raw.split(FIM_HEADER, 1)[0].decode(errors='replace')
  dados = {}
  for linha in texto.split('\r\n'):
    if ': ' in linha:
      chave, valor = linha.split(': ', 1)
      dados[chave] = valor
  return dados


class LeitorEnquadrado:
  def __init__(self, sock, bufsize: int = 65536):
    self.sock = sock
    self.bufsize = bufsize
    self.buf = bytearray()

  def _encher(self) -> bool:
    chunk = self.sock.recv(self.bufsize)
    if not chunk:
      return False
    self.buf.extend(chunk)
    return True

  def _ler_ate(self, delim: bytes):
    while True:
      i = self.buf.find(delim)
      if i >= 0:
        fim = i + len(delim)
        out = bytes(self.buf[:fim])
        del self.buf[:fim]
        return out
      if not self._encher():
        return None

  def _ler_exato(self, n: int):
    while len(self.buf) < n:
      if not self._encher():
        return None
    out = bytes(self.buf[:n])
    del self.buf[:n]
    return out

  def ler_mensagem(self):
    cab = self._ler_ate(FIM_HEADER)
    if cab is None:
      return None
    campos = parsear_campos(cab)
    n = int(campos.get('X-Length', '0'))
    if n <= 0:
      return campos, b''
    payload = self._ler_exato(n)
    if payload is None:
      return None
    return campos, payload
