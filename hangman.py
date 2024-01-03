'''
Created by: Nieves, Chelsea
SDEV400
Prof Craig Poma
Last Modified: 10 June 2023

'''
import logging
import sys
import random
import os
import boto3
from botocore.exceptions import ClientError

def main():
    '''Main function'''
    # instantiate S3
    s3 = S3Boto()
    # instantiate menu
    menu = Menu('')
    # call s3_handler method from S3Boto class
    table = Table()

    # call S3Boto class method s3_handler to manage S3 bucket creation and file upload
    s3.s3_handler()
    # call Table class method create_table() to create leaderboard in DynamoDB
    table.create_table()
    # call menu function from Menu class
    menu.menu()

class S3Boto():
    ''' Class to manage S3 bucket creation and objects '''
    # class variables
    client = boto3.client('s3')
    resource = boto3.resource('s3')
    bucket_name = 'nieves-chelsea-4'
    # file obtained from https://github.com/Xethron/Hangman/blob/master/words.txt
    file = 'Hangman/hangman_dictionary.txt' # list of guessable words

    def bucket_exists(self):
        ''' Determines if a bucket exists in specified client.
        :return: True if bucket exists, else False '''
        print(f'Checking if {self.bucket_name} exists...')
        try:
            # query bucket
            self.client.head_bucket(Bucket=self.bucket_name)
            print(f'Bucket {self.bucket_name} exists!')
        except ClientError as e:
            # If a client error is thrown, then check that it was a 404 error.
            # If it was a 404 error, then the bucket does not exist.
            error_code = int(e.response['Error']['Code'])
            if error_code == 403:
                print("Private Bucket. Forbidden Access!")
                return True
            elif error_code == 404:
                print("Bucket Does Not Exist!")
                return False
        return True

    def create_bucket(self):
        '''Create an S3 bucket in the S3 default
        region (us-east-1).
    
        :param bucket_name: Bucket to create
        :return: True if bucket created, else False '''
        # create bucket if bucket does not already exist
        if not self.bucket_exists():
            print(f'Trying to create bucket {self.bucket_name}...')
            try:
                self.client.create_bucket(Bucket = self.bucket_name)
                # print success message
                print('Bucket %s created successfully!', self.bucket_name)
            except ClientError as e:
                logging.error(e)
        else:
            # log error
            logging.info('Unable to create bucket or bucket %s already exists', self.bucket_name)
            return False
        return True

    def upload_file(self):
        ''' Upload a file to an S3 bucket

        :param bucket: Bucket to upload to
        :param object_name: S3 object name. If not specified then file_name is used
        :return: True if file was uploaded, else False '''

        # name of S3 object
        object_name = os.path.basename(self.file)

        # try to upload the file
        try:
            self.client.upload_file(self.file, self.bucket_name, object_name)
            # print success message
            print(f'{self.file} uploaded to {self.bucket_name} successfully!')
        except ClientError as e:
            # print error message
            print(f'Error: Unable to upload {self.file} to {self.bucket_name}')
            logging.error(e)
            return False
        return True

    def s3_handler(self):
        ''' method to handle S3 class '''
        # call method to create S3 bucket
        self.create_bucket()

        print('Trying to upload file...')
        # if bucket exists
        if self.bucket_exists():
            # upload file to bucket
            self.upload_file()
        else:
            print(f'{self.bucket_name} does not exist. Unable to upload file.')

