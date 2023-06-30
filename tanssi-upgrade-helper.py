#!/usr/bin/env python3
import glob
import os
import tomlkit
import subprocess
from simple_term_menu import TerminalMenu

def main():
    # need manual setup: clone all repos
    #setup_remote_all_repos()
    #upgrade_substrate()
    upgrade_polkadot()
    return
    x = all_cargo_toml_files("../polkadot")
    #edit_cargo_toml("../polkadot/erasure-coding/Cargo.toml", "https://github.com/paritytech/substrate", "https://github.com/moondance-labs/substrate", "tanssi-polkadot-v0.9.43")
    for cargo_file in x:
        edit_cargo_toml(cargo_file, "https://github.com/paritytech/substrate", "https://github.com/moondance-labs/substrate", "tanssi-polkadot-v0.9.43")

def setup_remote_all_repos():
    setup_remote("../substrate", "parity", "https://github.com/paritytech/substrate")
    setup_remote("../substrate", "moondance", "git@github.com:moondance-labs/substrate.git")
    setup_remote("../polkadot", "parity", "https://github.com/paritytech/polkadot")
    setup_remote("../polkadot", "moondance", "git@github.com:moondance-labs/polkadot.git")
    setup_remote("../cumulus", "parity", "https://github.com/paritytech/cumulus")
    setup_remote("../cumulus", "moondance", "git@github.com:moondance-labs/cumulus.git")

