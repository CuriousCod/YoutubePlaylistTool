import PySimpleGUI as sg
from tinydb import TinyDB, Query
import youtube_dlc as youtube_dl
from tinydb.operations import set as Set
import re, time, random, os, sys, webbrowser, subprocess, textwrap, datetime, configparser, atexit
from os import path
from collections import OrderedDict
from operator import getitem
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


def filtering():

    global globalOrder
    globalOrder = []
    vD = {}
    combine = []

    # Replace special characters with a space
    # These can crash the search
    filterText = values['videoFilter'].translate({ord(c): " " for c in "!@#$%^&*()[]{};:,./<>?\|`~-=_+"})

    videos = db.search((Link.videoId.search(filterText, flags=re.IGNORECASE)) |
                       (Link.videoId.search(filterText[-11:], flags=re.IGNORECASE)) |  # For youtube URL
                       (Link.title.search(filterText, flags=re.IGNORECASE)) |
                       (Link.uploader.search(filterText, flags=re.IGNORECASE)))

    for e, x in enumerate(videos):
        # Converting order to float to fix sorting
        vD[e + 1] = {'videoId': x['videoId'], 'duration': x['duration'], 'title': x['title'], 'order': float(x['order'])}

    for i in OrderedDict(sorted(vD.items(), key=lambda x: getitem(x[1], 'order'))):
        combine.append(vD[i]['videoId'] + ' - ' + vD[i]['duration'] + ' - ' + vD[i]['title'])
        # Convert float -> int -> str
        # Variable used for manual sorting
        globalOrder.append(str(int(vD[i]['order'])))

    # Quick Shuffle
    if shufflePlaylist is True:
        random.shuffle(combine)

    return combine

    """
    videoData = [i['videoId'] + ' - ' + i['duration'] + ' - ' + i['title'] for i in videos]

    # Grabbing video order info and formatting it into 0000
    # This is actually faster than searching through the database for the video order
    order = [int(i['order']) for i in videos]

    # Quick Shuffle
    if shufflePlaylist is True:
        random.shuffle(order)

    # Format to 0000
    order = ["%04d" % i for i in order]

    # Combining formatted ordering into the video list, old solution
#    for (item1, item2) in zip(order, videoData):
#        combine.append(item1 + ' - ' + item2)

    # Combining formatted ordering into the video list
    for x in range(len(order)):
        combine.append(order[x] + ' - ' + videoData[x])

    # Sorting based on order
    combine.sort()

    # Remove ordering from display
    combine = [i[7:] for i in combine]

    # List variable for reordering purposes
    # For some reason .sort() also affects the order list <_<
    globalOrder = sorted(order)
    globalOrder = list(map(int, globalOrder))
    globalOrder = list(map(str, globalOrder))

    return combine
    """


