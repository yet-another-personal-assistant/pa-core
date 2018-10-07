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
  Scenario: Fake brain
    Given I connected to the service
     When I type "hello"
      And press enter
     Then I see "Niege> hello"

  @fake
  Scenario: Only one reply
    Given that brain should reply
     | phrase | response | delay |
     | x      | x        |   0.5 |
     | y      | y        |     0 |
     When client1 is connected to the service
      And client2 is connected to the service
     When client1 sends "x"
      And client2 sends "y"
     Then client1 sees "Niege> x"
     Then client2 sees "Niege> y"
