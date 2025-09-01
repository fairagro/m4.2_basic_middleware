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


from types import TracebackType
from typing import Annotated, Any, List, NamedTuple, Type, Union
from pathlib import Path, PurePosixPath
import os
import tempfile

import git


class GitRepoConfig(NamedTuple):
    """
    A class for the configuration of a GitRepo.
    """

    repo_url: Annotated[str, "The ssh or https URL of the git repository"]
    local_path: Annotated[str, "The local path of the git repository"]
    user_name: Annotated[str, "The name of git user"]
    user_email: Annotated[str, "The email address of git usere"]
    branch: Annotated[str, "The branch of the git repository"] = "main"


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
    github_host_keys = """# github.com:22 SSH-2.0-1907b149
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
        self._ssh_tempdir = None
        self._repo = self._setup()

    def _cleanup(self) -> None:
        """
        delete temp dir, if used
        """
        if self._ssh_tempdir:
            self._ssh_tempdir.cleanup()
            self._ssh_tempdir = None

    # Make this class a context manager to reliably delete the temp dir
    def __enter__(self) -> "GitRepo":
        """
        Make this class a context manager to reliably delete the temp dir.

        Returns
        -------
        GitRepo
            The same instance of GitRepo
        """
        return self

    def __exit__(
            self,
            exc_type: Type[BaseException],
            exc_value: BaseException,
            traceback: TracebackType) -> None:
        """
        Make this class a context manager to reliably delete the temp dir.

        Parameters
        ----------
            exc_type : Type[BaseException]
                The type of the exception being handled, if any.
            exc_val : BaseException
                The exception instance being handled, if any.
            exc_tb : TracebackType
                The traceback of the exception being handled, if any.

        Returns
        -------
            None
        """
        self._cleanup()

    def __del__(self):
        """
        In case this class was not used as context manager, delete the temp
        dir, when it is garbage collected
        """
        self._cleanup()

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

    def pull(self) -> Any:
        """
        Performs a pull from origin on the git repo.

        Returns
        -------
        any
            The git fetch info list as returned by GitPython
        """
        return self._repo.remotes.origin.pull()

    def push(self) -> Any:
        """
        Performs a push to origin on the git repo.

        Returns
        -------
        any
            The git push info list as returned by GitPython.
        """
        return self._repo.remotes.origin.push()

    @staticmethod
    def _make_ssh_key_path(path: Path) -> PurePosixPath:
        # This is some ugly workaround for git on Windows. In this case git is based on MSYS, so the
        # ssh command requires POSIX compatible paths, whereas otherwise we deal with Windows paths
        # on Windows. Thus we need to convert the Windows path to the ssh key to MSYS-POSIX.
        # Be aware: this is brittle as it assumes that we always use MSYS ssh on Windows. Maybe
        # there are other ways to setup git.
        parts = path.parts
        if parts[0].endswith(':\\'):
            parts = ['/', parts[0].rstrip(':\\'), *parts[1:]]
        return PurePosixPath(*parts)

    def _setup_ssh_protocol(self) -> str:
        # We need a temp dir to store some ssh specific files
        self._ssh_tempdir = tempfile.TemporaryDirectory() # pylint: disable=consider-using-with

        # find the ssh key and use it. We need an absolute path for this so git can find it.
        # no matter which is the current working directory.
        temp_dir = Path(self._ssh_tempdir.name)
        ssh_key = GitRepo._make_ssh_key_path(temp_dir / "ssh_key")
        ssh_authorized_keys = GitRepo._make_ssh_key_path(temp_dir / "ssh_authorized_keys")

        # Get key from env and write to file
        private_key = os.environ.get("SSH_PRIVATE_KEY")
        if private_key is None:
            raise ValueError(
                "SSH_PRIVATE_KEY environment variable is not set.")
        with open(ssh_key, "w", encoding="utf-8") as file:
            file.write(private_key)
            file.write("\n")
        os.chmod(ssh_key, 0o600)

        # Write authorized_keys to file
        with open(ssh_authorized_keys, "w", encoding="utf-8") as file:
            file.write(GitRepo.github_host_keys)
        os.chmod(ssh_authorized_keys, 0o644)

        os.environ['GIT_SSH_COMMAND'] = (
            f'ssh '
            f'-F /dev/null '
            f'-i {ssh_key} '
            f'-o UserKnownHostsFile={ssh_authorized_keys} '
            f'-o StrictHostKeyChecking=yes'
        )

        return self._config.repo_url

    def _setup_https_protocol(self) -> str:
        access_token = os.environ.get("ACCESS_TOKEN")
        if access_token:
            _, rest = self._config.repo_url.split("https://", 1)
            repo_url = f"https://{access_token}@{rest}"
        else:
            repo_url = self._config.repo_url

        return repo_url


    def _setup(self):
        # find out local repo path
        local_path = self._config.local_path

        # detect git protocol and perform corrersponding setup
        if self._config.repo_url.startswith('git@'):
            repo_url = self._setup_ssh_protocol()
        elif self._config.repo_url.startswith('https://'):
            repo_url = self._setup_https_protocol()
        else:
            raise ValueError(
                f"The specified git repo URL '{self._config.repo_url}' "
                "does neither use the https nor the ssh protocol"
            )

        # Initialize existing repo or clone it, if this hasn't been done yet
        try:
            repo = git.Repo(local_path)
            if repo.remotes.origin.url != repo_url:
                raise RuntimeError(f"Repository '{local_path}' already exists and is not a "
                                   "clone of '{self._config.repo_url}'")
        except (git.NoSuchPathError, git.InvalidGitRepositoryError):
            repo = git.Repo.clone_from(repo_url, local_path)

        # set git config
        config_writer = repo.config_writer()
        config_writer.set_value("user", "name", self._config.user_name)
        config_writer.set_value("user", "email", self._config.user_email)
        # In case we use a persistent volume containing our git repo and someone else is
        # running/testing the basic middleware on another machine, we might end up
        # lagging behind the remote repo. So we need to specify a pull strategy. Rebase
        # seems to be most suitable (tests showed that fast-forward is not possible and
        # rebase works without merge commits that we do not want -- hopefully we never
        # run into conflicts.)
        config_writer.set_value("pull", "rebase", True)
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