def viewData():

    global globalOrder
    globalOrder = []
    vD = {}
    combine = []

    try:
        # Add all videos in db to a dictionary
        for e, x in enumerate(db):
            # Converting order to float to fix sorting
            vD[e + 1] = {'videoId': x['videoId'], 'duration': x['duration'], 'title': x['title'], 'order': float(x['order'])}

        # Sort dictionary based on key and add to a list
        for i in OrderedDict(sorted(vD.items(), key=lambda x: getitem(x[1], 'order'))):
            #print(vD[i]['title'])
            #print(vD[i]['order'])
            combine.append(vD[i]['videoId'] + ' - ' + vD[i]['duration'] + ' - ' + vD[i]['title'])
            # Convert float -> int -> str
            # Variable used for manual sorting
            globalOrder.append(str(int(vD[i]['order'])))

        # Quick Shuffle
        if shufflePlaylist is True:
            random.shuffle(combine)

    # In case of missing video order information run script
    except KeyError:
        runScript(2)
        viewData()

    return combine

    """
    videoData = [i['videoId'] + ' - ' + i['duration'] + ' - ' + i['title'] for i in db]
    
    # Grabbing video order info and formatting it into 0000
    # This is actually faster than searching through the database for the video order
    try:
        order = [int(i['order']) for i in db]

        # Quick Shuffle
        if shufflePlaylist is True:
            random.shuffle(order)

        # Format to 0000
        order = ["%04d" % i for i in order]

        # Combining formatted ordering into the video list
        for (item1, item2) in zip(order, videoData):
            combine.append(item1 + ' - ' + item2)

        # Sorting videos based on order
        combine.sort()

        # Remove ordering from display
        combine = [i[7:] for i in combine]

        # List variable for reordering purposes
        # Convert to int first to remove extra 0000 from order number
        # For some reason .sort() also affects the normal order list <_<
        globalOrder = sorted(order)
        globalOrder = list(map(int, globalOrder))
        globalOrder = list(map(str, globalOrder))

    return combine
    """

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
    if createWindow == 1:
        layout = [
            [sg.Multiline('', key='input', size=(48, 28), enable_events=True, focus=True, right_click_menu=['&Right', ['Paste']])],
            [sg.Button('Extract source', key='add source', size=(18, 2)),
             sg.Text(size=(16, 1)), sg.Button('OK', key='add links', size=(4, 2)), sg.Button('Cancel', key='cancel', size=(7, 2))]
        ]
        windowTitle = 'Youtube Playlist Tool - Add Videos'
        return sg.Window(windowTitle, layout, font='Courier 12', modal=True, icon='logo.ico')

    # Playlist selection window during download
    if createWindow == 2:
        layout = [
            [sg.Listbox('', key='playlistInput', size=(48, 28), enable_events=True)],
            [sg.Text(size=(16, 1)), sg.Button('OK', key='okPlaylistInput', size=(4, 2)), sg.Button('Cancel', key='cancelPlaylistInput', size=(7, 2))]
        ]
        windowTitle = 'Youtube Playlist Tool - Choose a playlist to download'
        return sg.Window(windowTitle, layout, font='Courier 12', modal=True, icon='logo.ico')


# For running db scripts
def runScript(script):

    ids = [i['videoId'] for i in db]
    x = 1
    for i in ids:
        if script == 1:
            db.update(Set('uploader', ''), Link.videoId == i)
        if script == 2:
            db.update(Set('order', str(x)), Link.videoId == i)
            x += 1


# Create new playlist db
def NewPlaylist(name):

    global db
    newPlaylist = sg.popup_get_text('Input playlist name', default_text=name)

    if newPlaylist is not None and newPlaylist != '':
        if not os.path.isfile(newPlaylist + '.ypl'):
            db = TinyDB(newPlaylist + '.ypl')
            window['videoFilter'].update('')
            window['videos'].update(viewData())
            window.TKroot.title('Youtube Playlist Tool - ' + newPlaylist)

            config['DEFAULT']['current playlist'] = newPlaylist + '.ypl'

            with open('config.ini', 'w') as f:
                config.write(f)

        else:
            answer = sg.popup_yes_no('Playlist already exists.\nOverwrite?')
            if answer:
                db = TinyDB(newPlaylist + '.ypl')
                window['videoFilter'].update('')
                window['videos'].update(viewData())
                window.TKroot.title('Youtube Playlist Tool - ' + newPlaylist)

                config['DEFAULT']['current playlist'] = newPlaylist + '.ypl'

                with open('config.ini', 'w') as f:
                    config.write(f)

            else:
                newPlaylist = None

    return newPlaylist


