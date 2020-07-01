# random-teams-bg
Select a random background image for Microsoft Teams. I use this because MS Teams can be very slow to select custom images when you have more than a few in the custom folder. I actually found that the limit is 112 custom images, and if you have more than that MS Teams will crash when you try to select a background image.

This script will clean out any hard links in the destination folder, and place a hard link in there to a random file in the source folder.

You can run this as a daily cron job, or manually anytime you like.

#### usage
```bash
random-teams-bg.py src dst
```
#### example
```bash
random-teams-bg.py ~/Backgrounds/ ~/Library/Application Support/Microsoft/Teams/Backgrounds/Uploads
```

Where `~/Backgrounds` is where you have a collection of images, and `~/Library/Application Support/Microsoft/Teams/Backgrounds/Uploads` is the destination directory where MS Teams reads from.
