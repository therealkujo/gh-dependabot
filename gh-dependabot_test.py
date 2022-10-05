#!/usr/bin/env python3

import unittest
import importlib.util
import importlib.machinery
import os
import sys
import subprocess
from unittest.mock import call, mock_open, patch
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
                                "vulnerableVersionRange": "<= 2.6.1"
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
                            'state': 'OPEN',
                            'summary': 'Pycrypto generates weak key parameters',
                            'vulnerable_versions': '<= 2.6.1'
                        }
                    ]
    csv_header_values = 'advisory_permalink,created_at,description,dismiss_reason,dismissed_at,dismissed_by,fix_reason,fixed_at,id,manifest_filepath,package_ecosystem,package_name,package_version,repo,severity,state,summary,vulnerable_versions\r\n'
    csv_row_values = 'https://github.com/advisories/GHSA-6528-wvf6-f6qg,2022-08-10T18:44:52Z,Its really dangerous ok,,,,,,RVA_kwDOHzNV0M6pkdQi,authn-service/requirements.txt,PIP,pycrypto,= 2.6.1,test,HIGH,OPEN,Pycrypto generates weak key parameters,<= 2.6.1\r\n'
    mock_gh_query = ['/opt/homebrew/bin/gh', 'api', 'graphql', '-F', 'org=github', '-F', 'repo=foo', '-F', 'cursor=null', '-f', 'query=\n    query ($org: String! $repo: String! $cursor: String){\n      repository(owner: $org name: $repo) {\n        name\n        vulnerabilityAlerts(first: 100 after: $cursor) {\n          pageInfo {\n            hasNextPage\n            endCursor\n          }\n          totalCount\n          nodes {\n            id\n            securityAdvisory {\n              ...advFields\n            }\n            securityVulnerability {\n              package {\n                ...pkgFields\n              }\n              vulnerableVersionRange\n            }\n            createdAt\n            state\n            fixedAt\n            fixReason\n            dismissedAt\n            dismissReason\n            dismisser {\n                login\n            }\n            vulnerableManifestPath\n            vulnerableRequirements\n          }\n        }\n      }\n    }\n    fragment advFields on SecurityAdvisory {\n      ghsaId\n      permalink\n      severity\n      description\n      summary\n    }\n    fragment pkgFields on SecurityAdvisoryPackage {\n      name\n      ecosystem\n    }\n    ']
    mock_gh_paginated_query = ['/opt/homebrew/bin/gh', 'api', 'graphql', '-F', 'org=github', '-F', 'repo=foo', '-F', 'cursor=Y3Vyc29yOnYyOpHOr2XWzA==', '-f', 'query=\n    query ($org: String! $repo: String! $cursor: String){\n      repository(owner: $org name: $repo) {\n        name\n        vulnerabilityAlerts(first: 100 after: $cursor) {\n          pageInfo {\n            hasNextPage\n            endCursor\n          }\n          totalCount\n          nodes {\n            id\n            securityAdvisory {\n              ...advFields\n            }\n            securityVulnerability {\n              package {\n                ...pkgFields\n              }\n              vulnerableVersionRange\n            }\n            createdAt\n            state\n            fixedAt\n            fixReason\n            dismissedAt\n            dismissReason\n            dismisser {\n                login\n            }\n            vulnerableManifestPath\n            vulnerableRequirements\n          }\n        }\n      }\n    }\n    fragment advFields on SecurityAdvisory {\n      ghsaId\n      permalink\n      severity\n      description\n      summary\n    }\n    fragment pkgFields on SecurityAdvisoryPackage {\n      name\n      ecosystem\n    }\n    ']

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

    @patch("gh_dependabot.parse_alerts")
    @patch("subprocess.run")
    def test_get_dependabot_alerts(self, fake_subprocess_run, fake_parse_alerts):
        non_paginated_result = str(b'{"data":{"repository":{"name":"ghas-bootcamp","vulnerabilityAlerts":{"pageInfo":{"hasNextPage":false,"endCursor":"Y3Vyc29yOnYyOpHOr2XWzA=="},"totalCount":1,"nodes":[{"id":"RVA_kwDOHzNV0M6pkdQi","securityAdvisory":{"ghsaId":"GHSA-6528-wvf6-f6qg","permalink":"https://github.com/advisories/GHSA-6528-wvf6-f6qg","severity":"HIGH","description":"This so bad","summary":"Pycrypto generates weak key parameters"},"securityVulnerability":{"package":{"name":"pycrypto","ecosystem":"PIP"},"vulnerableVersionRange":"<= 2.6.1"},"createdAt":"2022-08-10T18:44:52Z","state":"OPEN","fixedAt":null,"fixReason":null,"dismissedAt":null,"dismissReason":null,"dismisser":null,"vulnerableManifestPath":"authn-service/requirements.txt","vulnerableRequirements":"= 2.6.1"}]}}}}', 'UTF-8')
        fake_non_paginated_results = self.MockSubprocess(non_paginated_result)
        fake_subprocess_run.return_value = fake_non_paginated_results
        dependabot.get_dependabot_alerts('github/foo')
        
        fake_subprocess_run.assert_called_once_with(self.mock_gh_query, text=True, capture_output=True, check=True)
        fake_parse_alerts.assert_called_once()
        
        fake_subprocess_run.reset_mock()
        paginated_result = str(b'{"data":{"repository":{"name":"ghas-bootcamp","vulnerabilityAlerts":{"pageInfo":{"hasNextPage":true,"endCursor":"Y3Vyc29yOnYyOpHOr2XWzA=="},"totalCount":1,"nodes":[{"id":"RVA_kwDOHzNV0M6pkdQi","securityAdvisory":{"ghsaId":"GHSA-6528-wvf6-f6qg","permalink":"https://github.com/advisories/GHSA-6528-wvf6-f6qg","severity":"HIGH","description":"This so bad","summary":"Pycrypto generates weak key parameters"},"securityVulnerability":{"package":{"name":"pycrypto","ecosystem":"PIP"},"vulnerableVersionRange":"<= 2.6.1"},"createdAt":"2022-08-10T18:44:52Z","state":"OPEN","fixedAt":null,"fixReason":null,"dismissedAt":null,"dismissReason":null,"dismisser":null,"vulnerableManifestPath":"authn-service/requirements.txt","vulnerableRequirements":"= 2.6.1"}]}}}}', 'UTF-8')
        fake_paginated_result = self.MockSubprocess(paginated_result)
        fake_subprocess_run.side_effect = [fake_paginated_result, fake_non_paginated_results]
        dependabot.get_dependabot_alerts('github/foo')
        fake_subprocess_run.assert_has_calls([call(self.mock_gh_paginated_query, text=True, capture_output=True, check=True), call(self.mock_gh_query, text=True, capture_output=True, check=True)], any_order=True)

        fake_subprocess_run.reset_mock()
        fake_subprocess_run.return_value = subprocess.CalledProcessError(1, 'something broke')
        self.assertRaises(subprocess.CalledProcessError)

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

if __name__ == '__main__':
    unittest.main()
