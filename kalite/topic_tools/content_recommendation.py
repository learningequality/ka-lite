'''
All logic for generating and retriving content recommendations.
Three main functions:
    - get_resume_recommendations(user)
    - get_next_recommendations(user)
    - get_explore_recommendations(user)
'''
import datetime
import random
import collections

from django.db.models import Count

# TODO(benjaoming) this wildcard is crazy, needs to be burned
from kalite.topic_tools import *

from . import settings

from kalite.main.models import ExerciseLog, VideoLog, ContentLog

from kalite.facility.models import FacilityUser

def get_resume_recommendations(user, request):
    """Get the recommendation for the Resume section.

    Logic:
    Find the most recent incomplete item (video or exercise) and
    return that as the recommendation.
    Args:
    user -- The current user as a facility user model object.

    """

    final = get_most_recent_incomplete_item(user)
    if final:
        if final.get("kind") == "Content":
            return [get_content_data(request, final.get("id"))]
        if final.get("kind") == "Exercise":
            return [get_exercise_data(request, final.get("id"))]
    else:
        return []



def get_next_recommendations(user, request):
    """Get the recommendations for the Next section, and return them as a list.

    Logic:
    Next recommendations are currently comprised of 3 main subgroups: group recommendations,
    struggling exercises, and topic tree based data. Group recommendations consist of 
    finding the most common item tackled immediately after the most recent item, struggling
    is determined by the "struggling" model attribute, and topic tree data is based off
    the graphical distance between neighboring exercise/topic nodes. 
    Args:
    user -- The current user as a facility user model object.

    """

    exercise_parents_table = get_exercise_parents_lookup_table()

    most_recent = get_most_recent_exercises(user)

    if len(most_recent) > 0 and most_recent[0] in exercise_parents_table:
        current_subtopic = exercise_parents_table[most_recent[0]]['subtopic_id']
    else:
        current_subtopic = None

    #logic for recommendations based off of the topic tree structure
    if current_subtopic:
        topic_tree_based_data = generate_recommendation_data()[current_subtopic]['related_subtopics'][:settings.TOPIC_RECOMMENDATION_DEPTH]
        topic_tree_based_data = get_exercises_from_topics(topic_tree_based_data)
    else:
        topic_tree_based_data = []
    
    #for checking that only exercises that have not been accessed are returned
    topic_tree_based_data = [ex for ex in topic_tree_based_data if not ex in most_recent] 

    #logic to generate recommendations based on exercises student is struggling with
    struggling = get_exercise_prereqs(get_struggling_exercises(user))   

    #logic to get recommendations based on group patterns, if applicable
    group = get_group_recommendations(user)

   
    #now append titles and other metadata to each exercise id
    final = [] # final data to return
    for exercise_id in (group[:2] + struggling[:2] + topic_tree_based_data[:1]):  #notice the concatenation

        if exercise_id in exercise_parents_table:
            subtopic_id = exercise_parents_table[exercise_id]['subtopic_id']
            exercise = get_exercise_data(request, exercise_id)
            exercise["topic"] = get_topic_data(request, subtopic_id)
            final.append(exercise)


    #final recommendations are a combination of struggling, group filtering, and topic_tree filtering
    return final

def get_group_recommendations(user):
    """Returns a list of exercises immediately tackled by other individuals in the same group."""

    recent_exercises = get_most_recent_exercises(user)
    
    user_list = FacilityUser.objects.filter(group=user.group)

    if recent_exercises:

        #If the user has recently engaged with exercises, use these exercises as the basis for filtering
        user_exercises = ExerciseLog.objects\
            .filter(user__in=user_list).order_by("-latest_activity_timestamp")\
            .extra(select={'null_complete': "completion_timestamp is null"},
                order_by=["-null_complete", "-completion_timestamp"])
    
        exercise_counts = collections.defaultdict(lambda :0)

        for user in user_list:
            user_logs = user_exercises.filter(user=user)
            for i, log in enumerate(user_logs[1:]):
                prev_log = user_logs[i]
                if log.exercise_id in recent_exercises:
                    exercise_counts[prev_log.exercise_id] += 1

        exercise_counts = [{"exercise_id": key, "count": value} for key, value in exercise_counts.iteritems()]

    else:
        #If not, only look at the group data
        exercise_counts = ExerciseLog.objects.filter(user__in=user_list).values("exercise_id").annotate(count=Count("exercise_id"))

    #sort the results in order of highest counts to smallest
    sorted_counts = sorted(exercise_counts, key=lambda k:k['count'], reverse=False)
    
    #the final list of recommendations to return, WITHOUT counts
    group_rec = [c['exercise_id'] for c in sorted_counts]

    return group_rec

