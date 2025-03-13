# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Unit tests for the log_parser module.
"""

import json
import pytest
from src.modules.log_parser import LogParser, PCMK_KEYWORDS, SYS_KEYWORDS, main


@pytest.fixture
def log_parser_redhat():
    """
    Fixture for creating a LogParser instance.

    :return: LogParser instance
    :rtype: LogParser
    """
    return LogParser(
        start_time="2025-01-01 00:00:00",
        end_time="2025-01-01 23:59:59",
        log_file="test_log_file.log",
        ansible_os_family="REDHAT",
    )


@pytest.fixture
def log_parser_suse():
    """
    Fixture for creating a LogParser instance.

    :return: LogParser instance
    :rtype: LogParser
    """
    return LogParser(
        start_time="2023-01-01 00:00:00",
        end_time="2023-01-01 23:59:59",
        log_file="test_log_file.log",
        ansible_os_family="SUSE",
    )


class TestLogParser:
    def test_parse_logs_success(self, mocker, log_parser_redhat):
        """
        Test the parse_logs method for successful log parsing.

        :param mocker: Mocker fixture for mocking functions.
        :type mocker: pytest_mock.MockerFixture
        :param log_parser_redhat: LogParser instance.
        :type log_parser_redhat: LogParser
        """
        mocker.patch(
            "builtins.open",
            mocker.mock_open(
                read_data="""Jan 01 23:17:30 nodename LogAction: Action performed
                    Jan 01 23:17:30 nodename SAPHana: SAP HANA action
                    Jan 01 23:17:30 nodename Some other log entry"""
            ),
        )

        log_parser_redhat.parse_logs()
        result = log_parser_redhat.get_result()
        expected_filtered_logs = [
            "Jan 01 23:17:30 nodename LogAction: Action performed",
            "Jan 01 23:17:30 nodename SAPHana: SAP HANA action",
        ]
        filtered_logs = [log.strip() for log in json.loads(result["filtered_logs"])]
        assert filtered_logs == expected_filtered_logs
        assert result["status"] == "PASSED"

    def test_parse_logs_failure(self, mocker, log_parser_suse):
        """
        Test the parse_logs method for failed log parsing.

        :param mocker: Mocker fixture for mocking functions.
        :type mocker: pytest_mock.MockerFixture
        :param log_parser_suse: LogParser instance.
        :type log_parser_suse: LogParser
        """
        mocker.patch(
            "builtins.open",
            side_effect=FileNotFoundError("File not found"),
        )

        log_parser_suse.parse_logs()
        result = log_parser_suse.get_result()
        assert result["filtered_logs"] == []

    def test_main(self, mocker):
        """
        Test the main function of the log_parser module.

        :param mocker: Mocker fixture for mocking functions.
        :type mocker: pytest_mock.MockerFixture
        """
        mock_ansible_module = mocker.patch("src.modules.log_parser.AnsibleModule")
        mock_ansible_module.return_value.params = {
            "start_time": "2023-01-01 00:00:00",
            "end_time": "2023-01-01 23:59:59",
            "log_file": "test_log_file.log",
            "ansible_os_family": "SUSE",
        }

        parser = LogParser(
            start_time="2023-01-01 00:00:00",
            end_time="2023-01-01 23:59:59",
            log_file="test_log_file.log",
            ansible_os_family="SUSE",
        )
        parser.parse_logs()

        result = parser.get_result()
        expected_result = {
            "start_time": "2023-01-01 00:00:00",
            "end_time": "2023-01-01 23:59:59",
            "log_file": "test_log_file.log",
            "keywords": list(PCMK_KEYWORDS | SYS_KEYWORDS),
            "filtered_logs": [],
            "error": "",
        }
        assert result["filtered_logs"] == expected_result["filtered_logs"]

    def test_main_redhat(self, monkeypatch):
        """
        Test the main function of the log_parser module for RedHat.

        :param monkeypatch: Monkeypatch fixture for mocking.
        :type monkeypatch: pytest.MonkeyPatch
        """
        mock_result = {}

        class MockAnsibleModule:
            def __init__(self, argument_spec, supports_check_mode):
                self.params = {
                    "start_time": "2023-01-01 00:00:00",
                    "end_time": "2023-01-01 23:59:59",
                    "log_file": "test_log_file.log",
                    "ansible_os_family": "REDHAT",
                }
                self.check_mode = False

            def exit_json(self, **kwargs):
                mock_result.update(kwargs)

        with monkeypatch.context() as m:
            m.setattr("src.modules.log_parser.AnsibleModule", MockAnsibleModule)
            main()
            assert mock_result["status"] == "FAILED"
