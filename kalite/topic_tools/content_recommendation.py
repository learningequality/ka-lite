'''
All logic for generating and retriving content recommendations.
Three main functions:
    - get_resume_recommendations()
    - get_next_recommendations()
    - get_explore_recommendations()
'''

from kalite.topic_tools import * 
from kalite.main.models import ExerciseLog 
import kalite.facility
from kalite.facility.models import FacilityUser
'''
###
# The KING function for content recommendation. Call this single function for all 
# of your content recommendation needs (i.e. in the API call).
#
# @param user: the unique facility user model of the current user
# @param current_subtopic: optional latest subtopic id that the user has worked on/completed. This
#                          will act as a starting point for some of the algorithms (nearest neighbor, etc.)
#
# @return: Still deciding on this, but I assume that it will be a dictionary in the 
#          form: { 'next_steps':[ ... ], 'explore':[ ... ], etc. } 
###
def get_recommendations(user=None, current_subtopic=None):

    #the recommendations to return
    result = {
        "resume":{},        #not yet completed exercises, but have been started
        "next_steps":{},    #things user is struggling on, next relevant items
        "explore":{}        #less relevant exercises, for exploration
    }

    #preliminary user check
    if not user:
        #return 'Whoa there buddy, you did not specify a user!'
        user = 'Yamira Jones (Facility: Wilson Elementary (#1829))'


    #some initial data used in multiple areas
    current_subtopic = get_most_recent_subtopic(user)

    #get user exercise log
    #print ExerciseLog.objects.filter(user='Yamira Jones')


    ############### RESUME #############################
    result['resume'] = get_resume_recommendations(user)


    ############### NEXT STEPS ######################### Use current ordering of get_recommended_exercises()
    result['next_steps'] = get_next_recommendations(user)


    ############### EXPLORE ############################ Use middle->end get_recommended_exercises();
    result['explore'] = get_explore_recommendations(current_subtopic)

    return result
'''

########################################## 'RESUME' LOGIC #################################################

###
# Returns a list of all started but NOT completed exercises
#
# @param user: facility user model
# @return: a list of exercise id's that are not completed but have been started.
###
def get_resume_recommendations(user):
    #logic for where user left off
    current_exercises = get_most_recent_incomplete_exercises(user)[:5]    #5 most recent exercises (in-progress ones)
    return current_exercises




####################################### 'NEXT STEPS' LOGIC ################################################
''' TODO working on this: 
    - WORKING ON THE GROUP ESTIMATION PART (get_group_recommendations))
'''
###
# Returns a list of exercises to go to next. Influenced by other user patterns in the same group as well
# as the user's struggling pattern shown in the exercise log.
#
# Full List:
# - Incomplete exercises (where user left off - MOVED TO RESUME)
# - Struggling (pre-reqs for exercises marked as "struggling" for the student)
# - User patterns based on group analysis (maximum likelihood estimation and empirical count)
# - Topic tree structure recommendations based on the most recent subtopic accessed
#
# @param user: facility user model
#        current_subtopics: subtopic ids of the 5 most recently accessed exercise
# @return: a list of exercise id's of where the user should consider going next.
###
def get_next_recommendations(user):

    #logic for recommendations based off of the topic tree structure
    current_subtopic = get_most_recent_subtopic(user)                   #the most recent subtopic id accessed by user
    topic_tree_based_data = get_recommended_exercises(current_subtopic)
   

    #logic to generate recommendations based on exercises student is struggling with
    struggling = get_exercise_prereqs(get_struggling_exercises(user))


    #logic to get recommendations based on group patterns, if applicable
    group = get_group_recommendations(user)

    #final recommendations are a combination of current, struggling, group filtering, and topic_tree filtering
    return group + struggling + topic_tree_based_data[:10]




