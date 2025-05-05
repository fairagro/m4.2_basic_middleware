"""
This module deals with storing files in a git repository.

Classes
-------
    GitRepo
        A wrapper class for git.Repo that is able to initialize a new git
        repository or clone an existing one. It respects the configuration
        specified in terms of a GitRepoConfig instance.
    GitRepoConfig
        The configuration for a GitRepo object.
"""

__all__ = [
    'GitRepo',
    'GitRepoConfig'
]
__version__ = '0.1.0'
__author__ = 'carsten.scharfenberg@zalf.de'


from typing import Annotated, List, NamedTuple, Optional, Union
from pathlib import Path, PurePosixPath
import os
import tempfile

import git


class GitRepoConfig(NamedTuple):
    """
    A class for the configuration of a GitRepo.
    """

    repo_url: Annotated[str, "The ssh URL of the git repository"]
    local_path: Annotated[str, "The local path of the git repository"]
    user_name: Annotated[str, "The name of git user"]
    user_email: Annotated[str, "The email address of git usere"]
    branch: Annotated[Optional[str], "The branch of the git repository"] = "main"

class GitRepo:
    """
    A wrapper class for git.Repo that is able to initialize or clone git repository

    Methods
    -------
        add_and_commit(files, message)
            Add the specified files to the git repo and commits them.
        pull()
            Performs a pull from origin on the git repo.
        push()
            Performs a push to origin on the git repo.

    Properties
    ----------
        working_dir
            Then local working directory of the git repo
    """

    # So we do not need to turn off host key checking
    github_host_keys="""# github.com:22 SSH-2.0-1907b149
github.com ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCj7ndNxQowgcQnjshcLrqPEiiphnt+VTTvDP6mHBL9j1aNUkY4Ue1gvwnGLVlOhGeYrnZaMgRK6+PKCUXaDbC7qtbW8gIkhL7aGCsOr/C56SJMy/BCZfxd1nWzAOxSDPgVsmerOBYfNqltV9/hWCqBywINIR+5dIg6JTJ72pcEpEjcYgXkE2YEFXV1JHnsKgbLWNlhScqb2UmyRkQyytRLtL+38TGxkxCflmO+5Z8CSSNY7GidjMIZ7Q4zMjA2n1nGrlTDkzwDCsw+wqFPGQA179cnfGWOWRVruj16z6XyvxvjJwbz0wQZ75XK5tKSb7FNyeIEs4TT4jk+S4dhPeAUC5y+bDYirYgM4GC7uEnztnZyaVWQ7B381AK4Qdrwt51ZqExKbQpTUNn+EjqoTwvqNj4kqx5QUCI0ThS/YkOxJCXmPUWZbhjpCg56i+2aB6CmK2JGhn57K5mj0MNdBXA4/WnwH6XoPWJzK5Nyu2zB3nAZp+S5hpQs+p1vN1/wsjk=
# github.com:22 SSH-2.0-1907b149
# github.com:22 SSH-2.0-1907b149
github.com ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBEmKSENjQEezOmxkZMy7opKgwFB9nkt5YRrYMjNuG5N87uRgg6CLrbo5wAdT/y6v0mKV0U2w0WZ2YB/++Tpockg=
# github.com:22 SSH-2.0-1907b149
github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl
# github.com:22 SSH-2.0-1907b149
"""

    def __init__(self, config: GitRepoConfig) -> None:
        self._config = config
        self._ssh_tempdir = tempfile.TemporaryDirectory(dir='/tmp/ssh')
        self._ssh_key = os.path.abspath(
            os.path.join(self._ssh_tempdir.name, "ssh_key"))
        self._ssh_authorized_keys = os.path.abspath(
            os.path.join(self._ssh_tempdir.name, "authorized_keys"))
        self._repo = self._setup()

    def __del__(self) -> None:
        self._ssh_tempdir.cleanup()

    @property
    def working_dir(self) -> Union[str, os.PathLike[str]]:
        """
        Returns the local working directory of the git repo

        Returns
        -------
        Union[None, str, os.PathLike[str]]
            The local working directory of the git repo as path-like object
        """
        return self._repo.working_dir

    def add_and_commit(self, files: List[Path], message: str) -> git.Commit:
        """
        Add the specified files to the git repo and commits them.

        Parameters
        ----------
        files : List[Path]
            a list of (absolute) file path within the git working directory
            that are to be added to the git repo
        message : str
            the commit message

        Returns
        -------
        git.Commit
            The git commit object as returned by GitPython
        """
        self._repo.index.add(files)
        return self._repo.index.commit(message)

    def pull(self) -> any:
        """
        Performs a pull from origin on the git repo.

        Returns
        -------
        any
            The git fetch info list as returned by GitPython
        """
        return self._repo.remotes.origin.pull()

    def push(self) -> any:
        """
        Performs a push to origin on the git repo.

        Returns
        -------
        any
            The git push info list as returned by GitPython.
        """
        return self._repo.remotes.origin.push()

    @staticmethod
    def _make_ssh_key_path(original_path):
        # This is some ugly workaround for git on Windows. In this case git is based on MSYS, so the
        # ssh command requires POSIX compatible paths, whereas otherwise we deal with Windows paths
        # on Windows. Thus we need to convert the Windows path to the ssh key to MSYS-POSIX.
        # Be aware: this is brittle as it assumes that we always use MSYS ssh on Windows. Maybe
        # there are other ways to setup git.
        path = Path(original_path)
        parts = path.parts
        if parts[0].endswith(':\\'):
            parts = ['/', parts[0].rstrip(':\\'), *parts[1:]]
        return PurePosixPath(*parts)

    def _setup(self):
        # find out local repo path
        local_path = self._config.local_path

        # find the ssh key and use it. We need an absolute path for this so git can find it.
        # no matter which is the current working directory.
        ssh_key = GitRepo._make_ssh_key_path(self._ssh_key)
        ssh_authorized_keys = GitRepo._make_ssh_key_path(self._ssh_authorized_keys)

        # Get key from env and write to file
        private_key = os.environ.get("SSH_PRIVATE_KEY")
        if private_key is None:
            raise ValueError("SSH_PRIVATE_KEY environment variable is not set.")
        with open(ssh_key, "w") as file:
            file.write(private_key)
            file.write("\n")
        os.chmod(ssh_key, 0o600)

        # Write authorized_keys to file
        with open(ssh_authorized_keys, "w") as file:
            file.write(GitRepo.github_host_keys)
        os.chmod(ssh_authorized_keys, 0o644)

        os.environ['GIT_SSH_COMMAND'] = \
            f'ssh -F /dev/null -i {ssh_key} -o UserKnownHostsFile={ssh_authorized_keys} -o StrictHostKeyChecking=yes'

        # Initialize existing repo or clone it, if this hasn't been done yet
        try:
            repo = git.Repo(local_path)
            if repo.remotes.origin.url != self._config.repo_url:
                raise RuntimeError("Repository " + local_path + "already exists and is not a " +
                                   " clone of " + self._config.repo_url)
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

This repository is automatically maintained by the FAIRagro
[middleware](https://github.com/fairagro/m4.2_basic_middleware). It stores scraped meta
data from resarch data repositories in consolidated JSON-LD files.

<mark>Important:</mark> do not change this repo manually.
"""
                readme_path = os.path.join(local_path, 'README.md')
                with open(readme_path, "w", encoding="utf-8") as file:
                    file.write(readme)
                repo.index.add([readme_path])
                repo.index.commit("Initial commit")
            # create new branch
            repo.create_head(branch)
            repo.remotes.origin.push(branch)
        repo.git.checkout(branch)

        return repo
