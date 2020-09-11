import PySimpleGUI as sg
from tinydb import TinyDB, Query, where
import youtube_dl
from tinydb.operations import set as Set
import re, time, random
import pyperclip

sg.theme('Topanga')



menu_def = [['File', ['Select CustomLevels Folder', 'Exit']],
            ['Settings', ['Use Normal Auto Offset', 'Use Fast Auto Offset            X']],
            ['Help', 'About'], ]

menu_elem = sg.Menu(menu_def)

db = TinyDB('db.json')

Link = Query()


def viewData():
    titles = [i['title'] for i in db]
    ids = [i['videoId'] for i in db]
    dur = [i['duration'] for i in db]
    combine = []

    for (item1, item2, item3) in zip(ids, titles, dur):
        combine.append(item1 + ' - ' + item3 + ' - ' + item2)

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
    links.pop(0)
    links.pop()

    # Add youtube url format to the video id
    playlist = ['https://www.youtube.com/watch?v=' + i for i in links]

    return playlist

col1 = [
        [sg.Text('Filters', size=(38,2))],
        [sg.Text('Title', size=(38,1))],
        [sg.In(size=(38,2), key='Title')],
        [sg.Text('Author', size=(38, 1))],
        [sg.In(size=(38,2), key='Author')],
        [sg.Text('Tags', size=(38, 1))],
        [sg.In(size=(38,2), key='Tags')],
        [sg.Text('', size=(1, 1))],
        [sg.Button('Clear')],
        [sg.Text('', size=(38, 21))]
    ]

layout = [
#    [menu_elem],
    [sg.Listbox(values=viewData(), key='links', size=(100, 35), enable_events=True, right_click_menu=['&Right', ['Copy URL', 'Delete video']]),
     sg.Column(col1)],
    [sg.Button('Add'),
    sg.Button('Update'),
    sg.Button('Copy'),
    sg.Button('Copy Random', key='copy random')]
    #sg.Button('Script')] # For running quick db scripts

]

layout2 = [
    [sg.Multiline('', key='input', size=(48, 28), focus=True)],
    [sg.Button('Add links', key='add links'),
    sg.Button('Add source', key='add source')],
    [sg.Button('Cancel', key='cancel')]
]

global window
window = sg.Window('Youtube Playlist Tool', layout, font='Courier 12', size=(1280, 720)).finalize()
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

                    video_duration = str(int(info['duration'] / 60))
                    video_duration = video_duration + ':' + str(info['duration'] % 60).zfill(2)

                    db.update(Set('title', info['title']), Link.videoId == videoId)
                    db.update(Set('thumbnail', info['thumbnail']), Link.videoId == videoId)
                    db.update(Set('duration', video_duration), Link.videoId == videoId)
                    window['links'].update(viewData())

                url = db.get(Link.videoId == videoId)
                print('https://www.youtube.com/watch?v=' + url.get('videoId'))
                title = db.get(Link.videoId == videoId)
                print(title.get('title'))
                thumbnail = db.get(Link.videoId == videoId)
                print (thumbnail.get('thumbnail'))
                duration = db.get(Link.videoId == videoId)
                print (duration.get('duration'))
                uploader = db.get(Link.videoId == videoId)
                print (duration.get('uploader'))

        except IndexError:
            print('List is empty!')

    if event == 'Update':
        ids = [i['videoId'] for i in db]
        for i in ids:
            title = db.get(Link.videoId == i)
            title = title.get('title')
            if title == "":
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

window.close()