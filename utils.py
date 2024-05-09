import subprocess


class Utils:
    @staticmethod
    def fuzzy_find(query: str, files: list[str]) -> list[str]:
        result = subprocess.run(
            ["fzf", "--filter", query.encode()],
            input="\n".join(files).encode(),
            stdout=subprocess.PIPE,
        )
        return result.stdout.decode().splitlines()
