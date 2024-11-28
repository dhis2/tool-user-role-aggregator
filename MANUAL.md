# User Role Aggregator Tool - User Manual

## Introduction

The User Role Aggregator Tool is designed to streamline the management of user roles in DHIS2. It provides an easy-to-use interface to create new user roles that manage specific roles and modify existing user roles to add or update their managed roles.

## Table of Contents

1. [Requirements](#requirements)
2. [Installation](#installation)
3. [Usage](#usage)
    - [Create New User Admin Role](#create-new-user-admin-role)
    - [Update Existing User Admin Role](#update-existing-user-admin-role)
4. [Feedback and Notifications](#feedback-and-notifications)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)

## Requirements

- DHIS2 instance (with appropriate user privileges)
- Administrative access to the DHIS2 instance to install the web app

## Installation

### Downloading the App

1. **Go to GitHub Repository:**

   Navigate to the [GitHub repository](https://github.com/dhis2/tool-user-role-aggregator/releases) where the release of the app is available.

2. **Download the .zip File:**

   Locate the latest release and download the `.zip` file containing the app.

### Installing the App in DHIS2

1. **Login to DHIS2:**

   Login to your DHIS2 instance with administrative credentials.

2. **Access the App Management Module:**

   Navigate to the "App Management" module from the DHIS2 dashboard.

3. **Upload the .zip File:**

   - Click on the "Install from file" button.
   - Select the downloaded `.zip` file and upload it.

4. **Verify Installation:**

   After the upload completes, verify that the "User Role Aggregator App" appears in the list of installed apps.

**Warning**: Do not install this app directly in a production environment without thorough testing. Always test in a development or staging environment first to ensure all functionalities work as expected.

## Usage

### Create New User Role for User Admins

1. **Navigate to "Create New" Tab:**

   Click on the "Create New" tab to open the interface for creating a new user admin role.

2. **Enter Role Name:**

   Enter a name for the new role in the "Role Name" input field.

3. **Select User Roles to Manage:**

   Use the dropdown to select one or more user roles that the new admin role should be able to manage. This dropdown has search functionality to help find roles quickly.

4. **Select Additional Authorities:**

   Use the dropdown to add additional authorities for the new role. The authorities related to user management are pre-selected, but can be deselected.

5. **Create Role:**

   Click on the "Create Role" button to create the new user admin role. You will receive a success or error message based on the outcome.

### Validate or Update Existing User Admin Role

1. **Navigate to "Update" Tab:**

   Click on the "Update" tab to open the interface for updating an existing user admin role.

2. **Select Existing Admin Role:**

   Use the dropdown to select the existing admin role that you want to update.

3. **Validate Role:**

   Click on the "Validate Role" button. This will validate the selected role and display the managed roles it can handle.

4. **Modify Managed Roles:**

   Use the "Modify Managed Roles" dropdown to add additional roles that the selected admin role should be able to manage.

5. **Modify Role:**

   Click on the "Modify Role" button to save the changes. You will receive a success or error message based on the outcome.

## Feedback and Notifications

Feedback is provided through toast notifications that appear in the top-right corner of the app. These messages inform the user about the success or failure of their actions:

- **Success**: Green toast message.
- **Error**: Red toast message with error details.

## Testing

It is crucial to test this app thoroughly in a development or staging environment before deploying it to a production instance. This ensures that all functionalities work as expected and helps identify and fix any potential issues. 

### Steps for Testing:

1. **Setup Development Environment:**

   Ensure you have a DHIS2 development or staging instance set up and configured with necessary permissions, using a fresh copy of the production environment.

2. **Test User Role Creation:**

   - Try creating a new user admin role.
   - Verify that the role appears in the DHIS2 instance.
   - Check if the role has the expected authorities and can manage the specified roles.

3. **Test User Role Update:**

   - Select an existing user admin role.
   - Validate the role and check the current managed roles.
   - Modify the managed roles and save.
   - Verify that the changes reflect in the DHIS2 instance.

4. **Edge Cases:**

   - Test with missing or incorrect input data.
   - Verify error handling and feedback mechanisms.

## Reporting Issues:

If you encounter any issues not covered in this manual, please report them to the development team with detailed descriptions and steps to reproduce the problem. 
