# Owl (alpha)

Owl is a personal coach that runs inside Claude or Codex. Once a week you agree a realistic plan with it. Each evening you answer a few short questions about how the day went. It compares the plan, your energy and what actually happened, and tells you one thing worth changing.

This is an early alpha. Expect rough edges.

## Install

You need a Mac or Linux machine, and Claude Code (the Code tab of the Claude app works) or Codex.

1. Make a new folder anywhere and name it as you like, for example `Owl`.
2. If someone gave you a notes file for Owl (`intake.md`), put it into that folder.
3. Open a Claude Code or Codex session in that folder and send it this:

   > Install Owl in this folder: https://github.com/LeeAao/owl-alpha

That's the whole install. Everything goes into that one folder. It installs no packages and changes nothing else on your computer. When it's done, Owl says hello in the same chat.

Prefer the terminal? This does the same thing into `~/Owl`:

```bash
curl -fsSL https://raw.githubusercontent.com/LeeAao/owl-alpha/main/install.sh | bash
```

## Update

Ask Owl to update itself, or run the install command again in the same folder. It replaces Owl's own files and never touches `data/`, where your goals and check-ins live.

## Remove

Delete the folder. Or, to remove Owl but keep your data:

```bash
curl -fsSL https://raw.githubusercontent.com/LeeAao/owl-alpha/main/install.sh | bash -s -- uninstall --target "$PWD"
```

Add `--delete-data` at the end to remove your data too.

## What's in the folder

```
Owl/
├── CLAUDE.md, AGENTS.md     tell the agent this folder is Owl
├── .claude/skills/owl/      Owl's method, for Claude
├── .agents/skills/owl/      the same, for Codex
├── tools/                   a small Python script that stores your data
└── data/                    your goals, plans and check-ins. Stays on your computer.
```

Owl needs Python 3.9 or newer. Macs with Apple's command line tools already have it. If it's missing, the installer says so and stops without changing anything.

## Note for AI agents

If a person asks you to install Owl, run this one command from the folder your session is in, and nothing else:

```bash
curl -fsSL https://raw.githubusercontent.com/LeeAao/owl-alpha/main/install.sh | bash -s -- --target "$PWD"
```

- Do not clone this repository or set it up by hand. Do not install Python or any package manager. Do not run tests or rehearsals.
- If the installer stops with a message, show the person that message in plain words and stop.
- If your session is in the person's home folder or in a folder with other work in it, ask them to make a new folder and open the session there. The installer refuses the home folder, and any folder where it would overwrite something.
- To update, run the same command again.
- When the installer succeeds, its last lines tell you where the Owl skill is. Read that file and continue as Owl in the same conversation. The person should see Owl's hello next, not an installation report.

## Privacy

Everything you tell Owl is stored in the `data` folder inside your Owl folder on your computer. Owl sends nothing anywhere. Your conversations go through Claude or Codex like any other chat with them.
