Tool to automatically upgrade substrate-based Rust repos.

# Install

git clone https://github.com/tmpolaczyk/lucky-upgrade
cd lucky-upgrade
pip install -r requirements.txt

# Setup

There are a few assumptions:

* `lucky-upgrade` folder must be in the same folder as all the other repos: it must be possible to run `cd ../polkadot-sdk` from inside the `lucky-update` folder

* The user must have push permission to the moondance-labs repos

Uncomment the `setup_remote_all_repos` function in `main()` and run:

```
./lucky_upgrade.py
```

# Usage

There is no CLI yet, so just uncomment the functions you want to run in `main()` and run `./lucky_upgrade.py`.

# Linter

There is also a work in progress linter called `lucky_linter.py`, it can detect some toml mistakes such as not using `workspace = true`, but it is far from ready.
