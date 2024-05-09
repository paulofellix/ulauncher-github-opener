import json
import logging
import subprocess
from time import sleep

from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.event import (
    ItemEnterEvent,
    KeywordQueryEvent,
    PreferencesEvent,
    PreferencesUpdateEvent,
)
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem

from github import Github
from utils import Utils

logger = logging.getLogger(__name__)


class GithubOpenerExtension(Extension):

    preferences: dict[str, str] = {}
    repos: list[str] = []

    def __init__(self):
        super(GithubOpenerExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())
        self.subscribe(PreferencesEvent, PreferencesEventListener())
        self.subscribe(PreferencesUpdateEvent, PreferencesUpdateEventListener())

    def search(self, query: str) -> list[dict[str, str]]:
        # https://github.com/devs-atem/ms-contracts
        result_search = Utils.fuzzy_find(query, self.repos)
        result_list = []
        for result in result_search:
            repo = result.split("/")[-1]
            owner = result.split("/")[-2]
            result_list.append({"name": f"{owner}/{repo}", "url": result})
        return result_list

    def generate_repos_list(self):
        self.repos = []
        orgs = Github.get_user_orgs()
        for org in orgs:
            logger.info("Fetching repositories for %s" % org["login"])
            page = 1
            while True:
                repos = Github.get_org_repos(org["login"], page)
                if len(repos) == 0:
                    break
                self.repos.extend(list(map(lambda repo: repo["html_url"], repos)))
                page += 1
        logger.info("Fetched %s repositories" % len(self.repos))


class KeywordQueryEventListener(EventListener):

    def on_event(self, event: KeywordQueryEvent, extension: GithubOpenerExtension):
        items = []
        logger.info("preferences %s" % json.dumps(extension.preferences))

        query = event.get_argument() or ""
        if query:
            results = extension.search(query)
            for result in results:
                items.append(
                    ExtensionResultItem(
                        icon="images/icon.png",
                        name=result["name"],
                        description="Press Enter to open the repository",
                        on_enter=ExtensionCustomAction(
                            {
                                "action": "open_repo",
                                "url": result["url"],
                            }
                        ),
                    )
                )

        items.append(
            ExtensionResultItem(
                icon="images/refresh.png",
                name="Generate a list of repositories",
                description="Type a keyword to search for repositories",
                on_enter=ExtensionCustomAction({"action": "generate_repos_list"}),
            )
        )

        return RenderResultListAction(items)


class ItemEnterEventListener(EventListener):
    def on_event(self, event, extension):
        data = event.get_data()

        items = []
        if data["action"] == "generate_repos_list":
            extension.generate_repos_list()
        if data["action"] == "open_repo":
            subprocess.Popen(["xdg-open", data["url"]])


class PreferencesEventListener(EventListener):
    def on_event(self, event: PreferencesEvent, extension: GithubOpenerExtension):
        extension.preferences = dict(event.preferences or {})
        Github.set_api_key(extension.preferences.get("api_key", ""))
        extension.generate_repos_list()


class PreferencesUpdateEventListener(EventListener):
    def on_event(self, event: PreferencesUpdateEvent, extension: GithubOpenerExtension):
        extension.preferences[str(event.id)] = event.new_value or ""
        if event.id == "api_key":
            Github.set_api_key(event.new_value)
            extension.generate_repos_list()


if __name__ == "__main__":
    GithubOpenerExtension().run()