def get_struggling_exercises(user):
    """Return a list of all exercises (ids) that the user is currently struggling on."""

    # Return all exercise ids that the user is struggling on, ordered most recent first.
    struggles = ExerciseLog.objects.filter(
        user=user, struggling=True).order_by(
        "-latest_activity_timestamp").values_list(
        "exercise_id", flat=True)

    return struggles

def get_exercise_prereqs(exercises):
    """Return a list of prequisites (if applicable) for each specified exercise."""

    ex_cache = get_exercise_cache()
    prereqs = []
    for exercise in exercises:
        prereqs += ex_cache[exercise]['prerequisites']

    return prereqs


def get_explore_recommendations(user, request):
    """Get the recommendations for the Explore section, and return them as a list.

    Logic:
    Looks at a preset distance away, beginning at 2 to exclude self recommendations, to 
    recommend a topic for exploration. Currently, the cap is a distance of 6 so that all
    recommendations will still be of moderate relatedness. This number is not permanent, and
    can be tweaked as needed.
    Args:
    user -- The current user as a facility user model object.

    """

    data = generate_recommendation_data()                           #topic tree alg
    exercise_parents_table = get_exercise_parents_lookup_table()    #for finding out subtopic ids
    recent_exercises = get_most_recent_exercises(user)              #most recent ex

    #simply getting a list of subtopics accessed by user
    recent_subtopics = list(set([exercise_parents_table[ex]['subtopic_id'] for ex in recent_exercises if ex in exercise_parents_table]))

    #choose sample number, up to three
    sampleNum = min(len(recent_subtopics), settings.TOPIC_RECOMMENDATION_DEPTH)
    
    random_subtopics = random.sample(recent_subtopics, sampleNum)
    added = []                                                      #keep track of what has been added (below)
    final = []                                                      #final recommendations to return
    
    for subtopic_id in random_subtopics:

        related_subtopics = data[subtopic_id]['related_subtopics'][2:7] #get recommendations based on this, can tweak numbers!

        recommended_topic = next(topic for topic in related_subtopics if not topic in added and not topic in recent_subtopics)

        if recommended_topic:

            final.append({
                'suggested_topic': get_topic_data(request, recommended_topic),
                'interest_topic': get_topic_data(request, subtopic_id),
            })

            added.append(recommended_topic)

    return final

exercise_parents_lookup_table = {}
CACHE_VARS.append("exercise_parents_lookup_table")
def get_exercise_parents_lookup_table():
    """Return a dictionary with exercise ids as keys and topic_ids as values."""

    global exercise_parents_lookup_table

    if exercise_parents_lookup_table:
        return exercise_parents_lookup_table

    ### topic tree for traversal###
    tree = get_topic_tree(parent="root")

    #3 possible layers
    for topic in tree:
        for subtopic_id in topic['children']:
            exercises = get_topic_exercises(subtopic_id)

            for ex in exercises:
                if ex['id'] not in exercise_parents_lookup_table:
                    exercise_parents_lookup_table[ ex['id'] ] = {
                        "subtopic_id": subtopic_id,
                        "topic_id": topic['id'],
                    }

    return exercise_parents_lookup_table

def get_exercises_from_topics(topicId_list):
    """Return an ordered list of the first 5 exercise ids under a given subtopic/topic."""

    exs = []
    for topic in topicId_list:

        exercises = get_topic_exercises(topic)[:5] #can change this line to allow for more to be returned
        for e in exercises:
            exs += [e['id']] #only add the id to the list

    return exs

def get_most_recent_incomplete_item(user):
    """Return the most recently accessed item (video/exer) that has yet to be completed by user."""

    #get the queryset objects
    exercise_list = list(ExerciseLog.objects.filter(user=user, complete=False).order_by("-latest_activity_timestamp")[:1])
    video_list = list(VideoLog.objects.filter(user=user, complete=False).order_by("-latest_activity_timestamp")[:1])
    content_list = list(ContentLog.objects.filter(user=user, complete=False).order_by("-latest_activity_timestamp")[:1])

    item_list = []

    if exercise_list:
        item_list.append({
            "timestamp": exercise_list[0].latest_activity_timestamp or datetime.datetime.min,
            "id": exercise_list[0].exercise_id,
            "kind": "Exercise",
        })
    if video_list:
        item_list.append({
            "timestamp": video_list[0].latest_activity_timestamp or datetime.datetime.min,
            "id": video_list[0].video_id,
            "kind": "Content",
        })
    if content_list:
        item_list.append({
            "timestamp": content_list[0].latest_activity_timestamp or datetime.datetime.min,
            "id": content_list[0].content_id,
            "kind": "Content",
        })

    if item_list:
        item_list.sort(key=lambda x: x["timestamp"], reverse=True)
        return item_list[0]
    else:
        return None

