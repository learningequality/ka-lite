Feature: Coach reports
    In order to test the features of coach reports
    Coaches should be able to view relevant information
    about their students.

    Scenario: No data is present
        Given I am on the coach report
        And there is no data
        Then I should see a warning

