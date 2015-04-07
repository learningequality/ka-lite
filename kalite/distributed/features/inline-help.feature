@as_coach
Feature: Inline help
    Gives context to elements on the page using modal dialogs and highlighting elements.

    Scenario: Inline help on the "manage" page
        Given I'm on the manage page
        When I click the starting point
        Then I see a modal with step number 1
        And an element is highlighted
        And the modal has a "next" button
        When I click the "next" button
        Then I see a modal with step number 2

    Scenario: I click the "skip" button
        Given I've started the intro
        When I click the "skip" button
        Then the modal disappears
        Given I've started the intro
        Then I see a modal with step number 1

    Scenario: I give the "back" button a test drive
        Given I've started the intro
        Then I see a modal with step number 1
        And the back button is disabled
        When I click the "next" button
        Then I see a modal with step number 2
        When I click the "back" button
        Then I see a modal with step number 1

    Scenario: The page has no intro! Oh no!
        Given I'm on a page with no intro
        Then I should not see the starting point

    Scenario: I click outside the modal
        Given I've started the intro
        When I click outside the modal
        Then the modal disappears 
