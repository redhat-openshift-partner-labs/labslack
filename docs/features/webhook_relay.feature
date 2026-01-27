Feature: Webhook Relay
  As an external system
  I want to send messages via webhook to the Slack bot
  So that they are relayed to the designated Slack channel

  Background:
    Given the bot is configured with a relay channel
    And the webhook endpoint is available at "/webhook"
    And a valid API key "test-api-key-123" is configured

  Scenario: Successfully relay a webhook message
    Given a valid webhook payload:
      """
      {
        "message": "Deployment completed successfully",
        "source": "CI/CD Pipeline"
      }
      """
    And the request includes valid API key authentication
    When I POST to the webhook endpoint
    Then the response status should be 200
    And the message "Deployment completed successfully" should be relayed to the channel
    And the source "CI/CD Pipeline" should be included in the relay

  Scenario: Relay webhook with custom metadata
    Given a valid webhook payload:
      """
      {
        "message": "Alert: High CPU usage detected",
        "source": "Monitoring System",
        "severity": "warning",
        "timestamp": "2024-01-15T10:30:00Z"
      }
      """
    And the request includes valid API key authentication
    When I POST to the webhook endpoint
    Then the response status should be 200
    And the relayed message should include all provided metadata

  Scenario: Reject request with missing API key
    Given a valid webhook payload:
      """
      {
        "message": "Test message"
      }
      """
    And the request does not include API key authentication
    When I POST to the webhook endpoint
    Then the response status should be 401
    And the response should contain error "Unauthorized"
    And no message should be relayed

  Scenario: Reject request with invalid API key
    Given a valid webhook payload:
      """
      {
        "message": "Test message"
      }
      """
    And the request includes invalid API key "wrong-key"
    When I POST to the webhook endpoint
    Then the response status should be 401
    And no message should be relayed

  Scenario: Reject request with missing message field
    Given an invalid webhook payload:
      """
      {
        "source": "Some System"
      }
      """
    And the request includes valid API key authentication
    When I POST to the webhook endpoint
    Then the response status should be 400
    And the response should contain error "Missing required field: message"
    And no message should be relayed

  Scenario: Reject request with empty message
    Given an invalid webhook payload:
      """
      {
        "message": "",
        "source": "Some System"
      }
      """
    And the request includes valid API key authentication
    When I POST to the webhook endpoint
    Then the response status should be 400
    And the response should contain error "Message cannot be empty"
    And no message should be relayed

  Scenario: Handle malformed JSON
    Given a malformed request body that is not valid JSON
    And the request includes valid API key authentication
    When I POST to the webhook endpoint
    Then the response status should be 400
    And the response should contain error "Invalid JSON"

  Scenario: Health check endpoint
    When I GET the "/health" endpoint
    Then the response status should be 200
    And the response should indicate the service is healthy