def setup_remote(path, remote_name, remote_url):
    r = subprocess.run(["./setup_remote.sh", path, remote_name, remote_url], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = r.stdout.decode("utf-8")
    exit_code = r.returncode
    debug = True
    if debug:
        print(f"{path} setup_remote: {out}")
    assert exit_code == 0

def substrate_cherry_picks():
    return [
        "ff4688db0c59bcf3b29848a3e6bbc1750098ebf6"
    ]

def polkadot_cherry_picks():
    return [
        "27b78f58bdc35f1b0162007efabd0ffb0ed23327"
    ]

def git_fetch(path, remote_name):
    r = subprocess.run(["git", "fetch", remote_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=path)
    out = r.stdout.decode("utf-8")
    exit_code = r.returncode
    debug = True
    if debug:
        print(f"{path} git_fetch: {out}")
    assert exit_code == 0

def git_checkout(path, branch_name):
    r = subprocess.run(["git", "checkout", branch_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=path)
    out = r.stdout.decode("utf-8")
    exit_code = r.returncode
    debug = True
    if debug:
        print(f"{path} git_checkout: {out}")
    assert exit_code == 0

def git_create_branch(path, branch_name):
    while True:
        r = subprocess.run(["git", "checkout", "-b", branch_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=path)
        out = r.stdout.decode("utf-8")
        exit_code = r.returncode
        debug = True
        if debug:
            print(f"{path} git_create_branch: {out}")
        if exit_code != 0:
            print(f"Warning: {path} failed to create branch {branch_name}. Please delete the branch and press enter to continue")
            input("")
        else:
            return

def git_cherry_pick(path, commit_hash):
    r = subprocess.run(["git", "cherry-pick", commit_hash], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=path)
    out = r.stdout.decode("utf-8")
    exit_code = r.returncode
    debug = True
    if debug:
        print(f"{path} git_cherry_pick: {out}")
    if exit_code != 0:
        print(f"Warning: {path} cherry-pick failed {commit_hash}. Please resolve conflicts and press enter to continue")
        while True:
            input("")
            # Check if conflicts have been resolved
            return
    else:
        print(f"{path} succesful cherry-pick {commit_hash}")

def check_unstaged_changes(path):
    while True:
        r = subprocess.run(["git", "diff", "--exit-code"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=path)
        out = r.stdout.decode("utf-8")
        exit_code = r.returncode
        debug = True
        if debug:
            print(f"{path} check_unstaged_changes: {out}")
        if exit_code != 0:
            print(f"Warning: {path} has unstaged changes. Please commit them or use git stash to continue")
            input("Press enter to continue ")
        else:
            return

def has_unstaged_changes(path):
    r = subprocess.run(["git", "diff", "--exit-code"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=path)
    out = r.stdout.decode("utf-8")
    exit_code = r.returncode
    debug = True
    if debug:
        print(f"{path} hash_unstaged_changes: {out}")
    if exit_code != 0:
        return True
    else:
        return False

def git_push_set_upstream(path, remote_name, branch_name):
    r = subprocess.run(["git", "push", "--set-upstream", remote_name, branch_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=path)
    out = r.stdout.decode("utf-8")
    exit_code = r.returncode
    debug = True
    if debug:
        print(f"{path} git_push_set_upstream: {out}")
    assert exit_code == 0
    if exit_code != 0:
        print(f"Warning: {path} git push failed. Please commit them or use git stash to continue")
        input("Press enter to continue ")
    else:
        return

def git_commit(path, message):
    r = subprocess.run(["git", "commit", "-am", message], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=path)
    out = r.stdout.decode("utf-8")
    exit_code = r.returncode
    debug = True
    if debug:
        print(f"{path} git_commit: {out}")
    assert exit_code == 0

def git_commit_amend(path):
    r = subprocess.run(["git", "commit", "-a", "--amend", "--no-edit"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=path)
    out = r.stdout.decode("utf-8")
    exit_code = r.returncode
    debug = True
    if debug:
        print(f"{path} git_commit_amend: {out}")
    assert exit_code == 0

def upgrade_substrate():
    check_unstaged_changes("../substrate")
    git_fetch("../substrate", "parity")
    git_fetch("../substrate", "moondance")
    git_checkout("../substrate", "parity/polkadot-v0.9.43")
    git_create_branch("../substrate", "tanssi-polkadot-v0.9.43")
    # apply cherry-picks
    for c in substrate_cherry_picks():
        git_cherry_pick("../substrate", c)
    git_push_set_upstream("../substrate", "moondance", "tanssi-polkadot-v0.9.43")

def upgrade_polkadot():
    check_unstaged_changes("../polkadot")
    git_fetch("../polkadot", "parity")
    git_fetch("../polkadot", "moondance")
    git_checkout("../polkadot", "parity/release-v0.9.43")
    git_create_branch("../polkadot", "tanssi-polkadot-v0.9.43")
    # update deps to use forked repo
    def forked_deps():
        use_forked_deps("../polkadot", "https://github.com/paritytech/substrate", "https://github.com/moondance-labs/substrate", "tanssi-polkadot-v0.9.43")
    forked_deps()
    if has_unstaged_changes("../polkadot"):
        git_commit("../polkadot", "Use tanssi substrate fork")
    # apply cherry-picks
    for c in polkadot_cherry_picks():
        git_cherry_pick("../polkadot", c)
        forked_deps()
        git_commit_amend("../polkadot")
    git_push_set_upstream("../polkadot", "moondance", "tanssi-polkadot-v0.9.43")

def use_forked_deps(path, upstream_url, fork_url, fork_branch):
    x = all_cargo_toml_files(path)
    for cargo_file in x:
        edit_cargo_toml(cargo_file, upstream_url, fork_url, fork_branch)

def all_cargo_toml_files(path):
    files = glob.glob(path + "/**/Cargo.toml", recursive=True)
    def not_excluded(file_path):
        # Exclude target/ folder
        if file_path.startswith(path + "/target/"):
            return False
        else:
            return True
    files = [x for x in files if not_excluded(x)]
    return files

def edit_cargo_toml(cargo_toml_file_path, upstream_url, fork_url, fork_branch):
    cargo_file = cargo_toml_file_path
    with open(cargo_file, "r") as file:
        # Parse the contents of the file using tomlkit
        cargo_contents = tomlkit.parse(file.read())

    # Update the dependency section
    for dep_key_name in ["dependencies", "dev-dependencies", "build-dependencies"]:
        dependencies = cargo_contents.get(dep_key_name)
        if dependencies:
            for dependency_name, dependency_value in dependencies.items():
                if (
                    isinstance(dependency_value, dict)
                    and "git" in dependency_value
                    and dependency_value["git"] == upstream_url
                ):
                    dependency_value["git"] = fork_url
                    if fork_branch is not None:
                        dependency_value["branch"] = fork_branch

    # Write the modified contents back to the file
    with open(cargo_file, "w") as file:
        file.write(tomlkit.dumps(cargo_contents))

if __name__ == "__main__":
    main()
