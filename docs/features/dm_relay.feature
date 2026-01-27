Feature: DM Relay
  As a Slack user
  I want to send direct messages to the bot
  So that my message is relayed to the designated channel

  Background:
    Given the bot is configured with a relay channel
    And the bot is running

  Scenario: Successfully relay a DM to the configured channel
    Given I am a Slack user with ID "U12345678"
    When I send a DM to the bot with text "Need help with project X"
    Then the bot should relay the message to the configured channel
    And the relay should include my user ID "U12345678"

  Scenario: Relay DM with full metadata enabled
    Given I am a Slack user with ID "U12345678"
    And metadata inclusion is enabled
    When I send a DM to the bot with text "Question about deployment"
    Then the relayed message should include the sender information
    And the relayed message should include the timestamp
    And the relayed message should include the original text "Question about deployment"

  Scenario: Relay DM with metadata disabled
    Given I am a Slack user with ID "U12345678"
    And metadata inclusion is disabled
    When I send a DM to the bot with text "Quick note"
    Then the relayed message should only include the text "Quick note"

  Scenario: Ignore messages from the bot itself
    Given a message event originated from the bot itself
    When the event is processed
    Then no message should be relayed

  Scenario: Ignore message subtypes that are not user messages
    Given a message event with subtype "message_changed"
    When the event is processed
    Then no message should be relayed

  Scenario: Handle empty message gracefully
    Given I am a Slack user with ID "U12345678"
    When I send a DM to the bot with empty text
    Then no message should be relayed
