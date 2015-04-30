Feature: UI regression tests
    To ensure that basic functionality is not lost

    Scenario: Coach has a logout link
        Given I'm logged in as a coach
        And I can see the username dropdown menu
        When I click the username dropdown menu
        Then I see a logout link