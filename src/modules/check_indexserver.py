# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
This module is used to check if SAP HANA indexserver is configured.
"""

import logging
from ansible.module_utils.basic import AnsibleModule

try:
    from ansible.module_utils.sap_automation_qa import SapAutomationQA, TestStatus
except ImportError:
    from src.module_utils.sap_automation_qa import SapAutomationQA, TestStatus


class IndexServerCheck(SapAutomationQA):
    """
    This class is used to check if SAP HANA indexserver is configured.

    :param database_sid: SAP HANA database SID.
    :type database_sid: str
    :param os_distribution: Operating system distribution.
    :type os_distribution: str
    """

    def __init__(self, database_sid: str, os_distribution: str):
        super().__init__()
        self.database_sid = database_sid
        self.os_distribution = os_distribution

    def check_indexserver(self) -> None:
        """
        Checks if the indexserver is configured.
        """
        expected_properties = {
            "redhat": [
                {
                    "[ha_dr_provider_chksrv]": {
                        "provider": "ChkSrv",
                        "path": "/usr/share/SAPHanaSR/srHook",
                    }
                },
                {
                    "[ha_dr_provider_chksrv]": {
                        "provider": "ChkSrv",
                        "path": "/hana/shared/myHooks",
                    }
                },
            ],
            "suse": {
                "[ha_dr_provider_suschksrv]": {
                    "provider": "susChkSrv",
                    "path": "/usr/share/SAPHanaSR",
                }
            },
        }

        os_props_list = expected_properties.get(self.os_distribution)
        if not os_props_list:
            self.result.update(
                {
                    "status": TestStatus.ERROR.value,
                    "message": f"Unsupported OS distribution: {self.os_distribution}",
                    "details": {},
                    "indexserver_enabled": "no",
                }
            )
            return

        global_ini_path = f"/usr/sap/{self.database_sid}/SYS/global/hdb/custom/config/global.ini"
        global_ini = []
        try:
            with open(global_ini_path, "r", encoding="utf-8") as file:
                global_ini = [line.strip() for line in file.readlines()]

            self.log(
                logging.INFO,
                f"Successfully read the global.ini file: {global_ini}",
            )

            for os_props in os_props_list if isinstance(os_props_list, list) else [os_props_list]:
                section_title = list(os_props.keys())[0]
                if section_title in global_ini:
                    section_start = global_ini.index(section_title)
                    properties_slice = global_ini[section_start + 1 : section_start + 4]

                    self.log(
                        logging.INFO,
                        f"Extracted properties: {properties_slice}",
                    )

                    extracted_properties = {
                        prop.split("=")[0].strip(): prop.split("=")[1].strip()
                        for prop in properties_slice
                    }

                    if all(
                        extracted_properties.get(key) == value
                        for key, value in os_props[section_title].items()
                    ):
                        self.result.update(
                            {
                                "status": TestStatus.SUCCESS.value,
                                "message": "Indexserver is configured.",
                                "details": extracted_properties,
                                "indexserver_enabled": "yes",
                            }
                        )
                        return

            self.result.update(
                {
                    "status": TestStatus.ERROR.value,
                    "message": "Indexserver is not configured.",
                    "details": {},
                    "indexserver_enabled": "no",
                }
            )
        except Exception as e:
            self.result.update(
                {
                    "status": TestStatus.ERROR.value,
                    "message": f"Exception occurred while checking indexserver configuration: {e}",
                    "details": {},
                    "indexserver_enabled": "no",
                }
            )


def main():
    """
    Main function to check if SAP HANA indexserver is configured.
    """
    module = AnsibleModule(
        argument_spec=dict(
            database_sid=dict(type="str", required=True),
            ansible_os_family=dict(type="str", required=True),
        )
    )

    database_sid = module.params["database_sid"]
    os_distribution = module.params["ansible_os_family"]

    index_server_check = IndexServerCheck(database_sid, os_distribution)
    index_server_check.check_indexserver()

    module.exit_json(**index_server_check.get_result())


if __name__ == "__main__":
    main()
