
import pytest

from covis_db import hosts

# These basenames are in the test data set
good_dmas = ["DMAS", "dmas"]
good_covis_nas = ["COVIS-NAS", "covis-nas"]
good_old_nas = ["OLD-COVIS-NAS1", 'old-covis-nas6']

good_hostnames = good_dmas + good_covis_nas + good_old_nas

# These basenames are valid but not in the test data set
bad_hostnames = ["foobar"]


def test_validate_host():

    for hn in good_hostnames:
        assert hosts.validate_host(hn)

    for hn in bad_hostnames:
        assert hosts.validate_host(hn) == False


def test_individual_checks():

    for hn in good_dmas:
        assert hosts.is_dmas(hn)

    for hn in good_old_nas:
        assert hosts.is_old_nas(hn)

    for hn in good_covis_nas:
        assert hosts.is_nas(hn)

    for hn in bad_hostnames + good_covis_nas + good_old_nas:
        assert hosts.is_dmas(hn) == False
