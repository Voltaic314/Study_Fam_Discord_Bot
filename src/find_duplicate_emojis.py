from image_processing import Image_Processing
from file_processing import File_Processing

def generate_hash_dict(emote_list: list[object]) -> dict[object, hash]:
    hash_list = {}

    for emote in emote_list:
        emote_filename = f'{emote.name} - {emote.id}.jpg'
        hash_list[emote] = Image_Processing.difference_image_hashing(emote_filename)
        # remove each image after we hash them to save on resources
        File_Processing.remove_file(emote_filename, False)

    return hash_list

def find_duplicates_through_hashes(emote_hash_dict: dict[object, hash]) -> dict[object: object]:
    '''
    This function will go through the list of emote objects and compare their hashes
    to find duplicates. For more information on this go here: https://pypi.org/project/ImageHash/
    It will then return a dictionary objects with the emote objects as keys and a list
    of all potential duplicates as the values for that emote.

    Parameters: list of emote objects, must contain their hash attribute.

    Returns: Dictionary object - keys are the original emote, list of other similar emote as values
    '''
    emotes_and_duplicates = {}

    emote_list = list(emote_hash_dict.keys())

    # Check each emote's hash
    for i in range(len(emote_list)):

        first_emote = emote_list[i]
        first_hash = emote_hash_dict[first_emote]

        # make sure the emote actually has a hash to compare the others to... lol
        if not first_hash:
            continue

        for j in range(i+1, len(emote_hash_dict.keys())):

            comparison_emote = emote_list[j]
            comparison_hash = emote_hash_dict[comparison_emote]

            hashes_are_identical = first_hash == comparison_hash
            # print(f'the hamming distance of these 2 emotes is: {hamming_distance}')
            if  hashes_are_identical:
                if first_emote in emotes_and_duplicates.keys():
                    emotes_and_duplicates[first_emote].append(comparison_emote)
                
                else:
                    emotes_and_duplicates[first_emote] = [comparison_emote]

    return emotes_and_duplicates
