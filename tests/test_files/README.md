# Test Files

## Update Contents

- **test-package1_0.1.0-0_all.deb** - A basic deb package (install a txt file)
with no dependencies
- **test-package2_0.1.0-0_all.deb** -  Another basic deb package (install a
different txt file) that depends on test-package1
- **test-script.sh** - A bash script used in test update tar files.

## instructions.txt test files

- **instructions1.txt** -  Valid instructions file
- **instructions2.txt** - Invalid instruction dict
- **instructions3.txt** - Invalid instruction type
- **instructions4.txt** - Incomplete JSON
- **instructions5.txt** - Invalid JSON

## Valid Updates

- **test_update_2021-01-01-00-00-00.tar.xz** - Installs test-package1 and
test-package2 then run a bash script.
- **test_update_2021-01-01-01-01-01.tar.xz** - Removes test-package2 and
test-package1.

## Invalid Updates

- **test_update_2021-01-01-02-02-02.tar.xz** - invalid .tar.xz file
- **test_update_2021-01-01-03-03-03.tar.xz** - missing instructions.txt in tar
- **test_update_2021-01-01-04-04-04.tar.xz** - missing .deb file in tar
- **test_update_2021-01-01-05-05-05.tar.xz** - missing script in tar
- **test_update_2021-01-01-06-06-06.tar.xz** - invalid JSON contexts from
instructions.txt
- **test_update_2021-01-01-07-07-07.tar.xz** - invalid instructions.txt format
(not a JSON)
- **test_update.tar.xz** - invalid filename format

## dpkg status file

- **test_dpkg-status_2020-01-24-00-02-57.txt**
