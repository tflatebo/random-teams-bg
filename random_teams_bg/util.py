from PIL import Image
import sys, os, random, shutil, stat, time, pickledb, configparser, logging, argparse

# get a random file with full path from the dir that is passed in
# returns a tuple of a full path for the src and destination that 
# includes the randomly chosen filename in the path, like
# returns: ('/full/path/to/randomfile.jpg', '/new/path/randomfile.jpg')
def get_random_file(src, db, feature_usettldb):

    image_file = ''

    # returns list of files in src directory
    src_contents = os.listdir(src) 

    # randomize the list
    random.shuffle(src_contents)

    # for however many files there are in the directory
    # don't use a file for half that many
    #
    # for example, if there are 100 files in the dir, only use 
    # a file every 50 days
    limit = len(src_contents) / 2

    files = iter(src_contents)
    for file in files:
        # this keeps the algorithm from running out of files, and will always
        # at least select the last file
        image_file = file

        # should we use the ttldb to only select
        # files we haven't seen recently?
        if(feature_usettldb):
            # if we find a file that hasn't been recently used
            # stop and use it
            if not is_recent_file(file, limit, db):
                db.set(file, time.time())
                
                break

    return image_file

# this should return true if the file has been used "recently"
# meaning that if the file's timestamp in the db is less than 
# the limit, it is recently used, and we don't want to reuse it
def is_recent_file(file, limit, db):

    now = time.time()
    date = db.get(file)
    diff = now - date

    # if the file has a key, and the time since the key was used is less than the limit,
    # then it is a recent file
    if diff < (limit * 86400):
        logging.info("Found recently used file, skipping: " + file)
        return True

    # default is to return false, and allow the file to be used
    return False

# get a list of photos from an album
def get_google_photo_list(album_url):
    return 'foo'

# clean out the destination directory, but only remove hard links, this
# should protect against removing a bunch of files by mistake in case the 
# args are passed in out of order
def clean_dst_dir (dir) :

    try:
        for filename in os.listdir(dir):
            file_path = os.path.join(dir, filename)
            try:
                if is_hard_link(file_path): # only remove hard links
                    os.unlink(file_path)
                elif ("thumb." in file_path):
                    os.unlink(file_path)
                elif ("result.png" in file_path):
                    os.unlink(file_path)
                else:
                    logging.info('not cleaning ' + file_path)
            except Exception as e:
                logging.exception('Caught exception cleaning dst dir: %s' % (e))
    except Exception as e:
        logging.exception('Caught exception cleaning dst dir: %s' % (e))

# is something a hard link?
# return true if hard link
def is_hard_link(path):
    return os.lstat(path).st_nlink == 2

# is something a soft link?
# return true if soft link
def is_soft_link(path):
    return os.path.islink(path)

# open up the database
def open_db(name):
    try:
        db = pickledb.load(name, False)
    except Exception as e:
        logging.exception('Exception Reason: %s' % (e))
    
    return db

def close_db(db):
    db.dump()

def create_new_link(file, src_dir, dst_dir):
    src = src_dir + "/" + file
    dst = dst_dir + "/" + file

    os.link(src, dst)

# use an image to overlay onto the background
# generally this is a transparent PNG that is a logo 
# of some kind. this will place it at 0,20 (left top, 20 pixels down) 
# 
# since images can be all different aspect ratios 
# recently Google camera prefers a 4:3 or 1.333 ratio,
# and MS teams doesn't like that on my monitors, and my resolution 
# is 1080p so if the image isn't a 16:9 ratio (1.7777)
# the top and bottom get cut off. this will resize both the background 
# to that ratio and also resize the logo to fit according to a 
# 7.75:1 ratio (meaning there would be 7.75 widths of the logo in the image)
# 
# To use the Image.paste function, we also have to create a new transparent overlay
# that is the exact same size as the background, then put the logo onto that, 
# then paste that new transparent image onto the background. its easier.
# 
# this will save the new composited file into the config:output_dir/result.png
# then make a hardlink into config:dst_dir so the source image isn't modified
def overlay_logo(bg_filename, logo_filename, logo_filename_light, result_filename):

    background = Image.open(bg_filename).convert("RGBA")

    logging.info("resizing background from (w,h) " + str(background.size) + " to " + str((fixed_width, fixed_height)))
    new_background = background.resize((fixed_width, fixed_height))

    # find out what the new overlay size should be based on the background size
    # we use a ratio based on a 3968 bg image width
    # and a 512x384 overlay size
    new_owidth = int(fixed_width * (512/3968))
    new_oheight = int(new_owidth * (384/512))

    logo_offsetx = int(logo_offset[0] * fixed_width)
    logo_offsety = int(logo_offset[1] * fixed_height)

    # find out if the box where the overlay goes is light or dark
    if(background_is_dark(file, (logo_offsetx, logo_offsety, logo_offsetx + new_owidth, logo_offsety + new_oheight))):
        logo_filename = logo_filename_light

    overlay = Image.open(logo_filename).convert("RGBA")
    
    # resize the overlay to fit with the background image
    new_overlay = overlay.resize((new_owidth, new_oheight))

    # create a new empty overlay the same size as the background
    large_overlay = Image.new('RGBA', new_background.size, (255, 0, 0, 0))

    # paste the overlay logo onto the empty overlay in prep for pasting
    large_overlay.paste(new_overlay, (logo_offsetx, logo_offsety), new_overlay)

    # paste the overlay onto the same sized background
    new_background.paste(large_overlay, (0,0), large_overlay)

    # save the resulting image as a png
    return new_background.save(result_filename, "PNG")

