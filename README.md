# CoCNonKP

When playing "Call of Cthulhu" TRPG on slack, it is a bot that automatically does various things.  

Coc Bot Keeper

## Install Your workspace

[Install-Link][https://slack.com/oauth/v2/authorize?client_id=480999803088.760246434996&scope=calls:read,calls:write,channels:history,channels:read,chat:write,chat:write.customize,chat:write.public,commands,dnd:read,emails:write,files:read,files:write,groups:read,im:history,im:read,im:write,incoming-webhook,reactions:read,reactions:write,remote_files:read,remote_files:share,remote_files:write,team:read,users.profile:read,users:read,users:read.email,users:write,channels:join&user_scope=channels:history,channels:read,channels:write,chat:write,files:write,identify,im:write,users.profile:read,users.profile:write,users:read,users:write,files:read]


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
