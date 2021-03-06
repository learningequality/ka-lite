Feature: Create superuser from the in browser modal

    Scenario: Superuser already exists
        Given I am on the homepage
        Then there should be no modal displayed

    Scenario: Superuser does not exist yet
        Given superuser is deleted
        And I am on the homepage
        Then I should see a modal

    Scenario: Create superuser with empty username
        Given superuser is deleted
        And I am on the homepage
        Then I should see a modal
        When the username is empty
        And I click the create button
        Then the username border will turn red
        And the modal won't dismiss

    Scenario: Create superuser with string longer than 40
        Given superuser is deleted
        And I am on the homepage
        Then I should see a modal
        When I enter a username longer than 40 letters
        And I click the create button
        Then the modal won't dismiss

    Scenario: Create superuser with empty password
        Given superuser is deleted
        And I am on the homepage
        Then I should see a modal
        When the password is empty
        And I click the create button
        Then the password border will turn red
        And the modal won't dismiss

    Scenario: Create superuser with unmatched password
        Given superuser is deleted
        And I am on the homepage
        Then I should see a modal
        When I enter an unmatched password
        And I click the create button
        Then the confirmsuperpassword border will turn red
        And the modal won't dismiss

    Scenario: Create superuser with correct username and password and re-enter password
        Given superuser is deleted
        And I am on the homepage
        Then I should see a modal
        When I enter username correctly
        And I enter password correctly
        And I re-enter password correctly
        When I click the create button
        Then the modal will dismiss
        Given I am on the homepage
        Then there should be no modal displayed