# is the area where we are going to paste light or darK? if its lighter we use the standard 
# logo, otherwise we use the lighter logo against a dark background area
def background_is_dark(image_filename, box):

    img = Image.open(image_filename).convert("L")

    # crop to the rectangle where the overlay will
    sub_img = img.crop(box)

    pixel_map = sub_img.load()

    # inspect all pixels in the sub_img to see if they are dark
    dark_count = 0
    for x in range(sub_img.width):
        for y in range(sub_img.height):
            pixel = pixel_map[x,y]
            # if the grayscale of the pixel is less than 128 mark it as dark
            if(pixel < 128):
                dark_count = dark_count + 1

    logging.info("dark_count: " + str(dark_count) + " of " + str(sub_img.width * sub_img.height))

    # if more than 30% of the pixels are marked as dark, use the lighter image
    return dark_count > (sub_img.width * sub_img.height * 0.25)


###
#
# Main
# 
###

if __name__ == '__main__':

    file = None

    parser = argparse.ArgumentParser(description='Make a background for MS Teams.')
    parser.add_argument('cfg_file')
    parser.add_argument('--cfg', dest='cfg_file', default='config/random_teams_bg.cfg', help='Location of the config file')
    parser.add_argument('--file', dest='file', help='process source image file rather than from the source dir, must be absolute path')

    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.INFO)

    configParser = configparser.RawConfigParser()   
    configParser.read(args.cfg_file)

    # where are the background images
    src_dir = configParser.get('random_teams_bg', 'src_dir')
    # where is teams going to look for backgrounds
    dst_dir = configParser.get('random_teams_bg', 'dst_dir')
    # what is the ttl db name
    db_name = configParser.get('random_teams_bg', 'db_name')
    # shoudl we use a db to prevent using the same background too often?
    usettldb = configParser.get('random_teams_bg', 'usettldb')
    # should we use an overlay logo?
    logo = configParser.get('random_teams_bg', 'overlay_logo')
    # where does the output file get saved
    output_dir = configParser.get('random_teams_bg', 'output_dir')
    # where do we get the logo image from 
    logo_file = configParser.get('random_teams_bg', 'logo_file')
    # lighter logo for darker backgrounds
    logo_file_light = configParser.get('random_teams_bg', 'logo_file_light')
    # where to place the logo onto the background
    logo_offset = (float(configParser.get('random_teams_bg', 'logo_offset_x')), float(configParser.get('random_teams_bg', 'logo_offset_y')))
    # bring in the fixed width and height to resize all background images to
    fixed_width = int(configParser.get('random_teams_bg', 'fixed_width'))
    fixed_height = int(configParser.get('random_teams_bg', 'fixed_height'))

    random.seed()

    # open the pickledb
    db = open_db(db_name)

    # clean out anything in the destination directory
    clean_dst_dir(dst_dir)
    
    if args.file is None:
        # pull a random filename out of the pool of available files in the src_dir
        file = src_dir + '/' + get_random_file(src_dir, db, usettldb)
        logging.info("Picked " + file + " for background")
    else:
        file = args.file

    logging.info("file: " + file)

    # overlay a logo if configured to do so, also resizes background to configured size
    if(logo == 'True'):        
        overlay_logo(file, logo_file, logo_file_light, output_dir + "/result.png")
        file = "result.png"
        src_dir = output_dir

    # create hard link using the random file paths
    # this is what makes it available to MS Teams
    # recently I noticed you have to restart MS Teams to get it to 
    # recognize the image
    create_new_link(file, src_dir, dst_dir)

    logging.info("Created hard link for " + file + " in " + dst_dir)

    close_db(db)