def readPlaylistFromConfig():

    global db

    # Check config.ini for playlist name
    if path.isfile('config.ini'):
        config.read('config.ini')
        currentPlaylist = config['DEFAULT']['current playlist']
        mpvArg = config['DEFAULT']['mpv arguments']
        if mpvArg == '':
            mpvArg = '--slang=eng,en --fs --fs-screen=2 --sub-font-size=46'
    else:
        currentPlaylist = 'defaultPlaylist.ypl'
        mpvArg = '--slang=eng,en --fs --fs-screen=2 --sub-font-size=46'
        config['DEFAULT']['mpv arguments'] = mpvArg

    try:
        if currentPlaylist == '':
            print('No playlist found in config.ini\nUsing defaultPlaylist.ypl')
            currentPlaylist = 'defaultPlaylist.ypl'
    except FileNotFoundError:
        print('Playlist ' + currentPlaylist + ' not found\nUsing defaultPlaylist.ypl')
        currentPlaylist = 'defaultPlaylist.ypl'

    try:
        db = TinyDB(currentPlaylist)
    except OSError:
        print('Invalid playlist filename in config.ini\nUsing defaultPlaylist.ypl')
        currentPlaylist = 'defaultPlaylist.ypl'
        db = TinyDB(currentPlaylist)

    config['DEFAULT']['current playlist'] = currentPlaylist
    with open('config.ini', 'w') as f:
        config.write(f)

    return currentPlaylist, mpvArg


# Add youtube links from the input window
def addLinks():
    event, values = window2.read(timeout=0)
    links = values['input'].split('\n')
    print(links)

    for i in links:

        if i.find('https://www.youtube.com/watch?v=') != -1:
            videoId = i.find('watch?') + 8
            videoId = i[videoId:videoId + 11]

            if videoId.find(' ') == -1 and len(videoId) == 11:

                if (db.contains(Link.videoId == videoId)) is False:
                    db.insert({'videoId': videoId
                                  , 'title': '', 'thumbnail': '', 'duration': '', 'uploader': '',
                               'order': str(len(db) + 1)})

        if i.find('https://youtu.be/') != -1:
            videoId = i.find('be/') + 3
            videoId = i[videoId:videoId + 11]

            if videoId.find(' ') == -1 and len(videoId) == 11:

                if (db.contains(Link.videoId == videoId)) is False:
                    db.insert({'videoId': videoId
                                  , 'title': '', 'thumbnail': '', 'duration': '', 'uploader': '',
                               'order': str(len(db) + 1)})

    vpos = window['videos'].Widget.yview()

    window2['input'].update('')
    window['videos'].update(viewData())
    window['videos'].set_vscroll_position(vpos[0])
    window.refresh()
    window2.close()


# Reset listbox view
def clear():
    event, values = window.read(timeout=0)
    vpos = window['videos'].Widget.yview()
    selection = values['videos']

    window['videos'].update(viewData())
    window['videos'].set_vscroll_position(vpos[0])
    window['up'].update(disabled=False)
    window['down'].update(disabled=False)
    window['videos'].SetValue(selection)


# Update videos that have missing data
def update():
    ids = [i['videoId'] for i in db]
    missingData = []
    for i in ids:
        title = db.get(Link.videoId == i)
        title = title.get('title')
        if title == "":
            missingData.append(i)

    print(str(len(missingData)) + ' videos missing video information')
    if len(missingData) > 0:
        print('Downloading video information...')

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

            db.update(Set('title', info['title']), Link.videoId == i)
            db.update(Set('thumbnail', info['thumbnail']), Link.videoId == i)
            db.update(Set('duration', video_duration), Link.videoId == i)
            db.update(Set('uploader', info['uploader']), Link.videoId == i)
            time.sleep(3)
        except youtube_dl.utils.DownloadError:
            print('Unable to download video information!')

    vpos = window['videos'].Widget.yview()

    window['videos'].update(viewData())
    window['videos'].set_vscroll_position(vpos[0])

