from .linux_updater import LinuxUpdater


class DbusAdapter(object):
    """
    The dbus wrapper for the Linux updater. Dbus server.
    """

    dbus = """
    <node>
        <interface name="org.OreSat.LinuxUpdater">
            <method name='AddArchiveFile'>
                <arg type='s' name='file_path' direction='in'/>
                <arg type='b' name='output' direction='out'/>
            </method>
            <method name='StartUpdate'>
                <arg type='b' name='output' direction='out'/>
            </method>
            <method name='ForceUpdate'>
                <arg type='s' name='file_path' direction='in'/>
                <arg type='b' name='output' direction='out'/>
            </method>
            <method name='GetAptListOutput'>
                <arg type='b' name='output' direction='out'/>
            </method>
            <property name="CurrentState" type="d" access="read">
                <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
            </property>
            <property name="CurrentArchiveFile" type="s" access="read">
                <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
            </property>
            <property name="AvailableArchiveFiles" type="d" access="read">
                <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
            </property>
        </interface>
    </node>
    """ # this wont work in init()


    # -------------------------------------------------------------------------
    # non-dbus methods


    def __init__(self):
        self._updater = LinuxUpdater()


    # -------------------------------------------------------------------------
    # dbus properties


    @property
    def CurrentState(self):
        """
        Retuns the current state.
        """
        return self._updater.current_state


    @property
    def CurrentArchiveFile(self):
        """
        Retuns the current archvice filename being installed.
        """
        return self._updater.current_archive_file


    @property
    def AvailableArchiveFiles(self):
        """
        Retuns the current archvice files available to run.
        """
        return self._updater.available_archive_files


    # -------------------------------------------------------------------------
    # dbus methods


    def AddArchiveFile(self, file_path):
        # (str) -> bool
        """
        Adds file to archive file cache.

        Parameters
        ----------
        file_path : str
            Absolute path to archive file to add to cache.

        Returns
        -------
        bool
            True if file was added or False on failure.
        """
        return self._updater.add_archive_file(file_path)


    def StartUpdate(self):
        # () -> bool
        """
        Load the oldest archive file in cache and runs update.

        Returns
        -------
        bool
            True if updated worked or False on failure.
        """
        return self._updater.change_state("update")


    def GetPackageListFile(self):
        # () -> str
        """
        To get a file with a list of all the files installed.

        Returns
        -------
        str
            Absolute filepath to file with the list of installed packages.
        """
        return self._updater.get_pkg_installed_file()


    # -------------------------------------------------------------------------
    # signals

