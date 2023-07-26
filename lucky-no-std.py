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
    #upgrade_nimbus()
    #update_tanssi_cargo_lock("../tanssi/Cargo.lock")
    #ensure_default_features_false("../moonbeam")
    #ensure_default_features_false_at_root("../moonkit")
    #ensure_default_features_false_at_root("../tanssi")
    #ensure_valid_paths_at_root("../tanssi")
    #ensure_all_child_cargo_tomls_use_workspace_deps("../tanssi")
    #ensure_no_default_features_in_child_cargo_tomls("../tanssi")
    ensure_all_crates_with_std_feature_have_a_no_std_attr("../moonkit")
    #list_all_unique_git_deps("../moonkit")
    return

def ensure_all_crates_with_std_feature_have_a_no_std_attr(project_path):
    x = all_cargo_toml_files(project_path)
    for cargo_file in x:
        if toml_has_std_feature(cargo_file):
            # Ensure that src/lib.rs contains a no_std attr
            lib_rs_path = convert_to_lib_rs(cargo_file)
            if not src_lib_rs_has_no_std_attr(lib_rs_path):
                print("missing #![no_std] in", lib_rs_path)
                raise Exception("missing #![no_std] in", lib_rs_path)

def src_lib_rs_has_no_std_attr(lib_rs_path):
    line_to_check = '#![cfg_attr(not(feature = "std"), no_std)]'
    return find_line_in_file(lib_rs_path, line_to_check)

# Thanks ChatGPT
def find_line_in_file(file_path, line_to_check):
    with open(file_path, "r") as file:
        for line in file:
            if line.strip() == line_to_check:
                return True
    return False

# Thanks ChatGPT
def convert_to_lib_rs(input_string):
    if input_string.endswith("/Cargo.toml"):
        # Replace the last occurrence of '/Cargo.toml' with '/src/lib.rs'
        output_string = input_string.rsplit('/Cargo.toml', 1)[0] + '/src/lib.rs'
        return output_string
    else:
        raise ValueError(f"Input path is not a Cargo.toml file: {input_string}")

def toml_has_std_feature(cargo_file):
    # TODO: false positives
    # In case of workspace dependencies, we also need to find which crate uses them
    # Because if it is only used in dev-dependencies, it shouldn't matter (tests enable std feature)
    with open(cargo_file, "r") as file:
        # Parse the contents of the file using tomlkit
        cargo_contents = tomlkit.parse(file.read())

    # Update the dependency section
    features = cargo_contents.get("features")
    if isinstance(features, dict) and "std" in features:
        return True
    else:
        return False

def list_all_unique_git_deps(project_path):
    print(get_git_deps_from_cargo_toml(project_path + "/Cargo.toml"))

def get_git_deps_from_cargo_toml(cargo_toml_file_path):
    cargo_file = cargo_toml_file_path
    with open(cargo_file, "r") as file:
        # Parse the contents of the file using tomlkit
        cargo_contents = tomlkit.parse(file.read())

    deps = set()
    for dep_key_name in ["dependencies", "dev-dependencies", "build-dependencies", "workspace.dependencies"]:
        if dep_key_name.startswith("workspace."):
            dependencies = cargo_contents.get("workspace")
        else:
            dependencies = cargo_contents.get(dep_key_name)
        if dependencies and dep_key_name.startswith("workspace."):
            dependencies = dependencies.get(dep_key_name[10:])
        if dependencies:
            for dependency_name, dependency_value in dependencies.items():
                if (
                    isinstance(dependency_value, dict) and "git" in dependency_value
                ):
                    deps.add(dependency_value["git"])
                # TODO: what if is not dict

    return deps

def ensure_valid_paths_at_root(project_path):
    cargo_file = project_path + "/" + "Cargo.toml"
    edit_cargo_toml5(project_path, cargo_file)

def ensure_all_child_cargo_tomls_use_workspace_deps(project_path):
    x = all_cargo_toml_files(project_path)
    # exclude root Cargo.toml
    x.remove(project_path + "/" + "Cargo.toml")
    for cargo_file in x:
        edit_cargo_toml4(project_path, cargo_file)

