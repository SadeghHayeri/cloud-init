"""Tests for `cloud-init status`"""
from textwrap import dedent

import pytest

from tests.integration_tests.instances import IntegrationInstance
from tests.integration_tests.util import verify_clean_log

USER_DATA = """\
#cloud-config
apt_update: false
apt_upgrade: false
apt_reboot_if_required: false
"""


@pytest.mark.user_data(USER_DATA)
class TestSchemaDeprecations:
    def test_clean_log(self, class_client: IntegrationInstance):
        log = class_client.read_from_file("/var/log/cloud-init.log")
        verify_clean_log(log, ignore_deprecations=True)
        assert "WARNING]: Deprecated cloud-config provided:" in log
        assert "apt_reboot_if_required: DEPRECATED." in log
        assert "apt_update: DEPRECATED." in log
        assert "apt_upgrade: DEPRECATED." in log

    def test_schema_deprecations(self, class_client: IntegrationInstance):
        """Test schema behavior with deprecated configs."""
        user_data_fn = "/root/user-data"
        class_client.write_to_file(user_data_fn, USER_DATA)

        result = class_client.execute(
            f"cloud-init schema --config-file {user_data_fn}"
        )
        assert (
            result.ok
        ), "`schema` cmd must return 0 even with deprecated configs"
        assert not result.stderr
        assert "Cloud config schema deprecations:" in result.stdout
        assert "apt_update: DEPRECATED" in result.stdout
        assert "apt_upgrade: DEPRECATED" in result.stdout
        assert "apt_reboot_if_required: DEPRECATED" in result.stdout

        annotated_result = class_client.execute(
            f"cloud-init schema --annotate --config-file {user_data_fn}"
        )
        assert (
            annotated_result.ok
        ), "`schema` cmd must return 0 even with deprecated configs"
        assert not annotated_result.stderr
        expected_output = dedent(
            """\
            #cloud-config
            apt_update: false\t\t# D1
            apt_upgrade: false\t\t# D2
            apt_reboot_if_required: false\t\t# D3

            # Deprecations: -------------
            # D1: DEPRECATED. Dropped after April 2027. Use ``package_update``. Default: ``false``
            # D2: DEPRECATED. Dropped after April 2027. Use ``package_upgrade``. Default: ``false``
            # D3: DEPRECATED. Dropped after April 2027. Use ``package_reboot_if_required``. Default: ``false``


            Valid cloud-config: /root/user-data"""  # noqa: E501
        )
        assert expected_output in annotated_result.stdout
