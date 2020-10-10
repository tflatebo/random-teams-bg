# system packages
import unittest, pickledb, time, glob, os

# what we are testing
from random_teams_bg.util import is_hard_link, is_soft_link, is_recent_file, get_random_file

class TestRandomTeamsBG(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.src_dir = "test/data/src/"
        self.dst_dir = "test/data/dst/"
        self.db_name = "test/data/test.db"

        # setup files in src dir
        if not os.path.exists(self.src_dir):
            os.makedirs(self.src_dir)
        
        for f in ['file1', 'file2', 'file3']:
            fo = open(self.src_dir + f + '.jpg', 'w')
            fo.write(f)
            fo.close()
        
        # create hard link in dst dir
        os.link(self.src_dir + 'file1.jpg', self.dst_dir + 'hard_link.jpg')

        # create soft link in dst dir
        os.symlink(self.src_dir + 'file2.jpg', self.dst_dir + 'soft_link.jpg')

    @classmethod
    def tearDownClass(self):
        # clean up the dst dir
        dst_files = glob.glob(os.path.join(self.dst_dir, "*.jpg"))
        for f in dst_files:
            os.remove(f)

        # clean up the src dir
        src_files = glob.glob(os.path.join(self.src_dir, "*.jpg"))
        for f in src_files:
            os.remove(f)

    # setup the db every time
    def setUp(self):
        self.db = pickledb.load(self.db_name, False)
        yesterday = time.time() - 86400
        seven_days_ago = time.time() - (86400 * 7)
        tomorrow = time.time() + 86400

        # just in case, delete all keys from db
        self.db.deldb()

        # set keys in db
        self.db.set("file1.jpg", yesterday)
        self.db.set("file2.jpg", seven_days_ago)
        self.db.set("file3.jpg", tomorrow)

    def tearDown(self):
        self.db.deldb()

    # is a file a hard link?
    def test_hard_link(self):
        self.assertTrue(is_hard_link(self.dst_dir + "/hard_link.jpg"))

    # is a file a soft link?
    def test_soft_link(self):
        self.assertTrue(is_soft_link(self.dst_dir + "/soft_link.jpg"))

    # file1 is recent, and has a key that is from yesterday, which is less than 5 days ago
    def test_recent_file_with_one_day_old_key(self):        
        self.assertTrue(is_recent_file("file1.jpg", 5, self.db))

    # file2 is not recent, and has a key for 7 days ago
    def test_not_recent_file_with_seven_day_old_key(self):
        self.assertFalse(is_recent_file("file2.jpg", 5, self.db))

    # file3 is recent,has a key for tomorrow
    # if we treated this as not recent, the logic would be stupid 
    # and I don't want it to be complicated
    # also, if you wanted to blacklist a file, you could just put a very far future
    # timestamp in and it would never get used
    def test_recent_file_with_future_key(self):
        self.assertTrue(is_recent_file("file3.jpg", 5, self.db))

    # file999 doesn't exist, and is not recent
    def test_unknown_file_with_no_key(self):
        self.assertFalse(is_recent_file("file999.jpg", 5, self.db))

    # should only pick up any of the 3 files,
    def test_get_random_file_no_ttldb(self):
        list = ['file1.jpg', 'file2.jpg', 'file3.jpg']

        random_file = get_random_file(self.src_dir, self.db, False)

        self.assertTrue(random_file in list)

    # should still pick up file 2, but now we use the ttl db, and it should reset the key
    def test_get_random_file_use_ttldb(self):
        self.assertEqual(get_random_file(self.src_dir, self.db, True), 'file2.jpg')

        # since we picked up a file with an old key, it should have been reset, 
        # and should be more than 0 seconds old, and less than 5 seconds
        now = time.time()
        diff = now - self.db.get('file2.jpg')
        self.assertTrue(diff < 5)
        self.assertTrue(diff > 0)


if __name__ == "__main__":
    unittest.main()