def accessGSheets():
    # define the scope
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    # add credentials to the account
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
    except FileNotFoundError:
        print('client_secret.json not found!')
        print('Do you have rights to access the database?')
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

    playlistName = currentPlaylist[currentPlaylist.rfind('/') + 1:-4]

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
def downloadGSheets(currentPlaylist):

    global db

    table = accessGSheets()

    if table is None:
        print('Couldn\'t access database, canceling...')
        return currentPlaylist

    # List all the worksheets
    worksheet_list = table.worksheets()

    # Add all sheet titles to a list
    playlists = []
    for i in worksheet_list:
        playlists.append(i.title)

    if playlists is None:
        print('No playlists found in database.')
        return currentPlaylist

    # Create window to display uploaded playlists
    window3 = CreateWindowLayout(2)
    window3.finalize()

    window3['playlistInput'].update(playlists)

    selectPlaylistVersion = False
    chosenPlaylistRow = None
    chosenPlaylist = ''

    while True:
        event, values = window3.read()

        if event == sg.WIN_CLOSED or event == 'Exit':
            window3.close()
            break

        if event == 'cancelPlaylistInput':
            window3.close()
            break

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

        newPlaylist = NewPlaylist(chosenPlaylist)

        if newPlaylist is not None:
            currentPlaylist = newPlaylist

            with open(currentPlaylist + '.ypl', 'w', encoding='utf-8') as f:
                f.writelines(lines)

            print('Playlist downloaded successfully!')

        window['videoFilter'].update('')
        window['videos'].update(viewData())

    return currentPlaylist


# Delete selected videos
def deleteVideos():
    event, values = window.read(timeout=0)

    if values['videos']:
        popupInput = sg.popup_yes_no('Delete selected videos?')
        if popupInput == 'Yes':

            for i in values['videos']:

                # Reorder videos when one is deleted
                # Not the most efficient way to do this, but it works
                videoOrder = db.get(Link.videoId == i[0:i.find(' ')])
                videoOrder = int(videoOrder['order'])
                for x in range(len(db) - videoOrder - 1):
                    db.update(Set('order', str(videoOrder + x)), Link.order == str(videoOrder + x + 1))

                db.remove(Link.videoId == i[0:i.find(' ')])

            vpos = window['videos'].Widget.yview()

            window['videos'].update(filtering())
            window['videos'].set_vscroll_position(vpos[0])


# Read config.ini
def readConfig():

    if not os.path.isfile('config.ini'):
        writeDefaultConfig()

    try:
        config.read('config.ini')
    # Replace old config
    except configparser.MissingSectionHeaderError:
        writeDefaultConfig()

    recentFiles = config['HISTORY']['recent files'].split('\n')

    # If there are no recent file entries, remove empty entry
    if recentFiles[0] == '':
        recentFiles.pop(0)

    return recentFiles


def writeDefaultConfig():
    config['DEFAULT'] = {'Current Playlist': '',
                         'mpv Arguments': '--slang=eng,en --fs --fs-screen=2 --sub-font-size=46'}
    for i in range(1, 10):
        config['HISTORY'] = {'Recent Files': ''}
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
        config.read('config.ini')


# Move video up in listbox
def sortUp():

    global db
    selection = values['videos']

    for i in values['videos']:

        # Current selection
        x = db.get(Link.videoId == i[0:11])

        # Video above the selection
        # y = db.get(Link.order == str(int(x['order']) - 1))
        y = db.get(Link.order == str(globalOrder[globalOrder.index(x['order']) - 1]))

        # Check if video is on the top of the list
        # if y is not None:
        if globalOrder.index(x['order']) != 0:
            # db.update(Set('order', str(int(x['order']) - 1)), Link.videoId == x['videoId'])
            # db.update(Set('order', str(int(y['order']) + 1)), Link.videoId == y['videoId'])
            db.update(Set('order', str(globalOrder[globalOrder.index(x['order'])])), Link.videoId == y['videoId'])
            db.update(Set('order', str(globalOrder[globalOrder.index(x['order']) - 1])), Link.videoId == x['videoId'])
        # else:
        # break

    vpos = window['videos'].Widget.yview()

    window['videos'].update(filtering())
    window['videos'].SetValue(selection)
    window['videos'].set_vscroll_position(vpos[0])
    window.refresh()

