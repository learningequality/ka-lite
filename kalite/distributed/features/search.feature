Feature: Search Autocomplete on Homepage

    Scenario: Search for 'Math'
        Given I am on the homepage
        When I search for 'Math'
        Then I should see a list of options

    Scenario: Search for Some Content and Navigate
        Given I am on the homepage
        When I search for something
        Then I should see a list of options
        When I click on the first option
        Then I should navigate to a content page

