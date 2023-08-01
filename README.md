# gh-dependabot
A GH CLI extension for enabling Dependabot and viewing Dependabot alerts.

## Installation

### Dependencies

The extension requires you to be running Python 3 and also to have [click](https://click.palletsprojects.com/en/8.1.x/) and [pyrate-limiter](https://github.com/vutran1710/PyrateLimiter) installed.

To install these dependencies you can run:

```bash
python3 -m pip install click pyrate-limiter
```

To install the extension you can run:
```bash
gh extension install therealkujo/gh-dependabot
```
#### Click

Click is a really useful tool that helps build command line interfaces. It is highly configurable and helps to automagically generate all the interfaces based on my configuration. I have been using it for all my CLI tools to help reduce the amount of code I need to maintain just to have an interface and I can focus on the actual code itself.

#### Pyrate Limiter

Since the GitHub API can be very aggressive in the [secondary rate limit](https://docs.github.com/en/rest/overview/resources-in-the-rest-api#secondary-rate-limits), I decided to try and do some smoothing to space out all of my API calls to avoid being hit with the secondary rate limit. According to the [best practices guidelines](https://docs.github.com/en/rest/guides/best-practices-for-integrators#dealing-with-secondary-rate-limits) it's recommended to limit your requests to one per second when making a large number of requests. I decided to be conservative and limit my calls to one request per second regardless of the total number.

To achieve this, I used this python libary called [Pyrate Limiter](https://pypi.org/project/pyrate-limiter/) which helps you limit calls to specific funtions or code blocks by leveraging the leaky bucket algorithm. I decorated `call_gh_api` so that the function can only be called a maximum of 1 time per second to help slow down the API requests I send to GitHub. Hopefully I can avoid the secondary rate limit and only need to worry about the primary one. My bucket will eternally grow to ensure that all calls get executed but the more calls we make, the longer it will take.

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

Enables dependabot features on a given org or repo

```bash
Usage: gh dependabot enable [OPTIONS] [NAMES]...

  Enables dependabot features for an organization or repo

  NAME is space separated in the OWNER/NAME format or just ORGANIZATION

Options:
  -a, --alerts        Enable dependabot alerts
  -s, --security      Enable dependabot security updates
  -o, --organization  Enable dependabot at the organization level
  --help              Show this message and exit.
```

You will need to specify with the flags which dependabot feature you would like to enable.

If you would like to bulk enable dependabot alerts on multiple repos, you can give it a space separated list of repos

```bash
gh dependabot enable -a github/foo github/bar some/hello-world
```

If you would like to bulk enable dependabot alerts on multiple orgs, you can give it a space separated list of orgs

```bash
gh dependabot enable -ao foo bar
```

If you would like to bulk enable dependabot alerts for a subset of repositories based on whether they include one or more languages, you can use a combination or `gh repo list`, `jq`, and `xargs` to achieve this. Just replace YOUR_ORGANIZATION and YOUR_LIMIT with your own values. The example below enables dependabot alerts for all repositories in an organization that include either JavaScript or TypeScript.
```bash
gh repo list YOUR_ORGANIZATION --limit YOUR_LIMIT \            
--json nameWithOwner,languages \
--jq \
'.[] | (.languages) = [.languages[].node.name] |
select(.languages | any(. == "JavaScript" or . == "TypeScript"))' | jq 'del(.languages)' | jq -r '.nameWithOwner' | xargs gh dependabot enable -a
```

## Tests

If you want to run the unit tests, you will need to clone this repo and just run `./gh-dependabot_test.py`

If you would like to view the test coverage you can run `python -m coverage run ./gh-dependabot_test.py`

To view test coverage results, you can run `python -m coverage report`
