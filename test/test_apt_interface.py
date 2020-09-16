from oresat_updaterd import AptInterface


ai = AptInterface()


def test_pkg_list():
    """Test the apt pkg_list method"""
    try:
        apt_list = ai.package_list()
    except Exception:
        assert False

    if apt_list == "":
        assert False
    assert True


def test_install():
    """Test the apt install method"""
    try:
        ai.install("htop_2.2.0-1+b1_armhf.deb")
    except Exception:
        assert False
    assert True


def test_remove():
    """Test the apt remove method"""
    try:
        ai.remove("htop")
    except Exception:
        assert False
    assert True
