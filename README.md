JViewer
=======

![main_window](screenshot.png)

Simple jviewer app, supports power off  and iKVM.

Tested on s2400sc BMC.

Example (no params):
`python3 jviewer-starter.py`

Example (with params):
`jviewer-starter.py --server 192.168.0.13 --user user --password pass`

Does not require any additional libraries, except installed Java and Python with tk.

Tested on Windows 10 and ArchLinux with latest openJDK.

NOTE: To use ISO mount, consider using Linux.
