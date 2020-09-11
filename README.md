# YoutubePlaylistTool
Create and manage Youtube playlists using URLs. Useful when creating a playlist for some video players, for example mpv (https://mpv.io).

<b>Work in progress</b>

<h3>Adding videos</h3>

- Press Add button in application to open the input window </br>
- Paste Youtube URLs to the list in this format: www.youtube.com/watch?v= </br>
  - You can also add a playlist by copying a playlist's source code to clipboard and pressing Add Source button </br>
- Press Add Links button

<h3>Managing videos</h3>

- To obtain video information press the Update button or click individual video ids on the list (Grab a coffee, if you have a lot of videos). </br>
- Copy buttons copy the displayed list to clipboard (original or random order)
- You can delete videos from list using mouse right-click
- List is automatically saved to the db.json file in the application folder

<h3>Notes</h3>

- <b>Filters do not work yet!</b> </br>
- Only one playlist is supported at the moment. </br>
  - You can create additional playlists by renaming the db.json file </br>
- You can add cookies.txt to the application folder to avoid youtube-dl's 429 error when downloading video information
