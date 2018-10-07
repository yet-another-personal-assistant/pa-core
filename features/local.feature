Feature: Local access
  As a personal assistant user
  I want to be able to greet my personal assistant using local console
  So that I could use it without any network

  Background: Main script running
    Given I started the main script

  @slow
  Scenario: Local hello
     When I type "Привет"
      And press enter
     Then I see "Niege> Ой, приветик!"

  @fake
  Scenario: Local echo brain
    Given that brain should reply
     | phrase | response | delay |
     | hello  | hi       |   0.5 |
     When I type "hello"
      And press enter
     Then I see "Niege> hi"

  @fake
  Scenario: Local silent
    Given that brain should reply
     | phrase | response |
     | hello  | None     |
     When I type "hello"
      And press enter
     Then I see nothing

  @fake
  Scenario: Brain message
     When brain says "hello"
     Then I see "Niege> hello"