# Given a facility user model, return a list of ALL exercises (ids) that are immediately tackled by other users
# in the same user group - also ordered by empirical count (more people moving onto this -> higher in the
# list). "Immediately" means the very next exercise after the most recent one the given user has accessed.
#
# A group is defined as a collection of students within the same facility and group (as defined in models)
def get_group_recommendations(user):
    user = ExerciseLog.objects.filter(id__lte=1)[0].user        #random person, can delete after                                  
    most_recent_exercise = get_most_recent_exercises(user)[0]   #get most recently accessed exercise
    user_list = get_users_in_group('Student', user.group, user.facility) #may need to debug
    
    counts = [{'temp':0}]  #array of dictionaries to keep track of counts of subsequent exercises

    '''     NEEDS DEBUGGING     '''
    for student in user_list:
        student_exercises = get_most_recent_exercises(student)
        
        #if this student has taken/attempted this exercise
        if most_recent_exercise in student_exercises and len(student_exercises) > 0:
            next = student_exercises[0] #start at the most recent one - this will act like a prev pointer

            #loop through all exercises, keeping track of previous 
            for exercise in student_exercises:
              
                #a match, and not the first one (which would imply that there is no next)
                if(exercise == most_recent_exercise and exercise != next):
                    
                    found = False #boolean flag
                    
                    for c in counts:
                        #if a match
                        if next.exercise_id in c:
                            c[next.exercise_id] += 1
                            found = True

                    #if exercise not found, then make a new object with it with count = 1 
                    if not found:
                        counts.append({next.exercise_id : 1})

                    #break #stops inner for loop logic

                next = exercise


        ''' NOW NEED TO ORDER COUNTS FROM HIGHEST TO LOWEST '''
        ''' THEN SIMPLY RETURN THE EXERCISE IDS FROM HIGHEST TO LOWEST '''
        
    
    return []




# Given a facility user model, return a list ALL exercises (ids) that the user is struggling on
# This amounts to returning only those exercises that have their "struggling" attribute set
# to True. The exercise ids are also in order of most recent first. 
def get_struggling_exercises(user):
    exercises_by_user = ExerciseLog.objects.filter(user=user)
    exercises_by_user = ExerciseLog.objects.filter(id__lte=1)   #temp, delete after

    #sort exercises first, in order of most recent first
    exercises_by_user = sorted(exercises_by_user, key=lambda student: student.completion_timestamp, reverse=True)

    struggles = []                                              #TheStruggleIsReal
    for exercise in exercises_by_user:
        if exercise.struggling:
            struggles.append(exercise.exercise_id)

    return struggles




# Given a list of exercise ids, return a concatenated list of prereqs for each of the exercises
def get_exercise_prereqs(exercises):
    ex_cache = get_exercise_cache()
    prereqs = []
    for exercise in exercises:
        prereqs += ex_cache[exercise]['prerequisites']

    return prereqs
    

########################################## 'EXPLORE' LOGIC ################################################

###
# Returns a list of exercises that the user has not explored yet.
#
# @param: subtopic_id: the subtopic id of the most recent subtopic that the user has engaged in (possibly 
#         averaged).
# @return: a list of exercise id's of the 'middle to farthest neighbors,' or less immediately relevant
#           exercises based on topic tree structure.
###
def get_explore_recommendations(subtopic_id):
    data = generate_recommendation_data()[subtopic_id]['related_subtopics']
    
    data = data[(len(data)/2):]                     #only look at middle to furthest neighbors
   
    ''' Need to add some more analysis to ensure that the user has not done these exercises yet'''

    return get_exercises_from_topics(data)









##################################### GENERAL HELPER FUNCTIONS ############################################

''' TODO '''
# Returns the most recent subtopic id that the given user has started and/or completed.
def get_most_recent_subtopic(user):
    return 'early-math' #dummy return


#Given a list of subtopic/topic ids, returns an ordered list of the first 5 exercise ids under those ids
def get_exercises_from_topics(topicId_list):
    exs = []
    for topic in topicId_list:
        exercises = get_topic_exercises(topic)[:5] #can change this line to allow for more to be recommended
        for e in exercises:
            exs += [e['id']] #only add the id to the list

    return exs


#given a facility user model, return the most recent exercise ids that are still in-progress
def get_most_recent_incomplete_exercises(user):
    exercises_by_user = ExerciseLog.objects.filter(user=user)
    exercises_by_user = ExerciseLog.objects.filter(id__lte=1) #temp
    
    #sorted by completion time in descending order (most recent first)
    sorted_exercises = sorted(exercises_by_user, key=lambda student: student.completion_timestamp, reverse=True)

    exercise_list = []

    for exercise in sorted_exercises:
        if exercise.complete == False:                  #only look for incomplete
            exercise_list.append(exercise.exercise_id)  #append to list

    return exercise_list                                #most recent + incomplete



