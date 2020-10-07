import PySimpleGUI as sg
from tinydb import TinyDB, Query
import youtube_dl
from tinydb.operations import set as Set
import re, time, random, os, sys, webbrowser, subprocess
from os import path
import pyperclip

# DONE Add total video count -> Printed when pressing copy
# DONE Support for multiple db
# DONE Display current random seed
# DONE File open exception handling
# DONE Config.ini for default playlist
# DONE Add confirmation to video delete
# TODO Add recent playlists feature
# DONE youtu.be links
# DONE Tagging -> Added filter for uploaders, tagging is probably not necessary
# DONE Reorder playlist
# DONE Fix reordering bugs: Behavior during filtering
# TODO Remove copy order commands and switch it to displaying the list in random or default order
# DONE What to do with deleted video order numbers -> Reorder
# DONE Source file grabbing with Chrome, makes last line garbage -> Culture
# TODO More dynamic playlist filepath -> partially done, creating new playlist doesn't allow different directory
# TODO Sort by name
# TODO Source extraction, again


def filtering():

    global globalOrder
    combine = []

    videos = db.search((Link.videoId.search(values['videoFilter'], flags=re.IGNORECASE)) |
                       (Link.videoId.search(values['videoFilter'][-11:], flags=re.IGNORECASE)) |  # For youtube URL
                       (Link.title.search(values['videoFilter'], flags=re.IGNORECASE)) |
                       (Link.uploader.search(values['videoFilter'], flags=re.IGNORECASE)))

    videoData = [i['videoId'] + ' - ' + i['duration'] + ' - ' + i['title'] for i in videos]

    # Grabbing video order info and formatting it into 0000
    # This is actually faster than searching through the database for the video order
    order = [int(i['order']) for i in videos]

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

    #window['up'].update(disabled=True)
    #window['down'].update(disabled=True)

    # List variable for reordering purposes
    # For some reason .sort() also affects the order list <_<
    globalOrder = order
    globalOrder.sort()
    globalOrder = list(map(int, globalOrder))
    globalOrder = list(map(str, globalOrder))

    return combine


def viewData():

    global globalOrder
    combine = []

    # Get total db entries and sort by order, this is slow
    #for i in range(len(db))[1:]:
     #   x = db.get(Link.order == str(i))

      #  combine.append(x['videoId'] + ' - ' + x['duration'] + ' - ' + x['title'])

    videoData = [i['videoId'] + ' - ' + i['duration'] + ' - ' + i['title'] for i in db]

    # Grabbing video order info and formatting it into 0000
    # This is actually faster than searching through the database for the video order
    try:
        order = [int(i['order']) for i in db]

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
        # For some reason .sort() also affects the order list <_<
        globalOrder = order
        globalOrder.sort()
        globalOrder = list(map(int, globalOrder))
        globalOrder = list(map(str, globalOrder))

    # In case of missing video order information run script
    except KeyError:
        runScript(2)
        viewData()

    return combine


def extractVideos():
    text = pyperclip.paste()
    print(text.find('\"playlist\":'))
    print(text.rfind('\"playlistEditEndpoint\"'))

    text = text[text.find('\"playlist\":'):text.rfind('\"toggledAccessibilityData\"')]
    links = []

    # Grab all unique matches with the key VideoId and add them to the list
    for match in re.finditer('\"videoId\"', text):
        e = match.end()
        url = text[e + 2:e + 13]

        if url not in links:
            links.append(url)

    # Add youtube url format to the video id
    playlist = ['https://www.youtube.com/watch?v=' + i for i in links]

    if not playlist:
        return ['No videos found']
    else:
        return playlist


def CreateWindowLayout(createWindow):

    if createWindow == 1:
        layout = [
            [sg.Multiline('', key='input', size=(48, 28), enable_events=True, focus=True, right_click_menu=['&Right', ['Paste']])],
            [sg.Button('Extract source', key='add source', size=(18, 2)),
             sg.Text(size=(16, 1)), sg.Button('Cancel', key='cancel', size=(7, 2)), sg.Button('OK', key='add links', size=(4, 2))]
        ]
        windowTitle = 'Youtube Playlist Tool - Add Videos'

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


