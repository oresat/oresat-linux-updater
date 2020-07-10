import apt


class AptInterface():
    """
    Manges commication to apt using the python apt library.
    https://apt-team.pages.debian.net/python-apt/contents.html
    """

    def __int__(self):
        self._cache = apt.cache.Cache()


    def install(self, package_path):
        # (str) -> bool
        """
        Installs local deb package.

        Parameters
        ----------
        package_path : str
            Absoulte path to a deb package to install.

        Returns
        -------
        bool
            True if package was installed or False on failure..
        """

        for pkg in file_names:
            deb = apt.debfile.DebPackage(package_path)
            if not deb.check() or deb.install() != 0:
                return False

        return True


    def remove(self, package_name):
        # ([str]) -> bool
        """
        Removes a package.

        Parameters
        ----------
        package_names : str
            A package to remove.

        Returns
        -------
        bool
            True if all packages were removed or False on failure.
        """

        for pkg in package_names:
            package = self._cache[pkg_name]
            if package == None:
                return False

            package.mark_delete()

        self._cache.commit()
        return True


    def package_list(self):
        # () -> [str]
        """
        Make a list with all package currently installed.

        Returns
        -------
        [str]
            A list of file names.

        """

        self._apt_list = []
        for pkg in cache:
            if pkg.is_installed:
                self._apt_list.append(pkg.versions[0])

        return apt_list

