#!/usr/bin/env python3
import glob
import os
import tomlkit
import subprocess
import fileinput
import re
from simple_term_menu import TerminalMenu

# Cool command to see all github dependencies in Cargo.lock
# rg "source = \"git\+" Cargo.lock | sort -u

def main():
    # need manual setup: clone all repos
    #setup_remote_all_repos()
    #upgrade_substrate()
    #upgrade_polkadot()
    #upgrade_cumulus()
    #upgrade_frontier()
    # nimbus not needed, replaced by moonkit
    #upgrade_nimbus()
    upgrade_moonkit()
    #update_tanssi_cargo_lock("../tanssi/Cargo.lock")
    # Use moonkit instead of nimbus
    #use_forked_deps("../tanssi", "https://github.com/moondance-labs/nimbus", "https://github.com/moondance-labs/moonkit", "tanssi-polkadot-v0.9.43")
    return

def setup_remote_all_repos():
    setup_remote("../substrate", "parity", "https://github.com/paritytech/substrate")
    setup_remote("../substrate", "moondance", "git@github.com:moondance-labs/substrate.git")
    setup_remote("../polkadot", "parity", "https://github.com/paritytech/polkadot")
    setup_remote("../polkadot", "moondance", "git@github.com:moondance-labs/polkadot.git")
    setup_remote("../cumulus", "parity", "https://github.com/paritytech/cumulus")
    setup_remote("../cumulus", "moondance", "git@github.com:moondance-labs/cumulus.git")
    setup_remote("../frontier", "parity", "https://github.com/paritytech/frontier")
    setup_remote("../frontier", "moondance", "git@github.com:moondance-labs/frontier.git")
    setup_remote("../nimbus", "purestake", "https://github.com/PureStake/nimbus")
    setup_remote("../nimbus", "moondance", "git@github.com:moondance-labs/nimbus.git")
    setup_remote("../moonkit", "moonsong", "https://github.com/Moonsong-Labs/moonkit")
    setup_remote("../moonkit", "moondance", "git@github.com:moondance-labs/moonkit.git")

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
        #"ff4688db0c59bcf3b29848a3e6bbc1750098ebf6"
        "9202622403b4ecb4949ba48a3f8ba117d2f3b9bd"
    ]

def polkadot_cherry_picks():
    return [
        "27b78f58bdc35f1b0162007efabd0ffb0ed23327"
    ]

def cumulus_cherry_picks():
    # Copied from
    # git log --pretty=oneline
    raw_git_log = """
b07401a7018fc3c267dae0ea4098b2e3645de762 (HEAD -> tanssi-polkadot-v0.9.43, moondance/tanssi-polkadot-v0.9.43, polkadot-v0.9.43) Add set_current_relay_chain_state method for benchmarks
9938b4428a4e96ead68e8c5b1ca5da3bfa14f572 Send Reinitialize instead of Initialize
    """
    commits = []
    for line in raw_git_log.split("\n"):
        if len(line.strip()) == 0 or line.strip()[0] == "#":
            continue
        commits.append(line.strip().split(" ")[0])
    commits.reverse()
    return commits

def frontier_cherry_picks():
    return []

def nimbus_cherry_picks():
    return []