# Open playlist db
def openPlaylist():

    global currentPlaylist, mpvArg, db

    # Check config.ini for playlist name
    if path.exists('config.ini'):
        f = open('config.ini', 'r', encoding='utf-8')
        currentPlaylist = f.readline().rstrip('\n')
        mpvArg = f.readline()
        if mpvArg == '':
            mpvArg = '--slang=eng,en --fs --fs-screen=2 --sub-font-size=46'
        f.close()
    else:
        currentPlaylist = 'defaultPlaylist.ypl'
        mpvArg = '--slang=eng,en --fs --fs-screen=2 --sub-font-size=46'
        f = open('config.ini', 'w', encoding='utf-8')
        f.writelines([currentPlaylist, '\n', mpvArg])
        f.close()

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


sg.theme('Topanga')

menu_def = [['File', ['Open playlist', 'New playlist', 'Exit']],
            ['Settings', ['mpv arguments', 'Shuffle playlist']],
            ['Help', ['Readme', 'About']], ]

menu_elem = sg.Menu(menu_def)

openPlaylist()
Link = Query()
windowSize = (1280, 810)  # Default window size

global shufflePlaylist
shufflePlaylist = False

col1 = [
    [sg.Text('Filter', size=(6, 1)),
    sg.In(size=(20, 1), enable_events=True, key='videoFilter'),
    sg.Button('X', key='clear'), sg.Text(' Reorder'), sg.Button('↑', key='up'), sg.Button('↓', key='down'), sg.Text(' Copy method')],
    [sg.Text('', size=(46, 1)), sg.Radio('Normal', group_id='method', default=True, key='copy method'), sg.Radio('Shuffled', group_id='method')],
    [sg.Button('Add'),
    sg.Button('Update'),
    #sg.Button('Create Playlist', key='create playlist'),
    sg.Button('Copy'), sg.Text('', size=(26, 1), pad=(8, 1)), sg.Radio('List  ', group_id='type', default=True, key='copy type'), sg.Radio('mpv list', group_id='type')],
    #[sg.Button('Script')]  # For running quick db scripts
]

layout = [
    [menu_elem],
    [sg.Listbox(values=viewData(), key='videos', size=(130, 36), enable_events=True,
                right_click_menu=['&Right', ['Copy URL', 'Open URL', 'Play with mpv', 'Delete video(s)']],
                select_mode='extended')],
    [sg.Column(col1)], # sg.Text(' Tags', size=(6, 1))], sg.Multiline(size=(20, 2), enable_events=True, key='tags')],
    #[sg.Text('')],
    [
    #sg.Button('Copy Random', key='copy random'),
    #sg.Text('', size=(47, 1)),
    ]
]

