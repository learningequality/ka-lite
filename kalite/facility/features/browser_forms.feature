Feature: Facility Browser Forms
    In order to test the features of browser forms

    Scenario: No groups available on signup
        Given there is a facility
        And there are no groups
        And I am on the signup page
        Then the group selector should be hidden

    Scenario: Group available on signup
        Given there is a facility
        And there is a group
        And I am on the signup page
        Then the group selector should be shown
