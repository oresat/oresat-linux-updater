Daemon
======

A backend service for updating the Linux board using deb packages and bash 
scripts. It is mostly a D-Bus server with a update file cache, that can run 
update files from the Update Maker.

Basics:

- Giving the daemon update file will **not** trigger an update, only when the
  Update D-Bus method is called will an update start.
- The daemon can also generate status file that can be used to make future
  updates and to know what is install on the board.
- If a update fails the update file cache will be clear as it is assume all 
  future updates require older updates.

To start the daemon, if the Debian package is installed.

.. code-block:: bash

   $ sudo systemctl start oresat-linux-updaterd

State Machine
-------------

If the board is powerred off when the Updater is updating, it will try resume
the update next time the daemon is started.

.. image:: images/UpdaterStateMachine.jpg

.. autoclass:: oresat_linux_updater.daemon.State
   :members:
   :member-order: bysource
   :noindex:

D-Bus API
---------

.. autoclass:: oresat_linux_updater.daemon.Daemon
   :members:
   :exclude-members: start, quit
   :noindex:
