# Installing Owl: instructions for an AI agent

A person sent you here. They want Owl installed in the folder your session is open in, and they want it started right away. Do these three things.

## 1. Run one command from that folder

```bash
curl -fsSL https://raw.githubusercontent.com/LeeAao/owl-alpha/main/install.sh | bash -s -- --target "$PWD"
```

It puts everything into that one folder. It installs no packages and changes nothing else on the computer. If a notes file named `intake*.md` is in the folder, it moves it to `data/intake.md` for Owl to read.

Do not clone the repository. Do not install Python or a package manager. Do not run tests or rehearsals. Do not download anything else.

## 2. If it stops with a message

Tell the person what it said, in plain words, and stop. Don't try to work around it.

The usual cases: the session is open in the home folder or in a folder with other work (ask them to make a new empty folder and open the session there), or Python is missing (the message says what to do).

## 3. If it succeeds, become Owl in the same reply

The folder is now Owl. Read `.claude/skills/owl/SKILL.md` in it and follow it from its first step, in this same conversation and this same turn.

The person asked for Owl to start, so the next thing they see should be Owl's hello. Don't write an installation report, don't list the files, and don't ask whether to start.

## If you already cloned the repository

That works too. Run the clone's installer with the session folder as the target:

```bash
bash path/to/clone/install.sh --target "path/to/session/folder"
```

Leave the clone where it is. It is harmless, and the person can delete that folder whenever they like. Don't ask them to delete it now and don't mention commands for it. Then continue with step 3.
