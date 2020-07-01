#!/usr/bin/python3

import sys, os, random, shutil, stat

src_dir = sys.argv[1]
dst_dir = sys.argv[2]

# get a random file with full path from the dir that is passed in
# returns a tuple of a full path for the src and destination that 
# includes the randomly chosen filename in the path, like
# returns: ('/full/path/to/randomfile.jpg', '/new/path/randomfile.jpg')
def get_random_file (src, dst) :
    
    src_contents = os.listdir(src) # returns list

    image_file = (random.choice(src_contents)) # get the randomly chosen filename

    src_path = src + "/" + image_file
    dst_path = dst + "/" + image_file

    return src_path, dst_path

# clean out the destination directory, but only remove hard links, this
# should protect against removing a bunch of files by mistake in case the 
# args are passed in out of order
def clean_dst_dir (dir) :

    for filename in os.listdir(dir):
        file_path = os.path.join(dir, filename)
        try:
            if is_hard_link(file_path): # only remove hard links
                os.unlink(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

# is something a hard link?
# return true if hard link
def is_hard_link(path):
    return os.lstat(path).st_nlink == 2

# is something a soft link?
# return true if soft link
def is_soft_link(path):
    return os.path.islink(path)


###
#
# Main

# clean out anything in the destionation directory
clean_dst_dir(dst_dir)

# pull a random filename out of the pool of available files in the src_dir
(src, dst) = get_random_file(src_dir, dst_dir)

# create hard link using the random file paths
os.link(src, dst)

#
#
###