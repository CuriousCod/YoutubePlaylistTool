# YoutubePlaylistTool
Create, manage and play Youtube playlists using URLs. Optimized to playback videos with mpv (https://mpv.io).

<h3>Adding videos</h3>

- Press Add button to open the input window </br>
- Paste Youtube URLs to the list in this format: www.youtube.com/watch?v=[videoId] or https://youtu.be/[videoId] </br>
  - You can also add a playlist by copying a playlist's source code to clipboard and pressing Extract Source button or by pasting it to the textbox </br>

<h3>Managing videos</h3>

- To obtain video information press the Update button or click individual video ids on the list (grab a coffee, if you have a lot of videos). </br>
- Copy buttons copy the displayed list to clipboard (original or random order)
- You can delete videos from the list using mouse right-click
- List is automatically saved to the defaultPlaylist.ypl file in the application folder by default
- You can create new playlists from the File menu
- Use the arrow buttons to reorder videos
- Use Filter to search through videoIDs, titles and uploaders

<h3>Notes</h3>

- By adding mpv folder to path environment variable, you can play videos directly from the application assuming you have youtube-dl installed to mpv
  -  To play, press mouse right click on a video
- You can add cookies.txt to the application folder to avoid youtube-dl's 429 error when downloading video information
- Releases are compiled as .exe with auto-py-to-exe, this can cause false positives with anti-virus programs

![Preview image](https://www.dropbox.com/s/bslgt2uryabuu88/Screenshot%202021-08-23%2002.17.26.png?raw=1)
