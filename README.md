# YoutubePlaylistTool
Create and manage Youtube playlists using URLs. Useful when creating a playlist for some video players, for example mpv (https://mpv.io).

<b>Work in progress</b>

<h3>Adding videos</h3>

- Press Add button in application to open the input window </br>
- Paste Youtube URLs to the list in this format: www.youtube.com/watch?v= </br>
  - You can also add a playlist by copying a playlist's source code to clipboard and pressing Add Source button </br>
- Press Add Links button

<h3>Managing videos</h3>

- To obtain video information press the Update button or click individual video ids on the list (grab a coffee, if you have a lot of videos). </br>
- Copy buttons copy the displayed list to clipboard (original or random order)
- You can delete videos from list using mouse right-click
- List is automatically saved to the defaultPlaylist.ypl file in the application folder
- You can create new playlists from the File menu
- Use the arrow buttons to reorder videos
- Filter searches through videoIDs and titles

<h3>Notes</h3>

- You cannot reorder videos while filtering at the moment
- You can add cookies.txt to the application folder to avoid youtube-dl's 429 error when downloading video information
