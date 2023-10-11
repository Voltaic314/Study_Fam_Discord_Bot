'''
Author: Logan Maupin

This is just a collection of file related stuff for us to use
'''

import os

class File_Processing:

    def __init__(self, script_dir) -> None:
        self.cwd = os.getcwd()
        self.script_dir = script_dir

    @staticmethod
    def cwd_is_script_dir() -> bool:
        '''
        Checks to see if the current working directory is the script's directory. 

        Returns: True if the change was successful
        '''
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cwd_is_the_script_dir = os.getcwd() == script_dir
        return cwd_is_the_script_dir
    
    @staticmethod
    def return_file_name_with_current_directory(filename: str) -> str:

        # get the current file path we're operating in, so we don't have to hard code this in.
        # this also requires that the file be in the same working directory as this script.
        CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
        FILE_PATH_AND_NAME = os.path.join(CURRENT_DIRECTORY, filename)
        return FILE_PATH_AND_NAME
    
    @staticmethod
    def remove_file(filename: str, abs_path_used: bool) -> bool:
        '''
        This function removes the file that was saved after 
        hashing once this funcion is called.
        
        Returns: True if file did actually get removed
        '''

        # use absolute file paths for the sake of weird cwd related bugs
        if not abs_path_used:
            filename = os.path.abspath(filename)


        # first check to see if the file exists at all
        file_exists = os.path.exists(filename)

        if file_exists:
            os.remove(filename)
            # check to make sure that actually worked
            file_exists = os.path.exists(filename)

    @staticmethod
    def check_if_file_exists(filename):
        return os.path.exists(filename)
