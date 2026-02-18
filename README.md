# Bot Commands Documentation

## Overview
This document provides a comprehensive guide to the commands, usage examples, setup instructions, and features of the bot.

## Commands
### 1. Create a New Branch
- **Command:** `create_branch`
- **Usage:** This command creates a new branch in the repository.
  - **Example:** `create_branch feature-x`

### 2. Update a File
- **Command:** `create_or_update_file`
- **Usage:** This command allows you to create or update a file in the repository.
  - **Example:** `create_or_update_file path/to/file.md`

### 3. Merge a Pull Request
- **Command:** `merge_pull_request`
- **Usage:** Merges an open pull request into the specified branch.
  - **Example:** `merge_pull_request #42`

### 4. Push Files
- **Command:** `push_files`
- **Usage:** This command allows you to push files to the repository in a single commit.
  - **Example:** `push_files filesArray`

### 5. Update the Pull Request Branch
- **Command:** `update_pull_request_branch`
- **Usage:** Updates the branch of a pull request with the latest changes from the base branch.
  - **Example:** `update_pull_request_branch pullNumber`

## Usage Examples
- To create a new branch: `create_branch feature-xyz`
- To update the README: `create_or_update_file README.md`
- To merge a pull request: `merge_pull_request #31`
- To push files: `push_files files`
- To update the PR branch: `update_pull_request_branch 55`

## Setup Instructions
1. Clone the repository:
   ```bash
   git clone https://github.com/arvind021/babli.git
   ```
2. Navigate to the directory:
   ```bash
   cd babli
   ```
3. Install dependencies (if applicable):
   ```bash
   npm install
   ```
4. Start the bot:
   ```bash
   npm start
   ```

## Features
- Easy to use command structure.
- Supports common GitHub operations like branching, merging, and file management.
- Provides quick feedback on command execution.

Enjoy using the bot!