# Move video down in listbox
def sortDown():
    global db
    selection = values['videos']

    # Reverse the list, when traveling downwards
    for i in reversed(values['videos']):

        # Current selection
        x = db.get(Link.videoId == i[0:11])

        # Video below the selection
        # y = db.get(Link.order == str(int(x['order']) + 1))
        try:
            y = db.get(Link.order == str(globalOrder[globalOrder.index(x['order']) + 1]))

            # Old way to check if video is on the bottom of the list, doesn't actually do anything atm
            if y is not None:
                # db.update(Set('order', str(int(x['order']) + 1)), Link.videoId == x['videoId'])
                # db.update(Set('order', str(int(y['order']) - 1)), Link.videoId == y['videoId'])
                db.update(Set('order', str(globalOrder[globalOrder.index(x['order'])])), Link.videoId == y['videoId'])
                db.update(Set('order', str(globalOrder[globalOrder.index(x['order']) + 1])),
                          Link.videoId == x['videoId'])
            # else:
            #   break

        # When at the bottom of the list, interestingly this exception this doesn't occur on the top of the list
        except IndexError:
            continue

    vpos = window['videos'].Widget.yview()

    window['videos'].update(filtering())
    window['videos'].SetValue(selection)
    window['videos'].set_vscroll_position(vpos[0])
    window.refresh()


# Clean files when exiting app
def onExitApp():
    if os.path.isfile('playWithMPV.bat'):
        os.remove('playWithMPV.bat')


# Initialize stuff
config = configparser.ConfigParser()
recentFiles = readConfig()
currentPlaylist, mpvArg = readPlaylistFromConfig()
Link = Query()
windowSize = (1280, 810)  # Default window size
atexit.register(onExitApp)

global shufflePlaylist
shufflePlaylist = False

# Initialize pySimpleGUI
sg.theme('Topanga')

menu_def = [['File', ['New playlist', 'Open playlist', 'Recent playlists', [recentFiles], 'Exit']],
            ['Settings', ['mpv arguments', 'Shuffle playlist']],
            ['Sync', ['Upload playlist', 'Download playlist']],
            #['Videos', ['Add Videos', 'Update Video Data', 'Copy Videos to Clipboard']],
            ['Help', ['Readme', 'About']], ]



menu_elem = sg.Menu(menu_def)

col1 = [
    [sg.Text('Filter', size=(6, 1)),
    sg.In(size=(20, 1), enable_events=True, key='videoFilter'),
    sg.Button('X', key='clear'), sg.Text(' Reorder'), sg.Button('↑', key='up'), sg.Button('↓', key='down'), sg.Text(' Copy method')],
    [sg.Text('', size=(46, 1)), sg.Radio('Normal', group_id='method', default=True, key='copy method'), sg.Radio('Shuffled', group_id='method')],
    [sg.Button('Add'),
    sg.Button('Update'),
    #sg.Button('Create Playlist', key='create playlist'),
    sg.Button('Copy'),
    sg.Text('', size=(26, 1), pad=(8, 1)), sg.Radio('List  ', group_id='type', default=True, key='copy type'), sg.Radio('mpv list', group_id='type')],
    #[sg.Button('Script')]  # For running quick db scripts
]

layout = [
    [menu_elem],
    [sg.Listbox(values=viewData(), key='videos', size=(130, 36), enable_events=True,
                right_click_menu=['&Right', ['Copy URL', 'Open URL', 'Play with mpv', 'Delete video(s)']],
                select_mode='extended')],
    [sg.Column(col1)],  # sg.Text(' Tags', size=(6, 1))], sg.Multiline(size=(20, 2), enable_events=True, key='tags')],
    #[sg.Text('')],
    [
    #sg.Button('Copy Random', key='copy random'),
    #sg.Text('', size=(47, 1)),
    ]
]

