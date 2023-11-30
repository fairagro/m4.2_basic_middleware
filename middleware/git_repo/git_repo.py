from typing import Annotated, List, NamedTuple, Optional
from pathlib import Path, PurePosixPath
import os
import git

from utils import make_path_absolute


class GitRepoConfig(NamedTuple):

    repo_url: Annotated[str, "The ssh URL of the git repository"]
    local_path: Annotated[str, "The local path of the git repository"]
    user_name: Annotated[str, "The name of git user"]
    user_email: Annotated[str, "The email address of git usere"]
    branch: Annotated[Optional[str], "The branch of the git repository"] = "main"
    ssh_key_path: Annotated[Optional[str], "The path to the ssh key file"] = None


class GitRepo:

    def __init__(self, config: GitRepoConfig) -> None:
        self._config = config
        self._repo = self._setup()

    @property
    def working_dir(self):
        return self._repo.working_dir
    
    def add_and_commit(self, files: List[Path], message: str):
        self._repo.index.add(files)
        self._repo.index.commit(message)

    def pull(self):
        return self._repo.remotes.origin.pull()

    def push(self):
        return self._repo.remotes.origin.push()

    @staticmethod
    def _make_ssh_key_path(original_path):
        # This is some ugly workaround for git on Windows. In this case git is based on MSYS, so the
        # ssh command requires POSIX compatible paths, whereas otherwise we deal with Windows paths
        # on Windows. Thus we need to convert the Windows path to the ssh key to MSYS-POSIX.
        # Be aware: this is brittle as it assumes that we always use MSYS ssh on Windows. Maybe there
        # are other ways to setup git.
        path = Path(original_path)
        parts = path.parts
        if parts[0].endswith(':\\'):
            parts = ['/', parts[0].rstrip(':\\'), *parts[1:]]
        return PurePosixPath(*parts)

    def _setup(self):
        # find out local repo path
        local_path = make_path_absolute(self._config.local_path)

        # find the ssh key and use it
        ssh_key_path = make_path_absolute(self._config.ssh_key_path)
        if ssh_key_path:
            # Note: actutally /dev/null is OS-dependent. There is os.devnull to cope with this.
            # But for my git setup on Windwos, /dev/null is the correct value -- probably because
            # it uses an MSYS-based ssh. 
            os.environ['GIT_SSH_COMMAND'] = f'ssh -F /dev/null -i {GitRepo._make_ssh_key_path(ssh_key_path)}'

        # Initialize existing repo or clone it, if this hasn't been done yet
        try:
            repo = git.Repo(local_path)
            if repo.remotes.origin.url != self._config.repo_url:
                raise RuntimeError(f"Repository {local_path} already exists and is not a clone of {self._config.repo_url}")
        except (git.exc.NoSuchPathError, git.exc.InvalidGitRepositoryError):
            repo = git.Repo.clone_from(self._config.repo_url, local_path)

        # set git config
        config_writer = repo.config_writer()
        config_writer.set_value("user", "name", self._config.user_name)
        config_writer.set_value("user", "email", self._config.user_email)
        config_writer.release()

        # switch into desired branch or create it
        branch = self._config.branch
        if branch not in repo.branches:
            # before we can create a branch we need have a commit, so try to access it
            try:
                _ = repo.head.commit
            except ValueError:
                # create initial commit
                readme = """# Purpose of this repository #

    This repository is automatically maintained by the FAIRagro middleware. It stores scraped meta data from resarch data repositories in consolidated JSON-LD files.
    """
                readme_path = os.path.join(local_path, 'README.md')
                with open(readme_path, "w") as file:
                    file.write(readme)
                repo.index.add([readme_path])
                repo.index.commit("Initial commit")
            # create new branch
            repo.create_head(branch)
            repo.remotes.origin.push(branch)
        repo.git.checkout(branch)

        return repo