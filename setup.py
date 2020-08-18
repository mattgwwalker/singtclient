from setuptools import setup, find_packages

setup(name='singtclient',
      version='0.12.5',
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
