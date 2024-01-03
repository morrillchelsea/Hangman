# Hangman

## Description
Hangman game that enables the user to guess the letters of a randomly selected word.

This Hangman game was developed for a school course and demonstrates OOP as well my ability to work with AWS (Boto3 and DynamoDB). Unfortunately, as the file is stored and read from the S3 Bucket, the program is unable to run without a connection. I am working on modifying the code to use SQLite3 as a SQL DB to track top user scores instead of AWS as well as a local .txt file for word selection. 

### Future changes would include:
- Ability to run without AWS connection
- Create separate modules rather than classes
- Some sort of GUI or images displaying the figure of the Hangman.
- Ability for users to register or login to keep track of scores and wins/losses

### Specifications
Language: Python3 // Additional Libraries: boto3
