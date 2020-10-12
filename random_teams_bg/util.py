import sys, os, random, shutil, stat, time, pickledb, configparser, logging

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
        return True

    # default is to return false, and allow the file to be used
    return False

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
            except Exception as e:
                print('Exception Reason: %s' % (e))
    except Exception as e:
        print('Exception Reason: %s' % (e))

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

###
#
# Main
# 
###

if __name__ == '__main__':
    try:
        cfg_file = sys.argv[1]
    except IndexError:
        cfg_file = "config/random_teams_bg.cfg"
  
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.INFO)

    configParser = configparser.RawConfigParser()   
    configParser.read(cfg_file)

    src_dir = configParser.get('random_teams_bg', 'src_dir')
    dst_dir = configParser.get('random_teams_bg', 'dst_dir')
    db_name = configParser.get('random_teams_bg', 'db_name')
    usettldb = configParser.get('random_teams_bg', 'usettldb')

    random.seed()

    # open the pickledb
    db = open_db(db_name)

    # clean out anything in the destionation directory
    clean_dst_dir(dst_dir)

    # pull a random filename out of the pool of available files in the src_dir
    file = get_random_file(src_dir, db, usettldb)

    # create hard link using the random file paths
    create_new_link(file, src_dir, dst_dir)

    logging.info("Created hard link for " + file + " in " + dst_dir)

    close_db(db)
