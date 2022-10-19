# gh-dependabot
A GH CLI extension for using Dependabot

## Installation

### Dependencies

The extension requires you to be running Python 3 and also to have [click](https://click.palletsprojects.com/en/8.1.x/) installed.

To install click you can run

```bash
python3 -m pip install click pyrate-limiter
```

To install the extension you can run
```bash
gh extension install therealkujo/gh-dependabot
```

#### Pyrate Limiter

Since the GitHub API can be very aggressive in the [secondary rate limit](https://docs.github.com/en/rest/overview/resources-in-the-rest-api#secondary-rate-limits), I decided to try and do some smoothing to try and space out all of my API calls to avoid being hit with the secondary rate limit. According to the [best practices guidelines] (https://docs.github.com/en/rest/guides/best-practices-for-integrators#dealing-with-secondary-rate-limits) they recommend limiting to one request per second when making a large number of requests. I decided to be conservative and limit my calls to one request per second regardless of number.

To achieve this, I used this python libary called [Pyrate Limiter](https://pypi.org/project/pyrate-limiter/) which helps you limit calls to specific funtions or code blocks. I decorated `call_gh_api` so that the function can only be called a maximum of 1 time per second to help slow down the API requests I send to GitHub. Hopefully I can avoid the secondary rate limit and only need to worry about the primary one.

This is an experiment so I will try and tweak it to be more aggressive if I can when I run this with more customers and the need to do more bulk enables arises.

## Usage

### Export

Exports all the dependabot alerts for a given repo(s) to a csv file

```bash
Usage: gh dependabot export [OPTIONS] [REPO]...

  Pulls all dependabot alerts and exports them to a CSV file

  REPO is space separated in the OWNER/NAME format

Options:
  -o, --output TEXT  Path to the output file
  --help             Show this message and exit.
```

For example you can run `gh dependabot export -o alerts.csv github/foo` to export all dependabot alerts from the `github/foo` repository. 

If you want to export multiple repos, you can feed in a space separated list of repos

```bash
gh dependabot export -o alerts.csv github/foo github/bar some/hello-world
```

All the repos will be combined into one unified csv report but you can filter by repo when opening the file in something like Microsoft Excel

### Enable

Enables dependabot alerts on a given repo(s)

```bash
Usage: gh dependabot enable [OPTIONS] [REPO]...

  Enables dependabot alerts for a repo

  REPO is space separated in the OWNER/NAME format

Options:
  --help  Show this message and exit.
```

If you would like to bulk enable dependabot on multiple repos, you can give it a space separated list of repos

```bash
gh dependabot enable github/foo github/bar some/hello-world
```
