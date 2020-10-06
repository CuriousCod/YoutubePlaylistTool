from setuptools import setup

# Is not properly included in build atm
DATA_FILES = ['logo.ico']

setup(
    name='YoutubePlaylistTool',
    version='1.4',
    #package_dir= {''},
    #packages=[''],
    data_files=DATA_FILES,
    install_requires=['PySimpleGUI', 'tinydb', 'youtube_dl', 'pyperclip'],
    py_modules=['YPT'],
    url='https://github.com/CuriousCod/YoutubePlaylistTool',
    license='',
    author='KonaKona',
    author_email='',
    description='Create, manage and play Youtube playlists using URLs'
)
