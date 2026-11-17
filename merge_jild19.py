#!/usr/bin/env python3
"""Merge Jild 19 tashreeh chunks into jild-19.json.

Re-runnable: reads every jild-19-chunk-*.json listed in the manifest,
merges in chunk order, validates (unique ids, page coverage, no empty
jawab), writes jild-19.json, and updates the manifest statuses.

INPUT (verified on disk by the parent):
  16 chunk files for 12 chunks (04, 06, 08, 09 split into a/b halves),
  269 chunk items, volume_id 45.
  Source export ~/workspace/fatawa-app/content/jild-19.json: 599 unique
  pages pp. 5-692. Gaps (89, nothing invented): pp. 8-92 (85), 152,
  172, 610, 644.

COMBINE RULES (8 cases; parts ordered by min page; sawal from the
FIRST part unless noted; jawab = all parts concatenated in page
order; pages = UNION of all parts' pages; notes = all parts' notes):
  masala 24:   chunk 01 [138] + chunk 02 [139-141] -> [138-141].
              CONCATENATE both sawals (chunk 01's 377 chars + chunk
              02's 1,021 chars — Jild 12 masala-289 precedent; chunk
              01's sawal ends mid-sentence, chunk 02's carries the
              "تین صورتیں" verified on source p. 139). Jawab from
              chunk 02 (3,449 chars).
  masala 48:   chunk 02 [185-192] + chunk 03 [193] -> [185-193].
              Sawal from chunk 02 (3,337); jawab = 6,532 + 483.
  masala 91:   chunk 04 [292] + chunk 05 [293] -> [292, 293]. Sawal
              from chunk 04 (805); jawab = 399 + 654. TITLE FIX: both
              parts' titles end with "(حصہ اول)" — drop that suffix
              from the combined item's title, since the item will
              then be complete.
  masala 113:  chunk 05 [342] + chunk 06 [343] -> [342, 343].
              CONCATENATE both sawals (chunk 05's 664 chars + chunk
              06's 206-char question tail — verified from source:
              p. 342 ends mid-sentence, p. 343 continues then the
              question ends and the answer begins). Jawab from
              chunk 06 (1,335 chars).
  masala 140:  chunk 06 [391-392] + chunk 07 [393] -> [391-393].
              Sawal from chunk 06 (869); jawab = 1,532 + 1,204.
  masala 153:  chunk 07 [440] + chunk 08 [441-444] -> [440-444].
              Keep ONE sawal — chunk 08's fuller 487-char
              restatement; DISCARD chunk 07's 433-char partial
              (Jild 11 masala-16 rule). Jawab from chunk 08 (3,786).
  masala 172:  chunk 08 [489-490] + chunk 09 [491-492] -> [489-492].
              Sawal from chunk 08 (776); jawab from chunk 09 (1,948).
  masala 228 (CROSS-ID): chunk 10 'jild19-masala-228' [563-590] +
              chunk 11 'jild19-muna-wal-durar-2' [591-607] -> ONE item
              'jild19-masala-228', pages [563-607]. Sawal from chunk
              10 (1,041; chunk 11's half has empty sawal); jawab =
              33,074 + 19,890 concatenated. Continuity verified from
              source: p. 590 tail ends mid-sentence, p. 591 head
              continues the same sentence, no new heading.
After all 8 combines: 269 - 8 = 261 items covering 599 unique pages.

RENAME (1 — coordinator decision, verified from source p. 433):
  'jild19-masala-250' -> 'jild19-masala-150': p. 433 prints ۲۵۰
  between masala 147-149 and masala 151 — almost certainly a print
  error for ۱۵۰. No other item claims 150. The item's notes record
  the anomaly. Single item, pages [433-437], just renamed — NOT a
  combine.

SORT: merged items are sorted by start_page for the final file.
Chunk 07's file has an edit mishap: 'jild19-masala-147-149' is first
in the array; it belongs between 146 and 250 (by start_page 422).

DO-NOT-COMBINES: the three rasail are SEQUENCES of separately
numbered masail, NOT one mas'ala each — no mega-combines (فتح الملک
فی حکم التملیک pp. 243-404; اجود القرٰی pp. 541-562; کتاب المنٰی
والدرر pp. 563-607, which ends p. 607 INCOMPLETE as printed).
Distinct items kept separate: masala-57 p. 210 vs jild19-p212
(p. 212); masala-193 p. 501 vs jild19-p504 (p. 504); masala-220
p. 539 vs jild19-p541 [541-550].

EMPTY FIELDS: the ONLY empty jawabs among all 269 chunk items are
the 4 split heads (masala-24, -113, -153, -172) — each resolved by
its combine. The merged file must have ZERO empty jawab. After
merging, the only empty sawals are pesh-lafz, masala-70, masala-74,
masala-237 and khatima (by design; their notes explain).
"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))

# result id -> list of selectors, in page order.
# Selector forms:
#   ('id', sid)            — every item with this id (1 or 2 halves)
#   ('id_start', sid, sp)  — the item with this id starting at page sp
COMBINES = {
    'jild19-masala-24': [
        ('id', 'jild19-masala-24'),
    ],
    'jild19-masala-48': [
        ('id', 'jild19-masala-48'),
    ],
    'jild19-masala-91': [
        ('id', 'jild19-masala-91'),
    ],
    'jild19-masala-113': [
        ('id', 'jild19-masala-113'),
    ],
    'jild19-masala-140': [
        ('id', 'jild19-masala-140'),
    ],
    'jild19-masala-153': [
        ('id', 'jild19-masala-153'),
    ],
    'jild19-masala-172': [
        ('id', 'jild19-masala-172'),
    ],
    'jild19-masala-228': [
        ('id', 'jild19-masala-228'),
        ('id', 'jild19-muna-wal-durar-2'),
    ],
}

# Sawal handling per combined id (default: sawal from the first part).
#   'concat': concatenate the sawals of the listed part indices.
#   'from':   take the sawal from the part at this index only.
SAWAL_RULES = {
    'jild19-masala-24': ('concat', [0, 1]),
    'jild19-masala-113': ('concat', [0, 1]),
    'jild19-masala-153': ('from', 1),
}

# Title fix for masala-91: strip this trailing suffix from the
# combined item's title (both parts carry it; the item is complete
# after the combine).
TITLE_SUFFIX_DROP = {
    'jild19-masala-91': ' (حصہ اول)',
}

# Rename applied AFTER the combines (single item, not a combine).
RENAMES = {
    'jild19-masala-250': 'jild19-masala-150',
}

# Expected pages for every combined item (spot-check anchors).
EXPECTED_COMBINED_PAGES = {
    'jild19-masala-24': [138, 139, 140, 141],
    'jild19-masala-48': list(range(185, 194)),
    'jild19-masala-91': [292, 293],
    'jild19-masala-113': [342, 343],
    'jild19-masala-140': [391, 392, 393],
    'jild19-masala-153': list(range(440, 445)),
    'jild19-masala-172': [489, 490, 491, 492],
    'jild19-masala-228': list(range(563, 608)),
}

# Expected sawal/jawab char counts for every combined item.
EXPECTED_COMBINED_TEXT = {
    'jild19-masala-24': (1398, 3449),
    'jild19-masala-48': (3337, 7015),
    'jild19-masala-91': (805, 1053),
    'jild19-masala-113': (870, 1335),
    'jild19-masala-140': (869, 2736),
    'jild19-masala-153': (487, 3786),
    'jild19-masala-172': (776, 1948),
    'jild19-masala-228': (1041, 52964),
}

# The only ids that may be absorbed by a combine (must be gone after).
ABSORBED = ['jild19-muna-wal-durar-2']

# The only items allowed to keep an empty sawal after merging.
EMPTY_SAWAL_ALLOWED = {'jild19-pesh-lafz', 'jild19-masala-70',
                       'jild19-masala-74', 'jild19-masala-237',
                       'jild19-khatima'}


def combine_parts(result_id, parts):
    parts = sorted(parts, key=lambda it: min(it['pages']))
    first = parts[0]
    rule = SAWAL_RULES.get(result_id)
    if rule and rule[0] == 'concat':
        sawal = ''.join((parts[i].get('tashreeh_sawal', '') or '')
                        for i in rule[1])
    elif rule and rule[0] == 'from':
        sawal = parts[rule[1]].get('tashreeh_sawal', '') or ''
    else:
        sawal = first.get('tashreeh_sawal', '') or ''
    title = first.get('title') or ''
    suffix = TITLE_SUFFIX_DROP.get(result_id)
    if suffix and title.endswith(suffix):
        title = title[:-len(suffix)]
    combined = {
        'id': result_id,
        'title': title,
        'volume_id': 45,
        'pages': sorted(set().union(*[set(p['pages']) for p in parts])),
        'start_page': min(min(p['pages']) for p in parts),
        'tashreeh_sawal': sawal,
        'tashreeh_jawab': ''.join((p.get('tashreeh_jawab', '') or '') for p in parts),
        'notes': [n for p in parts for n in (p.get('notes') or [])],
    }
    return combined


def select_parts(all_items, selectors):
    """Resolve selectors to the matching items (each used at most once)."""
    parts = []
    used = set()
    for sel in selectors:
        if sel[0] == 'id':
            hits = [it for it in all_items
                    if it['id'] == sel[1] and id(it) not in used]
        elif sel[0] == 'id_start':
            hits = [it for it in all_items
                    if it['id'] == sel[1] and it['start_page'] == sel[2]
                    and id(it) not in used]
        else:
            raise ValueError(f'unknown selector {sel}')
        assert hits, f'no items matched selector {sel}'
        for it in hits:
            used.add(id(it))
        parts.extend(hits)
    return parts


def run_merge(manifest_path, base, write=False):
    manifest = json.load(open(manifest_path, encoding='utf-8'))
    all_items = []
    merged_chunks = []
    for entry in manifest['chunks']:
        nn = entry['chunk']
        if entry.get('status') == 'split-halves':
            print(f'chunk {nn}: split-halves placeholder — halves are separate entries, skipping')
            continue
        # A chunk may be one file ("file") or split halves ("files").
        file_list = entry.get('files') or [entry['file']]
        items = []
        for fname in file_list:
            path = os.path.join(base, fname)
            if not os.path.exists(path):
                print(f'chunk {nn}: {fname} not yet written')
                continue
            try:
                d = json.load(open(path, encoding='utf-8'))
            except json.JSONDecodeError as e:
                # File may still be streaming from its translator; skip it
                # for now instead of crashing the whole merge.
                print(f'chunk {nn}: {fname} not valid JSON yet ({e}) — skipping for now')
                continue
            items.extend(d['masail'])
        if not items:
            print(f'chunk {nn}: no items loaded — skipping')
            continue
        # Normalize: some translators omit start_page; derive it from pages.
        for it in items:
            if 'start_page' not in it:
                assert it.get('pages'), f'chunk {nn} item {it.get("id")} has no pages'
                it['start_page'] = it['pages'][0]
                print(f'chunk {nn}: derived start_page={it["start_page"]} for {it["id"]}')
            assert it['start_page'] == min(it['pages']), \
                f'chunk {nn} item {it["id"]}: start_page != first page'
            it['_src_file'] = file_list[0]
        all_items.extend(items)
        merged_chunks.append(nn)
        entry['status'] = 'merged'
        print(f'chunk {nn}: {len(items)} items merged')
    print(f'items before combines: {len(all_items)}')
    assert len(all_items) == 269, f'expected 269 chunk items, got {len(all_items)}'
    # COMBINE the 8 cases (one mas'ala split across chunks).
    for result_id, selectors in COMBINES.items():
        parts = select_parts(all_items, selectors)
        combined = combine_parts(result_id, parts)
        assert combined['pages'] == EXPECTED_COMBINED_PAGES[result_id], \
            f'{result_id}: pages {combined["pages"]} != expected {EXPECTED_COMBINED_PAGES[result_id]}'
        exp_sawal, exp_jawab = EXPECTED_COMBINED_TEXT[result_id]
        assert len(combined['tashreeh_sawal']) == exp_sawal, \
            f'{result_id}: sawal {len(combined["tashreeh_sawal"])} chars != expected {exp_sawal}'
        assert len(combined['tashreeh_jawab']) == exp_jawab, \
            f'{result_id}: jawab {len(combined["tashreeh_jawab"])} chars != expected {exp_jawab}'
        assert combined['tashreeh_jawab'], f'{result_id}: combined jawab is empty!'
        assert combined['tashreeh_sawal'], f'{result_id}: combined sawal is empty!'
        assert combined['start_page'] == min(combined['pages']), f'{result_id}: start_page != min(pages)'
        used_ids = set(id(p) for p in parts)
        all_items = [it for it in all_items if id(it) not in used_ids]
        all_items.append(combined)
        print(f'COMBINED {result_id}: {len(parts)} parts, pages {combined["pages"][0]}-{combined["pages"][-1]} '
              f'({len(combined["pages"])} pages), sawal {len(combined["tashreeh_sawal"])} chars, '
              f'jawab {len(combined["tashreeh_jawab"])} chars, notes {len(combined["notes"])}')
    # RENAME the single misprinted id (not a combine).
    for old_id, new_id in RENAMES.items():
        assert not any(it['id'] == new_id for it in all_items), \
            f'rename target {new_id} already exists!'
        hits = [it for it in all_items if it['id'] == old_id]
        assert len(hits) == 1, f'rename source {old_id}: expected exactly 1 item, found {len(hits)}'
        hits[0]['id'] = new_id
        print(f'RENAMED {old_id} -> {new_id} (pages {hits[0]["pages"][0]}-{hits[0]["pages"][-1]})')
    ids = [it['id'] for it in all_items]
    assert len(ids) == len(set(ids)), f'STILL DUPLICATE IDS: {[i for i in ids if ids.count(i) > 1]}'
    empty = [it['id'] for it in all_items if not it.get('tashreeh_jawab')]
    assert not empty, f'EMPTY JAWAB: {empty}'
    empty_sawal = [it['id'] for it in all_items if not it.get('tashreeh_sawal')]
    assert set(empty_sawal) == EMPTY_SAWAL_ALLOWED, \
        f'EMPTY SAWAL mismatch: {sorted(empty_sawal)} != {sorted(EMPTY_SAWAL_ALLOWED)}'
    print(f'empty sawal (by design only): {sorted(empty_sawal)}')
    pages = set()
    for it in all_items:
        pages.update(it['pages'])
    # PRIMARY coverage check (Jild 17 lesson): validate against the 599
    # unique pages directly, not against a range-minus-gaps computation.
    assert len(pages) == 599, f'expected 599 unique pages, got {len(pages)}'
    assert min(pages) == 5 and max(pages) == 692, \
        f'page span {min(pages)}-{max(pages)} != 5-692'
    # Secondary cross-check: manifest ranges minus listed gap pages.
    expected = set()
    for entry in manifest['chunks']:
        if entry['chunk'] in merged_chunks:
            expected.update(range(entry['start_page'], entry['end_page'] + 1))
            expected.difference_update(entry['missing_pages'])
    missing_covered = expected - pages
    extra = pages - expected
    print(f'total items: {len(all_items)} | pages covered: {len(pages)} | expected (manifest): {len(expected)}')
    print(f'uncovered expected pages: {sorted(missing_covered)}')
    print(f'extra pages (outside merged chunks): {sorted(extra)}')
    assert not missing_covered, 'pages missing from merged chunks!'
    assert not extra, 'pages outside merged chunks!'
    assert len(all_items) == 261, f'expected 261 items after combines, got {len(all_items)}'
    # sort by start_page for the final file
    all_items.sort(key=lambda it: it['start_page'])
    for it in all_items:
        it.pop('_src_file', None)
    if write:
        with open(os.path.join(base, 'jild-19.json'), 'w', encoding='utf-8') as f:
            json.dump({'masail': all_items}, f, ensure_ascii=False, indent=1)
        with open(os.path.join(base, 'chunks-manifest-jild19.json'), 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        print(f'WROTE jild-19.json: {len(all_items)} items, {len(pages)} pages, chunks merged: {merged_chunks}')
    return all_items, pages, merged_chunks


def main():
    manifest_path = os.path.join(BASE, 'chunks-manifest-jild19.json')
    run_merge(manifest_path, BASE, write=True)


if __name__ == '__main__':
    main()
