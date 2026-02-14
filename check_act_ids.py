from data_bridge.loader import JSONLoader
loader = JSONLoader('db')
sections, _, _ = loader.load_and_normalize_directory()
indian = [s for s in sections if 'indian_law_dataset' in s.act_id]
print('Act IDs:')
for act_id in sorted(set(s.act_id for s in indian)):
    count = len([s for s in indian if s.act_id == act_id])
    print(f'  {act_id}: {count}')
print(f'\nTotal: {len(indian)}')
