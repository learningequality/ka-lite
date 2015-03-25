@as_admin
Feature: The facilities tab
    Set our expectations

    Scenario: There's no facilities
        Given There are no facilities
        And I go to the facilities tab
        Then I should see an empty facilities message

    Scenario: Wherein I add a facility
        When I create a facility
        Given I go to the facilities tab
        Then I should see it in the table

    Scenario: I click the button
        Given There are no facilities
        And I go to the facilities tab
        When I click the add new facility button
        Then I am at the new facility form
        When I submit the form
        Then I see my new facility
