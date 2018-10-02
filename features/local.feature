Feature: Local access
  As a personal assistant user
  I want to be able to greet my personal assistant using local console
  So that I could use it without any network

  @slow
  Scenario: Local hello
    Given I started the main script
     When I type "Привет"
      And press enter
     Then I see "Niege> Ой, приветик!"
