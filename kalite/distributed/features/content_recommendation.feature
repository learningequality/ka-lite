@as_learner
Feature: Content Recommendation on the Homepage

	Scenario: the content recommendation page should be shown
		Given I have already made some progress on lessons
		When the home page is loaded
		Then the content recommendation cards should be shown
		And the resume card should be shown on the very left of the page
		And the next steps card should be shown in the middle of the page
		And the explore card should be shown on the very right of the page

	Scenario: the last video/exercise should be shown
		Given I have already made some progress on lessons
		When the home page is loaded
		And I click on the resume card lesson
		Then the last in-progress video/exercise should be shown

	Scenario: the last in-progress exercise should be shown
		Given I have already made some progress on lessons
		When the home page is loaded
		And I click in the middle of an exercise suggestion on the next steps card
		Then I should be taken to that exercise

	Scenario: the in-progress topic should be shown
		Given I have already made some progress on lessons
		When the home page is loaded
		And I click on the right of an exercise suggestion on the next steps card
		Then I should be taken to that topic

	Scenario: the suggested topic should be shown
		Given I have already made some progress on lessons
		When the home page is loaded
		And I click on a suggested topic on the explore card
		Then I should be taken to that topic
