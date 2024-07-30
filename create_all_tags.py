import os
from git import Repo

repo = Repo(".")


KNOWN_LOCATIONS_OF_STATE_GO = ("helper/resource/state.go", "helper/retry/state.go")
KNOWN_FUNC_DECLARATION = (
    "func (conf *StateChangeConf) WaitForStateContext(ctx context.Context) (interface{}, error) {\n",
)
PATCH = [
    "\t//",
    "\t// Begining of patch",
    "\t// ",
    "\t// Remove the delay before first lookup.",
    "\tconf.Delay = 0",
    "\t// Remove the PollInterval and MinTimeout to always use terraform's default (exponential backoff retry).",
    "\tconf.PollInterval = 0",
    "\tconf.MinTimeout = 0",
    "\t//",
    "\t// End Of Patch",
    "\t//",
    "",
]
# This list of tags can be generated from the terraform-provider-aws-local repo TODO: ADD REPO URL.
# The file ./required_tags.json will be updated automatically through a ci.
REQUIRED_TAGS = [
    "v2.0.1",
    "v2.0.4",
    "v2.1.0",
    "v2.10.1",
    "v2.12.0",
    "v2.13.0",
    "v2.14.0",
    "v2.16.0",
    "v2.17.0",
    "v2.19.0",
    "v2.2.0",
    "v2.20.0",
    "v2.21.0",
    "v2.22.0",
    "v2.23.0",
    "v2.24.0",
    "v2.24.1",
    "v2.25.0",
    "v2.26.1",
    "v2.27.0",
    "v2.28.0",
    "v2.29.0",
    "v2.3.0",
    "v2.30.0",
    "v2.31.0",
    "v2.32.0",
    "v2.33.0",
    "v2.34.0",
    "v2.4.0",
    "v2.4.1",
    "v2.4.2",
    "v2.4.3",
    "v2.4.4",
    "v2.5.0",
    "v2.6.1",
    "v2.7.0",
    "v2.7.1",
    "v2.8.0",
    "v2.9.0",
]


def main():
    errors = []
    created_tags = []

    for tag in REQUIRED_TAGS:
        patched_tag = tag + "-001"

        try:
            repo.remote("origin").fetch(f"refs/tags/{patched_tag}")
            print(f"Already exists at origin: {patched_tag}")
            continue
        except Exception:
            pass

        try:
            repo.delete_tag(repo.tag(tag))
        except Exception:
            pass

        repo.remote("upstream").fetch(f"refs/tags/{tag}:refs/tags/{tag}")
        print(f"Fetched from upstream: {tag}")

        repo.git.checkout(f"tags/{tag}")

        file_path = ""
        for file in KNOWN_LOCATIONS_OF_STATE_GO:
            if os.path.isfile(file):
                print(f"found file at {file}")
                file_path = file

        if not file_path:
            print(f"file not found, skipping {tag}")
            errors.append(f"Tag: {tag}, File not found")
            continue

        with open(file_path, "r") as f:
            content = f.readlines()

        patched = False
        for i, line in enumerate(content):
            if line in KNOWN_FUNC_DECLARATION:
                content.insert(i + 1, "\n".join(PATCH))
                patched = True
                break

        if not patched:
            print(f"Did not find function declaration in {file_path} for {tag}")
            errors.append(f"Tag: {tag} Function declaration not found.")
            continue

        with open(file_path, "w") as f:
            f.writelines(content)

        print(repo.git.diff("**/state.go"))
        user_input = input(
            f"\n\nModification to {file_path}\nIf approved press <enter>. Any other value will cancel the operation.\n"
            "If <enter> is pressed the changes to this file will be commited and a tag will be created and pushed."
        )
        if user_input != "":
            repo.git.checkout(f"tags/{tag} {file_path}".split())
            continue

        repo.index.add(file_path)
        repo.index.commit(f"creating tag for version {patched_tag}")
        repo.create_tag(patched_tag, force=True)
        created_tags.append(patched_tag)

    pushed_tags = repo.remote("origin").push(created_tags)
    print(f"Succesfully pushed tags: {[str(d.remote_ref) for d in pushed_tags]}")


if __name__ == "__main__":
    current_branch = repo.active_branch
    try:
        main()
    finally:
        diffs = repo.index.diff(None).iter_change_type("M")
        to_revert = [diff.a_rawpath.decode() for diff in diffs]
        if to_revert:
            print(
                f"\nReverting local changes to allow going back to original branch {to_revert=}"
            )
            repo.index.checkout([file for file in to_revert if file], force=True)
        current_branch.checkout()