global window
window = sg.Window('Youtube Playlist Tool - ' + currentPlaylist[currentPlaylist.find('/') + 1:-1-3], layout, font='Courier 12', size=(windowSize),
                   resizable=True, icon='logo.ico').finalize()

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Exit':  # if user closes window or clicks cancel
        break

    if event == 'Add':
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

    if event == 'Update':
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
            urls.append('https://www.youtube.com/watch?v=' + i[0:11])

        urls = ' '.join(urls)

        subprocess.Popen('mpv ' + mpvArg + ' ' + urls, shell=True)

    if event == 'Delete video(s)':
        deleteVideos()

    if event == 'Copy':

        urls = []

        for i in filtering():
            urls.append('https://www.youtube.com/watch?v=' + i[0:11])
            print('https://www.youtube.com/watch?v=' + i[0:11])

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

        playlistUrl = 'http://www.youtube.com/watch_videos?video_ids=' + ','.join(urls)
        print(playlistUrl)

    # For running db scripts
    if event == 'Script':
        runScript(2)

    if event == 'clear':
        window['videoFilter'].update('')
        clear()

    if event == 'up':

        selection = values['videos']

        for i in values['videos']:

            # Current selection
            x = db.get(Link.videoId == i[0:11])

            # Video above the selection
            #y = db.get(Link.order == str(int(x['order']) - 1))
            y = db.get(Link.order == str(globalOrder[globalOrder.index(x['order']) - 1]))

            # Check if video is on the top of the list
            #if y is not None:
            if globalOrder.index(x['order']) != 0:
                #db.update(Set('order', str(int(x['order']) - 1)), Link.videoId == x['videoId'])
                #db.update(Set('order', str(int(y['order']) + 1)), Link.videoId == y['videoId'])
                db.update(Set('order', str(globalOrder[globalOrder.index(x['order'])])), Link.videoId == y['videoId'])
                db.update(Set('order', str(globalOrder[globalOrder.index(x['order']) - 1])), Link.videoId == x['videoId'])
            #else:
                #break

        vpos = window['videos'].Widget.yview()

        window['videos'].update(filtering())
        window['videos'].SetValue(selection)
        window['videos'].set_vscroll_position(vpos[0])
        window.refresh()

    if event == 'down':

        selection = values['videos']

        # Reverse the list, when traveling downwards
        for i in reversed(values['videos']):

            # Current selection
            x = db.get(Link.videoId == i[0:11])

            # Video below the selection
            #y = db.get(Link.order == str(int(x['order']) + 1))
            try:
                y = db.get(Link.order == str(globalOrder[globalOrder.index(x['order']) + 1]))

                # Old way to check if video is on the bottom of the list, doesn't actually do anything atm
                if y is not None:
                    #db.update(Set('order', str(int(x['order']) + 1)), Link.videoId == x['videoId'])
                    #db.update(Set('order', str(int(y['order']) - 1)), Link.videoId == y['videoId'])
                    db.update(Set('order', str(globalOrder[globalOrder.index(x['order'])])), Link.videoId == y['videoId'])
                    db.update(Set('order', str(globalOrder[globalOrder.index(x['order']) + 1])), Link.videoId == x['videoId'])
                #else:
                 #   break

            # When at the bottom of the list, interestingly this exception this doesn't occur on the top of the list
            except IndexError:
                continue

        vpos = window['videos'].Widget.yview()

        window['videos'].update(filtering())
        window['videos'].SetValue(selection)
        window['videos'].set_vscroll_position(vpos[0])
        window.refresh()

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
            window['videoFilter'].update('')
            window['videos'].update(viewData())
            window.TKroot.title('Youtube Playlist Tool - ' + currentPlaylist[currentPlaylist.rfind('/') + 1:-1-3])

            with open('config.ini', 'w', encoding='utf-8') as f:
                f.writelines([currentPlaylist, '\n', mpvArg])

    if event == 'New playlist':
        currentPlaylist = sg.popup_get_text('Input playlist name')

        if currentPlaylist is not None:

            db = TinyDB(currentPlaylist + '.ypl')
            window['videoFilter'].update('')
            window['videos'].update(viewData())
            window.TKroot.title('Youtube Playlist Tool - ' + currentPlaylist)

            with open('config.ini', 'w', encoding='utf-8') as f:
                f.writelines([currentPlaylist + '.ypl', '\n', mpvArg])

    if event == 'mpv arguments':
        mpvArg = sg.popup_get_text('Input mpv launch arguments', default_text=mpvArg)

        if mpvArg is not None:
            with open('config.ini', 'w', encoding='utf-8') as f:
                f.writelines([currentPlaylist, '\n', mpvArg])
        else:
            mpvArg = ''

    if event == 'Shuffle playlist':
        shufflePlaylist = True
        window['videos'].update(filtering())
        shufflePlaylist = False

    if event == 'Readme':
        webbrowser.open('https://github.com/CuriousCod/YoutubePlaylistTool/tree/master')

    if event == 'About':
        sg.popup('Youtube Playlist Tool v1.4\n\nhttps://github.com/CuriousCod/YoutubePlaylistTool\n',
                 title='About', icon='logo.ico')

    # Works perfectly when maximizing window, otherwise only updates when any action is taken in the window
    if windowSize != window.size:
        print(window.size)
        CurrentWindowSize = window.size
        VideosElementSize = (int(CurrentWindowSize[0] * 0.1), int(CurrentWindowSize[1] * 0.044))
        print(VideosElementSize)
        window['videos'].set_size(VideosElementSize)
        windowSize = window.size

window.close()
