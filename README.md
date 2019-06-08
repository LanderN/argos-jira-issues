# WIP: Issue Management for JIRA (Powered by [Argos](https://github.com/p-e-w/argos))

## Requirements

- GNOME Shell
- Python3 with [`python-jira`](https://pypi.org/project/jira/)
- [Argos](https://github.com/p-e-w/argos)

## Features

- Transition from "Next" to "In Progress" and vice-versa
- Resolve issues and re-assign for review
- Link to browser
- **Automated time tracking**: automatically log time when progress is stopped!

## Screenshots
<img src="https://github.com/LanderN/argos-jira-issues/raw/master/images/notworking.png" width=600 />
<img src="https://github.com/LanderN/argos-jira-issues/raw/master/images/working.png" width=600 />

## Usage
See the [Argos README](https://github.com/p-e-w/argos/blob/master/README.md) for general information about how Argos works.

Create `.jira_credentials.json` and `.jira_reviewers.json` in `~/.config/argos`:
### .jira_credentials.json
This file contains your credentials to log into JIRA.
```
{
    "host": "https://<YOUR_JIRA>.atlassian.net",
    "username": "<YOUR_USERNAME>",
    "password": "<YOUR_API_KEY>"
}
```
Create an API key [here](https://id.atlassian.com/manage/api-tokens).
### .jira_reviewers.json
This file contains the **usernames** of users to display under "reassign for review".
```
["<USERNAME_1>", "<USERNAME_2>", ...]
```
Find usernames with `./jiraManager.py users`
