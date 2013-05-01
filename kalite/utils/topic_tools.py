import glob
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
        
def get_downloaded_youtube_ids():
    return [path.split("/")[-1].split(".")[0] for path in glob.glob("../../content/*.mp4")]
    
def get_video_counts(topic, db_name):
    """ Uses the (json) topic tree to query the django database for which video files exist
    
Returns the original topic dictionary, with two properties added to each NON-LEAF node:
  * nvideos_known: The # of videos in and under that node, that are known (i.e. in the Khan academy library)
  * nvideos_local: The # of vidoes in and under that node, that were actually downloaded and available locally
And the following property for leaf nodes:
  * on_disk
    """

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
                (child['nvideos_local'], child['nvideos_known']) = get_video_counts(topic=child, db_name=db_name)
                nvideos_local += child['nvideos_local']
                nvideos_known += child['nvideos_known']
                
        # BASE CASE:
        # All my children are leaves, so we'll query here (a bit more efficient than 1 query per leaf)
        else:
            videos = topicdata.get_videos(topic)
            if len(videos) > 0:
                # build the list of videos
                str = ""
                for video in videos:
                    str = str+" or youtube_id='%s'"%(video['youtube_id'])
                    video['on_disk'] = False
                    
                query = """SELECT youtube_id FROM main_videofile WHERE %s"""%(str[4:])
            
                # do a query to look for any of them
                #import pdb; pdb.set_trace()
                import sqlite3
                conn = sqlite3.connect(db_name)
                cursor = conn.cursor()
    
                found_videos = cursor.execute(query)
                found_videos = found_videos.fetchall()
                for fv_id in found_videos:
                    topic_vid = filter(lambda node: node["kind"] == "Video" and node["youtube_id"]==fv_id[0], topic["children"])
                    if len(topic_vid)==1:
                        topic_vid[0]['on_disk'] = True

                nvideos_local = len(found_videos)
                nvideos_known = len(videos)
                
    return (nvideos_local, nvideos_known)