#given a facility user model, return the most recent exercise ids - incomplete AND complete
def get_most_recent_exercises(user):
    exercises_by_user = ExerciseLog.objects.filter(user=user)
    
    #sorted by completion time in descending order (most recent first)
    sorted_exercises = sorted(exercises_by_user, key=lambda student: student.completion_timestamp, reverse=True)

    return sorted_exercises   



#given a user type (can be null), group id, and a facility name, return all users in that group
#calls the already defined function in facility module
def get_users_in_group(user_type, group_id, facility):
    return kalite.facility.get_users_from_group(user_type, group_id, facility)


###################################### BEGIN NEAREST NEIGHBORS ############################################

### MULTI-PURPOSE NEAREST NEIGHBORS ALGORITH, USE AS YOU PLEASE ###
### THE MAIN THING TO REMEMBER IS THAT get_recommended_exercises(subtopic) IS THE MAIN FUNCTION TO CALL ###

###
# Returns a dictionary with each subtopic and their related
# topics.
#
###
def generate_recommendation_data():

    #hardcoded data, each subtopic is the key with its related subtopics and current courses as the values. Not currently in use.
    data_hardcoded = {
        "early-math": {"related_subtopics": ["early-math", "arithmetic", "recreational-math"], "unrelated_subtopics": ["music", "history", "biology"]},
        "arithmetic": {"related_subtopics": ["arithmetic", "pre-algebra", "recreational-math"], "unrelated_subtopics": ["music", "history", "biology"]},
        "pre-algebra": {"related_subtopics": ["pre-algebra", "algebra", "recreational-math"], "unrelated_subtopics": ["music", "history", "biology"]},
        "algebra": {"related_subtopics": ["algebra", "geometry", "recreational-math", "competition-math", "chemistry"], "unrelated_subtopics": ["music", "history", "biology", "cosmology-and-astronomy"]},
        "geometry": {"related_subtopics": ["geometry", "algebra2", "recreational-math", "competition-math", "chemistry"], "unrelated_subtopics": ["music", "history", "biology", "cosmology-and-astronomy"]},
        "algebra2": {"related_subtopics": ["algebra2", "trigonometry", "probability", "competition-math", "chemistry", "microeconomics", "macroeconomics"], "unrelated_subtopics": ["music", "history", "biology", "cosmology-and-astronomy", "lebron-asks-subject", "art-history", "CAS-biodiversity", "Exploratorium"]},
        "trigonometry": {"related_subtopics": ["trigonometry", "linear-algebra", "precalculus", "physics", "microeconomics", "macroeconomics"], "unrelated_subtopics": ["music", "history", "biology", "cosmology-and-astronomy", "lebron-asks-subject", "art-history", "CAS-biodiversity", "Exploratorium"]},
        "probability": {"related_subtopics": ["probability", "recreational-math"], "unrelated_subtopics": ["music", "history", "biology", "cosmology-and-astronomy", "lebron-asks-subject", "art-history", "CAS-biodiversity", "Exploratorium"]},
        "precalculus": {"related_subtopics": ["precalculus", "differential calculus", "probability"], "unrelated_subtopics": ["music", "history", "biology", "cosmology-and-astronomy", "lebron-asks-subject", "art-history", "CAS-biodiversity", "Exploratorium"]},
        "differential-calculus": {"related_subtopics": ["differential-calculus", "differential-equations", "physics", "microeconomics", "macroeconomics"], "unrelated_subtopics": ["music", "history", "biology", "cosmology-and-astronomy", "lebron-asks-subject", "art-history", "CAS-biodiversity", "Exploratorium"]},
        "integral-calculus": {"related_subtopics": ["integral-calculus", "differential-equations", "physics", "microeconomics", "macroeconomics"], "unrelated_subtopics": ["music", "history", "biology", "cosmology-and-astronomy", "lebron-asks-subject", "art-history", "CAS-biodiversity", "Exploratorium"]},
        "multivariate-calculus": {"related_subtopics": ["multivariate-calculus", "differential-equations", "physics", "microeconomics", "macroeconomics"], "unrelated_subtopics": ["music", "history", "biology", "cosmology-and-astronomy", "lebron-asks-subject", "art-history", "CAS-biodiversity", "Exploratorium"]},
        "differential-equations": {"related_subtopics": ["differential-equations", "physics", "microeconomics", "macroeconomics"], "unrelated_subtopics": ["music", "history", "biology", "cosmology-and-astronomy", "lebron-asks-subject", "art-history", "CAS-biodiversity", "Exploratorium", "discoveries-projects"]},
        "linear-algebra": {"related_subtopics": ["linear-algebra", "precalculus"], "unrelated_subtopics": ["music", "history", "biology", "cosmology-and-astronomy", "lebron-asks-subject", "art-history", "CAS-biodiversity", "Exploratorium", "discoveries-projects"]},
        "recreational-math": {"related_subtopics": ["recreational-math", "pre-algebra", "algebra", "geometry", "algebra2"], "unrelated_subtopics": ["music", "history", "biology", "cosmology-and-astronomy", "lebron-asks-subject", "art-history", "CAS-biodiversity", "Exploratorium", "discoveries-projects"]},
        "competition-math": {"related_subtopics": ["competition-math","algebra", "geometry", "algebra2"], "unrelated_subtopics": ["music", "history", "biology", "cosmology-and-astronomy", "lebron-asks-subject", "art-history", "CAS-biodiversity", "Exploratorium", "discoveries-projects"]},


        "biology": {"related_subtopics": ["biology", "health-and-medicine", "CAS-biodiversity", "Exploratorium", "chemistry", "physics", "cosmology-and-astronomy", "nasa"], "unrelated_subtopics": ["music", "philosophy", "microeconomics", "macroeconomics", "history", "art-history", "asian-art-museum"]},
        "physics": {"related_subtopics": ["physics", "discoveries-projects", "cosmology-and-astronomy", "nasa", "Exploratorium", "biology", "CAS-biodiversity", "health-and-medicine", "differential-calculus"], "unrelated_subtopics": ["music", "philosophy", "microeconomics", "macroeconomics", "history", "art-history", "asian-art-museum"]},
        "chemistry": {"related_subtopics": ["chemistry", "organic-chemistry", "biology", "health-and-medicine", "physics", "cosmology-and-astronomy", "discoveries-projects", "CAS-biodiversity", "Exploratorium", "nasa"], "unrelated_subtopics": ["music", "philosophy", "microeconomics", "macroeconomics", "history", "art-history", "asian-art-museum"]},
        "organic-chemistry": {"related_subtopics": ["organic-chemistry", "biology", "health-and-medicine", "physics", "cosmology-and-astronomy", "discoveries-projects", "CAS-biodiversity", "Exploratorium", "nasa"], "unrelated_subtopics": ["music", "philosophy", "microeconomics", "macroeconomics", "history", "art-history", "asian-art-museum"]},
        "cosmology-and-astronomy": {"related_subtopics": ["cosmology-and-astronomy", "nasa", "chemistry", "biology", "health-and-medicine", "physics", "discoveries-projects", "CAS-biodiversity", "Exploratorium", "nasa"], "unrelated_subtopics": ["music", "philosophy", "microeconomics", "macroeconomics", "history", "art-history", "asian-art-museum"]},
        "health-and-medicine": {"related_subtopics": ["health-and-medicine", "biology", "chemistry", "CAS-biodiversity", "Exploratorium", "physics", "cosmology-and-astronomy", "nasa"], "unrelated_subtopics": ["music", "philosophy", "microeconomics", "macroeconomics", "history", "art-history", "asian-art-museum"]},
        "discoveries-projects": {"related_subtopics": ["discoveries-projects", "physics", "computing", "cosmology-and-astronomy", "nasa", "Exploratorium", "biology", "CAS-biodiversity", "health-and-medicine", "differential-calculus"], "unrelated_subtopics": ["music", "philosophy", "microeconomics", "macroeconomics", "history", "art-history", "asian-art-museum"]},

        "microeconomics": {"related_subtopics": ["microeconomics", "macroeconomics"], "unrelated_subtopics": ["music", "philosophy", "microeconomics", "macroeconomics", "history", "art-history", "asian-art-museum"]},
        "macroeconomics": {"related_subtopics": ["macroeconomics", "microeconomics", "core-finance"], "unrelated_subtopics": ["music", "philosophy", "microeconomics", "macroeconomics", "history", "art-history", "asian-art-museum"]},
        "core-finance": {"related_subtopics": ["core-finance", "entrepreneurship2", "macroeconomics", "microeconomics", "core-finance"], "unrelated_subtopics": ["music", "philosophy", "microeconomics", "macroeconomics", "history", "art-history", "asian-art-museum"]},
        "entrepreneurship2": {"related_subtopics": ["entrepreneurship2", "core-finance", "macroeconomics", "microeconomics", "core-finance"], "unrelated_subtopics": ["music", "philosophy", "microeconomics", "macroeconomics", "history", "art-history", "asian-art-museum"]},

        "history": {"related_subtopics": ["history", "art-history", "american-civics-subject", "asian-art-museum", "Exploratorium"], "unrelated_subtopics": ["biology", "music", "health-and-medicine"]},
        "art-history": {"related_subtopics": ["art-history", "ap-art-history", "asian-art-museum", "history", "american-civics-subject", "Exploratorium"], "unrelated_subtopics": ["biology", "music", "health-and-medicine"]},
        "american-civics-subject": {"related_subtopics": ["american-civics-subject", "history"], "unrelated_subtopics": ["biology", "music", "health-and-medicine"]},
        "music": {"related_subtopics": ["music"], "unrelated_subtopics": ["biology", "health-and-medicine"]},
        "philosophy": {"related_subtopics": ["philosophy"]},

        "computing": {"related_subtopics": ["computing", "early-math", "arithmetic", "pre-algebra", "geometry", "probability", "recreational-math", "biology", "physics", "chemistry", "organic-chemistry", "health-and-medicine", "discoveries-projects", "microeconomics", "macroeconomics", "core-finance", "music"]},

        "sat": {"related_subtopics": ["sat", "arithmetic", "pre-algebra", "algebra", "algebra2", "geometry", "probability", "recreational-math"]},
        "mcat": {"related_subtopics": ["mcat", "arithmetic", "pre-algebra", "geometry", "probability", "recreational-math", "chemistry", "biology", "physics", "organic-chemistry", "health-and-medicine"]},
        "NCLEX-RN": {"related_subtopics": ["NCLEX-RN", "chemistry", "biology", "physics", "organic-chemistry", "health-and-medicine"]},
        "gmat": {"related_subtopics": ["gmat", "arithmetic", "pre-algebra", "algebra", "algebra2" "geometry", "probability", "chemistry", "biology", "physics", "organic-chemistry", "health-and-medicine", "history", "microeconomics", "macroeconomics"]},
        "cahsee-subject": {"related_subtopics": ["cahsee-subject", "early-math", "arithmetic", "pre-algebra", "geometry", "probability", "recreational-math"]},
        "iit-jee-subject": {"related_subtopics": ["iit-jee-subject", "arithmetic", "pre-algebra", "geometry", "differential-equations", "differential-calculus", "integral-calculus", "linear-algebra", "probability", "chemistry", "physics", "organic-chemistry"]},
        "ap-art-history": {"related_subtopics": ["ap-art-history", "art-history", "history"]},

        "CAS-biodiversity": {"related_subtopics": ["CAS-biodiversity", "chemistry", "biology", "physics", "organic-chemistry", "health-and-medicine", "Exploratorium"]},
        "Exploratorium": {"related_subtopics": ["Exploratorium", "chemistry", "biology", "physics", "organic-chemistry", "health-and-medicine", "CAS-biodiversity", "art-history", "music"]},
        "asian-art-museum": {"related_subtopics": ["asian-art-museum", "art-history", "history", "ap-art-history"]},
        "ssf-cci": {"related_subtopics": ["ssf-cci", "art-history", "history"]},
    }


    ### populate data exploiting structure of topic tree ###
    if not TOPICS:
        tree = get_topic_tree() 
    else:
        tree = TOPICS[settings.CHANNEL][settings.LANGUAGE_CODE] #else grab the cached topic tree

    ######## DYNAMIC ALG #########

    data = {};

    ##
    # ITERATION 1 - grabs all immediate neighbors of each subtopic
    ##

    #array indices for the current topic and subtopic
    topic_index = 0
    subtopic_index = 0

    #for each topic 
    for topic in tree['children']:

        subtopic_index = 0

        #for each subtopic add the neighbors at distance 0 and 1 (at dist one has 2 for each)
        for subtopic in topic['children']:

            neighbors_dist_1 = get_neighbors_at_dist_1(topic_index, subtopic_index, tree)

            #add to data - distance 0 (itself) + distance 1
            data[ subtopic['id'] ] = { 'related_subtopics' : ([subtopic['id'] + ' 0'] + neighbors_dist_1) }
            subtopic_index+=1
            
        topic_index+=1

    ##
    # ITERATION 2 - grabs all subsequent neighbors of each subtopic via 
    # Breadth-first search (BFS)
    ##

    #loop through all subtopics currently in data dict
    for subtopic in data:
        related = data[subtopic]['related_subtopics'] # list of related subtopics (right now only 2)
        other_neighbors = get_subsequent_neighbors(related, data, subtopic)
        data[subtopic]['related_subtopics'] += other_neighbors ##append new neighbors


    ##
    # ITERATION 2.5 - Sort all results by increasing distance and to strip the final
    # result of all distance values in data (note that there are only 3 possible: 0,1,4).
    ##

    #for each item in data
    for subtopic in data:
        at_dist_4 = []          #array to hold the subtopic ids of recs at distance 4
        at_dist_lt_4 = []       #array to hold subtopic ids of recs at distance 0 or 1

        #for this item, loop through all recommendations
        for recc in data[subtopic]['related_subtopics']:
            if recc.split(" ")[1] == '4':   #if at dist 4, add to the array
                at_dist_4.append(recc.split(" ")[0]) 
            else:
                at_dist_lt_4.append(recc.split(" ")[0])

       
        sorted_related = at_dist_lt_4 + at_dist_4 #append later items at end of earlier
        data[subtopic]['related_subtopics'] = sorted_related


    ##
    # ITERATION 3 - Take into consideration user data in exercise log to filter data one last time
    ##    

    '''TODO LATER'''
    return data



