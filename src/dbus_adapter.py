from .linux_updater import LinuxUpdater
from .daemon import Daemon


class State(Enum):
    """
    All states for linux updater daemon,
    do NOT uses auto() since we DO care about the values.
    """
    failed = 0
    SLEEP = 1
    PREUPDATE = 2
    UPDATE = 3
    REVERT = 4
    FORCE = 5


class LinuxUpdaterDaemon(object):
    """
    The daemon wrapper for the Linux updater. Includes a Dbus server and state
    machine.
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
    """


    # -------------------------------------------------------------------------
    # non-dbus methods


    def __init__(self):
        self._working_dir = "/tmp/oresat-linux-updater/"
        self._file_cache_dir = "/var/cache/oresat-linux-updater"

        self._updater = LinuxUpdater(self._working_dir)

        # setup archive file cache
        self._file_cache = FileCache(self._file_cache_dir)

        # figure out initial current state
        if os.path.isfile(self._working_dir + "instructions.txt"):
            # resume update
            _current_state = State.update
        elif len(os.listdir(self._working_dir)) != 0:
            # unknown files and no instructions.txt
            _current_state = State.failed
        else:
            # no files in working dir
            _current_state = State.sleep

        # thread set up and start thread
        self._lock = threading.Lock()
        self._working_thread = threading.Thread(target=self._working_loop, name="working-thread")
        self._working_thread.start()
        self._running = True


    def __del__(self):
        # stop thread
        self._running = False
        if self._working_thread.is_alive():
            self._working_thread.join()


    def _working_loop:
        # () -> bool
        while(self.__running):
            if self._current_state == State.failed or self._current_state == State.sleep:
                time.sleep(1)
            elif self.__state == State.pre_update:
                self._pre_update()
            elif self._current_state == State.update:
                self._update()
            else: # should not happen
                syslog.syslog(syslog.LOG_ERR, "current_state is set to an unknowned state.")
                self._lock.acquire()
                self._change_state = State.failed
                self._lock.release()


    # -------------------------------------------------------------------------
    # dbus properties


    @property
    def CurrentState(self):
        """
        Retuns the current state.
        """
        return self._current_state.value


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


    def Update(self):
        # () -> bool
        """
        Load the oldest archive file in cache and runs update.

        Returns
        -------
        bool
            True if updated worked or False on failure.
        """

        if self._current_state == State.sleep:
            ret = self._updater.update()

        return False


    def UpdateNow(self, file_path):
        # (str) -> bool
        """
        Immedantly tries to to update with archive file, bypasses cache.

        Parameters
        ----------
        file_path : str
            Absolute path to archive file to add to cache.

        Returns
        -------
        bool
            True if updated worked or False on failure.
        """
        return self._updater.update_now(file_path)


    def GetPackageListFile(self):
        # () -> str
        """
        To get a file with a list of all the files installed.

        Returns
        -------
        str
            Absolute filepath to file with the list of installed packages.
        """
        return self._updater.get_pkg_list_file()


    # -------------------------------------------------------------------------
    # signals

