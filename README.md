# Owl (alpha)

Owl is a personal coach that runs inside Claude or Codex. Once a week you agree a realistic plan with it. Each evening you answer a few short questions about how the day went. It compares the plan, your energy and what actually happened, and tells you one thing worth changing.

This is an early alpha. Expect rough edges.

## Install

You need a Mac or Linux machine, and Claude (desktop app or Claude Code) or Codex.

```bash
curl -fsSL https://raw.githubusercontent.com/LeeAao/owl-alpha/main/install.sh | bash
```

That's the whole install. It creates one folder, `~/Owl`, and puts everything there. It installs no packages and changes nothing else on your computer.

Then open the folder `~/Owl` in Claude (Code tab, local session) or in Codex and say hi.

## Update

Run the install command again. It replaces Owl's own files and never touches `~/Owl/data`, where your goals and check-ins live.

## Remove

```bash
curl -fsSL https://raw.githubusercontent.com/LeeAao/owl-alpha/main/install.sh | bash -s -- uninstall
```

This removes Owl but keeps `~/Owl/data`. Add `--delete-data` at the end to remove your data too. Deleting the `~/Owl` folder by hand does the same thing.

## What's in the folder

```
~/Owl/
├── CLAUDE.md, AGENTS.md     tell the agent this folder is Owl
├── .claude/skills/owl/      Owl's method, for Claude
├── .agents/skills/owl/      the same, for Codex
├── tools/                   a small Python script that stores your data
└── data/                    your goals, plans and check-ins. Stays on your computer.
```

Owl needs Python 3.9 or newer. Macs with Apple's command line tools already have it. If it's missing, the installer says so and stops without changing anything.

## Note for AI agents

If a person asks you to install Owl, run the one-line install command above and show them its output. Do not clone this repository and set it up by hand, do not install Python or any package manager, and do not run tests or rehearsals. If the installer stops with a message, show the person that message and stop.

## Privacy

Everything you tell Owl is stored in `~/Owl/data` on your computer. Owl sends nothing anywhere. Your conversations go through Claude or Codex like any other chat with them.
