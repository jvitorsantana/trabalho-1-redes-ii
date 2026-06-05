#!/bin/sh
set -e

: "${PORT:=25565}"
: "${SAVE_DIR:=/app/recv}"
mkdir -p "$SAVE_DIR"

IFACE=$(ip route | awk '/default/ {print $5; exit}')
echo "[server-entry] aplicando cenario ${CENARIO:-A} em $IFACE"
case "${CENARIO:-A}" in
  A) tc qdisc add dev "$IFACE" root netem delay 10ms  loss 0%  ;;
  B) tc qdisc add dev "$IFACE" root netem delay 50ms  loss 5%  ;;
  C) tc qdisc add dev "$IFACE" root netem delay 100ms loss 10% ;;
  *) echo "[server-entry] CENARIO invalido: ${CENARIO}"; exit 1  ;;
esac

PROTO=$(echo "${MODE:-tcp}" | tr '[:lower:]' '[:upper:]')
PCAP_NAME="${PROTO}_${CENARIO:-A}.pcap"
PCAP_LOCAL=/tmp/captura.pcap
PCAP_OUT=/cap/${PCAP_NAME}

TPID=""

finalizar() {
  if [ -n "$TPID" ] && kill -0 "$TPID" 2>/dev/null; then
    echo "[server-entry] encerrando tcpdump..."
    kill -INT "$TPID" 2>/dev/null || true
    wait "$TPID" 2>/dev/null || true
  fi
  if [ -f "$PCAP_LOCAL" ]; then
    cp "$PCAP_LOCAL" "$PCAP_OUT" 2>/dev/null || true
    sync
    echo "[server-entry] pcap salvo em $PCAP_OUT ($(wc -c < "$PCAP_OUT" 2>/dev/null || echo 0) bytes)"
  fi
}

trap 'finalizar; exit 0' TERM INT

echo "[server-entry] iniciando tcpdump -> $PCAP_NAME"
tcpdump -i eth0 -n -B 65536 -w "$PCAP_LOCAL" "port $PORT" &
TPID=$!

sleep 1

echo "[server-entry] iniciando server.py (MODE=${MODE:-tcp})"
python3 -u server.py || true

finalizar
echo "[server-entry] concluido"
