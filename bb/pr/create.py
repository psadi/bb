# -*- coding: utf-8 -*-


"""
    bb.pr.create - creates a pull request in bitbucket
    while doing so it gathers all the facts required for a pr from the
    remote and local repository
"""

from typer import prompt, Exit
from bb.pr.diff import show_diff
from bb.utils import cmnd, ini, request, api, richprint, cp


def gather_facts(
    target: str,
    from_branch: str,
    project: str,
    repository: str,
    title_and_description: str,
) -> list:
    """
    It gathers facts for  the pull request from bitbucket and local git
    repository
    """

    username, token, bitbucket_host = ini.parse()
    with richprint.live_progress(f"Gathering facts on '{repository}' ..."):
        repo_id = None
        for repo in request.get(
            api.get_repo_info(bitbucket_host, project), username, token
        )[1]["values"]:
            if repo["name"] == repository:
                repo_id = repo["id"]

        reviewers = []
        if repo_id is not None:
            for dict_item in request.get(
                api.default_reviewers(
                    bitbucket_host, project, repo_id, from_branch, target
                ),
                username,
                token,
            )[1]:
                for key in dict_item:
                    if key == "name":
                        reviewers.append({"user": {"name": dict_item[key]}})

    table = richprint.table(
        [("SUMMARY", "bold yellow"), ("DESCRIPTION", "#FFFFFF")],
        [
            ("Project", project),
            ("Repository", repository),
            ("Repository ID", str(repo_id)),
            ("From Branch", from_branch),
            ("To Branch", target),
            ("Title", title_and_description[0]),
            ("Description", title_and_description[1]),
        ],
        True,
    )
    richprint.console.print(table)
    return reviewers


def create_pull_request(target: str, yes: bool, diff: bool, rebase: bool) -> None:
    """
    It creates a pull request.
    """

    username, token, bitbucket_host = ini.parse()
    from_branch = cmnd.from_branch()
    if target == from_branch:
        richprint.console.print("Source & target cannot be the same", style="bold red")
        raise Exit(code=1)

    if rebase:
        with richprint.live_progress(
            f"Rebasing {from_branch} with {target} ... "
        ) as live:
            cmnd.git_rebase(target)
            live.update(richprint.console.print("REBASED", style="bold green"))

    project, repository = cmnd.base_repo()
    title_and_description = cmnd.title_and_description()
    reviewers = gather_facts(
        target,
        from_branch,
        project,
        repository,
        title_and_description,
    )

    if yes or prompt("Proceed [y/n]").lower().strip() == "y":
        with richprint.live_progress("Creating Pull Request ..."):
            url = api.pull_request_create(bitbucket_host, project, repository)
            body = api.pull_request_body(
                title_and_description,
                from_branch,
                repository,
                project,
                target,
                reviewers,
            )
            pull_request = request.post(url, username, token, body)

        if pull_request[0] == 201:
            richprint.console.print(
                f"Pull Request Created: {pull_request[1]['links']['self'][0]['href']}",
                highlight=True,
                style="bold green",
            )
            _id = pull_request[1]["links"]["self"][0]["href"].split("/")[-1]
            cp.copy_to_clipboard(pull_request[1]["links"]["self"][0]["href"])
        elif pull_request[0] == 409:
            richprint.console.print(
                f"Message: {pull_request[1]['errors'][0]['message']}",
                highlight=True,
                style="bold red",
            )
            richprint.console.print(
                f"Existing Pull Request: {pull_request[1]['errors'][0]['existingPullRequest']['links']['self'][0]['href']}",
                highlight=True,
                style="bold yellow",
            )
            _id = pull_request[1]["errors"][0]["existingPullRequest"]["links"]["self"][
                0
            ]["href"].split("/")[-1]
            cp.copy_to_clipboard(
                pull_request[1]["errors"][0]["existingPullRequest"]["links"]["self"][0][
                    "href"
                ]
            )
        else:
            request.http_response_definitions(pull_request[0])
            raise Exit(code=1)

    if diff:
        show_diff(_id)
