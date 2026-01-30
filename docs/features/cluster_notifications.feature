Feature: Cluster Expiration Notifications
  As an external job scheduler
  I want to send cluster notifications via LabSlack
  So that OpenShift administrators are notified before clusters expire

  Background:
    Given the notification system is configured
    And the Slack user group "opladmins" exists
    And the notifications channel is available

  # --- Sending Notifications ---

  Scenario: Send 48-hour warning notification
    Given a valid API key
    When I POST to "/api/notify" with:
      | cluster_id        | ocp-prod-01                     |
      | cluster_name      | Production Cluster              |
      | notification_type | warning                         |
      | expiration_date   | 2024-03-15T12:00:00Z            |
    Then the response status should be 200
    And the response should include a notification_id
    And a Slack message should be sent to the notifications channel
    And the message should mention "@opladmins"
    And the message should include "ocp-prod-01"
    And the message should indicate "48 hours" until expiration

  Scenario: Send expired notification
    Given a valid API key
    When I POST to "/api/notify" with:
      | cluster_id        | ocp-prod-01                     |
      | cluster_name      | Production Cluster              |
      | notification_type | expired                         |
    Then the response status should be 200
    And a Slack message should indicate the cluster has expired

  Scenario: Send decommission notification
    Given a valid API key
    When I POST to "/api/notify" with:
      | cluster_id        | ocp-prod-01                     |
      | cluster_name      | Production Cluster              |
      | notification_type | decommission                    |
    Then the response status should be 200
    And a Slack message should indicate the cluster has been decommissioned

  Scenario: Send notification with custom message
    Given a valid API key
    When I POST to "/api/notify" with:
      | cluster_id        | ocp-prod-01                     |
      | cluster_name      | Production Cluster              |
      | notification_type | warning                         |
      | message           | Custom warning message          |
    Then the response status should be 200
    And the Slack message should contain "Custom warning message"

  # --- Validation ---

  Scenario: Notification without API key fails
    Given no API key is provided
    When I POST to "/api/notify" with:
      | cluster_id        | ocp-prod-01                     |
      | cluster_name      | Production Cluster              |
      | notification_type | warning                         |
    Then the response status should be 401

  Scenario: Notification with invalid API key fails
    Given an invalid API key
    When I POST to "/api/notify" with:
      | cluster_id        | ocp-prod-01                     |
      | cluster_name      | Production Cluster              |
      | notification_type | warning                         |
    Then the response status should be 401

  Scenario: Notification missing cluster_id fails
    Given a valid API key
    When I POST to "/api/notify" with:
      | cluster_name      | Production Cluster              |
      | notification_type | warning                         |
    Then the response status should be 400
    And the error should indicate "cluster_id is required"

  Scenario: Notification with invalid type fails
    Given a valid API key
    When I POST to "/api/notify" with:
      | cluster_id        | ocp-prod-01                     |
      | cluster_name      | Production Cluster              |
      | notification_type | invalid                         |
    Then the response status should be 400
    And the error should indicate "notification_type"

  # --- History ---

  Scenario: Successful notification is recorded in history
    Given a valid API key
    When I POST to "/api/notify" with:
      | cluster_id        | ocp-prod-01                     |
      | cluster_name      | Production Cluster              |
      | notification_type | warning                         |
    Then the notification should be recorded in the database
    And the record status should be "sent"

  Scenario: Failed notification is recorded with error
    Given a valid API key
    And the Slack API is unavailable
    When I POST to "/api/notify" with:
      | cluster_id        | ocp-prod-01                     |
      | cluster_name      | Production Cluster              |
      | notification_type | warning                         |
    Then the response status should be 500
    And the notification should be recorded in the database
    And the record status should be "failed"
    And the record should include the error message
