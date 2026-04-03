# Unused calls 2

Noticed following cases:

```text
Bash(uv run python3 -c "
      import polars as pl
      k = pl.read_parquet('data/prep/kaggle_players.parquet')
      s = pl.read_parquet('data/prep/sackmann_players.parquet')
      matched = k.filter(pl.col('player_code').is_in(s['player_code']))
      print(f'kaggle: {k.height}, sackmann: {s.height}, matched by player_code: {matched.height}, kaggle unmatched: {k.height -
      matched.height}')
      k_unmatched = k.filter(~pl.col('player_code').is_in(s['player_code']))
      print('Sample unmatched kaggle:')
      print(k_unmatched.head(10))
      ")
  ⎿  <string>:5: DeprecationWarning: `is_in` with a collection of the same datatype is ambiguous and deprecated.
     Please use `implode` to return to previous behavior.

     See https://github.com/pola-rs/polars/issues/22149 for more information.
     <string>:7: DeprecationWarning: `is_in` with a collection of the same datatype is ambiguous and deprecated.
     Please use `implode` to return to previous behavior.

     See https://github.com/pola-rs/polars/issues/22149 for more information.
     kaggle: 1794, sackmann: 65989, matched by player_code: 1625, kaggle unmatched: 169
     Sample unmatched kaggle:
     shape: (10, 5)
     ┌───────────────────┬───────────────┬─────────────┬────────────┬───────────────┐
     │ kaggle_player_idx ┆ player_name   ┆ name_last   ┆ name_first ┆ player_code   │
     │ ---               ┆ ---           ┆ ---         ┆ ---        ┆ ---           │
     │ u32               ┆ str           ┆ str         ┆ str        ┆ str           │
     ╞═══════════════════╪═══════════════╪═════════════╪════════════╪═══════════════╡
     │ 15                ┆ Al Ghareeb M. ┆ Al Ghareeb  ┆ M          ┆ al-ghareeb-m  │
     │ 17                ┆ Al-Alawi S.K. ┆ Al-Alawi    ┆ S.K        ┆ al-alawi-s    │
     │ 18                ┆ Al-Ghareeb M. ┆ Al-Ghareeb  ┆ M          ┆ al-ghareeb-m2 │
     │ 27                ┆ Almagro N.    ┆ Almagro N.  ┆ null       ┆ almagro-n-x   │
     │ 48                ┆ Andreev I.    ┆ Andreev I.  ┆ null       ┆ andreev-i-x   │
     │ 53                ┆ Aragone J.C.  ┆ Aragone     ┆ J.C        ┆ aragone-j2    │
     │ 54                ┆ Aragone JC    ┆ Aragone     ┆ JC         ┆ aragone-j3    │
     │ 62                ┆ Arnold L.     ┆ Arnold      ┆ L          ┆ arnold-l      │
     │ 85                ┆ Bahrouzyan O. ┆ Bahrouzyan  ┆ O          ┆ bahrouzyan-o  │
     │ 88                ┆ Bailly G.A.   ┆ Bailly      ┆ G.A        ┆ bailly-g2     │
     └───────────────────┴───────────────┴─────────────┴────────────┴───────────────┘

Bash(uv run python3 -c "
      import polars as pl
      k = pl.read_parquet('data/prep/kaggle_players.parquet')
      s = pl.read_parquet('data/prep/sackmann_players.parquet')
      kaggle_only = k.filter(~pl.col('player_code').is_in(s['player_code'].implode()))

      # Look for Cilic and Djokovic in both datasets
      for name in ['cilic', 'djokovic', 'nadal', 'federer']:
          print(f'=== {name} ===')
          krows = k.filter(pl.col('player_code').str.contains(name))
          srows = s.filter(pl.col('player_code').str.contains(name))
          ko = kaggle_only.filter(pl.col('player_code').str.contains(name))
          print(f'Kaggle: {krows.select(\"player_name\", \"name_last\", \"name_first\", \"player_code\").to_dicts()}')
          print(f'Sackmann: {srows.select(\"name_first\", \"name_last\", \"player_code\").to_dicts()}')
          print(f'Unmatched: {ko.select(\"player_name\", \"player_code\").to_dicts()}')
          print()
      ")
  ⎿  === cilic ===
     Kaggle: [{'player_name': 'Cilic M.', 'name_last': 'Cilic', 'name_first': 'M', 'player_code': 'cilic-m'}, {'player_name': 'Cilic
     M. ', 'name_last': 'Cilic M. ', 'name_first': None, 'player_code': 'cilic-m-x'}]
     Sackmann: [{'name_first': 'Marin', 'name_last': 'Cilic', 'player_code': 'cilic-m'}, {'name_first': 'Mile', 'name_last': 'Cilic',
      'player_code': 'cilic-m2'}]
     Unmatched: [{'player_name': 'Cilic M. ', 'player_code': 'cilic-m-x'}]

     === djokovic ===
     Kaggle: [{'player_name': 'Djokovic M.', 'name_last': 'Djokovic', 'name_first': 'M', 'player_code': 'djokovic-m'},
     {'player_name': 'Djokovic N.', 'name_last': 'Djokovic', 'name_first': 'N', 'player_code': 'djokovic-n'}, {'player_name':
     'Djokovic N. ', 'name_last': 'Djokovic N. ', 'name_first': None, 'player_code': 'djokovic-n-x'}]
     Sackmann: [{'name_first': 'Novak', 'name_last': 'Djokovic', 'player_code': 'djokovic-n'}, {'name_first': 'Marko', 'name_last':
     'Djokovic', 'player_code': 'djokovic-m'}, {'name_first': 'Djordje', 'name_last': 'Djokovic', 'player_code': 'djokovic-d'}]
     Unmatched: [{'player_name': 'Djokovic N. ', 'player_code': 'djokovic-n-x'}]

     === nadal ===
     Kaggle: [{'player_name': 'Nadal R.', 'name_last': 'Nadal', 'name_first': 'R', 'player_code': 'nadal-r'}, {'player_name': 'Nadal
     R. ', 'name_last': 'Nadal R. ', 'name_first': None, 'player_code': 'nadal-r-x'}, {'player_name': 'Nadal-Parera R.', 'name_last':
      'Nadal-Parera', 'name_first': 'R', 'player_code': 'nadal-parera-r'}]
     Sackmann: [{'name_first': 'Rafael', 'name_last': 'Nadal', 'player_code': 'nadal-r'}, {'name_first': 'Jorge', 'name_last':
     'Nadal', 'player_code': 'nadal-j'}, {'name_first': 'Joan', 'name_last': 'Nadal Vives', 'player_code': 'nadal-vives-j'}]
     Unmatched: [{'player_name': 'Nadal R. ', 'player_code': 'nadal-r-x'}, {'player_name': 'Nadal-Parera R.', 'player_code':
     'nadal-parera-r'}]

     === federer ===
     Kaggle: [{'player_name': 'Federer R.', 'name_last': 'Federer', 'name_first': 'R', 'player_code': 'federer-r'}, {'player_name':
     'Federer R. ', 'name_last': 'Federer R. ', 'name_first': None, 'player_code': 'federer-r-x'}]
     Sackmann: [{'name_first': 'Roger', 'name_last': 'Federer', 'player_code': 'federer-r'}]
     Unmatched: [{'player_name': 'Federer R. ', 'player_code': 'federer-r-x'}]
```
