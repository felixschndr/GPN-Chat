from git import Repo


class GitRootFinder:
    @staticmethod
    def get() -> str:
        repo = Repo(".", search_parent_directories=True)
        return repo.working_tree_dir
