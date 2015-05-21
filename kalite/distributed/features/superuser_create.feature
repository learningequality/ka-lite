Feature: Create superuser from the in browser modal

    Scenario: Superuser already exists
        Given there is superuser 
        And I am on the homepage
        Then there should be no modal displayed

    Scenario: Superuser does not exist yet
        Given there is no superuser
        And I am on the homepage
        Then I should see a modal
        And I will not be able to dismiss the modal until a superuser is created

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

    Scenario: Create superuser with incorrect email address
        Given I enter my email address incorrectly
        When I click the create button
        Then the email border will turn red
        And the modal won't dismiss

    Scenario: Create superuser with email address longer than 40
        Given I enter a email address longer than 40 letters
        When I click the create button
        Then the modal won't dismiss

    Scenario: Create superuser with correct username and password and email address
        Given I enter username correctly
        And I enter password correctly
        And I enter email correctly
        When I click the create button
        Then a superuser is created
        And the modal will dismiss