Feature: Create superuser from the in browser modal

    Scenario: Superuser already exists
        Given I am on the homepage
        And there is superuser 
        Then there should be no modal displayed

    Scenario: Superuser does not exist yet
        Given I am on the homepage
        And superuser is deleted
        Then refresh homepage
        And I should see a modal

    Scenario: Create superuser with empty username
        Given the username is empty
        When I click the create button
        Then the username border will turn red
        And the modal won't dismiss

    Scenario: Create superuser with string longer than 40
        Given I enter a username longer than 40 letters
        When I click the create button
        Then the modal won't dismiss

    Scenario: Create superuser with empty password
        Given the password is empty
        When I click the create button
        Then the password border will turn red
        And the modal won't dismiss

    Scenario: Create superuser with password longer than 40
        Given I enter a password longer than 40 letters
        When I click the create button
        Then the modal won't dismiss

    Scenario: Create superuser with unmatched password
        Given I enter an unmatched password
        When I click the create button
        Then the confirmsuperpassword border will turn red
        And the modal won't dismiss

    Scenario: Create superuser with correct username and password and re-enter password
        Given I enter username correctly
        And I enter password correctly
        And I re-enter password correctly
        When I click the create button
        Then a superuser is created
        And the modal will dismiss