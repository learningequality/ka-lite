'''
All logic for generating and retriving content recommendations.
Three main functions:
    - get_resume_recommendations(user)
    - get_next_recommendations(user)
    - get_explore_recommendations(user)
'''
import random
import kalite.facility
from kalite.topic_tools import * 
from kalite.facility.models import FacilityUser
from kalite.main.models import ExerciseLog , VideoLog





########################################## 'RESUME' LOGIC #################################################

###
# Returns a list of all started but NOT completed exercises
#
# @param user: facility user model
# @return: The most recent video/exercise that has been started but NOT completed
###
def get_resume_recommendations(user):
    #user = ExerciseLog.objects.filter(id__lte=1)[4].user        #random person, can delete after
    table = get_exercise_parents_lookup_table()
    # ! first pass returns only be the most recent vid/exercise !
    final = get_most_recent_incomplete_item(user)
    
    #add some more data with help of lookup table (if possible)
    if final['id'] in table:
        final['title'] = table[ final['id'] ]['title']
        final['subtopic_title'] = table[ final['id'] ]['subtopic_title']

    return [final] #for first pass, just return the most recent exercise/video




####################################### 'NEXT STEPS' LOGIC ################################################

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
#        
# @return: a list of exercise id's and their titles, [type], and subtopic for where the user 
#          should consider going next.
###
def get_next_recommendations(user):

    #user = ExerciseLog.objects.filter(id__lte=1)[4].user        #random person, can delete after    

    exercise_parents_table = get_exercise_parents_lookup_table()

    most_recent = get_most_recent_exercises(user)

    if len(most_recent) > 0 and most_recent[0] in exercise_parents_table:
        current_subtopic = exercise_parents_table[most_recent[0]]['subtopic_id']
    else:
        current_subtopic = None

    #logic for recommendations based off of the topic tree structure
    topic_tree_based_data = generate_recommendation_data()[current_subtopic]['related_subtopics'][:3]
    topic_tree_based_data = get_exercises_from_topics(topic_tree_based_data)
    
    #for checking that only exercises that have not been accessed are returned
    check = [] 
    for ex in topic_tree_based_data:
        if not ex in most_recent:
            check.append(ex)

    topic_tree_based_data = check

    #logic to generate recommendations based on exercises student is struggling with
    struggling = get_exercise_prereqs(get_struggling_exercises(user))   

    #logic to get recommendations based on group patterns, if applicable
    group = get_group_recommendations(user)

   
    #now append titles and other metadata to each exercise id
    final = [] # final data to return
    for exercise in (group[:2] + struggling[:2] + topic_tree_based_data[:1]):  #notice the concatenation

        if exercise in exercise_parents_table:
            final.append( {
                    exercise:   {'kind':exercise_parents_table[exercise]['kind'],
                                  'lesson_title':exercise_parents_table[exercise]['title'],
                                  'subtopic_title':exercise_parents_table[exercise]['subtopic_title'],
                                  'subtopic_id':exercise_parents_table[exercise]['subtopic_id']
                                } 
                            } 
                        )


    #final recommendations are a combination of struggling, group filtering, and topic_tree filtering
    return final




# Given a facility user model, return a list of ALL exercises (ids) that are immediately tackled by other users
# in the same user group - also ordered by empirical count (more people moving onto this -> higher in the
# list). "Immediately" means the very next exercise after the most recent one the given user has accessed.
#
# This function checks if the exercises returned have been accessed already, and only returns those that
# have not been.
#
# A group is defined as a collection of students within the same facility and group (as defined in models)
def get_group_recommendations(user):
    
    recent_excercises = get_most_recent_exercises(user)         #all exercises
   
    most_recent_exercise = recent_excercises[0]                 #get most recently accessed exercise

    user_list = get_users_in_group('Student', user.group, user.facility) #may need to debug
    
    counts = []  #array of dictionaries to keep track of counts of subsequent exercises, in form: {'exercise':'id', 'count':0}

    '''     NEEDS MORE TESTING WITH DATA     '''
    for student in user_list:
        student_exercises = get_most_recent_exercises(student)

        #if this student has taken/attempted this exercise
        if most_recent_exercise in student_exercises and len(student_exercises) > 1:
            next = student_exercises[0] #start at the most recent one - this will act like a prev pointer

            #loop through all exercises, keeping track of previous 
            for exercise in student_exercises:
    
                #a match to note, and not the first one (which would imply that there is no next)
                if(exercise == most_recent_exercise and exercise != next):

                    found = False #boolean flag
                    
                    for c in counts:

                        #if user has not already attempted this exercise, add it to list!
                        if not next in recent_excercises:

                            #if a match in counts (exists already)
                            if next == c['exercise']:
                                c['count'] += 1
                                found = True

                    #if exercise not found, then make a new object with it with count = 1 
                    if not found and not next in recent_excercises:
                        
                        counts.append({ "exercise": next, "count":1 })


                next = exercise


    #sort the results in order of highest counts to smallest
    sorted_counts = sorted(counts, key=lambda k:k['count'], reverse=False)
    
    group_rec = []  #the final list of recommendations to return, WITHOUT counts

    for c in sorted_counts:
        group_rec.append(c['exercise'])

    return group_rec




