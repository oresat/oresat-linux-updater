from updater import Updater


class DbusAdaptor(object):
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
        self._updater = Updater()


    # -------------------------------------------------------------------------
    # dbus properties


    @property
    def CurrentState(self):
        return self._updater.current_state


    @property
    def CurrentArchiveFile(self):
        return self._updater.current_archive_file


    @property
    def AvailableArchiveFiles(self):
        return self._updater.available_archive_files


    # -------------------------------------------------------------------------
    # dbus methods


    def AddArchiveFile(self, file_path):
        # (str) -> bool
        """ copies file into self.cache_dir """
        return self._updater.add_archive_file(file_path)


    def StartUpdate(self):
        # () -> bool
        """ Start updaing if in sleep state """
        return self._updater.change_state("update")


    def GetPackageListFile(self):
        """ To stop updaing """
        # () -> bool
        return self._updater.get_pkg_installed_file()


    # -------------------------------------------------------------------------
    # signals
