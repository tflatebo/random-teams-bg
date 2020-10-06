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

### running this in launchd as a daily job

Using these sites as a guide: 
https://apple.stackexchange.com/questions/364973/how-can-i-use-home-or-environment-variable-in-plist-file-of-launchdaemons?noredirect=1&lq=1

#### Update the .plist file to customize to your install
Edit the .plist file to update to the time of day you want it to run at, and also where you are going to put your script, and where your backgrounds and symlink is for your teams uploads dir.

#### Time of day to run:
```xml
            <key>Hour</key>
            <integer>07</integer>
            <key>Minute</key>
            <integer>35</integer>
```

#### Place of your script, backgrounds src dir and teams dst dir:
```xml
<string>exec /usr/local/bin/python3 $HOME/software/development/github/random-teams-bg/random-teams-bg.py $HOME/Backgrounds $HOME/Teams-BG</string>
```

#### Load your plist into launchd, it will run when you load, and then again every day at the time you specify:
```bash
cp random.teams.bg.plist $HOME/Library/LaunchAgents
launchctl load random.teams.bg.plist
```