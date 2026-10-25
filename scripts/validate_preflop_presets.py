"""Read-only cross-check against original actions, without derived observations.

Checks HU opening opportunities, BB responses to non-all-in 2 BB opens and
three-handed BB squeeze opportunities. Output contains aggregates and mismatch
IDs only; player names and original histories stay in the local database.
"""
import argparse
from collections import Counter
import json
from pathlib import Path

import duckdb

from src.history import parse_hand
from src.presets import PRESETS_BY_KEY
from src.sequences import matched_query


KEYS = ('hu_sb_open', 'hu_bb_vs_minraise', '3h_bb_squeeze')


def oracle(hand):
    seated = sorted(hand.players, key=lambda p: p['seat'])
    button = next(i for i, p in enumerate(seated) if p['dealer'])
    order = seated[button:] + seated[:button]
    positions = ['SB', 'BB'] if hand.format == 'HU' else ['BTN', 'SB', 'BB']
    names = dict(zip(positions, [p['name'] for p in order]))
    capacity = {p['name']: p['stack'] for p in hand.players}
    paid = dict.fromkeys(capacity, 0)
    pre = []
    active = set(capacity)
    raised = False
    for seq, action in enumerate(hand.actions):
        actor, kind, amount = action['player'], action['kind'], action['amount']
        if action['street'] == 0:
            if kind == 'ante':
                capacity[actor] -= amount
            else:
                paid[actor] += amount
        elif action['street'] == 1:
            total = amount if kind == 'raise_to' else paid[actor] + amount
            high = max(hand.bb, max(paid.values()))
            if kind in ('raise_to', 'allin'):
                contestable = any(capacity[n] > high for n in active if n != actor)
                outcome = ('shove' if total == capacity[actor] else 'raise') if total > high and contestable else 'call'
            else:
                outcome = kind
            if outcome == 'call' and not raised:
                outcome = 'limp'  # Includes a short SB all-in which cannot raise the blind.
            if outcome in ('raise', 'shove'):
                raised = True
            if kind == 'fold':
                active.remove(actor)
            pre.append(dict(seq=seq, actor=actor, total=total, outcome=outcome))
            if kind not in ('fold', 'check'):
                paid[actor] = total
    expected = {}

    def record(key, row):
        if hand.known_cards.get(row['actor'], {}).get('source') != 'dealt':
            expected[key] = (hand.hand_id, row['seq'], row['outcome'])

    if hand.format == 'HU':
        if pre and pre[0]['actor'] == names['SB']:
            record('hu_sb_open', pre[0])
        if (len(pre) >= 2 and pre[0]['actor'] == names['SB']
                and pre[0]['outcome'] == 'raise' and pre[0]['total'] == 2 * hand.bb
                and pre[1]['actor'] == names['BB']):
            record('hu_bb_vs_minraise', pre[1])
    elif (len(pre) >= 3 and [r['actor'] for r in pre[:3]] == [names[p] for p in positions]
          and pre[0]['outcome'] == 'raise' and pre[1]['outcome'] == 'call'
          and capacity[names['BB']] > pre[0]['total']):
        record('3h_bb_squeeze', pre[2])
    return expected


def validate(path, stake='EUR 5.00'):
    con = duckdb.connect(str(path), read_only=True)
    try:
        expected = {key: {} for key in KEYS}
        for raw, in con.execute('SELECT raw FROM hands WHERE stake=?', [stake]).fetchall():
            for key, (ident, seq, outcome) in oracle(parse_hand(raw)).items():
                expected[key][(ident, seq)] = outcome
        reports = {}
        for key in KEYS:
            preset = PRESETS_BY_KEY[key]
            sql, args = matched_query(preset.pattern, dict(format=preset.format, stake=stake))
            cursor = con.execute(sql, args)
            columns = [column[0] for column in cursor.description]
            actual = {}
            for values in cursor.fetchall():
                row = dict(zip(columns, values))
                actual[(row['hand_id'], row['seq'])] = row['result']
            exp = expected[key]
            reports[key] = dict(
                oracle_opportunities=len(exp), query_opportunities=len(actual),
                counts=dict(Counter(exp.values())),
                missing=sorted(exp.keys() - actual.keys()),
                unexpected=sorted(actual.keys() - exp.keys()),
                outcome_mismatches=sorted(k for k in exp.keys() & actual.keys() if exp[k] != actual[k]),
            )
        return reports
    finally:
        con.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--stake', default='EUR 5.00')
    args = parser.parse_args()
    reports = validate(args.db, args.stake)
    output = json.dumps(reports, indent=2)
    Path(args.output).write_text(output + '\n', encoding='utf-8')
    print(output)
    if any(r[k] for r in reports.values() for k in ('missing', 'unexpected', 'outcome_mismatches')):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
