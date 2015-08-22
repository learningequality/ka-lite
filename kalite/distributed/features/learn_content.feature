Feature: Content on the Learn page
    In order to test the features of content

    Scenario: Content is not available
        Given I open some content
        And the content is not available
        Then I should see an alert
        And the alert should tell me the content is not available
