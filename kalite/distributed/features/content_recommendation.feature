Feature: Content Recommendation on the Homepage

	Scenario: the content recommendation page should be shown
		Given that I log in
		And have already made some progress on lessons
		When the home page is loaded
		Then the content recommendation cards should be shown

	Scenario: the “resume” card should be shown 
		Given that I log in
		And have already made some progress on lessons
		When the home page is loaded
		Then the “resume” card should be shown on the very left of the page with the last video/lesson the user was learning

	Scenario: the “next steps” card should be shown
		Given that I log in
		And have already made some progress on lessons
		When the home page is loaded
		Then the “next steps” card should be shown in the middle of the page with the last video/lessons I was learning should be shown in succession

	Scenario: the “explore” card should be shown
		Given that I log in
		And have already made some progress on lessons
		When the home page is loaded
		Then the “explore” card should be shown on the very right of the page with with a mix of random topics and topics that are Related to ones that I have started learning

	Scenario: the last video/exercise should be shown
		Given that I log in
		And have already made some progress on lessons
		And home page is loaded
		When I click on the “resume” card lesson
		The last in-progress video/exercise should be shown (no longer on the home page)

	Scenario: the last in-progress exercise should be shown
		Given that I log in
		And have already made some progress on lessons
		And the home page is loaded
		When I click in the middle of an exercise suggestion on the “next steps” card (exercise name)
		I should be taken to that exercise

	Scenario: the in-progress topic should be shown
		Given that I log in
		And have already made some progress on lessons
		And the home page is loaded
		When I click on the right of an exercise suggestion on the “next steps” card (topic with arrow link)
		I should be taken to that topic - the sidebar will be unfolded to highlight the topic

	Scenario: the suggested topic should be shown
		Given that I log in
		And have already made some progress on lessons
		And the home page is loaded
		When I click on a suggested topic on the “explore” card
		I should be taken to that topic - the sidebar will be unfolded to highlight the topic
