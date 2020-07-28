from setuptools import setup, find_packages

setup(name='singtclient',
      version='0.5.4',
      packages=["singtclient"],
      include_package_data=True,
      install_requires=[
          "art",
          "numpy",
          "pyogg",
          "singtcommon",
          "sounddevice",
          "twisted",
      ]
)
