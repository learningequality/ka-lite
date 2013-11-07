This is a set of instructions for those who wish to use KA Lite locally to both local
video content and exercises.   This is the stated long term goal of www.learningequality.org
and the software is quite capable of doing this as is with a mininum of edits to the 
datafiles.  The files that must be maticulously edited to allow for local content are in the
kalite/static/data/ subdirectory and below and include:
topics.json
maplayout_data.json
youtube_to_slug_map.json
and addition of files in the topicdata directory which groups
exercises into collections.

The mjp_release-0.11 branch included 4 homebrew exercises the first of which
is just a direct copy of the absolute values khan academy exercise.
The others demonstrate use of both pictures, sound, and some calls out to
external resources which would not be available in an off-line environment.
All sound and picture resoures are stored in a dedicated subdirectory in the
ka-lite/kalite/static/js/khan-exercises/images subdirectory