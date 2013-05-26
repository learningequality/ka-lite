import glob, os
import logging
from main import topicdata

def find_videos_by_youtube_id(youtube_id, node=topicdata.TOPICS):
    videos = []
    if node.get("youtube_id", "") == youtube_id:
        videos.append(node)
    for child in node.get("children", []):
        videos += find_videos_by_youtube_id(youtube_id, child)
    return videos

# find_video_by_youtube_id("NSSoMafbBqQ")

def get_all_youtube_ids(node=topicdata.TOPICS):
    if node.get("youtube_id", ""):
        return [node.get("youtube_id", "")]
    ids = []
    for child in node.get("children", []):
        ids += get_all_youtube_ids(child)
    return ids

def get_dups(threshold=2):
    ids = get_all_youtube_ids()
    return [id for id in set(ids) if ids.count(id) >= threshold]
    
def print_videos(youtube_id):
    print "Videos with YouTube ID '%s':" % youtube_id
    for node in find_videos_by_youtube_id(youtube_id):
        print " > ".join(node["path"].split("/")[1:-3] + [node["title"]])
        
def get_downloaded_youtube_ids(videos_path="../content/"):
    return [path.split("/")[-1].split(".")[0] for path in glob.glob(videos_path + "*.mp4")]

def is_video_on_disk(youtube_id, videos_path="../content/"):
    return os.path.isfile(videos_path+youtube_id+".mp4")

def get_video_counts(topic, videos_path=None, db_name=None):
    """ Uses the (json) topic tree to query the django database for which video files exist
    
Returns the original topic dictionary, with two properties added to each NON-LEAF node:
  * nvideos_known: The # of videos in and under that node, that are known (i.e. in the Khan academy library)
  * nvideos_local: The # of vidoes in and under that node, that were actually downloaded and available locally
And the following property for leaf nodes:
  * on_disk
  
videos_path: the path to video files (Preferred method)
db_name: name of database to connect to (Old method) 
    """

    if videos_path:
        logging.debug("Using videos path = %s" % videos_path)
    elif db_name:
        logging.warn("Using old database method.  Inefficient and hacky!")
    else:
        raise NotImplementedException("Programming error: must specify vidoes_path or db_name")
        


    nvideos_local = 0
    nvideos_known = 0
    
    # Can't deal with leaves
    if not "children" in topic:
        raise Exception("should not be calling this function on leaves; it's inefficient!")
    
    # Only look for videos if there are more branches
    elif len(topic) > 0:
        # RECURSIVE CALL:
        #  The children have children, let them figure things out themselves
        # $ASSUMPTION: if first child is a branch, THEY'RE ALL BRANCHES.
        #              if first child is a leaf, THEY'RE ALL LEAVES
        if "children" in topic["children"][0]:
            for child in topic["children"]:
                (child,_,_) = get_video_counts(topic=child, videos_path=videos_path, db_name=db_name)
                nvideos_local += child['nvideos_local']
                nvideos_known += child['nvideos_known']
                
        # BASE CASE:
        # All my children are leaves, so we'll query here (a bit more efficient than 1 query per leaf)
        else:
            videos = topicdata.get_videos(topic)
            if len(videos) > 0:
                for video in videos:
                    video['on_disk'] = False
                if videos_path:
                    found_videos = []
                    for video in videos:
                        if is_video_on_disk(video['youtube_id'], videos_path):
                            found_videos.append((video['youtube_id'],))
                        
                elif db_name:
                    # build the list of videos
                    str = ""
                    for video in videos:
                        str = str+" or youtube_id='%s'"%(video['youtube_id'])
                    
                    query = """SELECT youtube_id FROM main_videofile WHERE %s"""%(str[4:])
            
                    # do a query to look for any of them
                    #import pdb; pdb.set_trace()
                    import sqlite3
                    conn = sqlite3.connect(db_name)
                    cursor = conn.cursor()
    
                    found_videos = cursor.execute(query)
                    found_videos = found_videos.fetchall()
                
                
                for fv_id in found_videos:
                    logging.debug('\t\tYoutube ID: %s'%fv_id[0])
                    topic_vid = find_videos_by_youtube_id(fv_id[0], node=topic)
                    if len(topic_vid)==1:
                        topic_vid[0]['on_disk'] = True

                nvideos_local = len(found_videos)
                nvideos_known = len(videos)
        
    topic['nvideos_local'] = nvideos_local
    topic['nvideos_known'] = nvideos_known
    return (topic, nvideos_local, nvideos_known)