import glob, os
import logging

from kalite import settings
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
        
def get_downloaded_youtube_ids(videos_path=settings.CONTENT_ROOT):
    return [path.split("/")[-1].split(".")[0] for path in glob.glob(videos_path + "*.mp4")]

def is_video_on_disk(youtube_id, videos_path=settings.CONTENT_ROOT):
    return os.path.isfile(videos_path+youtube_id+".mp4")


_vid_last_updated = 0
_vid_last_count = 0

def video_counts_need_update(videos_path=settings.CONTENT_ROOT):
    global _vid_last_count
    global _vid_last_updated
    
    if not os.path.exists(videos_path):
        return False
        
    files = os.listdir(videos_path)

    vid_count = len(files)
    if vid_count:
        # TODO(bcipolli) implement this as a linear search, rather than sort-then-select.
        vid_last_updated = os.path.getmtime(sorted([(videos_path + f) for f in files], key=os.path.getmtime, reverse=True)[0])
    else:
        vid_last_updated = 0
    need_update = (vid_count != _vid_last_count) or (vid_last_updated != _vid_last_updated)
    
    _vid_last_count   = vid_count
    _vid_last_updated = vid_last_updated
    
    return need_update
    
    
def get_video_counts(topic, videos_path, force=False):
    """ Uses the (json) topic tree to query the django database for which video files exist
    
    Returns the original topic dictionary, with two properties added to each NON-LEAF node:
      * nvideos_known: The # of videos in and under that node, that are known (i.e. in the Khan Academy library)
      * nvideos_local: The # of vidoes in and under that node, that were actually downloaded and available locally
    And the following property for leaf nodes:
      * on_disk

    Input Parameters:  
    * videos_path: the path to video files
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
                (child,_,_) = get_video_counts(topic=child, videos_path=videos_path)
                nvideos_local += child["nvideos_local"]
                nvideos_known += child["nvideos_known"]
                
        # BASE CASE:
        # All my children are leaves, so we'll query here (a bit more efficient than 1 query per leaf)
        else:
            videos = topicdata.get_videos(topic)
            if len(videos) > 0:
            
                found_videos = []
                for video in videos:
                    # Mark all videos as not found
                    video["on_disk"] = is_video_on_disk(video["youtube_id"], videos_path)
                    
                    # Find the video on disk
                    if video["on_disk"]:
                        found_videos.append((video["youtube_id"],))
                        nvideos_local += 1
                nvideos_known = len(videos)
        
    topic["nvideos_local"] = nvideos_local
    topic["nvideos_known"] = nvideos_known
    return (topic, nvideos_local, nvideos_known)