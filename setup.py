from setuptools import setup

# Is not properly included in build atm
DATA_FILES = ['logo.ico']

setup(
    name='YoutubePlaylistTool',
    version='1.4.1',
    #package_dir= {''},
    #packages=[''],
    data_files=DATA_FILES,
    install_requires=['PySimpleGUI', 'tinydb', 'youtube_dl', 'pyperclip', 'gspread', 'oauth2client'],
    py_modules=['YPT'],
    url='https://github.com/CuriousCod/YoutubePlaylistTool',
    license='',
    author='CuriousCod',
    author_email='',
    description='Create, manage and play Youtube playlists using URLs'
)