def moonkit_cherry_picks():
    return []

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
            print(f"Warning: {path} failed to create branch {branch_name}. Select how to proceed")
            options = ["Retry", "Delete branch", "Rename branch", "Use that branch (bad idea)", "Abort"]
            terminal_menu = TerminalMenu(options)
            menu_entry_index = terminal_menu.show()
            if menu_entry_index == 0:
                # Retry
                continue
            elif menu_entry_index == 1:
                # Delete branch
                r = subprocess.run(["git", "branch", "-D", branch_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=path)
                out = r.stdout.decode("utf-8")
                exit_code = r.returncode
                debug = True
                if debug:
                    print(f"{path} git_create_branch delete: {out}")
            elif menu_entry_index == 2:
                # Rename branch
                new_branch_name = input("Enter new branch name: ")
                r = subprocess.run(["git", "branch", "-m", branch_name, new_branch_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=path)
                out = r.stdout.decode("utf-8")
                exit_code = r.returncode
                debug = True
                if debug:
                    print(f"{path} git_create_branch rename: {out}")
                assert exit_code == 0
                return
            elif menu_entry_index == 3:
                # Use that branch
                input("Warning: this assumes that the branch is rebased on top of a compatible upstream branch. If there are any different commits, this tool may break unexpectedly. Press enter to accept the risk and continue")
                r = subprocess.run(["git", "checkout", branch_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=path)
                out = r.stdout.decode("utf-8")
                exit_code = r.returncode
                debug = True
                if debug:
                    print(f"{path} git_create_branch use: {out}")
                assert exit_code == 0
                return
            else:
                raise Exception(f"Failed to create branch {branch_name} in {path}")

        else:
            return

def git_cherry_pick(path, commit_hash):
    r = subprocess.run(["git", "cherry-pick", commit_hash], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=path)
    out = r.stdout.decode("utf-8")
    exit_code = r.returncode
    debug = True
    if debug:
        print(f"{path} git_cherry_pick: {out}")
    while exit_code != 0:
        print(f"Warning: {path} cherry-pick failed {commit_hash}. Please resolve any possible conflicts and select an option to continue")
        options = ["git cherry-pick --continue", "git cherry-pick --skip", "Already solved, start next cherry-pick", "Abort"]
        terminal_menu = TerminalMenu(options)
        menu_entry_index = terminal_menu.show()
        if menu_entry_index == 0:
            r = subprocess.run(["git", "cherry-pick", "--continue"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=path)
            out = r.stdout.decode("utf-8")
            exit_code = r.returncode
            debug = True
            if debug:
                print(f"{path} git_cherry_pick continue: {out}")
        elif menu_entry_index == 1:
            r = subprocess.run(["git", "cherry-pick", "--skip"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=path)
            out = r.stdout.decode("utf-8")
            exit_code = r.returncode
            debug = True
            if debug:
                print(f"{path} git_cherry_pick skip: {out}")
        elif menu_entry_index == 2:
            return
        else:
            raise Exception(f"Failed to cherry-pick {commit_hash} in {path}")

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
        print(f"{path} has_unstaged_changes: {out}")
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
    while exit_code != 0:
        print(f"Warning: {path} git push failed. Select how to fix that")
        options = ["Retry", "git push -f", "Abort"]
        terminal_menu = TerminalMenu(options)
        menu_entry_index = terminal_menu.show()
        if menu_entry_index == 0:
            # Retry
            r = subprocess.run(["git", "push", "--set-upstream", remote_name, branch_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=path)
            out = r.stdout.decode("utf-8")
            exit_code = r.returncode
            debug = True
            if debug:
                print(f"{path} git_push_set_upstream: {out}")
        elif menu_entry_index == 1:
            # git push -f
            r = subprocess.run(["git", "push", "-f", "--set-upstream", remote_name, branch_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=path)
            out = r.stdout.decode("utf-8")
            exit_code = r.returncode
            debug = True
            if debug:
                print(f"{path} git_push_set_upstream -f: {out}")
        else:
            raise Exception(f"Failed to push branch {branch_name} to {remote_name}")

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

def git_fetch_pr(path, remote_name, pr_id, branch_name=None):
    if branch_name is None:
        branch_name = f"{remote_name}-pr-{pr_id}"
    print(branch_name)
    # git fetch origin pull/148/head:pr-148
    r = subprocess.run(["git", "fetch", remote_name, f"pull/{pr_id}/head:{branch_name}"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=path)
    out = r.stdout.decode("utf-8")
    exit_code = r.returncode
    debug = True
    if debug:
        print(f"{path} git_fetch_pr: {out}")
    assert exit_code == 0
    return branch_name

def git_branch_commit_hash(path, branch_name):
    # git rev-parse tanssi-polkadot-v0.9.43
    r = subprocess.run(["git", "rev-parse", branch_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=path)
    out = r.stdout.decode("utf-8")
    exit_code = r.returncode
    debug = True
    if debug:
        print(f"{path} git_fetch_pr: {out}")
    assert exit_code == 0
    return out.strip()

def upgrade_substrate():
    check_unstaged_changes("../substrate")
    git_fetch("../substrate", "parity")
    git_fetch("../substrate", "moondance")
    git_checkout("../substrate", "parity/polkadot-v1.0.0")
    git_create_branch("../substrate", "tanssi-polkadot-v1.0.0")
    # apply cherry-picks
    for c in substrate_cherry_picks():
        git_cherry_pick("../substrate", c)
    git_push_set_upstream("../substrate", "moondance", "tanssi-polkadot-v1.0.0")

def upgrade_polkadot():
    check_unstaged_changes("../polkadot")
    git_fetch("../polkadot", "parity")
    git_fetch("../polkadot", "moondance")
    git_checkout("../polkadot", "parity/release-v1.0.0")
    git_create_branch("../polkadot", "tanssi-polkadot-v1.0.0")
    # update deps to use forked repo
    def forked_deps():
        use_forked_deps("../polkadot", "https://github.com/paritytech/substrate", "https://github.com/moondance-labs/substrate", "tanssi-polkadot-v1.0.0")
    forked_deps()
    if has_unstaged_changes("../polkadot"):
        git_commit("../polkadot", "Use tanssi substrate fork")
    # apply cherry-picks
    for c in polkadot_cherry_picks():
        git_cherry_pick("../polkadot", c)
        forked_deps()
        if has_unstaged_changes("../polkadot"):
            git_commit_amend("../polkadot")
    git_push_set_upstream("../polkadot", "moondance", "tanssi-polkadot-v1.0.0")

def upgrade_cumulus():
    check_unstaged_changes("../cumulus")
    git_fetch("../cumulus", "parity")
    git_fetch("../cumulus", "moondance")
    git_checkout("../cumulus", "parity/polkadot-v1.0.0")
    git_create_branch("../cumulus", "tanssi-polkadot-v1.0.0")
    # update deps to use forked repo
    def forked_deps():
        use_forked_deps("../cumulus", "https://github.com/paritytech/substrate", "https://github.com/moondance-labs/substrate", "tanssi-polkadot-v1.0.0")
        use_forked_deps("../cumulus", "https://github.com/paritytech/polkadot", "https://github.com/moondance-labs/polkadot", "tanssi-polkadot-v1.0.0")
    forked_deps()
    if has_unstaged_changes("../cumulus"):
        git_commit("../cumulus", "Use tanssi substrate fork")
    # apply cherry-picks
    for c in cumulus_cherry_picks():
        git_cherry_pick("../cumulus", c)
        forked_deps()
        if has_unstaged_changes("../cumulus"):
            git_commit_amend("../cumulus")
    git_push_set_upstream("../cumulus", "moondance", "tanssi-polkadot-v1.0.0")

def upgrade_frontier():
    check_unstaged_changes("../frontier")
    git_fetch("../frontier", "parity")
    git_fetch("../frontier", "moondance")
    # frontier PR not merged yet, but we can start from that branch
    #upstream_branch_name = git_fetch_pr("../frontier", "parity", 1078)
    #git_checkout("../frontier", upstream_branch_name)
    git_checkout("../frontier", "parity/polkadot-v1.0.0")
    git_create_branch("../frontier", "tanssi-polkadot-v1.0.0")
    # update deps to use forked repo
    def forked_deps():
        use_forked_deps("../frontier", "https://github.com/paritytech/substrate", "https://github.com/moondance-labs/substrate", "tanssi-polkadot-v1.0.0")
    forked_deps()
    if has_unstaged_changes("../frontier"):
        git_commit("../frontier", "Use tanssi substrate fork")
    # apply cherry-picks
    for c in frontier_cherry_picks():
        git_cherry_pick("../frontier", c)
        forked_deps()
        if has_unstaged_changes("../frontier"):
            git_commit_amend("../frontier")
    git_push_set_upstream("../frontier", "moondance", "tanssi-polkadot-v1.0.0")

def upgrade_nimbus():
    tanssi_branch_name = "tanssi-polkadot-v1.0.0"
    check_unstaged_changes("../nimbus")
    git_fetch("../nimbus", "purestake")
    git_fetch("../nimbus", "moondance")
    # starting from upstream/main
    git_checkout("../nimbus", "1168c153f3113c7f32750c37c367675abaad62ec")
    git_create_branch("../nimbus", tanssi_branch_name)
    # update deps to use forked repo
    def forked_deps():
        use_forked_deps("../nimbus", "https://github.com/paritytech/substrate", "https://github.com/moondance-labs/substrate", tanssi_branch_name)
        use_forked_deps("../nimbus", "https://github.com/paritytech/polkadot", "https://github.com/moondance-labs/polkadot", tanssi_branch_name)
        use_forked_deps("../nimbus", "https://github.com/paritytech/cumulus", "https://github.com/moondance-labs/cumulus", tanssi_branch_name)
    forked_deps()
    if has_unstaged_changes("../nimbus"):
        git_commit("../nimbus", "Use tanssi substrate fork")
    # apply cherry-picks
    for c in nimbus_cherry_picks():
        git_cherry_pick("../nimbus", c)
        forked_deps()
        if has_unstaged_changes("../nimbus"):
            git_commit_amend("../nimbus")
    git_push_set_upstream("../nimbus", "moondance", tanssi_branch_name)

def upgrade_moonkit():
    tanssi_branch_name = "tanssi-polkadot-v1.0.0"
    check_unstaged_changes("../moonkit")
    git_fetch("../moonkit", "moonsong")
    git_fetch("../moonkit", "moondance")
    # starting from upstream/main
    git_checkout("../moonkit", "moonsong/moonbeam-polkadot-v1.0.0")
    git_create_branch("../moonkit", "tanssi-polkadot-v1.0.0")
    # update deps to use forked repo
    def forked_deps():
        use_forked_deps("../moonkit", "https://github.com/paritytech/substrate", "https://github.com/moondance-labs/substrate", tanssi_branch_name)
        use_forked_deps("../moonkit", "https://github.com/paritytech/polkadot", "https://github.com/moondance-labs/polkadot", tanssi_branch_name)
        use_forked_deps("../moonkit", "https://github.com/paritytech/cumulus", "https://github.com/moondance-labs/cumulus", tanssi_branch_name)
        use_forked_deps("../moonkit", "https://github.com/moonbeam-foundation/substrate", "https://github.com/moondance-labs/substrate", tanssi_branch_name)
        use_forked_deps("../moonkit", "https://github.com/moonbeam-foundation/polkadot", "https://github.com/moondance-labs/polkadot", tanssi_branch_name)
        use_forked_deps("../moonkit", "https://github.com/moonbeam-foundation/cumulus", "https://github.com/moondance-labs/cumulus", tanssi_branch_name)
    forked_deps()
    if has_unstaged_changes("../moonkit"):
        git_commit("../moonkit", "Use tanssi substrate fork")
    # apply cherry-picks
    for c in moonkit_cherry_picks():
        git_cherry_pick("../moonkit", c)
        forked_deps()
        if has_unstaged_changes("../moonkit"):
            git_commit_amend("../moonkit")
    git_push_set_upstream("../moonkit", "moondance", tanssi_branch_name)

def search_and_replace_cargo_lock(path, url, new_commit_hash):
    escaped_url = re.escape(url)
    pattern = rf'source = "git\+{escaped_url}#(\w+)"'
    replacement = f'source = "git+{url}#{new_commit_hash}"'
    print(pattern)
    print(replacement)
    num = 0

    with fileinput.FileInput(path, inplace = True) as f:
        for line in f:
            replaced_line, count = re.subn(pattern, replacement, line)
            num += count
            print(replaced_line, end='')

    print(f"Replaced {num} lines for {url}")
    return num

def update_tanssi_cargo_lock(path):
    """
    url = "https://github.com/moondance-labs/substrate?branch=tanssi-polkadot-v0.9.43"
    new_commit_hash = git_branch_commit_hash("../substrate", "tanssi-polkadot-v0.9.43")
    num = search_and_replace_cargo_lock(path, url, new_commit_hash)

    url = "https://github.com/moondance-labs/polkadot?branch=tanssi-polkadot-v0.9.43"
    new_commit_hash = git_branch_commit_hash("../polkadot", "tanssi-polkadot-v0.9.43")
    num = search_and_replace_cargo_lock(path, url, new_commit_hash)

    url = "https://github.com/moondance-labs/cumulus?branch=tanssi-polkadot-v0.9.43"
    new_commit_hash = git_branch_commit_hash("../cumulus", "tanssi-polkadot-v0.9.43")
    num = search_and_replace_cargo_lock(path, url, new_commit_hash)

    url = "https://github.com/moondance-labs/frontier?branch=tanssi-polkadot-v0.9.43"
    new_commit_hash = git_branch_commit_hash("../frontier", "tanssi-polkadot-v0.9.43")
    num = search_and_replace_cargo_lock(path, url, new_commit_hash)

    url = "https://github.com/moondance-labs/nimbus?branch=tanssi-polkadot-v0.9.43"
    new_commit_hash = git_branch_commit_hash("../nimbus", "tanssi-polkadot-v0.9.43")
    num = search_and_replace_cargo_lock(path, url, new_commit_hash)
    """
    #url = "https://github.com/moondance-labs/moonkit?branch=tanssi-polkadot-v0.9.43"
    #new_commit_hash = git_branch_commit_hash("../moonkit", "tanssi-polkadot-v0.9.43")
    url = "https://github.com/moondance-labs/moonkit?branch=tomasz-pallet-migrations-cleanup-tanssi"
    new_commit_hash = git_branch_commit_hash("../moonkit", "tomasz-pallet-migrations-cleanup-tanssi")
    num = search_and_replace_cargo_lock(path, url, new_commit_hash)


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
    for dep_key_name in ["dependencies", "dev-dependencies", "build-dependencies", "workspace.dependencies"]:
        if dep_key_name.startswith("workspace."):
            dependencies = cargo_contents.get("workspace")
        else:
            dependencies = cargo_contents.get(dep_key_name)
        if dependencies and dep_key_name.startswith("workspace."):
            print("get ", dep_key_name[10:])
            dependencies = dependencies.get(dep_key_name[10:])
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
