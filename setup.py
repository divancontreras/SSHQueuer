import cx_Freeze
import os
from cx_Freeze import setup, Executable

base = None

os.environ['TK_LIBRARY'] = r"C:\Users\sesa467855\AppData\Local\Programs\Python\Python36-32\tcl\tk8.6"
os.environ['TCL_LIBRARY'] = r"C:\Users\sesa467855\AppData\Local\Programs\Python\Python36-32\tcl\tcl8.6"

executables = [Executable("main.py", base="Win32GUI")]
includefiles = ['resources', 'listbox.py', "main.py", 'session.py', 'window.py', 'object.pickle', 'auxiliary_classes.py']

packages = ["tkinter", "time", "shutil", "threading","base64", "paramiko",
            "datetime", "pickle", "operator", "os"]
options = {
    'build_exe': {
        'packages':packages,
        'include_files': includefiles,
    },

}

setup(
    name = "SimQ",
    options = options,
    version = "1.0",
    description = 'Simulation Queuer.',
    executables = executables,
)
