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
    
    
def get_videos_for_topic(topic_id=None, topics=None):
    """Gets all video nodes under the topic ID.  
    If topid ID is None, returns all videos under the topics node. """
    
    if topics is None:
        topics = topicdata.TOPICS


    # Found the topic!
    if topics.get("id",None) and (topics.get("id")==topic_id or topic_id is None):
        videos = filter(lambda node: node["kind"] == "Video", topics["children"])

        # Recursive case: traverse children
        if topics.get("children",None):
            for topic in topics.get("children",[]):
                videos += get_videos_for_topic(topics=topic)

        return videos
        
    # Didn't find the topic, but it has children to check...
    elif topics.get("children",None):
        videos = []
        for topic in topics.get("children"):
            videos += get_videos_for_topic(topic_id, topic)
                
        return videos   
    
    # Didn't find the topic, and no children... 
    else:
        return []
        