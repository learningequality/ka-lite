Feature: Logging into KA Lite
    Set our expectations

    Scenario: There is one facility
        Given there is one facility
        and I am on the homepage
        when I click log in
        then there should be no facility drop down

    Scenario: There is more than one facility
        Given there is more than one facility
        and I am on the homepage
        when I click log in
        then there should be a facility drop down

    Scenario: Logging in with the incorrect password
        Given there is one facility
        and I have an account
        and I am on the homepage
        when I click log in
        and I enter my username correctly
        and I enter my password incorrectly
        and I click the login button
        then the password should be highlighted
        and a tooltip should appear on the password box only

    Scenario: Logging in with the wrong username
        Given there is one facility
        and I have an account
        and I am on the homepage
        when I click log in
        and I enter my username incorrectly
        and I enter my password correctly
        and I click the login button
        then the username should be highlighted
        and a tooltip should appear on the username box only

    Scenario: Logging in with correct username and password
        Given there is one facility
        and I have an account
        and I am on the homepage
        when I click log in
        and I enter my username correctly
        and I enter my password correctly
        and I click the login button
        then the login button should disappear