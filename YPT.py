import PySimpleGUI as sg
from tinydb import TinyDB, Query
import youtube_dl
from tinydb.operations import set as Set
import re, time, random, os, sys, webbrowser
from os import path
import pyperclip

# TODO Add total video count
# DONE Support for multiple db
# DONE Display current random seed
# TODO File open exception handling
# DONE Config.ini for default playlist
# DONE Add confirmation to video delete


def filtering():
    videos = db.search((Link.videoId.search(values['videoFilter'], flags=re.IGNORECASE)) |
                       (Link.videoId.search(values['videoFilter'][-11:], flags=re.IGNORECASE)) |  # For youtube URL
                       (Link.title.search(values['videoFilter'], flags=re.IGNORECASE)))

    combine = [i['videoId'] + ' - ' + i['duration'] + ' - ' + i['title'] for i in videos]

    return combine


def viewData():

    combine = [i['videoId'] + ' - ' + i['duration'] + ' - ' + i['title'] for i in db]

    return combine


def extractVideos():
    text = pyperclip.paste()
    print(text.find('\"playlist\":'))
    print(text.rfind('\"playlistEditEndpoint\"'))

    text = text[text.find('\"playlist\":'):text.rfind('\"Save playlist\"')]
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


def addWindow():

    layout2 = [
        [sg.Multiline('', key='input', size=(48, 28), focus=True, right_click_menu=['&Right', ['Paste']])],
        [sg.Button('Extract source', key='add source', size=(18, 2)),
         sg.Text(size=(16, 1)), sg.Button('Cancel', key='cancel', size=(7, 2)), sg.Button('OK', key='add links', size=(4, 2))]
    ]
    return sg.Window('Youtube Playlist Tool - Add Videos', layout2, font='Courier 12', modal=True)


sg.theme('Topanga')

menu_def = [['File', ['Open playlist', 'New playlist', 'Exit']],
            ['Help', 'About'], ]

menu_elem = sg.Menu(menu_def)

if path.exists('config.ini'):
    f = open('config.ini', 'r', encoding='utf-8')
    currentPlaylist = f.read()
    f.close()
else:
    currentPlaylist = 'defaultPlaylist.ypl'

db = TinyDB(currentPlaylist)
Link = Query()

layout = [
    [menu_elem],
    [sg.Listbox(values=viewData(), key='videos', size=(130, 36), enable_events=True,
                right_click_menu=['&Right', ['Copy URL', 'Open URL', 'Delete video(s)']],
                select_mode='extended')],
    [sg.Text('Filter', size=(6, 1)),
    sg.In(size=(20, 1), enable_events=True, key='videoFilter'),
    sg.Button('X', key='clear')],
    [sg.Text('')],
    [sg.Button('Add'),
    sg.Button('Update'),
    sg.Button('Copy'),
    sg.Button('Copy Random', key='copy random')
    #sg.Button('Create Playlist', key='create playlist'),
    #sg.Text('', size=(47, 1)),
    ]
    #sg.Button('Script')] # For running quick db scripts
]

