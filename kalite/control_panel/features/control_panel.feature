@as_admin
Feature: The facilities tab
    Set our expectations

    Scenario: There's no facilities
        Given There are no facilities
        And I go to the facilities tab
        Then I should see an empty facilities message

    Scenario: Wherein I add a facility
        Given There are no facilities
        When I create a facility
        Given I go to the facilities tab
        Then I should see a facility in the table
