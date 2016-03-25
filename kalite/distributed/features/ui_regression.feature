Feature: UI regression tests
    To ensure that basic functionality is not lost

    Scenario: Coach has a logout link
        Given I'm logged in as a coach
        And I can see the username dropdown menu
        When I click the username dropdown menu
        Then I see a logout link

    Scenario: Login modal gets displayed when superusercreate modal presents
        Given superuser is deleted
        Given I'm on update_videos page
        Then I'm redirected to the homepage
        Then I see only superusercreate modal

    @as_coach
    Scenario: Documentation link shown to coaches
        Given I am on the homepage
        Then I see the documentation link

    @as_admin
    Scenario: Documentation link shown to admins
        Given I am on the homepage
        Then I see the documentation link

    @as_learner
    Scenario: Documentation link not shown to learners
        Given I am on the homepage
        Then I do not see the documentation link
