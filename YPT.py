import PySimpleGUI as sg
from tinydb import TinyDB, Query
import youtube_dl
from tinydb.operations import set as Set
import re, time, random, os, sys, webbrowser, subprocess, textwrap, datetime, configparser, atexit
from collections import OrderedDict
from operator import getitem
from enum import Enum
import pyperclip
import gspread
from oauth2client.service_account import ServiceAccountCredentials


# DONE Add total video count -> Printed when pressing copy
# DONE Support for multiple db
# DONE Display current random seed
# DONE File open exception handling
# DONE Config.ini for default playlist
# DONE Add confirmation to video delete
# DONE Add recent playlists feature
# DONE youtu.be links
# DONE Tagging -> Added filter for uploader, tagging is probably not necessary
# DONE Reorder playlist
# DONE Fix reordering bugs: Behavior during filtering
# TODO Switch copy order buttons to display the list in random or default order -> Basically sort options
# DONE What to do with deleted video order numbers -> Reorder
# DONE Source file grabbing with Chrome, makes last line garbage -> Culture
# TODO More dynamic playlist filepath -> partially done, creating new playlist doesn't allow different directory
# TODO Sort by name -> Could work as a radio button in menu -> Same as the other todo entry
# DONE Workaround for the command line is too long error -> .bat file
# TODO See if audio levels can be normalized -> No easy way to do this
# DONE db in google sheets
# TODO Option to choose what workbook to use
# TODO Option to close previous player, when sending a new play command

class WindowTypes(Enum):
    LINK_WINDOW = 1
    DOWNLOAD_WINDOW = 2

class ProcessAction(Enum):
    PROCESS_EXISTS = 1
    KILL_PROCESS = 2

def RemoveExtension(filename: str) -> str:
    return os.path.splitext(filename)[0]


def extractVideos():
    text = pyperclip.paste()
    print(text.find('\"playlist\":'))
    print(text.rfind('\"playlistEditEndpoint\"'))

    # Find start and end of playlist videos from the source code
    if text.rfind('\"toggledAccessibilityData\"') == -1:
        text = text[text.find('\"playlist\":'):text.rfind('\"setVideoId\"')]
    else:
        text = text[text.find('\"playlist\":'):text.rfind('\"toggledAccessibilityData\"')]

    links = []

    # Grab all unique matches with the key VideoId and add them to the list
    for match in re.finditer('\"videoId\"', text):
        e = match.end()
        extractedVideoId = text[e + 2:e + 13]

        if extractedVideoId not in links:
            links.append(extractedVideoId)

    # Add youtube url format to the video id
    playlist = ['https://www.youtube.com/watch?v=' + i for i in links]

    if not playlist:
        return ['No videos found']
    else:
        return playlist


def CreateWindowLayout(createWindow):
    # Link extraction window
    if createWindow == WindowTypes.LINK_WINDOW:
        layout = [
            [sg.Multiline('', key='input', size=(48, 28), enable_events=True, focus=True,
                          right_click_menu=['&Right', ['Paste']])],
            [sg.Button('Extract source', key='add source', size=(18, 2)),
             sg.Text(size=(16, 1)), sg.Button('OK', key='add links', size=(4, 2)),
             sg.Button('Cancel', key='cancel', size=(7, 2))]
        ]
        windowTitle = 'Youtube Playlist Tool - Add Videos'
        return sg.Window(windowTitle, layout, font='Courier 12', modal=True, icon='logo.ico')

    # Playlist selection window during download
    if createWindow == WindowTypes.DOWNLOAD_WINDOW:
        layout = [
            [sg.Listbox([""], key='playlistInput', size=(48, 28), enable_events=True)],
            [sg.Text(size=(16, 1)), sg.Button('OK', key='okPlaylistInput', size=(4, 2)),
             sg.Button('Cancel', key='cancelPlaylistInput', size=(7, 2))]
        ]
        windowTitle = 'Youtube Playlist Tool - Choose a playlist to download'
        return sg.Window(windowTitle, layout, font='Courier 12', modal=True, icon='logo.ico')


