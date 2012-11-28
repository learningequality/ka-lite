from main import topicdata

def find_video_by_youtube_id(youtube_id, node=topicdata.TOPICS):
    if node.get("youtube_id", "") == youtube_id:
        return node
    for child in node.get("children", []):
        result = find_video_by_youtube_id(youtube_id, child)
        if result:
            print str(result) + "\n"

# find_video_by_youtube_id("NSSoMafbBqQ")

def get_all_youtube_ids(node):
    if node.get("youtube_id", ""):
        return [node.get("youtube_id", "")]
    ids = []
    for child in node.get("children", []):
        ids += get_all_youtube_ids(child)
    return ids

