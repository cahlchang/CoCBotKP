# CoCNonKP

When playing "Call of Cthulhu" TRPG on slack, it is a bot that automatically does various things.  

Coc Non user Keeper

## development environment

1. create virtual env of Python
    - `python -m venv v-env`
2. activate venv
    - `source v-env/bin/activate`
3. install dependency libraries
    - `pip install -r requirements.txt -r test-requirements.txt`
4. deactivate venv (if you want to exit venv)
    - `deactivate`

## run test

- run `python -m pytest ./` on virtual env.

## deploy

- When commits are merged to master, lambda code is deployed by GitHub Actions automatically.

## Command Reference

- [Wiki](https://github.com/cahlchang/CoCNonKP/wiki/Command-Reference)
- [Doc(JP)](./command_reference.md)
