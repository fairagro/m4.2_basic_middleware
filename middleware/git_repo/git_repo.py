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
import git
import git.util

from utils import make_path_absolute


class GitRepoConfig(NamedTuple):
    """
    A class for the configuration of a GitRepo.
    """

    repo_url: Annotated[str, "The ssh URL of the git repository"]
    local_path: Annotated[str, "The local path of the git repository"]
    user_name: Annotated[str, "The name of git user"]
    user_email: Annotated[str, "The email address of git usere"]
    branch: Annotated[Optional[str], "The branch of the git repository"] = "main"
    ssh_key_path: Annotated[Optional[str], "The path to the ssh key file"] = None


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

    def __init__(self, config: GitRepoConfig) -> None:
        self._config = config
        self._repo = self._setup()

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
        local_path = make_path_absolute(self._config.local_path)

        # find the ssh key and use it
        ssh_key_path = make_path_absolute(self._config.ssh_key_path)
        if ssh_key_path:
            # Note: actutally /dev/null is OS-dependent. There is os.devnull to cope with this.
            # But for my git setup on Windwos, /dev/null is the correct value -- probably because
            # it uses an MSYS-based ssh.
            os_key_path = GitRepo._make_ssh_key_path(ssh_key_path)
            os.environ['GIT_SSH_COMMAND'] = \
                f'ssh -F /dev/null -o StrictHostKeyChecking=no -i {os_key_path}'

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

    This repository is automatically maintained by the FAIRagro middleware. It stores scraped meta
    data from resarch data repositories in consolidated JSON-LD files.
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
    