### 
# Returns a lookup table (a tree) that contains a list of related
# EXERCISES for each subtopic.
#
# @param data: a dicitonary with each subtopic and its related subtopics
###
def get_recommendation_tree(data):
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
      


###
# Returns a list of recommended exercise ids given a
# subtopic id. This will be the function called via the api
# endpoint.
#
# @param subtopic_id: the subtopic id (e.g. 'early-math')
###
def get_recommended_exercises(subtopic_id):

    #get a recommendation lookup tree
    tree = get_recommendation_tree(generate_recommendation_data())

    #currently returning everything, perhaps we should just limit the
    #recommendations to a set amount??
    return tree[subtopic_id]



###
# Helper function for generating recommendation data using the topic tree.
# Returns a list of the neihbors at distance 1 from the specified subtopic.
#
# @param topic: the index of the topic that the subtopic belongs to (e.g. math, sciences)
#        subtopic: the index of the subtopic to find the neighbors for
###
def get_neighbors_at_dist_1(topic, subtopic, tree):
    neighbors = []  #neighbor list to be returned
    topic_index = topic #store topic index
    topic = tree['children'][topic] #subtree rooted at the topic that we are looking at
    #curr_subtopic = tree['children'][topic]['children'][subtopic]['id'] #id of topic passed in

    #pointers to the previous and next subtopic (list indices)
    prev = subtopic - 1 
    next = subtopic + 1

    #if there is a previous topic (neighbor to left)
    if(prev > -1 ):
        neighbors.append(topic['children'][prev]['id'] + ' 1') # neighbor on the left side

    #else check if there is a neighboring topic (left)    
    else:
        if (topic_index-1) > -1:
            neighbor_length = len(tree['children'][(topic_index-1)]['children'])
            neighbors.append(tree['children'][(topic_index-1)]['children'][(neighbor_length-1)]['id'] + ' 4')

        else:
            neighbors.append(' ') # no neighbor to the left

    #if there is a neighbor to the right
    if(next < len(topic['children'])):
        neighbors.append(topic['children'][next]['id'] + ' 1') # neighbor on the right side

    #else check if there is a neighboring topic (right)
    else:
        if (topic_index + 1) < len(tree['children']):
            #the 4 denotes the # of nodes in path to this other node, will always be 4
            neighbors.append(tree['children'][(topic_index+1)]['children'][0]['id'] + ' 4') 

        else:
            neighbors.append(' ') # no neighbor on right side


    return neighbors



###
# Performs Breadth-first search given recommendation data.
# Returns neighbors of a node in order of increasing distance.
# 
# @param nearest_neighbors: array holding the current left and right neighbors at dist 1 (always 2)
# @param data: dictionary of subtopics and their neighbors at distance 1
# @param curr: the current subtopic
###

def get_subsequent_neighbors(nearest_neighbors, data, curr):
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

### END content recommendation ###