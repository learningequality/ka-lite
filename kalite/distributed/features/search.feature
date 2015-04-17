Feature: Search Autocomplete on Homepage

    Scenario: Search for 'Math'
        Given I am on the homepage
        When I search for 'Math'
        Then I should see a list of options

    Scenario: Search for Basic Addition and Navigate
        When I search for Basic Addition
        And I click on the first option
        Then I should navigate to Basic Addition

