from setuptools import setup

setup(name='singtclient',
      version='0.6.0',
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
