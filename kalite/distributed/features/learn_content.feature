@uses_content_paths
Feature: Content on the Learn page
    In order to test the features of content

    Scenario: Content is not available
        Given I open some unavailable content
        Then I should see an alert
        And the alert should tell me the content is not available

    Scenario: Content is available
        Given I open some available content
        Then I should see no alert

    @uses_video_with_subtitles
    Scenario: Subtitles are available when
        When I visit a video with subtitles
        Then the video player is aware of the subtitles