def readPlaylistFromConfig(config):
    # Check config.ini for playlist name
    if os.path.isfile('config.ini'):
        config.read('config.ini')
        currentPlaylist = config['DEFAULT']['current playlist']
        mpvArg = config['DEFAULT']['mpv arguments']
        if mpvArg == '':
            mpvArg = '--slang=eng,en --fs --fs-screen=2 --sub-font-size=46'
    else:
        currentPlaylist = f"{os.getcwd()}/defaultPlaylist.ypl"
        mpvArg = '--slang=eng,en --fs --fs-screen=2 --sub-font-size=46'
        config['DEFAULT']['mpv arguments'] = mpvArg

    try:
        if currentPlaylist == '':
            print('No playlist found in config.ini\nUsing defaultPlaylist.ypl')
            currentPlaylist = f"{os.getcwd()}\\defaultPlaylist.ypl"
    except FileNotFoundError:
        print('Playlist ' + currentPlaylist + ' not found\nUsing defaultPlaylist.ypl')
        currentPlaylist = f"{os.getcwd()}\\defaultPlaylist.ypl"

    try:
        db = TinyDB(currentPlaylist)
    except OSError:
        print('Invalid playlist filename in config.ini\nUsing defaultPlaylist.ypl')
        currentPlaylist = f"{os.getcwd()}\\defaultPlaylist.ypl"
        db = TinyDB(currentPlaylist)

    config['DEFAULT']['current playlist'] = currentPlaylist
    with open('config.ini', 'w') as f:
        config.write(f)

    return currentPlaylist, mpvArg, db


def accessGSheets():
    # define the scope
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    # add credentials to the account
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
    except FileNotFoundError:
        print('client_secret.json not found!')
        print('Do you have the rights to access the database?')
        return None

    # authorize the clientsheet
    client = gspread.authorize(creds)

    # Find a workbook by name
    try:
        table = client.open("YTPDB")
        return table
    except gspread.exceptions.SpreadsheetNotFound:
        return None


# Upload playlist
def uploadGSheets(currentPlaylist):
    table = accessGSheets()

    if table is None:
        print('Couldn\'t access database, cancelling...')
        return

    # List all the worksheets
    worksheet_list = table.worksheets()

    dateAndTime = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    sheets = []

    # Add all sheet titles to a list
    for i in worksheet_list:
        sheets.append(i.title)

    playlistName = os.path.basename(RemoveExtension(currentPlaylist))

    # Check if there is a sheet for the playlist
    try:
        sheetIndex = sheets.index(playlistName)
        sheet = table.worksheet(sheets[sheetIndex])
        newSheet = False
    except ValueError:
        try:
            sheet = table.add_worksheet(title=playlistName, rows=10, cols=10)
            sheet.insert_row(['DateTime', 'PartCount', 'Data'])
            newSheet = True
        except gspread.exceptions.APIError:
            print('Unable to add new playlist.')
            print('Do you have permission to edit the database?')
            return

    # Read the playlist into a string
    with open(currentPlaylist, 'r', encoding='utf-8') as f:
        line = f.readline()
        print(len(line))

        # Split text between 50000 characters to workaround cell character limit
        lines = textwrap.wrap(line, 50000)
        len(lines)

        # Grab latest entry from server
        previousLines = []
        if not newSheet:
            partCount = int(sheet.cell(2, 2).value)
            for i in range(partCount):
                previousLines.append(sheet.cell(2, i + 3, ).value)

        # Upload new backup, if different from previous one
        if previousLines != lines:

            # cell = sheet.find(currentPlaylist[currentPlaylist.rfind('/') + 1:-4], in_column=1)
            try:
                sheet.insert_row([dateAndTime, len(lines)], index=2)
            except gspread.exceptions.APIError:
                print('Unable to upload playlist.')
                print('Do you have permission to edit the database?')
                return

            for count, i in enumerate(lines):
                sheet.update_cell(2, count + 3, i)

            print('Playlist uploaded successfully!')
            return

        else:
            print('Previous backup is identical to current one.')
            print('Playlist not uploaded.')
            return


# Download playlist
def downloadGSheets():
    table = accessGSheets()

    if table is None:
        print('Couldn\'t access database, canceling...')
        return None, None

    # List all the worksheets
    worksheet_list = table.worksheets()

    # Add all sheet titles to a list
    playlists = []
    for i in worksheet_list:
        playlists.append(i.title)

    if playlists is None:
        print('No playlists found in database.')
        return None, None

    # Create window to display uploaded playlists
    window3 = CreateWindowLayout(WindowTypes.DOWNLOAD_WINDOW)
    window3.finalize()

    window3['playlistInput'].update(playlists)

    selectPlaylistVersion = False
    chosenPlaylistRow = None
    chosenPlaylist = ''

    while True:
        event, values = window3.read()

        if event == sg.WIN_CLOSED or event == 'Exit':
            window3.close()
            return None, None

        if event == 'cancelPlaylistInput':
            window3.close()
            return None, None

        if event == 'okPlaylistInput':
            if len(values['playlistInput']) > 0:
                # Display different versions of chosen playlist
                if selectPlaylistVersion:
                    chosenPlaylistRow = values['playlistInput'][0].split(' ')[0]
                    chosenPlaylistRow = int(chosenPlaylistRow) + 1
                    print(chosenPlaylistRow)
                    window3.close()
                    break
                # Display all available playlists, this runs first
                else:
                    chosenPlaylist = values['playlistInput'][0]
                    print(chosenPlaylist)
                    sheet = table.worksheet(chosenPlaylist)

                    # TODO Add more info about the playlist versions
                    playlistDates = sheet.col_values(1)
                    playlistVersions = [str(i) + ' ' + str(x) for i, x in enumerate(playlistDates)]

                    window3['playlistInput'].update(playlistVersions[1:])

                    # Loop to playlist version selection
                    selectPlaylistVersion = True

    if chosenPlaylistRow is not None:
        partCount = int(sheet.cell(chosenPlaylistRow, 2, ).value)
        print(partCount)

        lines = []

        for i in range(partCount):
            lines.append(sheet.cell(chosenPlaylistRow, i + 3).value)
        print(lines)

        if len(lines) > 0:
            print('Playlist downloaded successfully!')

        return lines, chosenPlaylist


