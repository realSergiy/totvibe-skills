# Improvements for peek

I have noticed current functionality of the peek skill is not enough. Even though the agent loaded the skill, he still went on to do the following:

```text
Bash(uv run peek data/prep/sackmann_matches.parquet -n 3 -t)
  ⎿  sackmann_matches[3]{tourney_id,match_num,winner_seed,winner_entry,loser_seed,loser_entry,score,best_of,round,minutes,w_ace,w_df,
     w_svpt,w_1stIn,w_1stWon,w_2ndWon,w_SvGms,w_bpSaved,w_bpFaced,l_ace,l_df,l_svpt,l_1stIn,l_1stWon,l_2ndWon,l_SvGms,l_bpSaved,l_bpF
     aced,winner_rank,winner_rank_points,loser_rank,loser_rank_points,winner_code,loser_code}:
       2000-301,1,1,null,null,null,7-5 4-6
     7-5,3,R32,108,18,4,96,49,39,28,17,3,5,7,8,106,55,39,29,17,4,7,11,1612,63,595,haas-t,tarango-j
       2000-301,2,null,Q,null,null,7-5
     7-5,3,R32,85,5,3,76,52,39,13,12,5,6,5,10,74,32,25,18,12,3,6,211,157,49,723,balcells-j,squillari-f
       2000-301,3,null,null,null,null,6-3
     6-1,3,R32,56,0,0,55,35,25,12,8,1,1,0,6,56,33,20,7,8,7,11,48,726,59,649,martin-a,berasategui-a
     types[34]: String,Int64,Int64,String,Int64,String,String,Int64,String,Int64,Int64,Int64,Int64,Int64,Int64,Int64,Int64,Int64,Int6
     4,Int64,Int64,Int64,Int64,Int64,Int64,Int64,Int64,Int64,Int64,Int64,Int64,Int64,String,String
     rows: 74906

● Bash(uv run python -c "
      import polars as pl
      t = pl.read_parquet('data/prep/sackmann_tourneys.parquet')
      print(t.group_by('tourney_level', 'draw_size').len().sort('tourney_level', 'draw_size'))
      ")
  ⎿  shape: (21, 3)
     ┌───────────────┬───────────┬─────┐
     │ tourney_level ┆ draw_size ┆ len │
     │ ---           ┆ ---       ┆ --- │
     │ str           ┆ i64       ┆ u32 │
     ╞═══════════════╪═══════════╪═════╡
     │ A             ┆ 8         ┆ 8   │
     │ A             ┆ 12        ┆ 2   │
     │ A             ┆ 16        ┆ 1   │
     │ A             ┆ 18        ┆ 2   │
     │ A             ┆ 24        ┆ 1   │
     │ …             ┆ …         ┆ …   │
     │ M             ┆ 56        ┆ 52  │
     │ M             ┆ 64        ┆ 89  │
     │ M             ┆ 96        ┆ 29  │
     │ M             ┆ 128       ┆ 21  │
     │ O             ┆ 64        ┆ 1   │
     └───────────────┴───────────┴─────┘

● Bash(uv run python -c "
      import polars as pl
      t = pl.read_parquet('data/prep/sackmann_tourneys.parquet')
      print(t.group_by('tourney_level', 'draw_size').len().sort('tourney_level', 'draw_size').to_init_repr())
      " 2>&1 | head -60)
  ⎿  pl.DataFrame(
         [
             pl.Series('tourney_level', ['A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'D', 'D', 'F', 'F', 'G', 'M', 'M', 'M',
     'M', 'M', 'O'], dtype=pl.String),
             pl.Series('draw_size', [8, 12, 16, 18, 24, 28, 32, 48, 56, 64, 2, 4, 8, 16, 128, 48, 56, 64, 96, 128, 64],
     dtype=pl.Int64),
             pl.Series('len', [8, 2, 1, 2, 1, 198, 961, 57, 37, 40, 118, 1777, 28, 1, 99, 26, 52, 89, 29, 21, 1], dtype=pl.UInt32),
         ]
     )

Bash(uv run python -c "
      import polars as pl
      t = pl.read_parquet('data/prep/sackmann_tourneys.parquet')
      # Check what rounds exist in matches
      m = pl.read_parquet('data/prep/sackmann_matches.parquet')
      print('Rounds:', sorted(m['round'].unique().to_list()))
      print()
      # Check D level
      print('D level tourneys:')
      print(t.filter(pl.col('tourney_level') == 'D').head(3))
      print()
      # Check F level
      print('F level tourneys:')
      print(t.filter(pl.col('tourney_level') == 'F').head(3))
      print()
      # Check O level
      print('O level tourneys:')
      print(t.filter(pl.col('tourney_level') == 'O'))
      ")
  ⎿  Rounds: ['BR', 'ER', 'F', 'QF', 'R128', 'R16', 'R32', 'R64', 'RR', 'SF']

     D level tourneys:
     shape: (3, 7)
     ┌────────────┬─────────────────────────┬─────────┬───────────┬───────────────┬──────────────┬──────┐
     │ tourney_id ┆ tourney_name            ┆ surface ┆ draw_size ┆ tourney_level ┆ tourney_date ┆ year │
     │ ---        ┆ ---                     ┆ ---     ┆ ---       ┆ ---           ┆ ---          ┆ ---  │
     │ str        ┆ str                     ┆ str     ┆ i64       ┆ str           ┆ i64          ┆ i32  │
     ╞════════════╪═════════════════════════╪═════════╪═══════════╪═══════════════╪══════════════╪══════╡
     │ 2000-D074  ┆ Davis Cup G2 QF: HKG vs ┆ Hard    ┆ 4         ┆ D             ┆ 20000128     ┆ 2000 │
     │            ┆ PAK                     ┆         ┆           ┆               ┆              ┆      │
     │ 2000-D066  ┆ Davis Cup G1 QF: CHN vs ┆ Hard    ┆ 4         ┆ D             ┆ 20000128     ┆ 2000 │
     │            ┆ UZB                     ┆         ┆           ┆               ┆              ┆      │
     │ 2000-D061  ┆ Davis Cup WG R1: SVK vs ┆ Hard    ┆ 4         ┆ D             ┆ 20000204     ┆ 2000 │
     │            ┆ AUT                     ┆         ┆           ┆               ┆              ┆      │
     └────────────┴─────────────────────────┴─────────┴───────────┴───────────────┴──────────────┴──────┘

     F level tourneys:
     shape: (3, 7)
     ┌────────────┬──────────────┬─────────┬───────────┬───────────────┬──────────────┬──────┐
     │ tourney_id ┆ tourney_name ┆ surface ┆ draw_size ┆ tourney_level ┆ tourney_date ┆ year │
     │ ---        ┆ ---          ┆ ---     ┆ ---       ┆ ---           ┆ ---          ┆ ---  │
     │ str        ┆ str          ┆ str     ┆ i64       ┆ str           ┆ i64          ┆ i32  │
     ╞════════════╪══════════════╪═════════╪═══════════╪═══════════════╪══════════════╪══════╡
     │ 2000-605   ┆ Masters Cup  ┆ Hard    ┆ 8         ┆ F             ┆ 20001127     ┆ 2000 │
     │ 2001-605   ┆ Masters Cup  ┆ Hard    ┆ 8         ┆ F             ┆ 20011112     ┆ 2001 │
     │ 2002-605   ┆ Masters Cup  ┆ Hard    ┆ 8         ┆ F             ┆ 20021111     ┆ 2002 │
     └────────────┴──────────────┴─────────┴───────────┴───────────────┴──────────────┴──────┘

     O level tourneys:
     shape: (1, 7)
     ┌────────────┬────────────────┬─────────┬───────────┬───────────────┬──────────────┬──────┐
     │ tourney_id ┆ tourney_name   ┆ surface ┆ draw_size ┆ tourney_level ┆ tourney_date ┆ year │
     │ ---        ┆ ---            ┆ ---     ┆ ---       ┆ ---           ┆ ---          ┆ ---  │
     │ str        ┆ str            ┆ str     ┆ i64       ┆ str           ┆ i64          ┆ i32  │
     ╞════════════╪════════════════╪═════════╪═══════════╪═══════════════╪══════════════╪══════╡
     │ 2024-0096  ┆ Paris Olympics ┆ Clay    ┆ 64        ┆ O             ┆ 20240729     ┆ 2024 │
     └────────────┴────────────────┴─────────┴───────────┴───────────────┴──────────────┴──────┘

Bash(uv run python -c "
      import polars as pl
      t = pl.read_parquet('data/prep/sackmann_tourneys.parquet')
      m = pl.read_parquet('data/prep/sackmann_matches.parquet')

      # For A-level, we need to figure out 250 vs 500
      # Let's look at some A-level tournament names with different draw sizes
      a = t.filter(pl.col('tourney_level') == 'A')
      print('A-level by draw_size:')
      for ds in sorted(a['draw_size'].unique().to_list()):
          sub = a.filter(pl.col('draw_size') == ds)
          print(f'  draw_size={ds}: {sub.shape[0]} tourneys, e.g. {sub[\"tourney_name\"].head(3).to_list()}')
      print()

      # For M-level
      m_t = t.filter(pl.col('tourney_level') == 'M')
      print('M-level by draw_size:')
      for ds in sorted(m_t['draw_size'].unique().to_list()):
          sub = m_t.filter(pl.col('draw_size') == ds)
          print(f'  draw_size={ds}: {sub.shape[0]} tourneys, e.g. {sub[\"tourney_name\"].head(3).to_list()}')
      ")
  ⎿  A-level by draw_size:
       draw_size=8: 8 tourneys, e.g. ['Laver Cup', 'Laver Cup', 'Laver Cup']
       draw_size=12: 2 tourneys, e.g. ['Atp Cup', 'Laver Cup']
       draw_size=16: 1 tourneys, e.g. ['Atp Cup']
       draw_size=18: 2 tourneys, e.g. ['United Cup', 'United Cup']
       draw_size=24: 1 tourneys, e.g. ['Atp Cup']
       draw_size=28: 198 tourneys, e.g. ['Bastad', 'Newport', 'Gstaad']
       draw_size=32: 961 tourneys, e.g. ['Adelaide', 'Doha', 'Chennai']
       draw_size=48: 57 tourneys, e.g. ['Memphis', 'Kitzbuhel', 'Long Island']
       draw_size=56: 37 tourneys, e.g. ['Barcelona', "Queen's Club", 'Indianapolis']
       draw_size=64: 40 tourneys, e.g. ['Dusseldorf', 'Sydney Olympics', 'Dusseldorf']

     M-level by draw_size:
       draw_size=48: 26 tourneys, e.g. ['Stuttgart Masters', 'Paris Masters', 'Stuttgart Masters']
       draw_size=56: 52 tourneys, e.g. ['Monte Carlo Masters', 'Rome Masters', 'Hamburg Masters']
       draw_size=64: 89 tourneys, e.g. ['Indian Wells Masters', 'Monte Carlo Masters', 'Rome Masters']
       draw_size=96: 29 tourneys, e.g. ['Miami Masters', 'Miami Masters', 'Miami Masters']
       draw_size=128: 21 tourneys, e.g. ['Indian Wells Masters', 'Miami Masters', 'Indian Wells Masters']

Bash(uv run python -c "
      import polars as pl
      t = pl.read_parquet('data/prep/sackmann_tourneys.parquet')
      m = pl.read_parquet('data/prep/sackmann_matches.parquet')

      # Check what rounds exist per tourney_level
      joined = m.join(t.select('tourney_id', 'tourney_level', 'draw_size'), on='tourney_id')
      print('Rounds per tourney_level:')
      for lvl in sorted(joined['tourney_level'].unique().to_list()):
          sub = joined.filter(pl.col('tourney_level') == lvl)
          print(f'  {lvl}: {sorted(sub[\"round\"].unique().to_list())}')
      ")
  ⎿  Rounds per tourney_level:
       A: ['BR', 'ER', 'F', 'QF', 'R16', 'R32', 'R64', 'RR', 'SF']
       D: ['RR']
       F: ['BR', 'F', 'RR', 'SF']
       G: ['F', 'QF', 'R128', 'R16', 'R32', 'R64', 'SF']
       M: ['F', 'QF', 'R128', 'R16', 'R32', 'R64', 'SF']
       O: ['BR', 'F', 'QF', 'R16', 'R32', 'R64', 'SF']

Bash(uv run python -c "
      import polars as pl
      t = pl.read_parquet('data/prep/sackmann_tourneys.parquet')
      # Look at A-level tourneys with draw_size 28 or 32 to see the names
      a32 = t.filter((pl.col('tourney_level') == 'A') & (pl.col('draw_size').is_in([28, 32])))
      print('A-level 28/32D unique names:')
      for n in sorted(a32['tourney_name'].unique().to_list()):
          print(f'  {n}')
      ")
  ⎿  A-level 28/32D unique names:
       ATP Rio de Janeiro
       Acapulco
       Adelaide
       Adelaide 1
       Adelaide 2
       Almaty
       Amersfoort
       Amsterdam
       Antalya
       Antwerp
       Astana
       Atlanta
       Auckland
       Bangkok
       Banja Luka
       Basel
       Bastad
       Beijing
       Belgrade
       Belgrade
       Belgrade 2...(truncated)

Bash(uv run python -c "
      import polars as pl
      t = pl.read_parquet('data/prep/sackmann_tourneys.parquet')
      a48 = t.filter((pl.col('tourney_level') == 'A') & (pl.col('draw_size').is_in([48, 56, 64])))
      print('A-level 48/56/64D unique names:')
      for n in sorted(a48['tourney_name'].unique().to_list()):
          print(f'  {n}')
      ")
  ⎿  A-level 48/56/64D unique names:
       Athens Olympics
       Barcelona
       Beijing Olympics
       Dubai
       Dusseldorf
       Great Ocean Road Open
       Hamburg
       Indianapolis
       Kitzbuhel
       London Olympics
       Long Island
       Memphis
       Murray River Open
       New Haven
       Nottingham
       Queen's Club
       Rio Olympics
       Stuttgart
       Sydney Olympics
       Tokyo
       Tokyo Olympics
       Washington
       Winston-Salem

Bash(uv run python3 -c "
      import polars as pl
      path = 'data/prep/sackmann_tourneys.parquet'
      df = pl.read_parquet(path)
      cols = df.columns
      n = 5
      preview = df.head(n)
      rows_list = []
      for row in preview.iter_rows():
          rows_list.append(','.join(str(v) for v in row))
      print(f'sackmann_tourneys[{n}]{{\",\".join(cols)}}:')
      for r in rows_list:
          print(f'  {r}')
      types = [str(df[c].dtype) for c in cols]
      print(f'types[{len(types)}]: {\",\".join(types)}')
      print(f'rows: {len(df)}')
      print()
      print('Has tourney_code:', 'tourney_code' in cols)
      print('Has points_break_code:', 'points_break_code' in cols)
      ")
  ⎿  sackmann_tourneys[5]{",".join(cols)}:
       2000-339,Adelaide,Hard,32,A,20000103,2000,A250_32D
       2000-451,Doha,Hard,32,A,20000103,2000,A250_32D
       2000-891,Chennai,Hard,32,A,20000103,2000,A250_32D
       2000-301,Auckland,Hard,32,A,20000110,2000,A250_32D
       2000-338,Sydney,Hard,32,A,20000110,2000,A250_32D
     types[8]: String,String,String,Int64,String,Int64,Int32,String
     rows: 3548

     Has tourney_code: True
     Has points_break_code: False

Bash(uv run python3 -c "
      import polars as pl
      df = pl.read_parquet('data/prep/kaggle_tourneys.parquet')
      print('Columns:', df.columns)
      print('Unique col2:', sorted(df[df.columns[2]].unique().to_list()))
      print()
      m = pl.read_parquet('data/prep/kaggle_matches.parquet')
      print('Unique rounds:', sorted(m['Round'].unique().to_list()))
      print()
      bp = pl.read_parquet('data/processed/atp_points_breakdown.parquet')
      print('points_break_code:', sorted(bp['points_break_code'].unique().to_list()))
      ")
  ⎿  Columns: ['kaggle_tourney_idx', 'Tournament', 'Series', 'Court', 'Surface']
     Unique col2: ['ATP250', 'ATP500', 'Grand Slam', 'International', 'International Gold', 'Masters', 'Masters 1000', 'Masters Cup']

     Unique rounds: ['1st Round', '2nd Round', '3rd Round', '4th Round', 'Quarterfinals', 'Round Robin', 'Semifinals', 'The Final']

     points_break_code: ['A250_32D_F', 'A250_32D_Q1', 'A250_32D_Q2', 'A250_32D_QF', 'A250_32D_R16', 'A250_32D_SF', 'A250_48D_F',
     'A250_48D_Q1', 'A250_48D_Q2', 'A250_48D_QF', 'A250_48D_R16', 'A250_48D_R32', 'A250_48D_SF', 'A500_32D_F', 'A500_32D_Q1',
     'A500_32D_Q2', 'A500_32D_QF', 'A500_32D_R16', 'A500_32D_SF', 'A500_48D_F', 'A500_48D_Q1', 'A500_48D_Q2', 'A500_48D_QF',
     'A500_48D_R16', 'A500_48D_R32', 'A500_48D_SF', 'AFin_F', 'AFin_RR', 'AFin_SF', 'C100_F', 'C100_Q1', 'C100_Q2', 'C100_QF',
     'C100_R16', 'C100_SF', 'C125_F', 'C125_Q1', 'C125_Q2', 'C125_QF', 'C125_R16', 'C125_SF', 'C175_F', 'C175_Q1', 'C175_Q2',
     'C175_QF', 'C175_R16', 'C175_SF', 'C50_F', 'C50_Q1', 'C50_Q2', 'C50_QF', 'C50_R16', 'C50_SF', 'C75_F', 'C75_Q1', 'C75_Q2',
     'C75_QF', 'C75_R16', 'C75_SF', 'G_F', 'G_Q1', 'G_Q2', 'G_Q3', 'G_QF', 'G_R128', 'G_R16', 'G_R32', 'G_R64', 'G_SF', 'ITF15_F',
     'ITF15_QF', 'ITF15_R16', 'ITF15_SF', 'ITF25_F', 'ITF25_QF', 'ITF25_R16', 'ITF25_SF', 'M_56D_F', 'M_56D_Q1', 'M_56D_Q2',
     'M_56D_QF', 'M_56D_R16', 'M_56D_R32', 'M_56D_R64', 'M_56D_SF', 'M_96D_F', 'M_96D_Q1', 'M_96D_Q2', 'M_96D_QF', 'M_96D_R128',
     'M_96D_R16', 'M_96D_R32', 'M_96D_R64', 'M_96D_SF']

Bash(uv run python3 -c "
      import polars as pl
      t = pl.read_parquet('data/prep/kaggle_tourneys.parquet')
      m = pl.read_parquet('data/prep/kaggle_matches.parquet')
      print('tourney join col:', 'kaggle_tourney_idx' in m.columns)
      print()
      # Check round values and how many per series
      joined = m.join(t, on='kaggle_tourney_idx', how='left')
      rounds_by_series = joined.group_by('Series','Round').len().sort('Series','Round')
      for row in rounds_by_series.iter_rows():
          print(row)
      ")
  ⎿  tourney join col: True

     ('ATP250', '1st Round', 8091)
     ('ATP250', '2nd Round', 5222)
     ('ATP250', '3rd Round', 183)
     ('ATP250', 'Quarterfinals', 2503)
     ('ATP250', 'Semifinals', 1263)
     ('ATP250', 'The Final', 639)
     ('ATP500', '1st Round', 3149)
     ('ATP500', '2nd Round', 1855)
     ('ATP500', '3rd Round', 296)
     ('ATP500', 'Quarterfinals', 765)
     ('ATP500', 'Semifinals', 387)
     ('ATP500', 'The Final', 202)
     ('Grand Slam', '1st Round', 6358)
     ('Grand Slam', '2nd Round', 3190)
     ('Grand Slam', '3rd Round', 1589)
     ('Grand Slam', '4th Round', 795)
     ('Grand Slam', 'Quarterfinals', 397)
     ('Grand Slam', 'Semifinals', 200)
     ('Grand Slam', 'The Final', 103)
     ('International', '1st Round', 5887)
     ('International', '2nd Round', 3034)
     ('International', '3rd Round', 123)
     ('International', 'Quarterfinals', 1475)
     ('International', 'Round Robin', 116)
     ('International', 'Semifinals', 742)
     ('International', 'The Final', 375)
     ('International Gold', '1st Round', 1560)
     ('International Gold', '2nd Round', 1077)
     ('International Gold', '3rd Round', 354)
     ('International Gold', 'Quarterfinals', 359)
     ('International Gold', 'Semifinals', 181)
     ('International Gold', 'The Final', 89)
     ('Masters', '1st Round', 2148)
     ('Masters', '2nd Round', 1481)
     ('Masters', '3rd Round', 744)
     ('Masters', '4th Round', 105)
     ('Masters', 'Quarterfinals', 318)
     ('Masters', 'Semifinals', 154)
     ('Masters', 'The Final', 79)
     ('Masters 1000', '1st Round', 3628)
     ('Masters 1000', '2nd Round', 2911)
     ('Masters 1000', '3rd Round', 1454)
     ('Masters 1000', '4th Round', 339)
     ('Masters 1000', 'Quarterfinals', 558)
     ('Masters 1000', 'Semifinals', 280)
     ('Masters 1000', 'The Final', 143)
     ('Masters Cup', 'Round Robin', 310)
     ('Masters Cup', 'Semifinals', 52)
     ('Masters Cup', 'The Final', 25)

Bash(uv run python3 -c "
      import polars as pl
      bp = pl.read_parquet('data/processed/atp_points_breakdown.parquet')
      # Check what round codes exist for 32D and 48D
      for prefix in ['A250_32D', 'A250_48D', 'A500_32D', 'A500_48D']:
          codes = sorted([c for c in bp['points_break_code'].to_list() if c.startswith(prefix)])
          print(f'{prefix}: {codes}')
      ")
  ⎿  A250_32D: ['A250_32D_F', 'A250_32D_Q1', 'A250_32D_Q2', 'A250_32D_QF', 'A250_32D_R16', 'A250_32D_SF']
     A250_48D: ['A250_48D_F', 'A250_48D_Q1', 'A250_48D_Q2', 'A250_48D_QF', 'A250_48D_R16', 'A250_48D_R32', 'A250_48D_SF']
     A500_32D: ['A500_32D_F', 'A500_32D_Q1', 'A500_32D_Q2', 'A500_32D_QF', 'A500_32D_R16', 'A500_32D_SF']
     A500_48D: ['A500_48D_F', 'A500_48D_Q1', 'A500_48D_Q2', 'A500_48D_QF', 'A500_48D_R16', 'A500_48D_R32', 'A500_48D_SF']

● Bash(uv run python3 -c "
      import polars as pl

      m = pl.read_parquet('data/prep/kaggle_matches.parquet')
      t = pl.read_parquet('data/prep/kaggle_tourneys.parquet')
      joined = m.join(t, on='kaggle_tourney_idx', how='left')

      # How many 1st Round matches in 32-draw and 48-draw classified tourneys?
      for code in ['A250_32D_R32', 'A500_32D_R32', 'A250_48D_R64', 'A500_48D_R64']:
          parts = code.rsplit('_', 1)
          print(f'{code}: these are 1st Round matches that produce an unmatched code')
      print()

      # The breakdown table convention: 32D events have R16 as earliest round
      # meaning 1st Round of 32-draw should map to R16, not R32
      # And for 48D events R32 is earliest, so 1st Round should map to R32
      print('Fix: For 32-draw events, 1st Round maps to R16 (not R32)')
      print('     For 48-draw events, 1st Round maps to R32 (already correct)')
      print('     For 48-draw events, but 1st Round currently maps to R64 (wrong)')
      ")
  ⎿  A250_32D_R32: these are 1st Round matches that produce an unmatched code
     A500_32D_R32: these are 1st Round matches that produce an unmatched code
     A250_48D_R64: these are 1st Round matches that produce an unmatched code
     A500_48D_R64: these are 1st Round matches that produce an unmatched code

     Fix: For 32-draw events, 1st Round maps to R16 (not R32)
          For 48-draw events, 1st Round maps to R32 (already correct)
          For 48-draw events, but 1st Round currently maps to R64 (wrong)
```

