Feature: Local access
  As a personal assistant user
  I want to be able to greet my personal assistant using local console
  So that I could use it without any network

  Scenario: Local prompt
    When I start the main script
    Then I see the input prompt
    
  Scenario: Local hello
    Given I started the main script
    When I type "Привет"
     And press enter
    Then I see "Niege> Ой, приветик!"
     And I see the input prompt
