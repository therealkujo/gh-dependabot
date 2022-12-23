#!/usr/bin/env python3

import unittest
import importlib.util
import importlib.machinery
import os
import sys
import time
from unittest.mock import Mock, call, mock_open, patch
from click.testing import CliRunner
from io import StringIO


def import_path(path):
    module_name = os.path.basename(path).replace('-', '_')
    spec = importlib.util.spec_from_loader(
        module_name,
        importlib.machinery.SourceFileLoader(module_name, path)
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[module_name] = module
    return module


dependabot = import_path('gh-dependabot')


class TestDependabot(unittest.TestCase):

    # Uncomment the below line if you need to view the full diff of what is different in test behavior
    # maxDiff = None

    graphql_alerts = [
                        {
                            "id": "RVA_kwDOHzNV0M6pkdQi",
                            "securityAdvisory": {
                                "ghsaId": "GHSA-6528-wvf6-f6qg",
                                "permalink": "https://github.com/advisories/GHSA-6528-wvf6-f6qg",
                                "severity": "HIGH",
                                "description": "Its really dangerous ok",
                                "summary": "Pycrypto generates weak key parameters"
                            },
                            "securityVulnerability": {
                                "package": {
                                    "name": "pycrypto",
                                    "ecosystem": "PIP"
                                },
                                "vulnerableVersionRange": "<= 2.6.1",
                                "advisory":{
                                    "cvss":{
                                        "score": 9.8
                                    }
                                }
                            },
                            "createdAt": "2022-08-10T18:44:52Z",
                            "state": "OPEN",
                            "fixedAt": None,
                            "fixReason": None,
                            "dismissedAt": None,
                            "dismissReason": None,
                            "dismisser": None,
                            "vulnerableManifestPath": "authn-service/requirements.txt",
                            "vulnerableRequirements": "= 2.6.1"
                        },
                    ]
    parsed_alerts = [
                        {
                            'advisory_permalink': 'https://github.com/advisories/GHSA-6528-wvf6-f6qg',
                            'created_at': '2022-08-10T18:44:52Z',
                            'description': 'Its really dangerous ok',
                            'dismiss_reason': None,
                            'dismissed_at': None,
                            'dismissed_by': None,
                            'fix_reason': None,
                            'fixed_at': None,
                            'id': 'RVA_kwDOHzNV0M6pkdQi',
                            'manifest_filepath': 'authn-service/requirements.txt',
                            'package_ecosystem': 'PIP',
                            'package_name': 'pycrypto',
                            'package_version': '= 2.6.1',
                            'repo': 'test',
                            'severity': 'HIGH',
                            'cvss_score': 9.8,
                            'state': 'OPEN',
                            'summary': 'Pycrypto generates weak key parameters',
                            'vulnerable_versions': '<= 2.6.1'
                        }
                    ]
    csv_header_values = 'advisory_permalink,created_at,description,dismiss_reason,dismissed_at,dismissed_by,fix_reason,fixed_at,id,manifest_filepath,package_ecosystem,package_name,package_version,repo,severity,cvss_score,state,summary,vulnerable_versions\r\n'
    csv_row_values = 'https://github.com/advisories/GHSA-6528-wvf6-f6qg,2022-08-10T18:44:52Z,Its really dangerous ok,,,,,,RVA_kwDOHzNV0M6pkdQi,authn-service/requirements.txt,PIP,pycrypto,= 2.6.1,test,HIGH,9.8,OPEN,Pycrypto generates weak key parameters,<= 2.6.1\r\n'
    gh_query = ['/opt/homebrew/bin/gh', 'api', 'graphql', '-F', 'org=github', '-F', 'repo=foo', '-F', 'cursor=null', '-f', 'query=\n    query ($org: String! $repo: String! $cursor: String){\n        repository(owner: $org name: $repo) {\n            name\n            vulnerabilityAlerts(first: 100 after: $cursor) {\n                pageInfo {\n                    hasNextPage\n                    endCursor\n                }\n                totalCount\n                nodes {\n                    id\n                    securityAdvisory {\n                        ...advFields\n                    }\n                    securityVulnerability {\n                        package {\n                            ...pkgFields\n                        }\n                        vulnerableVersionRange\n                        advisory {\n                            cvss {\n                                score\n                            }\n                        }\n                    }\n                    createdAt\n                    state\n                    fixedAt\n                    fixReason\n                    dismissedAt\n                    dismissReason\n                    dismisser {\n                        login\n                    }\n                    vulnerableManifestPath\n                    vulnerableRequirements\n                }\n            }\n        }\n    }\n    fragment advFields on SecurityAdvisory {\n        ghsaId\n        permalink\n        severity\n        description\n        summary\n    }\n    fragment pkgFields on SecurityAdvisoryPackage {\n        name\n        ecosystem\n    }\n    ']
    gh_paginated_query = ['/opt/homebrew/bin/gh', 'api', 'graphql', '-F', 'org=github', '-F', 'repo=foo', '-F', 'cursor=Y3Vyc29yOnYyOpHOr2XWzA==', '-f', 'query=\n    query ($org: String! $repo: String! $cursor: String){\n        repository(owner: $org name: $repo) {\n            name\n            vulnerabilityAlerts(first: 100 after: $cursor) {\n                pageInfo {\n                    hasNextPage\n                    endCursor\n                }\n                totalCount\n                nodes {\n                    id\n                    securityAdvisory {\n                        ...advFields\n                    }\n                    securityVulnerability {\n                        package {\n                            ...pkgFields\n                        }\n                        vulnerableVersionRange\n                        advisory {\n                            cvss {\n                                score\n                            }\n                        }\n                    }\n                    createdAt\n                    state\n                    fixedAt\n                    fixReason\n                    dismissedAt\n                    dismissReason\n                    dismisser {\n                        login\n                    }\n                    vulnerableManifestPath\n                    vulnerableRequirements\n                }\n            }\n        }\n    }\n    fragment advFields on SecurityAdvisory {\n        ghsaId\n        permalink\n        severity\n        description\n        summary\n    }\n    fragment pkgFields on SecurityAdvisoryPackage {\n        name\n        ecosystem\n    }\n    ']

    dependabot_enable_success_output = "HTTP/2.0 204 No Content\nAccess-Control-Allow-Origin: *\nAccess-Control-Expose-Headers: ETag, Link, Location, Retry-After, X-GitHub-OTP, X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Used, X-RateLimit-Resource, X-RateLimit-Reset, X-OAuth-Scopes, X-Accepted-OAuth-Scopes, X-Poll-Interval, X-GitHub-Media-Type, X-GitHub-SSO, X-GitHub-Request-Id, Deprecation, Sunset\nContent-Security-Policy: default-src 'none'\nDate: Tue, 01 Apr 1990 01:02:03 GMT\nGithub-Authentication-Token-Expiration: 2099-04-01 07:00:00 UTC\nReferrer-Policy: origin-when-cross-origin, strict-origin-when-cross-origin\nServer: GitHub.com\nStrict-Transport-Security: max-age=31536000; includeSubdomains; preload\nVary: Accept-Encoding, Accept, X-Requested-With\nX-Accepted-Oauth-Scopes: repo\nX-Content-Type-Options: nosniff\nX-Frame-Options: deny\nX-Github-Api-Version-Selected: 2022-08-09\nX-Github-Media-Type: github.v3; format=json\nX-Github-Request-Id: CCEE:9972:181CEB0:312E601:6345FB6B\nX-Oauth-Scopes: admin:gpg_key, admin:public_key, admin:ssh_signing_key, codespace, delete:packages, gist, project, read:org, repo, user, workflow, write:discussion, write:packages\nX-Ratelimit-Limit: 5000\nX-Ratelimit-Remaining: 4998\nX-Ratelimit-Reset: 1665534015\nX-Ratelimit-Resource: core\nX-Ratelimit-Used: 2\nX-Xss-Protection: 0\n\n"

    dependabot_enable_error_output = 'HTTP/2.0 404 Not Found\nAccess-Control-Allow-Origin: *\nAccess-Control-Expose-Headers: ETag, Link, Location, Retry-After, X-GitHub-OTP, X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Used, X-RateLimit-Resource, X-RateLimit-Reset, X-OAuth-Scopes, X-Accepted-OAuth-Scopes, X-Poll-Interval, X-GitHub-Media-Type, X-GitHub-SSO, X-GitHub-Request-Id, Deprecation, Sunset\nContent-Security-Policy: default-src \'none\'\nDate: Tue, 01 Apr 1990 01:02:03 GMT\nGithub-Authentication-Token-Expiration: 2099-04-01 07:00:00 UTC\nReferrer-Policy: origin-when-cross-origin, strict-origin-when-cross-origin\nServer: GitHub.com\nStrict-Transport-Security: max-age=31536000; includeSubdomains; preload\nVary: Accept-Encoding, Accept, X-Requested-With\nX-Accepted-Oauth-Scopes: repo\nX-Content-Type-Options: nosniff\nX-Frame-Options: deny\nX-Github-Api-Version-Selected: 2022-08-09\nX-Github-Media-Type: github.v3; format=json\nX-Github-Request-Id: CCEE:9972:181CEB0:312E601:6345FB6B\nX-Oauth-Scopes: admin:gpg_key, admin:public_key, admin:ssh_signing_key, codespace, delete:packages, gist, project, read:org, repo, user, workflow, write:discussion, write:packages\nX-Ratelimit-Limit: 5000\nX-Ratelimit-Remaining: 4998\nX-Ratelimit-Reset: 1665534015\nX-Ratelimit-Resource: core\nX-Ratelimit-Used: 2\nX-Xss-Protection: 0\n\n{"message":"Not Found","documentation_url":"https://docs.github.com/rest"}'

    dependabot_enable_parsed_headers = {'Access-Control-Allow-Origin': '*', 'Access-Control-Expose-Headers': 'ETag, Link, Location, Retry-After, X-GitHub-OTP, X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Used, X-RateLimit-Resource, X-RateLimit-Reset, X-OAuth-Scopes, X-Accepted-OAuth-Scopes, X-Poll-Interval, X-GitHub-Media-Type, X-GitHub-SSO, X-GitHub-Request-Id, Deprecation, Sunset', 'Content-Security-Policy': "default-src 'none'", 'Date': 'Tue, 01 Apr 1990 01:02:03 GMT', 'Github-Authentication-Token-Expiration': '2099-04-01 07:00:00 UTC', 'Referrer-Policy': 'origin-when-cross-origin, strict-origin-when-cross-origin', 'Server': 'GitHub.com', 'Strict-Transport-Security': 'max-age=31536000; includeSubdomains; preload', 'Vary': 'Accept-Encoding, Accept, X-Requested-With', 'X-Accepted-Oauth-Scopes': 'repo', 'X-Content-Type-Options': 'nosniff', 'X-Frame-Options': 'deny', 'X-Github-Api-Version-Selected': '2022-08-09', 'X-Github-Media-Type': 'github.v3; format=json', 'X-Github-Request-Id': 'CCEE:9972:181CEB0:312E601:6345FB6B', 'X-Oauth-Scopes': 'admin:gpg_key, admin:public_key, admin:ssh_signing_key, codespace, delete:packages, gist, project, read:org, repo, user, workflow, write:discussion, write:packages', 'X-Ratelimit-Limit': '5000', 'X-Ratelimit-Remaining': '4998', 'X-Ratelimit-Reset': '1665534015', 'X-Ratelimit-Resource': 'core', 'X-Ratelimit-Used': '2'}

    dependabot_enable_success_parsed_output = ('204', dependabot_enable_parsed_headers, '')

    dependabot_repo_enable_command = ['--method', 'PUT', '-H', 'Accept: application/vnd.github+json', '/repos/foo/bar/vulnerability-alerts']

    dependabot_repo_enable_full_command = ['/opt/homebrew/bin/gh', 'api', '--include', '--method', 'PUT', '-H', 'Accept: application/vnd.github+json', '/repos/foo/bar/vulnerability-alerts']

    dependabot_org_enable_command = ['--method', 'POST', '-H', 'Accept: application/vnd.github+json', '/orgs/foo/dependabot_alerts/enable_all']

    dependabot_org_enable_full_command = ['/opt/homebrew/bin/gh', 'api', '--include', '--method', 'POST', '-H', 'Accept: application/vnd.github+json', '/orgs/foo/dependabot_alerts/enable_all']

    class MockSubprocess():
        def __init__(self, stdout):
            self.stdout = stdout

    def test_parse_alerts(self):

        self.assertListEqual(dependabot.parse_alerts('test', self.graphql_alerts), self.parsed_alerts)

    @patch("sys.stdout", new_callable=StringIO)
    def test_generate_csv(self, fake_stdout):
        fake_open = mock_open()
        with patch("builtins.open", fake_open, create=True):
            dependabot.generate_csv(self.parsed_alerts, 'sample.csv')

        fake_open.assert_called_with('sample.csv', 'w', newline='')
        fake_open.return_value.write.assert_has_calls([call(self.csv_header_values), call(self.csv_row_values)])

        dependabot.generate_csv(self.parsed_alerts, None)
        self.assertEqual(fake_stdout.getvalue(), self.csv_header_values + self.csv_row_values)

    @patch("click.echo")
    @patch("gh_dependabot.call_gh_api")
    @patch("gh_dependabot.parse_alerts")
    def test_get_dependabot_alerts(self, fake_parse_alerts, fake_call_gh_api, fake_echo):
        non_paginated_result = str(b'{"data":{"repository":{"name":"ghas-bootcamp","vulnerabilityAlerts":{"pageInfo":{"hasNextPage":false,"endCursor":"Y3Vyc29yOnYyOpHOr2XWzA=="},"totalCount":1,"nodes":[{"id":"RVA_kwDOHzNV0M6pkdQi","securityAdvisory":{"ghsaId":"GHSA-6528-wvf6-f6qg","permalink":"https://github.com/advisories/GHSA-6528-wvf6-f6qg","severity":"HIGH","description":"This so bad","summary":"Pycrypto generates weak key parameters"},"securityVulnerability":{"package":{"name":"pycrypto","ecosystem":"PIP"},"vulnerableVersionRange":"<= 2.6.1"},"createdAt":"2022-08-10T18:44:52Z","state":"OPEN","fixedAt":null,"fixReason":null,"dismissedAt":null,"dismissReason":null,"dismisser":null,"vulnerableManifestPath":"authn-service/requirements.txt","vulnerableRequirements":"= 2.6.1"}]}}}}', 'UTF-8')
        fake_call_gh_api.return_value = ('200', [], non_paginated_result)
        fake_parse_alerts.return_value = self.parsed_alerts
        result = dependabot.get_dependabot_alerts('github/foo')
        fake_parse_alerts.assert_called_once()
        fake_call_gh_api.assert_called_once()
        self.assertListEqual(result, self.parsed_alerts)

        fake_call_gh_api.return_value = ('404', [], 'Something broke')
        self.assertFalse(dependabot.get_dependabot_alerts('github/foo'))
        fake_echo.assert_called()

        fake_parse_alerts.reset_mock()
        paginated_result = str(b'{"data":{"repository":{"name":"ghas-bootcamp","vulnerabilityAlerts":{"pageInfo":{"hasNextPage":true,"endCursor":"Y3Vyc29yOnYyOpHOr2XWzA=="},"totalCount":1,"nodes":[{"id":"RVA_kwDOHzNV0M6pkdQi","securityAdvisory":{"ghsaId":"GHSA-6528-wvf6-f6qg","permalink":"https://github.com/advisories/GHSA-6528-wvf6-f6qg","severity":"HIGH","description":"This so bad","summary":"Pycrypto generates weak key parameters"},"securityVulnerability":{"package":{"name":"pycrypto","ecosystem":"PIP"},"vulnerableVersionRange":"<= 2.6.1"},"createdAt":"2022-08-10T18:44:52Z","state":"OPEN","fixedAt":null,"fixReason":null,"dismissedAt":null,"dismissReason":null,"dismisser":null,"vulnerableManifestPath":"authn-service/requirements.txt","vulnerableRequirements":"= 2.6.1"}]}}}}', 'UTF-8')
        fake_call_gh_api.side_effect = [('200', [], paginated_result), ('200', [], non_paginated_result)]
        fake_parse_alerts.return_value = self.parsed_alerts
        result = dependabot.get_dependabot_alerts('github/foo')
        self.assertListEqual(result, self.parsed_alerts + self.parsed_alerts)

    @patch("gh_dependabot.generate_csv")
    @patch("gh_dependabot.get_dependabot_alerts")
    def test_export(self, fake_get_dependabot_alerts, fake_generate_csv):
        fake_get_dependabot_alerts.return_value=[]
        runner = CliRunner()
        result = runner.invoke(dependabot.export, '-o test.csv github/foo'.split())
        # dependabot.export('github/foo', 'test.csv')
        self.assertEqual(0, result.exit_code)
        fake_get_dependabot_alerts.assert_called_once_with('github/foo')
        fake_generate_csv.assert_called_once_with([], 'test.csv')

        fake_get_dependabot_alerts.reset_mock()
        fake_get_dependabot_alerts.side_effect = [['first,repo,results'], ['second,repo,results']]
        fake_generate_csv.reset_mock()
        result = runner.invoke(dependabot.export, '-o test.csv github/foo github/bar'.split())
        self.assertEqual(0, result.exit_code)
        fake_get_dependabot_alerts.assert_has_calls([call('github/foo'), call('github/bar')])
        fake_generate_csv.assert_called_once_with(['first,repo,results', 'second,repo,results'], 'test.csv')

    def test_parse_api_output(self):
        expected_success_result = ('204', self.dependabot_enable_parsed_headers, '')
        result = dependabot.parse_api_output(self.dependabot_enable_success_output)
        self.assertTupleEqual(expected_success_result, result)

        expected_fail_result = ('404', self.dependabot_enable_parsed_headers, '{"message":"Not Found","documentation_url":"https://docs.github.com/rest"}')
        result = dependabot.parse_api_output(self.dependabot_enable_error_output)
        self.assertTupleEqual(expected_fail_result, result)

    @patch("shutil.which")
    @patch("time.sleep")
    @patch("click.echo")
    @patch("gh_dependabot.parse_api_output")
    @patch("subprocess.run")
    def test_call_gh_api(self, fake_subprocess_run, fake_parse_api_output, fake_echo, fake_sleep, fake_which):
        fake_which.return_value = '/opt/homebrew/bin/gh'
        fake_subprocess_run.return_value = self.MockSubprocess(self.dependabot_enable_success_output)
        fake_parse_api_output.return_value = self.dependabot_enable_success_parsed_output
        result = dependabot.call_gh_api(self.dependabot_repo_enable_command)
        self.assertTupleEqual(result, self.dependabot_enable_success_parsed_output)
        fake_subprocess_run.assert_called_once_with(self.dependabot_repo_enable_full_command, text=True, capture_output=True, check=True)
        fake_parse_api_output.assert_called_once_with(self.dependabot_enable_success_output)

        fake_subprocess_run.reset_mock()
        fake_parse_api_output.reset_mock()
        result = dependabot.call_gh_api(self.dependabot_org_enable_command)
        self.assertTupleEqual(result, self.dependabot_enable_success_parsed_output)
        fake_subprocess_run.assert_called_once_with(self.dependabot_org_enable_full_command, text=True, capture_output=True, check=True)
        fake_parse_api_output.assert_called_once_with(self.dependabot_enable_success_output)

        fake_parse_api_output.reset_mock()
        current_time = int(time.time())
        patched_headers = self.dependabot_enable_parsed_headers.copy()
        patched_headers['X-Ratelimit-Reset'] = current_time + 10
        patched_headers['X-Ratelimit-Remaining'] = '0'
        fake_api_primary_rate_limit_parsed_output = ('403', patched_headers, '{"message":"API rate limit exceeded for xxx.xxx.xxx.xxx.","documentation_url":"https://docs.github.com/rest/overview/resources-in-the-rest-api#rate-limiting"}')
        fake_parse_api_output.side_effect = [fake_api_primary_rate_limit_parsed_output, self.dependabot_enable_success_parsed_output ]
        result = dependabot.call_gh_api(self.dependabot_repo_enable_command)
        self.assertTupleEqual(result, self.dependabot_enable_success_parsed_output)
        fake_sleep.assert_called_once_with(14)
        fake_echo.assert_called_once_with('GitHub primary rate limit hit. Sleeping for 14 seconds')

        fake_parse_api_output.reset_mock()
        fake_sleep.reset_mock()
        fake_echo.reset_mock()
        current_time = int(time.time())
        patched_headers = self.dependabot_enable_parsed_headers.copy()
        patched_headers['Retry-After'] = '5'
        secondary_rate_limit_body = '{"message":"You have exceeded a secondary rate limit and have been temporarily blocked from content creation. Please retry your request again later.","documentation_url":"https://docs.github.com/rest/overview/resources-in-the-rest-api#secondary-rate-limiting"}'
        fake_api_secondary_api_rate_limit_parsed_output = ('403', patched_headers, secondary_rate_limit_body)
        fake_parse_api_output.side_effect = [fake_api_secondary_api_rate_limit_parsed_output, self.dependabot_enable_success_parsed_output ]
        result = dependabot.call_gh_api(self.dependabot_repo_enable_command)
        self.assertTupleEqual(result, self.dependabot_enable_success_parsed_output)
        fake_parse_api_output.assert_called_with(self.dependabot_enable_success_output)
        fake_sleep.assert_called_once_with(10)
        fake_echo.assert_called_once_with('GitHub secondary rate limit hit. Sleeping for 10 seconds')

        fake_parse_api_output.reset_mock()
        fake_sleep.reset_mock()
        fake_echo.reset_mock()
        fake_api_secondary_api_rate_limit_parsed_output = ('403', self.dependabot_enable_parsed_headers, secondary_rate_limit_body)
        fake_parse_api_output.side_effect = [fake_api_secondary_api_rate_limit_parsed_output, self.dependabot_enable_success_parsed_output ]
        result = dependabot.call_gh_api(self.dependabot_repo_enable_command)
        self.assertTupleEqual(result, self.dependabot_enable_success_parsed_output)
        fake_parse_api_output.assert_called_with(self.dependabot_enable_success_output)
        fake_sleep.assert_called_once_with(60)
        fake_echo.assert_called_once_with('GitHub secondary rate limit hit. Sleeping for 60 seconds')

    @patch("click.echo")
    @patch("gh_dependabot.call_gh_api")
    def test_enable_feature(self, fake_call_gh_api, fake_echo):
        fake_call_gh_api.return_value = self.dependabot_enable_success_parsed_output
        self.assertTrue(dependabot.enable_feature('foo/bar', False, 'alerts'))
        fake_call_gh_api.assert_called_once_with(self.dependabot_repo_enable_command)

        fake_call_gh_api.reset_mock()
        fake_call_gh_api.return_value = self.dependabot_enable_success_parsed_output
        self.assertTrue(dependabot.enable_feature('foo', True, 'alerts'))
        fake_call_gh_api.assert_called_once_with(self.dependabot_org_enable_command)

        fake_call_gh_api.reset_mock()
        fake_api_error_parsed_output = ('404', self.dependabot_enable_parsed_headers, '{"message":"Not Found","documentation_url":"https://docs.github.com/rest/overview"}')
        fake_call_gh_api.return_value = fake_api_error_parsed_output
        self.assertFalse(dependabot.enable_feature('foo/bar', False, 'alerts'))
        fake_echo.assert_called()

    @patch("click.echo")
    @patch("gh_dependabot.print_result")
    @patch("gh_dependabot.enable_feature")
    def test_enable(self, fake_enable_feature, fake_print_result, fake_echo):
        fake_enable_feature.side_effect = [True, False]
        runner = CliRunner()
        runner.invoke(dependabot.enable, '-a github/foo github/bar'.split())
        fake_echo.assert_has_calls([call('Enabling dependabot alerts for github/foo'), call('Enabling dependabot alerts for github/bar')])
        fake_print_result.assert_has_calls([call('alerts', ['github/foo'], 'repositories', True), call('alerts', ['github/bar'], 'repositories', False)])

        fake_echo.reset_mock()
        fake_print_result.reset_mock()
        fake_enable_feature.reset_mock()
        fake_enable_feature.side_effect = [True, False]
        runner.invoke(dependabot.enable, '-s github/foo github/bar'.split())
        fake_echo.assert_has_calls([call('Enabling dependabot security updates for github/foo'), call('Enabling dependabot security updates for github/bar')])
        fake_print_result.assert_has_calls([call('security updates', ['github/foo'], 'repositories', True), call('security updates', ['github/bar'], 'repositories', False)])

    @patch("click.echo")
    def test_print_result(self, fake_echo):
        dependabot.print_result('alerts', ['github/foo'], 'repositories', True)
        fake_echo.assert_has_calls([call('Successfully enabled dependabot alerts for 1 repositories'), call('List of successfully enabled repositories:'),call('github/foo')])

        fake_echo.reset_mock()
        dependabot.print_result('alerts', ['github/bar'], 'repositories', False)
        fake_echo.assert_has_calls([call('Unable to enable dependabot alerts for 1 repositories'), call('List of unsuccessful repositories:'), call('github/bar')])

if __name__ == '__main__':
    unittest.main()