def ensure_no_default_features_in_child_cargo_tomls(project_path):
    x = all_cargo_toml_files(project_path)
    # exclude root Cargo.toml
    x.remove(project_path + "/" + "Cargo.toml")
    for cargo_file in x:
        edit_cargo_toml3(project_path, cargo_file)

def ensure_default_features_false_at_root(project_path):
    cargo_file = project_path + "/" + "Cargo.toml"
    edit_cargo_toml2(project_path, cargo_file)

def ensure_default_features_false(project_path):
    x = all_cargo_toml_files(project_path)
    for cargo_file in x:
        edit_cargo_toml(cargo_file)

def all_cargo_toml_files(path):
    files = glob.glob(path + "/**/Cargo.toml", recursive=True)
    def not_excluded(file_path):
        # Exclude target/ folder
        if file_path.startswith(path + "/target/"):
            return False
        elif file_path.startswith(path + "/test/node_modules/"):
            return False
        else:
            return True
    files = [x for x in files if not_excluded(x)]
    return files

def has_std_feature(path, dependency_name):
    while True:
        r = subprocess.run(["cargo", "feature", dependency_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=path)
        out = r.stdout.decode("utf-8")
        exit_code = r.returncode
        debug = True
        if debug:
            print(f"{path} has_std_feature: {out}")
        if exit_code != 0:
            assert False

        if "\"std\"" in out:
            print(f"{dependency_name}: has std")
            return True
        else:
            print(f"{dependency_name}: does not have std")
            return False

def edit_cargo_toml5(path, cargo_toml_file_path):
    # TODO: false positives
    # In case of workspace dependencies, we also need to find which crate uses them
    # Because if it is only used in dev-dependencies, it shouldn't matter (tests enable std feature)
    cargo_file = cargo_toml_file_path
    with open(cargo_file, "r") as file:
        # Parse the contents of the file using tomlkit
        cargo_contents = tomlkit.parse(file.read())

    # Update the dependency section
    for dep_key_name in ["workspace.dependencies"]:
        if dep_key_name.startswith("workspace."):
            dependencies = cargo_contents.get("workspace")
        else:
            dependencies = cargo_contents.get(dep_key_name)
        if dependencies and dep_key_name.startswith("workspace."):
            dependencies = dependencies.get(dep_key_name[10:])
        if dependencies:
            for dependency_name, dependency_value in dependencies.items():
                if (
                    isinstance(dependency_value, dict)
                    and "path" in dependency_value
                ):
                    if not os.path.exists(path + "/" + dependency_value["path"]):
                        raise Exception(f"{cargo_file} has invalid dependency {dependency_name} (path does not exist)")
                # TODO: what if is not dict

    # Write the modified contents back to the file
    with open(cargo_file, "w") as file:
        file.write(tomlkit.dumps(cargo_contents))

def edit_cargo_toml4(path, cargo_toml_file_path):
    # TODO: false positives
    # In case of workspace dependencies, we also need to find which crate uses them
    # Because if it is only used in dev-dependencies, it shouldn't matter (tests enable std feature)
    cargo_file = cargo_toml_file_path
    with open(cargo_file, "r") as file:
        # Parse the contents of the file using tomlkit
        cargo_contents = tomlkit.parse(file.read())

    # Update the dependency section
    for dep_key_name in ["dependencies", "dev-dependencies", "build-dependencies"]:
        if dep_key_name.startswith("workspace."):
            dependencies = cargo_contents.get("workspace")
        else:
            dependencies = cargo_contents.get(dep_key_name)
        if dependencies and dep_key_name.startswith("workspace."):
            dependencies = dependencies.get(dep_key_name[10:])
        if dependencies:
            for dependency_name, dependency_value in dependencies.items():
                if (
                    isinstance(dependency_value, dict)
                    and "workspace" not in dependency_value
                ):
                    raise Exception(f"{cargo_file} has invalid dependency {dependency_name} (not from workspace)")
                if not isinstance(dependency_value, dict):
                    raise Exception(f"{cargo_file} has invalid dependency {dependency_name} (not from workspace)")

    # Write the modified contents back to the file
    with open(cargo_file, "w") as file:
        file.write(tomlkit.dumps(cargo_contents))

def edit_cargo_toml3(path, cargo_toml_file_path):
    # TODO: false positives
    # In case of workspace dependencies, we also need to find which crate uses them
    # Because if it is only used in dev-dependencies, it shouldn't matter (tests enable std feature)
    cargo_file = cargo_toml_file_path
    with open(cargo_file, "r") as file:
        # Parse the contents of the file using tomlkit
        cargo_contents = tomlkit.parse(file.read())

    # Update the dependency section
    for dep_key_name in ["dependencies", "dev-dependencies", "build-dependencies"]:
        if dep_key_name.startswith("workspace."):
            dependencies = cargo_contents.get("workspace")
        else:
            dependencies = cargo_contents.get(dep_key_name)
        if dependencies and dep_key_name.startswith("workspace."):
            dependencies = dependencies.get(dep_key_name[10:])
        if dependencies:
            for dependency_name, dependency_value in dependencies.items():
                if (
                    isinstance(dependency_value, dict)
                    and "workspace" in dependency_value
                    and "default-features" in dependency_value
                ):
                    del dependency_value["default-features"]
                # TODO: what if is not dict

    # Write the modified contents back to the file
    with open(cargo_file, "w") as file:
        file.write(tomlkit.dumps(cargo_contents))

def edit_cargo_toml2(path, cargo_toml_file_path):
    # TODO: false positives
    # In case of workspace dependencies, we also need to find which crate uses them
    # Because if it is only used in dev-dependencies, it shouldn't matter (tests enable std feature)
    cargo_file = cargo_toml_file_path
    with open(cargo_file, "r") as file:
        # Parse the contents of the file using tomlkit
        cargo_contents = tomlkit.parse(file.read())

    # Update the dependency section
    #for dep_key_name in ["dependencies", "dev-dependencies", "build-dependencies", "workspace.dependencies"]:
    for dep_key_name in ["dependencies", "workspace.dependencies"]:
        if dep_key_name.startswith("workspace."):
            dependencies = cargo_contents.get("workspace")
        else:
            dependencies = cargo_contents.get(dep_key_name)
        if dependencies and dep_key_name.startswith("workspace."):
            dependencies = dependencies.get(dep_key_name[10:])
        if dependencies:
            for dependency_name, dependency_value in dependencies.items():
                if (
                    isinstance(dependency_value, dict)
                    and "workspace" not in dependency_value
                ):
                    try:
                        if has_std_feature(path, dependency_name):
                            dependency_value["default-features"] = False
                    except AssertionError:
                        pass
                # TODO: what if is not dict

    # Write the modified contents back to the file
    with open(cargo_file, "w") as file:
        file.write(tomlkit.dumps(cargo_contents))


def edit_cargo_toml(cargo_toml_file_path):
    cargo_file = cargo_toml_file_path
    with open(cargo_file, "r") as file:
        # Parse the contents of the file using tomlkit
        cargo_contents = tomlkit.parse(file.read())

    # Update the dependency section
    #for dep_key_name in ["dependencies", "dev-dependencies", "build-dependencies", "workspace.dependencies"]:
    for dep_key_name in ["dependencies", "workspace.dependencies"]:
        if dep_key_name.startswith("workspace."):
            dependencies = cargo_contents.get("workspace")
        else:
            dependencies = cargo_contents.get(dep_key_name)
        if dependencies and dep_key_name.startswith("workspace."):
            dependencies = dependencies.get(dep_key_name[10:])
        if dependencies:
            for dependency_name, dependency_value in dependencies.items():
                if (
                    isinstance(dependency_value, dict)
                    and "workspace" not in dependency_value
                ):
                    dependency_value["default-features"] = False
                # TODO: what if is not dict

    # Write the modified contents back to the file
    with open(cargo_file, "w") as file:
        file.write(tomlkit.dumps(cargo_contents))

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

if __name__ == "__main__":
    main()
