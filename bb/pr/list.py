# -*- coding: utf-8 -*-

"""
    bb.pr.show lists all pr is current repo
    can also show all pr's authored/revewing either in current repo
    or all repos
"""

from bb.utils import api, cmnd, ini, request, richprint


def to_richprint(repo_name: str, pr_repo_dict: dict) -> None:
    """
    This function takes in a repository name, a dictionary of pull requests, and a header dictionary
    and prints the data to the console
    """
    for status, data in pr_repo_dict.items():
        richprint.render_tree(repo_name, status, data)


def state_check(_input) -> str:
    """state to rich print mapping for table"""
    state: dict = {
        "CLEAN": f"[bold green]{_input}[/bold green]",
        "CONFLICTED": f"[blink bold black on red]{_input}[/blink bold black on red]",
        "APPROVED": f"[bold green]{_input}[/bold green]",
        "UNAPPROVED": f"[bold red]{_input}[/bold red]",
        "NEEDS_WORK": f"[bold yellow]{_input}[/bold yellow]",
        "NONE": "[bold cyan]NOT REVIEWED[/bold cyan]",
    }

    return state[_input.upper()]


def outcome(_pr: dict) -> tuple:
    """
    show the current status of the pr clean/conflicted
    """
    return (
        "[bold green]CLEAN"
        if "mergeResult" not in _pr["properties"]
        else f"{state_check(_pr['properties']['mergeResult']['outcome'])}",
    )


def review_status(reviewers: list) -> str:
    """how the Pr reviewer status"""
    users = []
    if len(reviewers) > 0:
        for user in reviewers:
            if bool(user["user"]["active"]):
                users.append(f"{state_check(user['status'])}")
    else:
        users.append(state_check("NONE"))
    return " & ".join(list(set(users)))


def construct_repo_dict(role_info: list) -> dict:
    """
    parses the role info (reviewer/author), constructs a dict that can be sent to
    richprint tree view
    """
    repo_dict: dict = {}
    if (role_info[0]) == 200 and (len(role_info[1]["values"]) > 0):
        for _pr in role_info[1]["values"]:
            repo = f"{_pr['fromRef']['repository']['slug']}"
            if repo not in repo_dict:
                repo_dict.update({repo: {}})
                if _pr["state"] not in repo_dict[repo].values():
                    repo_dict.update({repo: {_pr["state"]: {}}})
            pr_url_id: tuple = (
                _pr["links"]["self"][0]["href"].split("/")[-1],
                _pr["links"]["self"][0]["href"],
            )
            _list = [
                (
                    "[bold]Status[/bold]",
                    f"{_pr['fromRef']['displayId']} -> {_pr['toRef']['displayId']} | {outcome(_pr)[0]} | {review_status(_pr['reviewers'])}",
                ),
                ("[bold]Tittle[/bold]", _pr["title"]),
                (
                    "[bold]Description[/bold]",
                    _pr["description"] if "description" in _pr.keys() else "-",
                ),
                (
                    "[bold]Author[/bold]",
                    f"{_pr['author']['user']['displayName']} [{_pr['author']['user']['name']}]({_pr['author']['user']['emailAddress']})",
                ),
                (
                    "[bold]Url[/bold]",
                    pr_url_id[1],
                ),
            ]
            repo_dict[repo][_pr["state"]].update({pr_url_id[0]: _list})
    return repo_dict


def list_pull_request(role: str, _all: bool) -> None:
    """
    Shows the list of pull requests authored and pull requests reviewing
    """
    username, token, bitbucket_host = ini.parse()
    project, repository = cmnd.base_repo()
    request_url = api.current_pull_request(bitbucket_host, project, repository)
    if role != "current":
        request_url = api.pull_request_viewer(bitbucket_host, role)

    with richprint.live_progress(f"Fetching Pull Requests ({role}) ... ") as live:
        role_info: list = request.get(request_url, username, token)
        repo_dict = construct_repo_dict(role_info)

        live.update(richprint.console.print("DONE", style="bold green"))

        if len(repo_dict) > 0:
            for repo_name, pr_repo_dict in repo_dict.items():
                if repo_name.lower() == repository.lower() and not _all:
                    to_richprint(repo_name, pr_repo_dict)
                    break

                to_richprint(repo_name, pr_repo_dict)
        else:
            richprint.console.print(
                "There are no open pr's :clap-emoji:", style="bold white"
            )
