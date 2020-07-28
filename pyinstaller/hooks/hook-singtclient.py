#from PyInstaller.utils.hooks import copy_metadata

#datas = copy_metadata("singtclient")

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("singtclient")
