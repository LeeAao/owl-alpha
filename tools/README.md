# tools

`owl.py` is Owl's storage. It keeps the profile, weekly plans, daily check-ins and notes as JSON files in `../data`. Standard library only, Python 3.9 or newer.

The agent calls it. A person never needs to. The command list is at the top of the file, and `python3 owl.py --help` shows the options.

Tests live in `tests/` in the repository: `python3 -m unittest discover tests`.
