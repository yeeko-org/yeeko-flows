"""Auditoría de un flujo sembrado: alcanzabilidad y destinos colgados.

Independiente del FlowSeeder para poder correrla sobre cualquier dict de
piezas (p. ej. desde shell contra un flujo ya en BD).
"""
from collections import deque

from infrastructure.box.models import Destination, Fragment, Piece, Reply


def connectivity(pieces: dict[str, Piece],
                 start: str) -> tuple[set[str], int]:
    """BFS desde `start` siguiendo destinos (de pieza, reply y written) y
    fragmentos embedded. Regresa (piezas no alcanzables, destinos colgados
    sin piece_dest)."""
    by_id = {piece.id: name for name, piece in pieces.items()}
    dangling = 0
    adj: dict[int, set] = {pid: set() for pid in by_id}
    for name, piece in pieces.items():
        qs = list(piece.destinations.all())
        for reply in Reply.objects.filter(fragment__piece=piece):
            qs += list(reply.destinations.all())
        if piece.written_id:
            qs += list(Destination.objects.filter(
                written_id=piece.written_id))
        for dest in qs:
            if dest.destination_type == "piece":
                if dest.piece_dest_id:
                    adj[piece.id].add(dest.piece_dest_id)
                else:
                    dangling += 1
        for frag in Fragment.objects.filter(
                piece=piece, fragment_type="embedded"):
            if frag.embedded_piece_id:
                adj[piece.id].add(frag.embedded_piece_id)
        # Los FormWa avanzan por dest_piece_pk (addl_params), no por
        # Destination: sin esto, todo lo que cuelga del submit se reporta
        # como inalcanzable.
        for frag in Fragment.objects.filter(
                piece=piece, fragment_type="behavior"):
            dest_pk = (frag.addl_params or {}).get("dest_piece_pk")
            if dest_pk:
                adj[piece.id].add(dest_pk)

    seen = {pieces[start].id}
    queue = deque([pieces[start].id])
    while queue:
        cur = queue.popleft()
        for nxt in adj.get(cur, ()):
            if nxt in by_id and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    unreached = {by_id[pid] for pid in by_id if pid not in seen}
    return unreached, dangling
