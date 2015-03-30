Feature: Exercises on the Learn page
    In order to test the features of exercises
    Internally we distinguish between Khan exercises and perseus exercises,
    But the user doesn't and we shouldn't here.

    Scenario: Exercise is not available
        Given I open an exercise
        And the exercise is not available
        Then I should see an alert

    Scenario: Exercise is available
        Given I open an exercise
        And the exercise is available
        Then I will be happy 