# Given a facility user model, return a list ALL exercises (ids) that the user is struggling on
# This amounts to returning only those exercises that have their "struggling" attribute set
# to True. The exercise ids are also in order of most recent first. 
def get_struggling_exercises(user):
    
    exercises_by_user = ExerciseLog.objects.filter(user=user)

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
# Returns a list of subtopic ids that the user has not explored yet. 
#
# @param: user - the facility user model corresponding to the current user
#
# @return: a list of exercise id's of the 'middle to farthest neighbors,' or less immediately relevant
#           exercises based on topic tree structure.
###
def get_explore_recommendations(user):

    ''' 
        Logic: grab 3 random exercises from recent exercises, get their subtopic ids, then using
        generate_recommendation_data(), get the elements at position 1 and 2 (nearest). return these

    '''

    #user = ExerciseLog.objects.filter(id__lte=1)[4].user            #random person, can delete after   

    data = generate_recommendation_data()                           #topic tree alg
    exercise_parents_table = get_exercise_parents_lookup_table()    #for finding out subtopic ids
    recent_exercises = get_most_recent_exercises(user)              #most recent ex

    #simply getting a list of subtopics accessed by user
    recent_subtopics = []
    for ex in recent_exercises:
        if not exercise_parents_table[ex]['subtopic_id'] in recent_subtopics:
            recent_subtopics.append(exercise_parents_table[ex]['subtopic_id'])

    #choose sample number, up to three
    if len(recent_exercises) > 0:
        sampleNum = 1 #must be at least 1

        if len(recent_exercises) > 1:
            sumpleNum = 2

            if len(recent_exercises) > 2:
                sampleNum = 3

    else:
        sampleNum = 0 #user has not attempted any
    
    random_exercises = random.sample(recent_exercises, sampleNum)   #grab the valid/appropriate number of exs, up to 3
    added = []                                                      #keep track of what has been added (below)
    final = []                                                      #final recommendations to return
    
    for ex in random_exercises:
        exercise_data = exercise_parents_table[ex]
        subtopic_id = exercise_data['subtopic_id']                      #subtopic_id of current
        related_subtopics = data[subtopic_id]['related_subtopics'][2:5] #get recommendations based on this, can tweak numbers!

        recommended_topics = []                                         #the recommended topics
    
        for subtopic in related_subtopics:
            curr = get_subtopic_data(subtopic)

            if not curr['id'] in recent_subtopics:                      #check for an unaccessed recommendation
                recommended_topics.append(curr)                         #add to return
                                                                                             
        #dictionary to add to the final list
        to_append = {   "accessed": exercise_data['subtopic_title'], 
                        "recommended_topics": recommended_topics
                    }
    
        #if valid (i.e. not a repeat and also some recommendations)
        if (not exercise_data['subtopic_id'] in added) and (len(to_append['recommended_topics']) > 0):   
            final.append(to_append)                                     #valid, so append
            added.append(exercise_data['subtopic_id'])                  #make note


    return final




#given a subtopic id, return corresponding data: the subtopic title, ... (right now only the title + id)
def get_subtopic_data(subtopic_id):

    ### topic tree for traversal###
    tree = generate_topic_tree()

    for topic in tree['children']:
        for subtopic in topic['children']:
            
            #a match!!
            if subtopic['id'] == subtopic_id:

                return { "title":subtopic['title'], "id":subtopic_id }

    return [] #ideally should never get here



##################################### GENERAL HELPER FUNCTIONS ############################################


#returns a dictionary of exercises with their metadata.
#subtopics are the immediate parents (ex: early-math, biology) and topics are one more level above (math)
def get_exercise_parents_lookup_table():

    ### topic tree for traversal###
    tree = generate_topic_tree()

    #create a lookup table from traversing the tree - can cache if needed, but is decently fast if TOPICS exists
    exercise_parents_table = {}

    #3 possible layers
    for topic in tree['children']:
        for subtopic in topic['children']:
            for ex in subtopic['children']:

                exercise_parents_table[ ex['id'] ] = { "subtopic_id":subtopic['id'], "topic_id":topic['id'],
                    "subtopic_title":subtopic['title'], "topic_title": topic['title'] , "kind":ex['kind'], "title":ex['title']}

                if 'children' in ex: #if there is another layer of children

                    for ex2 in ex['children']:

                        exercise_parents_table[ ex2['id'] ] = { "subtopic_id":subtopic['id'], "topic_id":topic['id'],
                        "subtopic_title":subtopic['title'], "topic_title": topic['title'] , "kind":ex2['kind'],"title":ex['title']}

                        #if there is yet another level
                        if 'children' in ex2:

                            for ex3 in ex2['children']:
                                exercise_parents_table[ ex3['id'] ] = { "subtopic_id":subtopic['id'], "topic_id":topic['id'],
                                "subtopic_title":subtopic['title'], "topic_title": topic['title'] , "kind":ex3['kind'],"title":ex['title']}

                  
    return exercise_parents_table


