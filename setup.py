from setuptools import setup, find_packages

setup(name='singtclient',
      version='0.10.5',
      packages=find_packages(), #["singtclient"],
      include_package_data=True,
      install_requires=[
          "art",
          "numpy",
          "pyogg",
          "scipy",
          "setuptools",
          "singtcommon",
          "sounddevice",
          "twisted",
      ]
)
