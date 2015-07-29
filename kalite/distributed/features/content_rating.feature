Feature: Content Rating
    Tests for the content rating form/widget, which should appear on content pages (video, exercises, etc)

    Scenario: User rates an unrated item
        Given I am on a content page
        Then I see a feedback form
        When I fill out the form
        Then my feedback is displayed

    Scenario: User alters a rating
        Given I have filled out a feedback form
        Then I see an edit button
        When I edit my feedback
        Then my edited feedback is displayed

    Scenario: User deletes a rating
        Given I have filled out a feedback form
        Then I see a delete button
        When I delete my feedback
        Then I see a blank form

    @as_admin
    Scenario: Admin exports user ratings
        Given some user feedback exists
        When I export csv data
        Then the user feedback is present