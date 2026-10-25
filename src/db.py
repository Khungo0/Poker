"""Persistencia local SQLite. Sin sincronización externa ni uso en tiempo real."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from .ipoker import Hand
from .stats import Observation

DEFAULT_DB = Path(__file__).resolve().parent.parent / 'data' / 'population.sqlite'

def connect(path: Path = DEFAULT_DB):
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS hands (
            hand_id TEXT PRIMARY KEY, stake TEXT NOT NULL, format TEXT NOT NULL, source TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS observations (
            hand_id TEXT NOT NULL, stake TEXT NOT NULL, format TEXT NOT NULL,
            spot TEXT NOT NULL, actor TEXT NOT NULL, opponent TEXT NOT NULL,
            bb_eff REAL NOT NULL, result TEXT NOT NULL,
            FOREIGN KEY (hand_id) REFERENCES hands(hand_id)
        );
        CREATE INDEX IF NOT EXISTS ix_obs_filters ON observations(spot,format,stake,bb_eff);
        CREATE INDEX IF NOT EXISTS ix_obs_actor ON observations(actor);
        CREATE TABLE IF NOT EXISTS labels (
            player TEXT PRIMARY KEY, category TEXT NOT NULL
            CHECK(category IN ('Reg','Fish','Sin clasificar'))
        );
    ''')
    return conn


def insert_hands(conn, hands: list[Hand], facts: list[Observation]):
    added = 0
    with conn:
        for hand in hands:
            row = conn.execute('INSERT OR IGNORE INTO hands VALUES (?,?,?,?)',
                               (hand.hand_id,hand.stake,hand.format,hand.source))
            added += row.rowcount
        valid = set(r[0] for r in conn.execute('SELECT hand_id FROM hands'))
        # Avoid duplicate facts on repeated import; facts for existing hands already present.
        known = set(r[0] for r in conn.execute('SELECT DISTINCT hand_id FROM observations'))
        newfacts = [f for f in facts if f.hand_id in valid and f.hand_id not in known]
        conn.executemany('INSERT INTO observations VALUES (?,?,?,?,?,?,?,?)', [
            (f.hand_id,f.stake,f.format,f.spot,f.actor,f.opponent,f.bb_eff,f.result)
            for f in newfacts
        ])
    return added, len(newfacts)


def set_label(conn, player: str, category: str):
    if category not in ('Reg','Fish','Sin clasificar'):
        raise ValueError('Categoría inválida')
    with conn:
        conn.execute('INSERT INTO labels VALUES (?,?) ON CONFLICT(player) DO UPDATE SET category=excluded.category',
                     (player, category))


def players(conn):
    return conn.execute('''SELECT actor AS player, COUNT(DISTINCT hand_id) AS hands,
       COALESCE((SELECT category FROM labels WHERE player=actor),'Sin clasificar') AS category
       FROM observations GROUP BY actor ORDER BY hands DESC, player''').fetchall()


def filtered_observations(conn, spot, format_, stake, minbb, maxbb, population, opponent_population='Todos'):
    query = '''SELECT o.result, o.actor, o.bb_eff,
        COALESCE(l.category,'Sin clasificar') AS category,
        COALESCE(lo.category,'Sin clasificar') AS opponent_category
        FROM observations o LEFT JOIN labels l ON o.actor=l.player
        LEFT JOIN labels lo ON o.opponent=lo.player
        WHERE o.spot=? AND o.bb_eff BETWEEN ? AND ?'''
    params = [spot,minbb,maxbb]
    if format_ != 'Todos':
        query += ' AND o.format=?'; params.append(format_)
    if stake != 'Todos':
        query += ' AND o.stake=?'; params.append(stake)
    if population != 'Todos':
        query += " AND COALESCE(l.category,'Sin clasificar')=?"; params.append(population)
    if opponent_population != 'Todos':
        query += " AND COALESCE(lo.category,'Sin clasificar')=?"; params.append(opponent_population)
    return conn.execute(query, params).fetchall()


def counts(conn):
    return conn.execute('SELECT COUNT(*) hands FROM hands').fetchone()['hands'], conn.execute('SELECT COUNT(*) n FROM observations').fetchone()['n']
