from oresat_updaterd.linux_updater import LinuxUpdater


linux_updater = LinuxUpdater()

print(linux_updater.get_pkg_list_file())
