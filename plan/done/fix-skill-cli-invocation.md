# Fix Invocation

## Issue 1

Agent triend to run peek with

```text
Bash(python -m peek data/prep/kaggle_players.parquet -c)
```

Need to make it clear for the coding agent that skill tools can be invoked directly without python like `peek data/prep/kaggle_players.parquet -c`

## Issue 2

I have just installed a skill with `just i` but having:

```bash
srg@srg-kub2510-b15a11m:~$ suggest test-skill "blah blah"
bash: /home/srg/.nvm/versions/node/v24.11.1/bin/suggest: Permission denied
```
