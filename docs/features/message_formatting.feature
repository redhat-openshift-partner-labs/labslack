Feature: Message Formatting
  As a relay bot
  I want to format messages with configurable metadata
  So that recipients understand the message context

  Scenario: Format DM message with full metadata
    Given a DM message from user "U12345678" with text "Hello, I need assistance"
    And the message was sent at timestamp "1705312200.123456"
    And metadata inclusion is enabled
    When the message is formatted for relay
    Then the formatted message should include a header with user mention "<@U12345678>"
    And the formatted message should include the timestamp
    And the formatted message should include the original text "Hello, I need assistance"

  Scenario: Format DM message without metadata
    Given a DM message with text "Just the message please"
    And metadata inclusion is disabled
    When the message is formatted for relay
    Then the formatted message should only contain "Just the message please"

  Scenario: Format webhook message with source
    Given a webhook message with text "Build #123 passed"
    And the source is "Jenkins"
    And metadata inclusion is enabled
    When the message is formatted for relay
    Then the formatted message should include the source "Jenkins"
    And the formatted message should include the text "Build #123 passed"

  Scenario: Format webhook message with custom fields
    Given a webhook message with text "Server alert"
    And the following custom fields:
      | field    | value      |
      | severity | critical   |
      | host     | prod-web-1 |
    And metadata inclusion is enabled
    When the message is formatted for relay
    Then the formatted message should include field "severity" with value "critical"
    And the formatted message should include field "host" with value "prod-web-1"

  Scenario: Escape special Slack formatting characters
    Given a DM message with text "Use <script> tags and @mentions"
    When the message is formatted for relay
    Then special characters should be properly escaped

  Scenario: Truncate very long messages
    Given a message with text exceeding 4000 characters
    When the message is formatted for relay
    Then the message should be truncated to 4000 characters
    And a truncation indicator should be appended

  Scenario: Handle messages with attachments reference
    Given a DM message with text "See attached"
    And the message has 2 file attachments
    When the message is formatted for relay
    Then the formatted message should indicate "2 attachments"