def get_most_recent_exercises(user):
    """Return a list of the most recent exercises (ids) accessed by the user."""

    exercises_by_user = ExerciseLog.objects.filter(user=user).order_by("-latest_activity_timestamp").values_list("exercise_id", flat=True)
 
    return exercises_by_user

recommendation_data = {}
CACHE_VARS.append("recommendation_data")
def generate_recommendation_data():
    """Traverses topic tree to generate a dictionary with related subtopics per subtopic."""

    global recommendation_data
    if recommendation_data:
        return recommendation_data

    ### populate data exploiting structure of topic tree ###
    tree = get_topic_tree(parent="root")

    ######## DYNAMIC ALG #########

    ##
    # ITERATION 1 - grabs all immediate neighbors of each subtopic
    ##

    #array indices for the current topic and subtopic
    topic_index = 0
    subtopic_index = 0

    #for each topic 
    for topic in tree:

        subtopic_index = 0

        #for each subtopic add the neighbors at distance 0 and 1 (at dist one has 2 for each)
        for subtopic_id in topic['children']:

            neighbors_dist_1 = get_neighbors_at_dist_1(topic_index, subtopic_index, topic)

            #add to recommendation_data - distance 0 (itself) + distance 1
            recommendation_data[ subtopic_id ] = { 'related_subtopics' : ([subtopic_id + ' 0'] + neighbors_dist_1) }
            subtopic_index+=1
            
        topic_index+=1

    ##
    # ITERATION 2 - grabs all subsequent neighbors of each subtopic via 
    # Breadth-first search (BFS)
    ##

    #loop through all subtopics currently in recommendation_data dict
    for subtopic in recommendation_data:
        related = recommendation_data[subtopic]['related_subtopics'] # list of related subtopics (right now only 2)
        other_neighbors = get_subsequent_neighbors(related, recommendation_data, subtopic)
        recommendation_data[subtopic]['related_subtopics'] += other_neighbors ##append new neighbors


    ##
    # ITERATION 2.5 - Sort all results by increasing distance and to strip the final
    # result of all distance values in recommendation_data (note that there are only 3 possible: 0,1,4).
    ##

    #for each item in recommendation_data
    for subtopic in recommendation_data:
        at_dist_4 = []          #array to hold the subtopic ids of recs at distance 4
        at_dist_lt_4 = []       #array to hold subtopic ids of recs at distance 0 or 1

        #for this item, loop through all recommendations
        for recc in recommendation_data[subtopic]['related_subtopics']:
            if recc.split(" ")[1] == '4':   #if at dist 4, add to the array
                at_dist_4.append(recc.split(" ")[0]) 
            else:
                at_dist_lt_4.append(recc.split(" ")[0])

       
        sorted_related = at_dist_lt_4 + at_dist_4 #append later items at end of earlier
        recommendation_data[subtopic]['related_subtopics'] = sorted_related



    return recommendation_data

def get_recommendation_tree(data):
    """Returns a dictionary of related exercises for each subtopic.


    Args:
    data -- a dictionary with each subtopic and its related_subtopics (from generate_recommendation_data())
    
    """

    recommendation_tree = {}  # tree to return

    #loop through all subtopics passed in data
    for subtopic in data:
        recommendation_tree[str(subtopic)] = [] #initialize an empty list for the current s.t.

        related_subtopics = data[subtopic]['related_subtopics'] #list of related subtopic ids

        #loop through all of the related subtopics
        for rel_subtopic in related_subtopics:
            
            #make sure related is not an empty string (shouldn't happen but to be safe)
            if len(rel_subtopic) > 0:
                exercises = get_topic_exercises(rel_subtopic)

                for ex in exercises:
                    recommendation_tree[str(subtopic)].append(ex['id'])

    return recommendation_tree
      
def get_recommended_exercises(subtopic_id):
    """Return a list of recommended exercises (ids) based on the given subtopic."""

    if not subtopic_id:
        return []

    #get a recommendation lookup tree
    tree = get_recommendation_tree(generate_recommendation_data())

    #currently returning everything, perhaps we should just limit the
    #recommendations to a set amount??
    return tree[subtopic_id]

