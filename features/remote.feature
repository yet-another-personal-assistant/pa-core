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
