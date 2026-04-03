# Feedback 2

## 1. Invocation issue

Agent triend to run peek with

```text
Bash(python -m peek data/prep/kaggle_players.parquet -c)
```

Need to make it clear for the coding agent that skill tools can be invoked directly without python like `peek data/prep/kaggle_players.parquet -c`

## 2. Unused calls

Noticed following cases:

```
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
```

## 3. Failure to run a skill post-install

I have just installed a skill with `just i` but having:

```bash
srg@srg-kub2510-b15a11m:~$ suggest test-skill "blah blah"
bash: /home/srg/.nvm/versions/node/v24.11.1/bin/suggest: Permission denied
```
