@as_coach
Feature: Coach reports
    In order to test the features of coach reports
    Coaches should be able to view relevant information
    about their students.

    Scenario: No data is present
        Given there is no data
        And I am on the coach report
        Then I should see a warning
        And there should be no Show Tabular Report button

    Scenario: I teach two groups
        Given there are two groups
        And I am on the coach report
        When I click on the dropdown button under the Group label
        Then I should see the list of two groups that I teach
        And I should see the option of selecting all groups
        When I select the preferred group
        Then I should see the contents of the summary change according to the group selected

    Scenario: I want to see all the relevant data
        Given there are three learners
        And all learners have completed ten exercises
        And I am on the coach report
        When I click on the Show Tabular Report button
        Then I should see the tabular report
        And there should be three learner rows displayed
        And there should be ten exercise columns displayed
        And I should see a Hide Tabular Report button

    Scenario Outline: I want to read student data from the tabular report
        Given the "<learner>" "<progress verbs>" an "<exercise>"
        And I am on the tabular report
        Then I should see the "<exercise>" marked for "<learner>" as "<progress text>" and coloured "<progress colour>"

    Examples: Learners
        | learner | progress verbs | progress text | progress colour | exercise                           |
        | some    | attempted      | 50%           | light blue      | relate-addition-and-subtraction    |
        | all     | completed      | None          | dark green      | subtraction_1                      |
        | struggle| struggling     | 30%           | red             | addition_2                         |

    Scenario: I want to know more about an exercise
        Given I am on the tabular report
        When I click on the partial colored cell
        Then I should see the detail panel emerge from beneath the row

    Scenario: I finished viewing the details of the exercise
        Given I am on the detail panel
        When I click on the partial colored cell
        Then I should not see the detail panel anymore

    Scenario: I finished viewing the details of the exercise and look at another
        Given I am on the detail panel
        When I click on the completed colored cell
        Then I should see the contents of the detail panel change according to the completed cell

    Scenario: I finished viewing the detailed report of my group
        Given I am on the tabular report
        When I click on the Hide Tabular Report button
        Then I should not see the tabular report anymore

    Scenario: I want to know more about a specific learner
        Given I am on the tabular report
        When I click on the learner name
        Then I should be taken to the learner's progress report page

    Scenario: I want to know more about a specific exercise
        Given I am on the tabular report
        When I click on the exercise name
        Then I should be taken to that exercise within the Learn tab