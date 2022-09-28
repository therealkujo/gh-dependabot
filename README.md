# gh-dependabot
A GH CLI extension for using Dependabot

## Installation

```bash
gh extension install https://github.com/therealkujo/gh-dependabot
```

## Usage

### Export

Exports all the dependabot alerts for a given repo(s) to a csv file

```bash
Usage: gh dependabot export [OPTIONS] [REPO]...

  Pulls all dependabot alerts and exports them to a CSV file

  REPO is space separated in the OWNER/NAME format

Options:
  -o, --output TEXT  Path to the output file  [required]
  --help             Show this message and exit.
```

For example you can run `gh dependabot export -o alerts.csv github/foo` to export all dependabot alerts from the `github/foo` repository. 

If you want to export multiple repos, you can feed in a space separated list of repos

```bash
gh dependabot export -o alerts.csv github/foo github/bar some/hello-world
```

All the repos will be combined into one unified csv report but you can filter by repo when opening the file in something like Microsoft Excel
