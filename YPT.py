import PySimpleGUI as sg
from tinydb import TinyDB, Query
import youtube_dl
from tinydb.operations import set as Set
import re, time, random
import pyperclip

# TODO Add total video count
# TODO Support for multiple db
# TODO Display current random seed

sg.theme('Topanga')

menu_def = [['File', ['Select CustomLevels Folder', 'Exit']],
            ['Settings', ['Use Normal Auto Offset', 'Use Fast Auto Offset            X']],
            ['Help', 'About'], ]

menu_elem = sg.Menu(menu_def)

db = TinyDB('db.json')

Link = Query()


def filtering():
    videos = db.search((Link.videoId.search(values['videoFilter'], flags=re.IGNORECASE)) |
                       (Link.videoId.search(values['videoFilter'][-11:], flags=re.IGNORECASE)) |
                       (Link.title.search(values['videoFilter'], flags=re.IGNORECASE)))

    combine = [i['videoId'] + ' - ' + i['duration'] + ' - ' + i['title'] for i in videos]

    return combine

def viewData():
    #titles = [i['title'] for i in db]
    #ids = [i['videoId'] for i in db]
    #dur = [i['duration'] for i in db]
    #combine = []

    combine = [i['videoId'] + ' - ' + i['duration'] + ' - ' + i['title'] for i in db]

    #for (item1, item2, item3) in zip(ids, titles, dur):
    #    combine.append(item1 + ' - ' + item3 + ' - ' + item2)

    return combine


def extractVideos():
    text = pyperclip.paste()
    links = []

    # Grab all unique matches with the key VideoId and add them to the list
    for match in re.finditer('\"videoId\"', text):
        e = match.end()
        url = text[e + 2:e + 13]

        if url not in links:
            links.append(url)

    # Remove first and last unrelated entries from the list
    try:
        links.pop(0)
        links.pop()
    except IndexError:
        return 'Found no videos'

    # Add youtube url format to the video id
    playlist = ['https://www.youtube.com/watch?v=' + i for i in links]

    return playlist

col1 = [ # Not in use
        [sg.Text('Filter', size=(38,2))],
        [sg.In(size=(38,2), enable_events=True, key='videoFilter')],
        [sg.Text('', size=(1, 1))],
        [sg.Button('Clear')],
        [sg.Text('', size=(38, 28))]

    ]

layout = [
#    [menu_elem],
    [sg.Listbox(values=viewData(), key='links', size=(130, 36), enable_events=True, right_click_menu=['&Right', ['Copy URL', 'Delete video']])],
    [sg.Text('Filter', size=(6, 1)),
    sg.In(size=(20, 1), enable_events=True, key='videoFilter'),
    sg.Button('X', key='clear')],
    [sg.Text('')],
    [sg.Button('Add'),
    sg.Button('Update'),
    sg.Button('Copy'),
    sg.Button('Copy Random', key='copy random'),
    sg.Text('', size=(47, 1)),
    ]
    #sg.Button('Script')] # For running quick db scripts

]

layout2 = [
    [sg.Multiline('', key='input', size=(48, 28), focus=True, right_click_menu=['&Right', ['Paste']])],
    [sg.Button('Add links', key='add links'),
    sg.Button('Add source', key='add source')],
    [sg.Button('Cancel', key='cancel')]
]

global window
window = sg.Window('Youtube Playlist Tool', layout, font='Courier 12', size=(1280, 800)).finalize()
window2 = sg.Window('Youtube Playlist Tool - Add Videos', layout2, font='Courier 12', disable_close=True).finalize()
window2.hide()

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Exit':  # if user closes window or clicks cancel
        break

    if event == 'Add':
        window2.un_hide()
        while True:
            event, values = window2.read()

            if event == sg.WIN_CLOSED or event == 'Exit':  # if user closes window or clicks cancel
                break

            if event == 'cancel':
                window2.hide()
                break

            if event == 'add source':
                    window2['input'].update(extractVideos())

            if event == 'Paste':
                window2['input'].update(pyperclip.paste())

            if event == 'add links':
                links = values['input'].split('\n')
                print(links)

                for i in links:
                    if i.find('https://www.youtube.com/watch?v=') != -1:
                        videoId = i.find('watch?') + 8
                        print('asd')

                        if (db.contains(Link.videoId == i[videoId:videoId + 11])) is False:
                            db.insert({'videoId': i[videoId:videoId + 11]
                                       , 'title': '', 'thumbnail': '', 'duration': '', 'uploader': ''})

                window2['input'].update('')
                window['links'].update(viewData())
                window2.hide()
                window.refresh()
                break

    if event == 'links':

        try:
            if values['links'][0] != '':

                videoId = values['links'][0][0:11]
                print(videoId)

                title = db.get(Link.videoId == videoId)
                title = title.get('title')

                if title == "":
                    ydl = youtube_dl.YoutubeDL({'outtmpl': '%(id)s.%(ext)s', 'cookiefile': 'cookies.txt'})
                    info = ydl.extract_info(values['links'][0][0:11], download=False)
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
                    window['links'].update(viewData())

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
        for i in ids:
            title = db.get(Link.videoId == i)
            title = title.get('title')
            if title == "":
                try:
                    ydl = youtube_dl.YoutubeDL({'outtmpl': '%(id)s.%(ext)s', 'cookiefile': 'cookies.txt'})
                    info = ydl.extract_info(i, download=False)
                    print(info['title'])
                    print(info['thumbnail'])
                    print(info['duration'])
                    print(info['uploader'])

                    video_duration = str(int(info['duration'] / 60))
                    video_duration = video_duration + ':' + str(info['duration'] % 60).zfill(2)

                    db.update(Set('title', info['title']), Link.videoId == i)
                    db.update(Set('thumbnail', info['thumbnail']), Link.videoId == i)
                    db.update(Set('duration', video_duration), Link.videoId == i)
                    db.update(Set('uploader', info['uploader']), Link.videoId == i)
                    time.sleep(3)
                except youtube_dl.utils.DownloadError:
                    print('Unable to download video information!')

        window['links'].update(viewData())

    if event == 'Copy URL':
        videoId = values['links'][0][0:11]
        url = 'https://www.youtube.com/watch?v=' + videoId
        pyperclip.copy(url)

    if event == 'Delete video':
        db.remove(Link.videoId == values['links'][0][0:11])
        window['links'].update(viewData())

    if event == 'Copy':
        ids = [i['videoId'] for i in db]
        urls = ['https://www.youtube.com/watch?v=' + i for i in ids]
        pyperclip.copy('\n'.join(urls))
        print('Copied in original order')

    if event == 'copy random':
        ids = [i['videoId'] for i in db]
        urls = ['https://www.youtube.com/watch?v=' + i for i in ids]
        random.shuffle(urls)
        pyperclip.copy('\n'.join(urls))
        print('Copied in random order')

    if event == 'Script':
        ids = [i['videoId'] for i in db]
        for i in ids:
            db.update(Set('uploader', ''), Link.videoId == i)

    if event == 'clear':
        window['videoFilter'].update('')
        window['links'].update(viewData())

    if event == 'videoFilter':
        if len(values['videoFilter']) > 2:
            window['links'].update(filtering())
        else:
            window['links'].update(viewData())

window.close()