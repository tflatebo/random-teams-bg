# random-teams-bg
Select a random background image for Microsoft Teams. If you use the daily job, it will give you a new file every day to use as your background. If you manually put a file using the upload button in the Teams UI, it will leave those in place. The idea is you want to only have a few background images to select from to make it easy on you.

You will need to source your own background images and place them in the src_dir (see below). The script will then place a hard link to one of the files in your src_dir. Every time you run the script, it will destroy and recreate the hard link.

Because random turned out to not really be what I wanted, I added a ttl database (kv store using pickledb) so that it will only use files that haven't been used recently.

The algorithm goes like this:
1. Collect all filenames in src_dir into a list
2. Shuffle the list
3. Pop the first member off of the list
4. If the popped file hasn't been used in (total_files_in_src_dir/2) days, then return it, else pop next file
5. If the popped file has a key/ttl, but it is older than (total_files_in_src_dir/2) days, reset the key/ttl and return the file

If you don't want this feature, just set `usettldb=False` in the config file
 
I wrote this script because MS Teams can be very slow to select custom images when you have more than a few in the custom folder. I actually found that the limit is 112 custom images, and if you have more than that MS Teams will crash when you try to select a background image.

You can run this as a daily launchd job, or manually anytime you like. Launchd is recommended.

#### usage
```bash
random_teams_bg/util.py config_file
```
#### example
```bash
random_teams_bg/util.py config/teams_bg.cfg
```

You will need to edit the two config files:
````bash
config/random_teams_bg.cfg  # the config values for the scrip to run
config/teams.bg.plist       # config for running via launchd (recommended)
````

#### config file
````bash
[random_teams_bg]
src_dir=<your home dir>/Backgrounds/  # src dir for your background files
dst_dir=<your home dir>/Teams-BG/     # where this is a synlink to ~/Library/Application Support/Microsoft/Teams/Backgrounds/Uploads
db_name=<install location of the script>/random-teams-bg/bg.db
usettldb=True  # turn this on if you want to have files used every so often, this will put a ttl on the file: the count of files in the src_dir / 2 number of days, works best with more than 20 or so files. I have about 250.
overlay_logo=True # if you want to use the logo overlay feature you need this plus the next two
output_dir=<your home dir>/tmp # where will it write the output file (result.png) after the overlay
logo_file=<your home dir/logos/logo.png # where is the logo file that will get overlayed onto background. this should be a transparent PNG if you want it to look good
logo_file_light=<your home dir>/logos/logo_light.png # a lighter version of your logo, autodetects if the background is too dark and will use this
fixed_width=3968 # resize all backgrounds to this width
fixed_height=2232 # resize all backgrounds to this height
logo_offset_x=0.21 # place the logo image at this ratio of the bg width
logo_offset_y=0.15 # place logo at this ratio of bg height
````

### running this in launchd as a daily job

Using these sites as a guide: 
https://apple.stackexchange.com/questions/364973/how-can-i-use-home-or-environment-variable-in-plist-file-of-launchdaemons?noredirect=1&lq=1

#### Update the .plist file to customize to your install
Edit the .plist file to update to the time of day you want it to run at, and also where you are going to put your script, and where your backgrounds and symlink is for your teams uploads dir.

#### time of day to run:
```xml
    <key>Hour</key>
    <integer>07</integer>
    <key>Minute</key>
    <integer>35</integer>
```

#### place of your script, and config file, with full path:
```xml
<string>exec /usr/local/bin/python3 $HOME/software/development/github/random-teams-bg/random_teams_bg/util.py $HOME/software/development/github/random-teams-bg/config/random_teams_bg.cfg</string>
```

#### load your plist into launchd, it will run when you load, and then again every day at the time you specify:
```bash
cp teams.bg.plist $HOME/Library/LaunchAgents
launchctl load teams.bg.plist
ls -l /tmp/ # you should see two files, teams-bg.err and teams-bg.out with the current timestamp, the .out file will get updated every time it successfully runs
```

### tests
Run tests from the root of the project
```bash
# is you are using virtual env
source .venv/bin/activate
# run the tests
python -m unittest 
........
----------------------------------------------------------------------
Ran 8 tests in 0.003

OK
```

## LICENSE
MIT License