class Table():
    ''' class to manage DynamoDB objects and methods '''
    # class variables
    resc = boto3.resource('dynamodb')
    #declareboto3 client instance
    client = boto3.client('dynamodb')
    table_name = 'Leaderboard'
    # define table
    table = resc.Table(table_name)

    def add_items(self, initials, score):
        ''' Method to input data to table Statistics '''
        # scan number of items currently in DynamoDB
        scan_items = self.table.scan()
        # assign num of items in table to items var
        items = len(scan_items['Items'])
        # add to num of items to increment userid key
        incr_userid = items + 1
        # assign incremented key to userid var 
        userid = incr_userid

        try:
            # put_item request to add item to dynamodb
            self.table.put_item(
                Item={
                    'UserID' : userid,
                    'Initials': initials,
                    'Score': score
                    #'Rank': rank
                }
            )
        except ClientError as err:
            logging.error(
                "Couldn't add initials %s to table %s. Here's why: %s: %s",
                initials, self.table.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise

    def view_my_stats(self, initials):
        ''' method to handle viewing user's game score history '''
        #while selection_handler():
        #display program title
        print('\nLeaderboard\n')

        #scan items in dynamodb table
        response = self.client.scan(
            TableName= self.table_name, #assign table name filter to scan
            FilterExpression='Initials = :initials',
            ExpressionAttributeValues={
                ':initials': {'S': f'{initials}'}
            }
        )
        #if items not in response
        if response['Count'] == 0:
            #output leaderboard item not found
            print('\nNo data in leaderboard')
            print('You have not played any games\n')
        else:
            for i in response['Items']:
                print({'Initials': i['Initials'], 'Score': i['Score']}, '\n')

    def view_leaderboard(self):
        ''' method to output top 5 scores from leaderboard to user '''
        return

    def create_table(self):
        '''Using the AWS SDK and Python within your AWS Educate Cloud9 environment, create a
        DynamoDB table'''

        # call create_table operation to add table to db
        try:
            new_table = self.resc.create_table(
                #Assign name 'Courses' to table
                TableName= self.table_name,
                KeySchema=[
                    {
                        'AttributeName': 'UserID', #Name of attribute to be assigned as PK
                        'KeyType': 'HASH'#Assign keytype HASH to Attribute CourseID
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName' : 'UserID', #Assign name to PK
                        'AttributeType' : 'N' #Assign data type number to PK
                    }
                ],
                ProvisionedThroughput={
                    #The maximum number of strongly consistent reads consumed per second
                    #before DynamoDB returns a ThrottlingException
                    'ReadCapacityUnits': 5, 
                    #The maximum number of writes consumed per second
                    #before DynamoDB returns a ThrottlingException
                    'WriteCapacityUnits': 5
                }
            )
            print('Table status:', new_table.table_status) #Output table creation status
            #set up waiter to wait until table exists to put items
            waiter = self.client.get_waiter('table_exists')
            waiter.wait(
                TableName=self.table_name,
                WaiterConfig={
                    'Delay': 20,
                    'MaxAttempts': 25
                }
            )
        except self.client.exceptions.ResourceInUseException:
            #Output error if table already exists
            print(f'Table {self.table_name} exists.')
            return False
        return True

class Score():
    ''' Class to handle scorekeeping '''
    def __init__(self, score):
        self.score = score

    def set_score(self,op, points):
        ''' Method to handle addition or deduction of points based on correctness of user guess '''
        if op == '+':
            self.score = self.score + points
        else:
            self.score = self.score - points

    def get_score(self):
        ''' Getter method to output user score '''
        return self.score

    def set_initials(self):
        ''' Method to get and validate user initals as input  '''
        # create instance of class Hangman()
        h = Hangman('', '')
        # loop to get input
        while True:
            try:
                initials = input("Enter initials: ").strip().upper()
            except ValueError:
                print('Invalid input.')
            # initials must be 3 char in length
            if len(initials) > 3 or len(initials) < 3:
                print('Initials must be three characters.')
            else:
                # validate input
                if h.validate_input(initials):
                    # return initials
                    return initials

    def win(self):
        ''' Method to handle if user wins the game '''
        # create instance of Table() class
        l = Table()
        # add 100 points to score for user win
        self.set_score('+', 100)
        # print winner message
        print('You win!')
        # output final score to user
        print(f'Score: {self.get_score()}')
        
        #prompt user to add initials to leaderboard
        if self.add_leaderboard():
            # get initials as input and assign to var
            initials = self.set_initials()
            # add items to DynamoDB leaderboard
            l.add_items(initials, self.score)

    def lose(self):
        ''' Method to handle if user loses the game '''
        # subtract 50 points for loss
        self.set_score('-', 50)
        # output final score to user
        print(f'Score: {self.get_score()}')
        # game is over
        print('Game over!')

    def add_leaderboard(self):
        ''' method to handle if user wants to play the game again
        :return: True if yes, False if no'''
        while True:
            try:
                #prompt user to search for additional course titles
                c = input('Add name to leaderboard? y = Yes n = No: ').strip().lower()
            except ValueError:
                print('Invalid entry.')
                continue
            if c == 'y':
                return True
            elif c == 'n':
                return False
            else:
                print('Error: Please enter y or n.')

class Hangman():
    '''Class to handle gameplay'''
    def __init__(self, guess, random_word):
        ''' method to run when class is instantiated ''' 
        self.guess = guess
        self.random_word = random_word

    def set_guess(self, guess):
        ''' setter method for guess variable '''
        self.guess = guess

    def get_guess(self):
        ''' getter method for guess variable
        :return: self.guess '''
        return self.guess

    def set_word(self):
        ''' read file from S3 bucket and output random word to be guessed '''
        # instantialize S3Boto() class
        s3 = S3Boto()
        data = s3.client.get_object(Bucket= s3.bucket_name, Key= 'dictionary.txt')
        contents = data['Body'].read()
        words = list(map(str, contents.decode("utf-8").split()))

        # assign random string to variable
        self.random_word = random.choice(words)

    def get_word(self):
        ''' getter method for variable random_word
        :return: self.random_word '''
        return self.random_word

    def has_numbers(self, strng):
        ''' function to determine if input contains any numbers in string
        :return: True if numbers in string, else False '''
        return any(char.isdigit() for char in strng)

    def validate_input(self, strng):
        ''' function for validating user input for guess variable
        :return: True if valid, else False '''
        #define special characters
        special_characters = '!@#$%^&*()-+?_=,<>/"'
        #check if input is blank
        if strng == '':
            print('Input cannot be blank.')
        #check if input is numerical
        elif strng.isnumeric():
            print('Input cannot be numerical.')
        #check if input contains numbers
        elif self.has_numbers(strng):
            print('Input may not contain numbers.')
        #check if input contains any special characters
        elif any(c in special_characters for c in strng):
            print('Input cannot contain any special characters')
        else:
            #return true if input is valid
            return True
        #invalid input, return false
        return False

    def play_again(self):
        ''' method to handle if user wants to play the game again
        :return: True if yes, False if no'''
        while True:
            try:
                #prompt user to search for additional course titles
                c = input('Play again? y = Yes n = No (Return to Main Menu): ').strip().lower()
            except ValueError:
                print('Invalid entry.')
                continue
            if c == 'y':
                return True
            elif c == 'n':
                return False
            else:
                print('Error: Please enter y or n.')

    def new_game(self):
        ''' method to play new game of hangman '''
        # create instance of Menu class
        m = Menu(None)
        # instantiate Score class
        s = Score(0)
        # assign a random word from dictionary.txt to random_word variable
        self.set_word()
        random_word = self.get_word()
        # create a set of letters in random_word
        word_letters = set(random_word)
        # set of letters the user has previously guessed
        letters_guessed = set()
        # user begins with 6 lives
        lives = 6

        while lives > 0 and len(word_letters) > 0 and self.guess != random_word:
            #output lives left
            print(f'\nYou have {lives} lives left.')
            # output current score
            print(f'Score: {s.get_score()}')
            #output letters guessed
            print('Guessed letters:', ','.join(letters_guessed))

            # prints letter in random_word if previously guessed
            # else print -
            # (ie w - r d)
            word_list = [letter if letter in letters_guessed
                    else '-' for letter in random_word]

            print('\n', ' '.join(word_list))

            while True:
                try:
                    guess = input('\nGuess a letter or word: ').strip().lower()
                    # if input is valid
                    if self.validate_input(guess):
                        # assign input to self.guess
                        self.set_guess(guess)
                        break
                except ValueError:
                    print('Invalid input')
                    continue

            # if user guesses a single letter in the word
            if len(self.guess) == 1:
                # if letter has not been guessed previously
                if self.guess not in letters_guessed:
                    # append letter to letters_guessed set
                    letters_guessed.add(self.guess)
                    # earn 10 points for correct guess
                    s.set_score('+', 10)
                    # if letter guessed correctly
                    if self.guess in word_letters:
                        # remove - and replace with correct letter
                        word_letters.remove(self.guess)
                    else:
                        print('Incorrect guess.')
                        # remove 1 life for incorrect guess
                        lives = lives - 1
                        # lose 10 points for incorrect guess
                        s.set_score('-', 10)
                # if letter has already been guessed
                elif self.guess in letters_guessed:
                    print('\nYou have already guessed that letter. Please try again.')
            # if user guesses entire word
            if len(self.guess) > 1:
                # if word guess is incorrect
                if self.guess != random_word:
                    print('Incorrect guess.')
                    # remove 1 life for incorrect guess
                    lives = lives - 1
                    # lose 10 points for incorrect guess
                    s.set_score('-', 10)
                elif self.guess == random_word:
                    s.set_score('+', 50)

        # if user is out of lives
        if lives == 0:
            # print word
            print(f'Sorry, you lose. The word was: {random_word}')
            s.lose()
        else:
            # print word
            print(f'You have correctly guessed: {random_word}')
            s.win()

        # check if user wants to play again
        if self.play_again():
            # begin a new game
            self.new_game()
        else:
            # return to main menu
            m.menu()

    # menu option 3
    def display_rules(self):
        ''' Prints rules to user
        Obtained from https://en.wikipedia.org/wiki/Hangman_(game) '''

        print('\nHow to Play:\n')
        print('The word to guess is represented by a row of dashes representing each letter of the\
        word. Proper nouns, such as names, places, brands, or slang are forbidden.\n')
        print('If the guessing player suggests a letter which occurs in the word, the letter will\
        appear in all of its correct positions and 10 points are added to the score.')
        print('If the suggested letter does not occur in the word or the word is guessed\
        incorrectly, a life is removed and 10 points are deducted from the score.\n')
        print('The game ends once the word is guessed, or if all of the lives are gone —\
        signifying that all guesses have been used.\n')
        print('Winning by guessing each character individually earns the user 100 points.\n')
        print('The player guessing the word may, at any time, attempt to guess the whole word.\
        If the word is correct, 150 points are earned, the game is over and the guesser wins.\
        Otherwise, a life is removed.\n')

    # menu option 0
    def exit_handler(self):
        '''Prints message thanking user for playing and exits program'''
        print('\nThank you for playing!')
        print('Exiting program.')
        sys.exit()

class Menu():
    ''' Class to handle program Main Menu and selections ''' 
    def __init__(self, choice):
        ''' method to run when class is instantiated ''' 
        self.choice = choice

    def set_choice(self, choice):
        ''' setter method for choice variable '''
        self.choice = choice

    def menu_handler(self):
        ''' function to handle menu option choice '''
        # create instance of class Hangman
        h = Hangman('', '')
        t = Table()
        s = Score(0)
        if self.choice == 1:
            # play game
            h.new_game()
        elif self.choice == 2:
            # view scoreboard
            t.view_my_stats(s.set_initials())
        elif self.choice == 3:
            # display leadrboard
            t.view_leaderboard()
        elif self.choice == 4:
            # display game rules
            h.display_rules()
        elif self.choice == 0:
            # exit program
            h.exit_handler()
        else:
            # choice not acceptable menu option
            print('Invalid selection')

    def menu(self):
        ''' method to output menu options to user and accept user input '''
        # print welcome message
        print('\nWelcome to Hangman!')
        print("-------------------------------------------")

        # loop to get user input
        while True:
            # print menu options
            print('\nPlease select an option from the menu below: ')
            print('1. New Game')
            print('2. View My Scores')
            print('3. View Scoreboard')
            print('4. How to Play')
            print('0. Exit Game')

            try:
                # get user input
                choice = int(input("Menu option: "))
                # if user input is valid
                if len(str(choice)) > 1:
                    print('Menu selection cannot contain more than one digit')
                elif choice < 0:
                    print('Menu option cannot be a negative number')
                # input is valid
                else:
                    # assign input to self.choice
                    self.set_choice(choice)
                    self.menu_handler()
            except ValueError:
                # choice not acceptable menu option
                print('\nInvalid selection.')
                continue

# Call main function
if __name__ == '__main__':
    main()
