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

  @fake
  Scenario: Presence message
     When I start the main script
     Then brain sees new local channel

  @fake
  Scenario: Go to bed
     When I start the main script
     Then brain sees new local channel
     When brain sends "go to bed" message to me
     Then I see "Niege> go to bed"

  @fake
  Scenario: Hello
     When I start the main script
     Then brain sees new local channel
     When I type "hello"
      And press enter
     Then I see "Niege> hello"
