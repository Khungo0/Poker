"""Importador exploratorio del formato XML histórico de iPoker.

El parser conserva el texto de las acciones y NO infiere los datos ausentes.
Los dialectos de iPoker varían entre skins; se requieren archivos reales para validación.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from typing import Iterable
import xml.etree.ElementTree as ET
import re


@dataclass(frozen=True)
class Player:
    name: str
    seat: str
    chips: float
    dealer: bool


@dataclass(frozen=True)
class Action:
    round_number: int
    player: str
    kind: str
    amount: float
    original: str


@dataclass(frozen=True)
class Hand:
    hand_id: str
    players: tuple[Player, ...]
    actions: tuple[Action, ...]
    bb: float
    sb: float
    stake: str
    source: str

    @property
    def format(self) -> str:
        return 'HU' if len(self.players) == 2 else '3H'


def money(raw: str | None) -> float:
    """Devuelve importe numérico de variantes 1,679.00 / 1.679,00 / €0,10."""
    if not raw:
        return 0.0
    txt = re.sub(r'[^\d.,\-]', '', str(raw))
    if not txt:
        return 0.0
    if ',' in txt and '.' in txt:
        if txt.rfind(',') > txt.rfind('.'):
            txt = txt.replace('.', '').replace(',', '.')
        else:
            txt = txt.replace(',', '')
    elif ',' in txt:
        parts = txt.split(',')
        txt = txt.replace(',', '.') if len(parts) == 2 and len(parts[-1]) <= 2 else txt.replace(',', '')
    elif '.' in txt and txt.count('.') > 1:
        parts = txt.split('.')
        txt = ''.join(parts[:-1]) + '.' + parts[-1]
    try:
        return float(Decimal(txt))
    except InvalidOperation:
        return 0.0


def action_kind(text: str, type_code: str | None) -> str:
    x = re.sub(r'\s+', ' ', text.strip().lower())
    if type_code == '1' or x in {'sb', 'small blind', 'post sb'}:
        return 'SB'
    if type_code == '2' or x in {'bb', 'big blind', 'post bb'}:
        return 'BB'
    if 'fold' in x:
        return 'fold'
    if 'check' in x:
        return 'check'
    if 'call' in x or 'complete' in x:
        return 'call'
    if any(key in x for key in ('raise', 'all in', 'all-in', 'allin', 'shove')):
        return 'raise'
    if 'bet' in x:
        return 'bet'
    return 'unknown'


def parse_ipoker_xml(data: bytes, source: str, stake: str) -> tuple[list[Hand], list[str]]:
    """Importa archivos tipo <session><game>...</game></session>.

    Rechaza XML con DTD/ENTITY y avisa de las manos sin suficiente información.
    No se intenta parsear otras redes/formas sin ejemplos validados.
    """
    if len(data) > 50_000_000:
        raise ValueError('Archivo demasiado grande (máximo 50 MB por importación).')
    if re.search(rb'<!\s*(DOCTYPE|ENTITY)', data, flags=re.I):
        raise ValueError('XML con DTD o ENTITY no está permitido.')
    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        raise ValueError(f'XML no válido: {e}') from e
    session_code = root.attrib.get('sessioncode', source)
    warnings: list[str] = []
    hands: list[Hand] = []
    games = [root] if root.tag.lower() == 'game' else root.findall('.//game')
    if not games:
        raise ValueError('No encontré etiquetas <game> compatibles con iPoker.')
    for ordinal, game in enumerate(games):
        general = game.find('general')
        if general is None:
            warnings.append(f'Juego {ordinal+1}: sin <general>; omitido')
            continue
        pl_root = general.find('players')
        if pl_root is None:
            warnings.append(f'Juego {ordinal+1}: sin <players>; omitido')
            continue
        players = tuple(
            Player(name=p.attrib.get('name', ''), seat=p.attrib.get('seat',''),
                   chips=money(p.attrib.get('chips')), dealer=p.attrib.get('dealer','0') == '1')
            for p in pl_root.findall('player')
        )
        if len(players) not in (2, 3) or any(not p.name for p in players):
            warnings.append(f'Juego {ordinal+1}: no es HU/3H válido; omitido')
            continue
        actions: list[Action] = []
        for rd in game.findall('round'):
            try:
                no = int(rd.attrib.get('no','-1'))
            except ValueError:
                continue
            for element in rd.findall('action'):
                raw = element.attrib.get('actiontxt','')
                actions.append(Action(
                    round_number=no,
                    player=element.attrib.get('player',''),
                    kind=action_kind(raw, element.attrib.get('type')),
                    amount=money(element.attrib.get('sum')),
                    original=raw,
                ))
        ambiguous = sum(1 for a in actions if a.kind == 'unknown' and a.round_number == 1)
        if ambiguous:
            warnings.append(f'Juego {ordinal+1}: {ambiguous} acciones preflop desconocidas; se excluirá del análisis')
        small = next((a.amount for a in actions if a.round_number == 0 and a.kind == 'SB'), 0.0)
        big = next((a.amount for a in actions if a.round_number == 0 and a.kind == 'BB'), 0.0)
        if big <= 0 or small <= 0:
            warnings.append(f'Juego {ordinal+1}: blinds no detectadas; omitido')
            continue
        hand_code = game.attrib.get('gamecode', str(ordinal))
        fingerprint = f'{session_code}:{hand_code}'
        ident = sha256(fingerprint.encode('utf-8')).hexdigest()
        hands.append(Hand(ident, players, tuple(actions), big, small, stake, source))
    return hands, warnings
