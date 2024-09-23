from git import Repo


class GitRootFinder:
    """
    This class provides a method to find the root directory of a git repository.
    """

    @staticmethod
    def get() -> str:
        """
        :return: The working tree directory of the current Git repository.
        """
        repo = Repo(".", search_parent_directories=True)
        return repo.working_tree_dir
