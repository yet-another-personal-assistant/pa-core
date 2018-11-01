Feature: Remote access
  As a personal assistant user
  I want to be able to greet my personal assistant using inet socket
  So that I could use it from a different computer
  
  Background: Service is started
    Given the service is started

  @slow
  Scenario: Remote hello
    Given I connected to the service
     When I type "Привет"
      And press enter
     Then I see "Niege> Ой, приветик!"

  @fake
  Scenario: Presence message
     When I connect to the service
     Then I see "Please enter your name> "
     When I type "user1"
      And press enter
     Then brain sees new remote channel for user1

  @fake
  Scenario: Hello message
    Given user1 connected to the service
     When user1 types "hello"
      And presses enter
     Then user1 sees "Niege> hello"

  @fake
  Scenario: Presence message
    Given user1 connected to the service
     When brain sends "go to bed" message to user1
     Then user1 sees "Niege> go to bed"