I also have feedback from the agent about the peek tool:

```text
Here's what I actually needed during the research that peek couldn't do, forcing me into raw python one-liners:

  1. Column listing without row data — peek <path> -c
  Most of my early calls just needed column names (and whether a column exists). Printing 2 preview rows wastes tokens when I only care
  about schema. A columns-only flag would be the single highest-impact addition.

  2. Unique values of a column — peek <path> -u Series
  I ran multiple scripts just to get df["Series"].unique(). This is the most common exploratory operation after "what columns exist."
  Compact output like Series[8]: ATP250,ATP500,Grand Slam,... fits TOON well.

  3. Group-by counts — peek <path> -g Series,Round
  I needed group_by("Series","Round").len() to understand the data shape. This is the second most common exploratory operation. Output as
  a compact table.

  4. Multi-file peek — peek data/prep/kaggle_*.parquet -c
  I inspected 3-4 files in sequence. Glob support with columns-only mode would collapse multiple tool calls into one.

  5. Column filter — peek <path> --cols tourney_id,tourney_code,round
  When previewing rows, I rarely need all columns. Selecting a subset keeps output narrow and token-efficient, especially for wide
  dataframes (kaggle_matches has 15 columns but I only cared about 3-4 at a time).

  These five cover ~90% of what pushed me to raw python. Everything else (joins, conditional filters, computed columns) is genuinely
  ad-hoc analysis that belongs in scripts.
```

Please analyse the work that agent has been doing, understand why. Then brainstorm with me how we could we extend and improve the peek skill. We can either extend the peek or create multiple cli tools (peek_cols, peek_unique, peek_group etc.) combined into a single SKILL.md. The main goal is to ensure the peek skill is valuable enough for the agen to use it: it needs to be simple to understand how to use, require minimum token for inputs and produce outputs with the information that will most likely be required but in minimum tokens. Consider if we could expose flexible interface for the agent (either chained polars db commands or SQL). Consider all the best ideas possible.
