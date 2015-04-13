Feature: Logging into KA Lite
    Set our expectations

    Scenario: There is one facility
        Given there is one facility
        and that I am on the homepage
        when I click log in
        then there should be no facility drop down

    Scenario: There is more than one facility
        Given there is more than one facility
        and that I am on the homepage
        when I click log in
        then there should be a facility drop down

    Scenario: Logging in with the incorrect password
        Given that I have an account
        and that I am on the homepage
        when I enter my username
        and I enter my password incorrectly
        then the password should be highlighted
        and a tooltip should appear on the password box only

    Scenario: Logging in with the wrong username
        Given that I have an account
        and that I am on the homepage
        when I enter my username wrong
        and I enter my password correctly
        then the username should be highlighted
        and a tooltip should appear on the username box only