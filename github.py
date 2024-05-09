import enum
import requests


class Method(enum.Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class Github:

    __apiKey = ""

    @staticmethod
    def run_request(method: Method, url: str, data=None):
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + Github.__apiKey,
        }

        response = requests.request(method.value, url, headers=headers, data=data)
        return response

    @staticmethod
    def set_api_key(apiKey):
        Github.__apiKey = apiKey

    @staticmethod
    def get_user_orgs() -> list[dict]:
        url = "https://api.github.com/user/orgs"
        response = Github.run_request(Method.GET, url)
        if response.status_code != 200:
            raise Exception("Failed to get user orgs")
        return response.json()

    @staticmethod
    def get_org_repos(org, page) -> list[dict]:
        url = f"https://api.github.com/orgs/{org}/repos?page={page}&per_page=100"
        response = Github.run_request(Method.GET, url)
        return response.json()