global window
window = sg.Window('Youtube Playlist Tool - ' + currentPlaylist[0:-1-3], layout, font='Courier 12', size=(1280, 800)).finalize()

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Exit':  # if user closes window or clicks cancel
        break

    if event == 'Add':
        window2 = addWindow()
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

            if event == 'add links':
                links = values['input'].split('\n')
                print(links)

                for i in links:
                    if i.find('https://www.youtube.com/watch?v=') != -1:
                        videoId = i.find('watch?') + 8

                        if (db.contains(Link.videoId == i[videoId:videoId + 11])) is False:
                            db.insert({'videoId': i[videoId:videoId + 11]
                                       , 'title': '', 'thumbnail': '', 'duration': '', 'uploader': ''})

                window2['input'].update('')
                window['videos'].update(viewData())
                window2.close()
                window.refresh()
                break

    if event == 'videos':

        try:
            if values['videos'][0] != '':

                videoId = values['videos'][0][0:11]
                print(videoId)

                title = db.get(Link.videoId == videoId)
                title = title.get('title')

                if title == "":
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
                    window['videos'].update(viewData())

                data = db.get(Link.videoId == videoId)
                print(data)
                print('https://www.youtube.com/watch?v=' + data.get('videoId'))
                print(data.get('title'))
                print(data.get('thumbnail'))
                print(data.get('duration'))
                print(data.get('uploader'))

        except IndexError:
            print('List is empty!')

    if event == 'Update':
        ids = [i['videoId'] for i in db]
        missingData = []
        for i in ids:
            title = db.get(Link.videoId == i)
            title = title.get('title')
            if title == "":
                missingData.append(i)

        print(str(len(missingData)) + ' videos missing information.')
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

        window['videos'].update(viewData())

    if event == 'Copy URL':

        urls = []

        for i in values['videos']:
            videoId = i[0:11]
            urls.append('https://www.youtube.com/watch?v=' + videoId)
            pyperclip.copy('\n'.join(urls))

    if event == 'Open URL':
        videoId = values['videos'][0][0:11]
        url = 'https://www.youtube.com/watch?v=' + videoId
        webbrowser.open(url)

    if event == 'Delete video(s)':

        popupInput = sg.popup_yes_no('Delete selected videos?')
        if popupInput == 'Yes':
            urls = []

            for i in values['videos']:
                db.remove(Link.videoId == i[0:11])

            window['videos'].update(viewData())

    if event == 'Copy':
        urls = []

        for i in filtering():
            urls.append('https://www.youtube.com/watch?v=' + i[0:11])
            print('https://www.youtube.com/watch?v=' + i[0:11])

        pyperclip.copy('\n'.join(urls))
        print('Copied in original order')

    if event == 'copy random':
        urls = []

        for i in filtering():
            urls.append('https://www.youtube.com/watch?v=' + i[0:11])
            print('https://www.youtube.com/watch?v=' + i[0:11])

        seed = random.randrange(sys.maxsize)
        random.seed(seed)
        random.shuffle(urls)

        pyperclip.copy('\n'.join(urls))
        print('Copied in random order')
        print('Seed')
        print(seed)

    # Very limited, not used atm
    if event == 'create playlist':
        urls = []

        for i in filtering():
            urls.append(i[0:11])

        playlistUrl = 'http://www.youtube.com/watch_videos?video_ids=' + ','.join(urls)
        print(playlistUrl)

    # For running db scripts
    if event == 'Script':
        ids = [i['videoId'] for i in db]
        for i in ids:
            db.update(Set('uploader', ''), Link.videoId == i)

    if event == 'clear':
        window['videoFilter'].update('')
        window['videos'].update(viewData())

    if event == 'videoFilter':
        if len(values['videoFilter']) > 2:
            window['videos'].update(filtering())
        else:
            window['videos'].update(viewData())

    if event == 'Open playlist':
        currentPlaylist = sg.popup_get_file('', title='Select Playlist',
                                          no_window=True, modal=True, keep_on_top=True, file_types=(('YPL files', '*.ypl'),), initial_folder=os.getcwd())
        if not currentPlaylist:
            print('No file selected!')
        else:
            db = TinyDB(currentPlaylist)
            window['videos'].update(viewData())
            window.TKroot.title('Youtube Playlist Tool - ' + currentPlaylist[currentPlaylist.rfind('/') + 1:-1-3])

            f = open('config.ini', 'w', encoding='utf-8')
            f.writelines(currentPlaylist[currentPlaylist.rfind('/') + 1:])
            f.close()

    if event == 'New playlist':
        currentPlaylist = sg.popup_get_text('Input playlist name')
        db = TinyDB(currentPlaylist + '.ypl')
        window['videos'].update(viewData())
        window.TKroot.title('Youtube Playlist Tool - ' + currentPlaylist)

        f = open('config.ini', 'w', encoding='utf-8')
        f.writelines(currentPlaylist + '.ypl')
        f.close()

    if event == 'About':
        webbrowser.open('https://github.com/CuriousCod/YoutubePlaylistTool/tree/master')

window.close()