#Given a list of subtopic/topic ids, returns an ordered list of the first 5 exercise ids under those ids
def get_exercises_from_topics(topicId_list):
    exs = []
    for topic in topicId_list:
        exercises = get_topic_exercises(topic)[:5] #can change this line to allow for more to be returned
        for e in exercises:
            exs += [e['id']] #only add the id to the list

    return exs


#given a facility user model, return all recent EXERCISE ids that are still in-progress
def get_most_recent_incomplete_exercises(user):
    exercises_by_user = ExerciseLog.objects.filter(user=user)
    
    #sorted by completion time in descending order (most recent first)
    sorted_exercises = sorted(exercises_by_user, key=lambda student: student.completion_timestamp, reverse=True)

    exercise_list = []

    for exercise in sorted_exercises:
        if exercise.complete == False:                  #only look for incomplete
            exercise_list.append(exercise.exercise_id)  #append to list

    return exercise_list                                #most recent + incomplete


#given a facility user model, return all recent VIDEO ids that are still in-progress
def get_most_recent_incomplete_videos(user):
    videos_by_user = VideoLog.objects.filter(user=user)
    
    #sorted by completion time in descending order (most recent first)
    sorted_videos = sorted(videos_by_user, key=lambda student: student.completion_timestamp, reverse=True)

    video_list = []

    #basically same as in get_most_recent_incomplete exercise
    for vid in sorted_videos:
        if vid.complete == False:                       #only look for incomplete
            video_list.append(vid.video_id)             #append to list

    return video_list                                   #most recent + incomplete


#given a facility user model, returns information of the
#most recently accessed and incomplete video/exercise. Can expand this later on to
#include more later, like all items in order or perhaps more logs to look at. 
def get_most_recent_incomplete_item(user):
    #get the queryset objects
    exercises_by_user = ExerciseLog.objects.filter(user=user)
    videos_by_user = VideoLog.objects.filter(user=user)

    #sort both
    sorted_exercises = sorted(exercises_by_user, key=lambda student: student.completion_timestamp, reverse=True)
    sorted_videos = sorted(videos_by_user, key=lambda student: student.completion_timestamp, reverse=True)

    #now ensure that the item has status = incomplete
    exercise_list = []    
    for exercise in sorted_exercises:
        if exercise.complete == False:                  #only look for incomplete
            exercise_list.append(exercise)              #append to list

    video_list = []
    for vid in sorted_videos:
        if vid.complete == False:                       #only look for incomplete
            video_list.append(vid)                      #append to list

    #compare the most recent
    if exercise_list[0].completion_timestamp > video_list[0].completion_timestamp:
        
        return {
            "kind": "Exercise",
            "id": exercise_list[0].exercise_id
        }
    
    #else default to returning a video 
    else:

        return {
            "kind": "Video",
            "id": video_list[0].video_id,
            "youtube_id": video_list[0].youtube_id
        }


#given a facility user model, return the most recent exercise ids - incomplete AND complete
def get_most_recent_exercises(user):
    exercises_by_user = ExerciseLog.objects.filter(user=user)

    #sorted by completion time in descending order (most recent first)
    sorted_exercises = sorted(exercises_by_user, key=lambda student: student.completion_timestamp, reverse=True)

    final = []
    for ex in sorted_exercises:
        final.append(ex.exercise_id)
    
    return final


#given a user type (can be null), group id, and a facility name, return all users in that group
#calls the already defined function in facility module
def get_users_in_group(user_type, group_id, facility):
    return kalite.facility.get_users_from_group(user_type, group_id, facility)


#returns a topic tree representation like in the older versions of ka-lite
def generate_topic_tree():

      ### populate data exploiting structure of topic tree ###
    if not TOPICS:
        tree = get_topic_tree() 
    else:
        tree = TOPICS[settings.CHANNEL][settings.LANGUAGE_CODE] #else grab the cached topic tree

    return tree


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
    tree = generate_topic_tree()

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

    if not subtopic_id:
        return []

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