global window
window = sg.Window('Youtube Playlist Tool - ' + currentPlaylist[currentPlaylist.rfind('/') + 1:-1-3], layout, font='Courier 12', size=(windowSize),
                   resizable=True, icon='logo.ico').finalize()

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Exit':  # if user closes window or clicks cancel
        break

    if event == 'Add' or event == 'Add Videos':
        window2 = CreateWindowLayout(1)
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
                addLinks()
                break

    # When listbox is clicked
    if event == 'videos':
        try:
            if values['videos'][0] != '':

                videoId = values['videos'][0][0:11]
                print(videoId)

                title = db.get(Link.videoId == videoId)
                try:
                    title = title.get('title')

                    if title == "":
                        try:
                            ydl = youtube_dl.YoutubeDL({'outtmpl': '%(id)s.%(ext)s', 'cookiefile': 'cookies.txt'})
                            info = ydl.extract_info(values['videos'][0][0:11], download=False)
                            print(info['title'])
                            print(info['thumbnail'])
                            print(info['duration'])
                            print(info['uploader'])

                            video_duration = str(int(info['duration'] / 60))
                            video_duration = video_duration + ':' + str(info['duration'] % 60).zfill(2)

                            db.update(Set('title', info['title']), Link.videoId == videoId)
                            db.update(Set('thumbnail', info['thumbnail']), Link.videoId == videoId)
                            db.update(Set('duration', video_duration), Link.videoId == videoId)
                            db.update(Set('uploader', info['uploader']), Link.videoId == videoId)

                            vpos = window['videos'].Widget.yview()

                            window['videos'].update(viewData())
                            window['videos'].set_vscroll_position(vpos[0])

                        except youtube_dl.utils.DownloadError:
                            print('Unable to download video data')

                    data = db.get(Link.videoId == videoId)
                    print(data)
                    print('https://www.youtube.com/watch?v=' + data.get('videoId'))
                    print(data.get('title'))
                    print(data.get('thumbnail'))
                    print(data.get('duration'))
                    print(data.get('uploader'))

                except AttributeError:
                    print('Unable to find db entry')

        except IndexError:
            print('List is empty!')

    if event == 'Update' or event == 'Update Video Data':
        update()

    if event == 'Copy URL':
        urls = []

        for i in values['videos']:
            videoId = i[0:11]
            urls.append('https://www.youtube.com/watch?v=' + videoId)
            pyperclip.copy('\n'.join(urls))

    if event == 'Open URL':

        if values['videos']:
            videoId = values['videos'][0][0:11]
            url = 'https://www.youtube.com/watch?v=' + videoId
            webbrowser.open(url)

    if event == 'Play with mpv':
        urls = []

        for i in values['videos']:
            urls.append('https://youtu.be/' + i[0:11])

        urls = ' '.join(urls)

        with open('playWithMPV.bat', 'w', encoding='utf-8') as f:
            f.writelines('mpv ' + mpvArg + ' ' + urls)

        #subprocess.Popen('mpv ' + mpvArg + ' ' + urls, shell=True)
        subprocess.Popen('playWithMPV.bat', shell=True)

    if event == 'Delete video(s)':
        deleteVideos()

    if event == 'Copy' or event == 'Copy Videos to Clipboard':

        urls = []

        for i in filtering():
            urls.append('https://youtu.be/' + i[0:11])
            print('https://youtu.be/' + i[0:11])

        # Run shuffle based on radio button value
        if values['copy method'] is False:
            seed = random.randrange(sys.maxsize)
            random.seed(seed)
            random.shuffle(urls)
            print(str(len(urls)) + ' videos copied to clipboard (shuffled)')
            print('Seed')
            print(seed)
        else:
            print(str(len(urls)) + ' videos copied to clipboard')

        if values['copy type'] is True:
            pyperclip.copy('\n'.join(urls))
        else:
            pyperclip.copy(' '.join(urls))

    # Create playlist for Youtube
    # Very limited, not used atm (max 50 videos per playlist, playlist cannot be saved)
    if event == 'create playlist':
        urls = []

        for i in filtering():
            urls.append(i[0:11])

        random.shuffle(urls)

        for i in range(0, len(urls), 50):
            playlistUrl = 'http://www.youtube.com/watch_videos?video_ids=' + ','.join(urls[i:i + 50])
            print(playlistUrl + '\n')

    # For running db scripts, hidden in normal circumstances
    if event == 'Script':
        runScript(2)

    if event == 'clear':
        window['videoFilter'].update('')
        clear()

    if event == 'up':
        sortUp()

    if event == 'down':
        sortDown()

    if event == 'videoFilter':
        if len(values['videoFilter']) > 2:
            window['videos'].update(filtering())
        else:
            clear()

    if event == 'Open playlist':
        currentPlaylist = sg.popup_get_file('', title='Select Playlist',
                                          no_window=True, modal=True, keep_on_top=True, file_types=(('YPL files', '*.ypl'),), initial_folder=os.getcwd())
        if not currentPlaylist:
            print('No file selected!')
        else:
            db = TinyDB(currentPlaylist)
            config['DEFAULT']['current playlist'] = currentPlaylist

            if currentPlaylist not in recentFiles:
                if len(recentFiles) > 10:
                    recentFiles.pop(9)
                recentFiles.insert(0, currentPlaylist)
                menu_elem.Update(menu_def)
            config['HISTORY']['recent files'] = '\n'.join(recentFiles)

            window['videoFilter'].update('')
            window['videos'].update(viewData())
            window.TKroot.title('Youtube Playlist Tool - ' + currentPlaylist[currentPlaylist.rfind('/') + 1:-1-3])

            with open('config.ini', 'w',) as f:
                config.write(f)

    if event == 'New playlist':
        currentPlaylist = NewPlaylist('')

    if event == 'mpv arguments':
        arguments = sg.popup_get_text('Input mpv launch arguments', default_text=mpvArg)

        if arguments is not None:
            mpvArg = arguments
            config['DEFAULT']['mpv arguments'] = mpvArg
            with open('config.ini', 'w') as f:
                config.write(f)

    if event == 'Shuffle playlist':
        shufflePlaylist = True
        window['videos'].update(filtering())
        shufflePlaylist = False

    # Download a playlist from Google Sheets
    if event == 'Download playlist':
        currentPlaylist = downloadGSheets(currentPlaylist)

    # Upload a playlist into Google Sheets
    if event == 'Upload playlist':
        uploadGSheets(currentPlaylist)

    if event == 'Readme':
        webbrowser.open('https://github.com/CuriousCod/YoutubePlaylistTool/tree/master')

    if event == 'About':
        sg.popup('Youtube Playlist Tool v1.5.0\n\nhttps://github.com/CuriousCod/YoutubePlaylistTool\n',
                 title='About', icon='logo.ico')

    # Recent files event
    for i in recentFiles:
        if event == i:
            if os.path.isfile(i):
                currentPlaylist = i
                db = TinyDB(currentPlaylist)

                recentFiles.pop(recentFiles.index(i))
                recentFiles.insert(0, currentPlaylist)
                menu_elem.Update(menu_def)

                window['videoFilter'].update('')
                window['videos'].update(viewData())
                window.TKroot.title('Youtube Playlist Tool - ' + currentPlaylist[currentPlaylist.rfind('/') + 1:-1-3])

                config['DEFAULT']['current playlist'] = currentPlaylist
                config['HISTORY']['recent files'] = '\n'.join(recentFiles)

                with open('config.ini', 'w') as f:
                    config.write(f)
                break
            else:
                print('Playlist doesn\'t exist.')

    # Works perfectly when maximizing window, otherwise only updates when any action is taken in the window
    if windowSize != window.size:
        #print(window.size)
        CurrentWindowSize = window.size
        VideosElementSize = (int(CurrentWindowSize[0] * 0.1), int(CurrentWindowSize[1] * 0.045))
        #print(VideosElementSize)
        window['videos'].set_size(VideosElementSize)
        windowSize = window.size

window.close()
