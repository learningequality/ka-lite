Feature: Coach reports
    In order to test the features of coach reports
    Coaches should be able to view relevant information
    about their students.

    Scenario: No data is present
        Given I am on the coach report
        And there is no data
        Then I should see a warning
		
	Scenario: I teach multiple groups
		Given I am on the coach report
		When I click on the dropdown button under the Group label
		Then I should see the list of groups that I teach
		When I can click on a group name
		Then I should see the contents of the summary change according to the group selected
		
	Scenario: I teach two groups
		Given I am on the coach report
		When I click on the dropdown button under the Group label
		Then I should see the the two groups listed
		And I should see the option of selecting all groups
		When I can click on a group name
		Then I should see the contents of the summary change according to the group selected
		
	Scenario: I want a more detailed report of my group
		Given I selected the preferred group
		When I click on the Show Tabular Report button
		Then I should see the tabular report 
	
		Given there are three learners
		And they have each completed ten exercises
		When I click on the Show Tabular Report button
		Then I should see the tabular report
		And there should be three learner rows displayed
		And there should be ten exercise columns displayed
		And I should see a Hide Tabular Report button
		
		Given that a learner completed the full exercise
		Then I should see the exercise marked as one hundred percent and colored green
		
		Given that a learner did not start the exercise
		Then I should see the exercise unmarked and colored gray
		
		Given that a learner is progressing on an exercise
		Then I should see the exercise marked with a percentage and colored light green
		
		Given that a learner is struggling on a exercise
		Then I should see the exercise marked with a percentage and colored red
	
	Scenario: I want to know more about an exercise
		Given I am on the tabular report
		When I click on a colored cell
		Then I should see the detail panel emerge from beneath the row
		And I should see the exercise name, number of questions, number of attempts, and actions made
		
	Scenario: I finished viewing the details of the exercise
		Given I am on the detail panel
		When I click on the same colored cell
		Then I should not see the detail panel anymore
		
		Given I don't remember what cell I clicked on
		When I click on a random colored cell
		Then I should see the contents of the detail panel change according to that cell
		When I click on the cell again
		Then I should not see the detail panel anymore
		
	Scenario: I finished viewing the detailed report of my group
		Given that the tabular report is displayed
		When I click on the Hide Tabular Report button
		Then I should not see the tabular report anymore
		
	Scenario: I want to know more about a specific learner
		Given that I am on the tabular report
		When I click on the learner name
		Then I should be taken to the learner's progress report page

	Scenario: I want to know more about a specific exercise
		Given that I am on the tabular report
		When I click on the exercise name
		Then I should be taken to that exercise within the Learn tab