# Read config.ini
def readConfig(config) -> list:
    if not os.path.isfile('config.ini'):
        writeDefaultConfig(config)

    try:
        config.read('config.ini')
    # Replace old config
    except configparser.MissingSectionHeaderError:
        writeDefaultConfig(config)

    recentFiles = config['HISTORY']['recent files'].split('\n')

    # If there are no recent file entries, remove empty entry
    if recentFiles[0] == '':
        recentFiles.pop(0)

    return recentFiles


def writeDefaultConfig(config):
    config['DEFAULT'] = {'Current Playlist': '',
                         'mpv Arguments': '--slang=eng,en --fs --fs-screen=2 --sub-font-size=46'}
    for i in range(1, 10):
        config['HISTORY'] = {'Recent Files': ''}
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
        config.read('config.ini')


def ScaleWindow(window):
    CurrentWindowSize = window.size
    VideosElementSize = (int(CurrentWindowSize[0] * 0.1), int(CurrentWindowSize[1] * 0.045))

    window['videos'].set_size(VideosElementSize)
    return window.size


# Clean files when exiting app
def onExitApp():
    if os.path.isfile('mpvPlaylist.txt'):
        os.remove('mpvPlaylist.txt')


class GUI:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.recentFiles = readConfig(self.config)
        self.currentPlaylist, self.mpvArg, self.db = readPlaylistFromConfig(self.config)
        self.link = Query()
        self.windowSize = (1280, 840)  # Default window size
        self.player = []
        self.values = None
        self.window = None
        self.shufflePlaylist = False

        atexit.register(onExitApp)

        self.InitializeGUI()

    def filtering(self):
        global globalOrder
        globalOrder = []
        vD = {}
        combine = []

        # Replace special characters with a space
        # These can crash the search
        filterText = self.values['videoFilter'].translate({ord(c): " " for c in "!@#$%^&*()[]{};:,./<>?\|`~-=_+"})

        videos = self.db.search((self.link.videoId.search(filterText, flags=re.IGNORECASE)) |
                                (self.link.videoId.search(filterText[-11:], flags=re.IGNORECASE)) |  # For youtube URL
                                (self.link.title.search(filterText, flags=re.IGNORECASE)) |
                                (self.link.uploader.search(filterText, flags=re.IGNORECASE)))

        for e, x in enumerate(videos):
            # Converting order to float to fix sorting
            vD[e + 1] = {'videoId': x['videoId'], 'duration': x['duration'], 'title': x['title'],
                         'order': float(x['order'])}

        for i in OrderedDict(sorted(vD.items(), key=lambda x: getitem(x[1], 'order'))):
            combine.append(f"{vD[i]['videoId']} - {vD[i]['duration']} - {vD[i]['title']}")
            # Convert float -> int -> str
            # Variable used for manual sorting
            globalOrder.append(str(int(vD[i]['order'])))

        # Quick Shuffle
        if self.shufflePlaylist is True:
            random.shuffle(combine)

        return combine

    def viewData(self):
        global globalOrder
        globalOrder = []
        vD = {}
        combine = []

        try:
            # Add all videos in db to a dictionary
            for e, x in enumerate(self.db):
                # Converting order to float to fix sorting
                vD[e + 1] = {'videoId': x['videoId'], 'duration': x['duration'], 'title': x['title'],
                             'order': float(x['order'])}

            # Sort dictionary based on key and add to a list
            for i in OrderedDict(sorted(vD.items(), key=lambda x: getitem(x[1], 'order'))):
                # print(vD[i]['title'])
                # print(vD[i]['order'])
                combine.append(f"{vD[i]['videoId']} - {vD[i]['duration']} - {vD[i]['title']}")
                # Convert float -> int -> str
                # Variable used for manual sorting
                globalOrder.append(str(int(vD[i]['order'])))

            # Quick Shuffle
            if self.shufflePlaylist is True:
                random.shuffle(combine)

        # In case of missing video order information run script
        except KeyError:
            print("Database is corrupt")
            # runScript(2)
            # viewData(db)
            return None

        return combine

    # Move video up in listbox
    def sortUp(self):
        selection = self.values['videos']

        for i in self.values['videos']:

            # Current selection
            x = self.db.get(self.link.videoId == i[0:11])

            # Video above the selection
            # y = db.get(link.order == str(int(x['order']) - 1))

            y = self.db.get(self.link.order == str(globalOrder[globalOrder.index(x['order']) - 1]))

            # Check if video is on the top of the list
            # if y is not None:
            if globalOrder.index(x['order']) != 0:
                # db.update(Set('order', str(int(x['order']) - 1)), link.videoId == x['videoId'])
                # db.update(Set('order', str(int(y['order']) + 1)), link.videoId == y['videoId'])
                self.db.update(Set('order', str(globalOrder[globalOrder.index(x['order'])])),
                               self.link.videoId == y['videoId'])
                self.db.update(Set('order', str(globalOrder[globalOrder.index(x['order']) - 1])),
                               self.link.videoId == x['videoId'])
            # else:
            # break

        vpos = self.window['videos'].Widget.yview()

        self.window['videos'].update(self.filtering())
        self.window['videos'].SetValue(selection)
        self.window['videos'].set_vscroll_position(vpos[0])
        self.window.refresh()

    # Move video down in listbox
    def sortDown(self):
        selection = self.values['videos']

        # Reverse the list, when traveling downwards
        for i in reversed(self.values['videos']):

            # Current selection
            x = self.db.get(self.link.videoId == i[0:11])

            # Video below the selection
            # y = db.get(link.order == str(int(x['order']) + 1))
            try:
                y = self.db.get(self.link.order == str(globalOrder[globalOrder.index(x['order']) + 1]))

                # Old way to check if video is on the bottom of the list, doesn't actually do anything atm
                if y is not None:
                    # db.update(Set('order', str(int(x['order']) + 1)), link.videoId == x['videoId'])
                    # db.update(Set('order', str(int(y['order']) - 1)), link.videoId == y['videoId'])
                    self.db.update(Set('order', str(globalOrder[globalOrder.index(x['order'])])),
                                   self.link.videoId == y['videoId'])
                    self.db.update(Set('order', str(globalOrder[globalOrder.index(x['order']) + 1])),
                                   self.link.videoId == x['videoId'])
                # else:
                #   break

            # When at the bottom of the list, interestingly this exception doesn't occur on the top of the list
            except IndexError:
                continue

        vpos = self.window['videos'].Widget.yview()

        self.window['videos'].update(self.filtering())
        self.window['videos'].SetValue(selection)
        self.window['videos'].set_vscroll_position(vpos[0])
        self.window.refresh()

    # Add youtube links from the input window
    def addLinks(self, window2):
        event, values = window2.read(timeout=0)

        links = values['input'].split('\n')
        # Remove any empty lines
        links = [x for x in links if x.strip()]
        print(links)

        for i in links:
            videoId = ""

            if i.find('https://www.youtube.com/watch?v=') != -1:
                videoId = i.find('watch?') + 8
                videoId = i[videoId:videoId + 11]
                videoId = videoId.strip().replace(" ", "")

            elif i.find('https://youtu.be/') != -1:
                videoId = i.find('be/') + 3
                videoId = i[videoId:videoId + 11]
                videoId = videoId.strip().replace(" ", "")

            if len(videoId) == 11:

                if (self.db.contains(self.link.videoId == videoId)) is False:
                    self.db.insert({'videoId': videoId
                                       , 'title': '', 'thumbnail': '', 'duration': '', 'uploader': '',
                                    'order': str(len(self.db) + 1)})
                else:
                    print(f"Video with id {videoId} is already on the playlist")
            else:
                if videoId:
                    print(f"Video id {videoId} is invalid")

        vpos = self.window['videos'].Widget.yview()

        window2['input'].update('')
        self.window['videos'].update(self.viewData())
        self.window['videos'].set_vscroll_position(vpos[0])
        self.window.refresh()
        window2.close()

    # Reset listbox view
    def ClearListbox(self):
        # event, values = window.read(timeout=0)
        vpos = self.window['videos'].Widget.yview()
        selection = self.values['videos']

        self.window['videos'].update(self.viewData())
        self.window['videos'].set_vscroll_position(vpos[0])
        self.window['up'].update(disabled=False)
        self.window['down'].update(disabled=False)
        self.window['videos'].SetValue(selection)

    # Update videos that have missing data
    def UpdateVideoData(self):
        ids = [i['videoId'] for i in self.db]
        missingData = []
        for i in ids:
            title = self.db.get(self.link.videoId == i)
            title = title.get('title')
            if title == "":
                missingData.append(i)

        if len(missingData) > 0:
            print(str(len(missingData)) + ' videos missing data')
            print('Downloading video data...')
        else:
            print("All videos are up to date")

        for count, i in enumerate(missingData):
            try:
                ydl = youtube_dl.YoutubeDL({'outtmpl': '%(id)s.%(ext)s', 'cookiefile': 'cookies.txt'})
                info = ydl.extract_info(i, download=False)
                print(info['title'])
                print(info['thumbnail'])
                print(info['duration'])
                print(info['uploader'])
                print('Completed ' + str(count + 1) + ' / ' + str(len(missingData)) + ' videos')

                video_duration = str(int(info['duration'] / 60))
                video_duration = video_duration + ':' + str(info['duration'] % 60).zfill(2)

                self.db.update(Set('title', info['title']), self.link.videoId == i)
                self.db.update(Set('thumbnail', info['thumbnail']), self.link.videoId == i)
                self.db.update(Set('duration', video_duration), self.link.videoId == i)
                self.db.update(Set('uploader', info['uploader']), self.link.videoId == i)
                time.sleep(3)
            except youtube_dl.utils.DownloadError:
                print('Unable to download video information!')

        vpos = self.window['videos'].Widget.yview()

        self.window['videos'].update(self.viewData())
        self.window['videos'].set_vscroll_position(vpos[0])

    # For running db scripts
    def runScript(self, script):
        ids = [i['videoId'] for i in self.db]
        for enum, i in enumerate(ids):
            if script == 1:
                self.db.update(Set('uploader', ''), self.link.videoId == i)
            if script == 2:
                self.db.update(Set('order', enum + 1), self.link.videoId == i)

    # Create new playlist db
    def NewPlaylist(self, name):
        newPlaylist = sg.popup_get_text('Input playlist name', default_text=name)

        if newPlaylist is not None and newPlaylist != '':
            newPlaylist = f"{os.getcwd()}\\{newPlaylist}.ypl"
            if not os.path.isfile(newPlaylist):
                self.db = TinyDB(newPlaylist)
                self.window['videoFilter'].update('')
                self.window['videos'].update(self.viewData())
                self.window.TKroot.title('Youtube Playlist Tool - ' + os.path.basename(RemoveExtension(newPlaylist)))

                self.config['DEFAULT']['current playlist'] = newPlaylist

                with open('config.ini', 'w') as f:
                    self.config.write(f)

            else:
                answer = sg.popup_yes_no('Playlist already exists.\nOverwrite?')
                if answer:
                    self.db = TinyDB(newPlaylist)
                    self.window['videoFilter'].update('')
                    self.window['videos'].update(self.viewData())
                    self.window.TKroot.title(
                        'Youtube Playlist Tool - ' + os.path.basename(RemoveExtension(newPlaylist)))

                    self.config['DEFAULT']['current playlist'] = newPlaylist

                    with open('config.ini', 'w') as f:
                        self.config.write(f)

                else:
                    newPlaylist = None

        return newPlaylist

    # Delete selected videos
    def deleteVideos(self):
        # event, values = window.read(timeout=0)

        if self.values['videos']:
            popupInput = sg.popup_yes_no('Delete selected videos?')
            if popupInput == 'Yes':

                for i in self.values['videos']:

                    # Reorder videos when one is deleted
                    # Not the most efficient way to do this, but it works
                    videoOrder = self.db.get(self.link.videoId == i[0:i.find(' ')])
                    videoOrder = int(videoOrder['order'])
                    for x in range(len(self.db) - videoOrder - 1):
                        self.db.update(Set('order', str(videoOrder + x)), self.link.order == str(videoOrder + x + 1))

                    self.db.remove(self.link.videoId == i[0:i.find(' ')])

                vpos = self.window['videos'].Widget.yview()

                self.window['videos'].update(self.filtering())
                self.window['videos'].set_vscroll_position(vpos[0])

    # Disable/Enable playback buttons depending on current video playback status
    def ToggleButtons(self):
        videoPlaying = bool
        videoSelected = len(self.values["videos"]) > 0

        videoPlaying = self.SubprocessActions(ProcessAction.PROCESS_EXISTS)

        self.window["button_playVideo"].update(disabled=not videoSelected)
        self.window["button_stopPlayback"].update(disabled=not videoPlaying)

    def SubprocessActions(self, action: ProcessAction) -> bool:
        if action == ProcessAction.PROCESS_EXISTS:
            for process in self.player:
                # Check if process has returned a return code
                if process.poll() is None:
                    return True
            return False

        # Kill all previous processes from the list
        if action == ProcessAction.KILL_PROCESS:
            stoppedProcesses = []
            for enum, process in enumerate(self.player):
                if process.poll() is None:
                    process.kill()
                    stoppedProcesses.append(enum)

            # Clean up process list
            stoppedProcesses = reversed(stoppedProcesses)
            for i in stoppedProcesses:
                self.player.pop(i)

        return True

    def InitializeGUI(self):

        # Initialize pySimpleGUI
        sg.theme('Topanga')

        menu_def = [['File', ['New playlist', 'Open playlist', 'Recent playlists', [self.recentFiles], 'Exit']],
                    ['Settings', ['mpv arguments', 'Shuffle playlist']],
                    ['Sync', ['Upload playlist', 'Download playlist']],
                    # ['Videos', ['Add Videos', 'Update Video Data', 'Copy Videos to Clipboard']],
                    ['Help', ['Readme', 'About']], ]

        menu_elem = sg.Menu(menu_def)

        col1 = [
            [sg.Text("Edit Playlist")],
            [sg.Button('Add videos', k="Add"),
             sg.Button('Update playlist', k="Update")
             # sg.Button('Create Playlist', key='create playlist'),
             ]
        ]

        col2 = [
            [sg.Text("Search & Sort", justification="center")],
            [sg.Text('Filter', size=(6, 0)),
             sg.In(size=(20, 0), enable_events=True, key='videoFilter'),
             sg.Button('X', key='clear')],
            [sg.Text('Reorder tracks', k="Reorder"), sg.Button('↑', key='up'), sg.Button('↓', key='down')],
            # [sg.Button('Script')]  # For running quick db scripts
        ]

        col3 = [[sg.Text('Copy Settings', pad=((20, 0), (0, 0)))],
                [sg.Text(''), sg.Radio('Normal', group_id='method', default=True, key='copy method'),
                 sg.Radio('Shuffled', group_id='method',
                          tooltip="Copy a shuffled version of the current playlist into the clipboard")],
                [sg.Text(''), sg.Radio('List  ', group_id='type', default=True, key='copy type',
                                       tooltip="Copy videos into a list separated by a line break"),
                 sg.Radio('mpv list', group_id='type',
                          tooltip="Copy videos into a list format supported by the mpv player (Space as separator)")],
                [sg.Button('Copy To Clipboard', k="Copy", pad=(18, 0), s=(20, 0))]
                ]

        col4 = [[sg.Text('Playback Controls')],
                [sg.Button('▶', k="button_playVideo", size=(3, 0)), sg.Button("■", k="button_stopPlayback", size=(3, 0))],
                [sg.Checkbox("Allow only one player", k="checkbox_allowOnlyOnePlayer", default=True, tooltip="Closes previous video players before opening a new one")]
                ]

        layout = [
            [menu_elem],
            [sg.Listbox(values=self.viewData(), key='videos', size=(130, 36), enable_events=True,
                        right_click_menu=['&Right', ['Copy URL', 'Open URL', 'Play with mpv', 'Delete video(s)']],
                        select_mode='extended')],
            [sg.Column(col1, vertical_alignment="top"), sg.VerticalSeparator(),
             sg.Column(col2, vertical_alignment="top"), sg.VerticalSeparator(),
             sg.Column(col3, vertical_alignment="top"), sg.VerticalSeparator(),
             sg.Column(col4, vertical_alignment="top")],
        ]

        self.window = sg.Window(f"Youtube Playlist Tool - {os.path.basename(RemoveExtension(self.currentPlaylist))}",
                                layout,
                                font='Courier 12', size=self.windowSize,
                                resizable=True, icon='logo.ico').finalize()

        # Bind window resize events to the while loop
        self.window.bind('<Configure>', "WindowEvent")

        while True:
            event, self.values = self.window.read()
            if event == sg.WIN_CLOSED or event == 'Exit':  # if user closes window or clicks cancel
                break

            if event == 'Add' or event == 'Add Videos':
                window2 = CreateWindowLayout(WindowTypes.LINK_WINDOW)
                window2.finalize()

                while True:
                    event, values = window2.read()

                    if event == sg.WIN_CLOSED or event == 'Exit':
                        window2.close()
                        break

                    if event == 'cancel':
                        window2.close()
                        break

                    if event == 'add source':
                        window2['input'].update('\n'.join(extractVideos()))

                    if event == 'Paste':
                        window2['input'].update(pyperclip.paste())

                    if event == 'input':
                        if values['input'].find('html') != -1:
                            window2['input'].update('')
                            window2['input'].update('\n'.join(extractVideos()))

                    if event == 'add links':
                        self.addLinks(window2)
                        break

            # When listbox is clicked
            if event == 'videos':
                try:
                    if self.values['videos'][0] != '':

                        videoId = self.values['videos'][0][0:11]
                        print(videoId)

                        title = self.db.get(self.link.videoId == videoId)
                        try:
                            title = title.get('title')

                            if title == "":
                                try:
                                    ydl = youtube_dl.YoutubeDL(
                                        {'outtmpl': '%(id)s.%(ext)s', 'cookiefile': 'cookies.txt'})
                                    info = ydl.extract_info(self.values['videos'][0][0:11], download=False)
                                    print(info['title'])
                                    print(info['thumbnail'])
                                    print(info['duration'])
                                    print(info['uploader'])

                                    video_duration = str(int(info['duration'] / 60))
                                    video_duration = video_duration + ':' + str(info['duration'] % 60).zfill(2)

                                    self.db.update(Set('title', info['title']), self.link.videoId == videoId)
                                    self.db.update(Set('thumbnail', info['thumbnail']), self.link.videoId == videoId)
                                    self.db.update(Set('duration', video_duration), self.link.videoId == videoId)
                                    self.db.update(Set('uploader', info['uploader']), self.link.videoId == videoId)

                                    vpos = self.window['videos'].Widget.yview()

                                    self.window['videos'].update(self.viewData())
                                    self.window['videos'].set_vscroll_position(vpos[0])

                                except youtube_dl.utils.DownloadError:
                                    print('Unable to download video data')

                            data = self.db.get(self.link.videoId == videoId)
                            print(data)
                            print('https://www.youtube.com/watch?v=' + data.get('videoId'))

                            # TODO This can also pop the same AttributeError exception, if youtube-dl doesn't work
                            #  properly
                            print(data.get('title'))
                            print(data.get('thumbnail'))
                            print(data.get('duration'))
                            print(data.get('uploader'))

                        except AttributeError as e:
                            print('Unable to find db entry')

                except IndexError:
                    print('List is empty!')

            if event == 'Update' or event == 'Update Video Data':
                self.UpdateVideoData()

            if event == 'Copy URL':
                urls = []

                for i in self.values['videos']:
                    videoId = i[0:11]
                    urls.append('https://www.youtube.com/watch?v=' + videoId)
                    pyperclip.copy('\n'.join(urls))

            if event == 'Open URL':

                if self.values['videos']:
                    videoId = self.values['videos'][0][0:11]
                    url = 'https://www.youtube.com/watch?v=' + videoId
                    webbrowser.open(url)

            if event == 'Play with mpv' or event == 'button_playVideo':
                urls = []

                for i in self.values['videos']:
                    urls.append('https://youtu.be/' + i[0:11])

                if len(urls) > 0:

                    with open('mpvPlaylist.txt', 'w', encoding='utf-8') as f:
                        for url in urls:
                            f.write(url + "\n")

                    if self.values["checkbox_allowOnlyOnePlayer"]:
                        self.SubprocessActions(ProcessAction.KILL_PROCESS)

                    self.player.append(subprocess.Popen(["mpv", self.mpvArg, "--playlist=mpvPlaylist.txt"]))

                    self.window["button_stopPlayback"].update(disabled=False)

            if event == "button_stopPlayback":
                self.SubprocessActions(ProcessAction.KILL_PROCESS)

            if event == 'Delete video(s)':
                self.deleteVideos()

            if event == 'Copy' or event == 'Copy Videos to Clipboard':

                urls = []

                for i in self.filtering():
                    urls.append('https://youtu.be/' + i[0:11])
                    print('https://youtu.be/' + i[0:11])

                # Run shuffle based on radio button value
                if self.values['copy method'] is False:
                    seed = random.randrange(sys.maxsize)
                    random.seed(seed)
                    random.shuffle(urls)
                    print(str(len(urls)) + ' videos copied to clipboard (shuffled)')
                    print('Seed')
                    print(seed)
                else:
                    print(str(len(urls)) + ' videos copied to clipboard')

                if self.values['copy type'] is True:
                    pyperclip.copy('\n'.join(urls))
                else:
                    pyperclip.copy(' '.join(urls))

            # Create playlist for Youtube
            # Very limited, not used atm (max 50 videos per playlist, playlist cannot be saved)
            if event == 'create playlist':
                urls = []

                for i in self.filtering():
                    urls.append(i[0:11])

                random.shuffle(urls)

                for i in range(0, len(urls), 50):
                    playlistUrl = 'http://www.youtube.com/watch_videos?video_ids=' + ','.join(urls[i:i + 50])
                    print(playlistUrl + '\n')

            # For running db scripts, hidden in normal circumstances
            if event == 'Script':
                self.runScript(2)

            if event == 'clear':
                self.window['videoFilter'].update('')
                self.ClearListbox()

            if event == 'up':
                self.sortUp()

            if event == 'down':
                self.sortDown()

            if event == 'videoFilter':
                if len(self.values['videoFilter']) > 2:
                    self.window['videos'].update(self.filtering())
                else:
                    self.ClearListbox()

            if event == 'Open playlist':
                self.currentPlaylist = sg.popup_get_file('', title='Select Playlist',
                                                         no_window=True, modal=True, keep_on_top=True,
                                                         file_types=(('YPL files', '*.ypl'),),
                                                         initial_folder=os.getcwd())
                if not self.currentPlaylist:
                    print('No file selected!')
                else:
                    self.db = TinyDB(self.currentPlaylist)
                    self.config['DEFAULT']['current playlist'] = self.currentPlaylist

                    if self.currentPlaylist not in self.recentFiles:
                        if len(self.recentFiles) > 10:
                            self.recentFiles.pop(9)
                        self.recentFiles.insert(0, self.currentPlaylist)
                        menu_elem.Update(menu_def)
                    else:
                        currentIndex = self.recentFiles.index(self.currentPlaylist)
                        self.recentFiles.insert(0, self.recentFiles.pop(currentIndex))
                        menu_elem.Update(menu_def)

                    self.config['HISTORY']['recent files'] = '\n'.join(self.recentFiles)

                    self.window['videoFilter'].update('')
                    self.window['videos'].update(self.viewData())
                    self.window.TKroot.title(
                        f"Youtube Playlist Tool - {os.path.basename(RemoveExtension(self.currentPlaylist))} ")

                    with open('config.ini', 'w', ) as f:
                        self.config.write(f)

            if event == 'New playlist':
                self.currentPlaylist = self.NewPlaylist('')

            if event == 'mpv arguments':
                arguments = sg.popup_get_text('Input mpv launch arguments', default_text=self.mpvArg)

                if arguments is not None:
                    self.mpvArg = arguments
                    self.config['DEFAULT']['mpv arguments'] = self.mpvArg
                    with open('config.ini', 'w') as f:
                        self.config.write(f)

            if event == 'Shuffle playlist':
                self.shufflePlaylist = True
                self.window['videos'].update(self.filtering())
                self.shufflePlaylist = False

            # Download a playlist from Google Sheets
            if event == 'Download playlist':
                chosenPlaylist = None
                newPlaylist = None

                lines, chosenPlaylist = downloadGSheets()

                if chosenPlaylist is not None:
                    newPlaylist = self.NewPlaylist(chosenPlaylist)

                if newPlaylist is not None:
                    self.currentPlaylist = newPlaylist

                    with open(self.currentPlaylist, 'w', encoding='utf-8') as f:
                        f.writelines(lines)

                    self.window['videoFilter'].update('')
                    self.window['videos'].update(self.viewData())

            # Upload a playlist into Google Sheets
            if event == 'Upload playlist':
                uploadGSheets(self.currentPlaylist)

            if event == 'Readme':
                webbrowser.open('https://github.com/CuriousCod/YoutubePlaylistTool/tree/master')

            if event == 'About':
                sg.popup('Youtube Playlist Tool v1.6.0\n\nhttps://github.com/CuriousCod/YoutubePlaylistTool\n',
                         title='About', icon='logo.ico')

            # Recent files event
            for enum, i in enumerate(self.recentFiles):
                if event == i:
                    if os.path.isfile(i):
                        currentPlaylist = i
                        self.db = TinyDB(currentPlaylist)

                        self.recentFiles.pop(self.recentFiles.index(i))
                        self.recentFiles.insert(0, currentPlaylist)
                        menu_elem.Update(menu_def)

                        self.window['videoFilter'].update('')
                        self.window['videos'].update(self.viewData())
                        self.window.TKroot.title(
                            f"Youtube Playlist Tool - {os.path.basename(RemoveExtension(currentPlaylist))}")

                        self.config['DEFAULT']['current playlist'] = currentPlaylist
                        self.config['HISTORY']['recent files'] = '\n'.join(self.recentFiles)

                        with open('config.ini', 'w') as f:
                            self.config.write(f)
                        break
                    else:
                        print('Playlist doesn\'t exist.')
                        self.recentFiles.pop(enum)
                        menu_elem.Update(menu_def)

            if event == "WindowEvent":
                ScaleWindow(self.window)

            self.ToggleButtons()

        self.window.close()