def get_neighbors_at_dist_1(topic_index, subtopic_index, topic):
    """Return a list of the neighbors at distance 1 from the specified subtopic."""

    neighbors = []  #neighbor list to be returned

    tree = get_topic_tree(parent="root")

    #pointers to the previous and next subtopic (list indices)
    prev = subtopic_index - 1 
    next = subtopic_index + 1

    #if there is a previous topic (neighbor to left)
    if(prev > -1 ):
        neighbors.append(topic['children'][prev] + ' 1') # neighbor on the left side

    #else check if there is a neighboring topic (left)    
    else:
        if (topic_index-1) > -1:
            neighbor_length = len(tree[(topic_index-1)]['children'])
            neighbors.append(tree[(topic_index-1)]['children'][(neighbor_length-1)] + ' 4')

        else:
            neighbors.append(' ') # no neighbor to the left

    #if there is a neighbor to the right
    if(next < len(topic['children'])):
        neighbors.append(topic['children'][next] + ' 1') # neighbor on the right side

    #else check if there is a neighboring topic (right)
    else:
        if (topic_index + 1) < len(tree):
            #the 4 denotes the # of nodes in path to this other node, will always be 4
            neighbors.append(tree[(topic_index+1)]['children'][0] + ' 4') 

        else:
            neighbors.append(' ') # no neighbor on right side


    return neighbors

def get_subsequent_neighbors(nearest_neighbors, data, curr):
    """BFS algorithm. Returns a list of the other neighbors (dist > 1) for the given subtopic.


    Args:
    nearest_neighbors -- list of neighbors at dist 1 from subtopic.
    data -- the dictionary of subtopics and their neighbors at distance 1
    curr -- the current subtopic
    
    """

    left_neigh = nearest_neighbors[1].split(' ')  # subtopic id and distance string of left neighbor
    right_neigh = nearest_neighbors[2].split(' ') # same but for right

    left = left_neigh[0]    #subtopic id of left
    right = right_neigh[0]  #subtopic id of right

    left_dist = -1          #dummy value
    right_dist = -1

    at_four_left = False    #boolean flag to denote that all other nodes to the left are at dist 4
    at_four_right = False   #same as above but for right nodes

    #checks, only applies to when left or right is ' ' (no neighbor)
    if  len(left_neigh) > 1:
        left_dist = left_neigh[1]           #distance of left neighbor
    else:
        left = ' '

    if len(right_neigh) > 1:
        right_dist = right_neigh[1]         #distance of right neighbor
    else:
        right = ' '

    other_neighbors = []

    # Loop while there are still neighbors
    while left != ' ' or right != ' ':

        if left == '':
            left= ' '

        # If there is a left neighbor, append its left neighbor
        if left != ' ':
            if data[left]['related_subtopics'][1] != ' ':

                #series of checks for each case
                #if all other nodes are at dist 4 (the first dist 4 was found)
                if(at_four_left):
                    new_dist = 4
                    at_four_left = True

                else:
                    #if immediate left node is 4
                    if data[ curr ]['related_subtopics'][1].split(' ')[1] == '4': 
                        at_four_left = True
                        new_dist = 4
                    elif data[left]['related_subtopics'][1].split(' ')[1] == '4': #if the next left neighbor is at dist 4
                        at_four_left = True
                        new_dist = 4
                    else: #this means that the next left node is at dist 1
                        new_dist = 1

                other_neighbors.append(data[left]['related_subtopics'][1].split(' ')[0] + ' ' + str(new_dist))
            left = data[left]['related_subtopics'][1].split(' ')[0]
        
        if right == '':
            right = ' '

        # Repeat for right neighbor
        if right != ' ':
            if data[right]['related_subtopics'][2] != ' ':

                #series of checks for each case
                #if all other nodes are at dist 4 (the first dist 4 was found)
                if(at_four_right):
                    new_dist = 4
                    at_four_right = True

                else:
                    #if immediate right node is 4
                    if data[ curr ]['related_subtopics'][2].split(' ')[1] == '4':           
                        new_dist = 4
                    elif data[right]['related_subtopics'][2].split(' ')[1] == '4': #if the next right neighbor is at dist 4
                        new_dist = 4
                    else: #this means that the next right node is at dist 1
                        new_dist = 1

                if new_dist == 4:
                    at_four_right = True

                other_neighbors.append(data[right]['related_subtopics'][2].split(' ')[0] + ' ' + str(new_dist))
            right = data[right]['related_subtopics'][2].split(' ')[0]

    return other_neighbors
