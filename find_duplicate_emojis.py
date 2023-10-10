from emote import Emote


def get_static_emotes(emote_tuple: tuple) -> list[object]:

    # iterate through the emotes and only create a list of emote objects from static image emotes
    list_of_emotes = []
    for emote in emote_tuple:
        if not emote.animated:

            list_of_emotes.append(Emote(emote))

    return list_of_emotes


def get_hamming_distance(hex_str1: str, hex_str2: str) -> int:
    # Make sure the input strings have the same length
    if len(hex_str1) != len(hex_str2):
        raise ValueError("Input strings must have the same length")

    # Convert hexadecimal strings to integers
    int1 = int(hex_str1, 16)
    int2 = int(hex_str2, 16)

    # Calculate the XOR of the two integers
    xor_result = int1 ^ int2

    # Count the number of set bits (1s) in the XOR result
    hamming_dist = bin(xor_result).count('1')

    return hamming_dist



def find_duplicates_through_hashes(list_of_emotes: list[object]) -> dict[object: object]:
    '''
    This function will go through the list of emote objects and compare their hashes
    to find duplicates. For more information on this go here: https://pypi.org/project/ImageHash/
    It will then return a dictionary objects with the emote objects as keys and a list
    of all potential duplicates as the values for that emote.

    Parameters: list of emote objects, must contain their hash attribute.

    Returns: Dictionary object - keys are the original emote, list of other similar emote as values
    '''
    dictionary_of_ids_and_duplicate_ids = {}

    # If the hamming distance is past 8, then we can conclude the emotes are duplicate images
    ideal_hamming_distance = 8

    # Check each emote's hash
    for emote in list_of_emotes:
        dictionary_of_ids_and_duplicate_ids[emote] = []
        for second_emote in list_of_emotes:
            
            # FIXME: This is a big O(n^2) algorithm, this should be further improved for efficiency
            # Luckily you can only have up to 50 static emotes so this is just 2500 comparisons at max.
            if emote != second_emote:
                hash_string_hamming_distance = get_hamming_distance(emote.hash_string, second_emote.hash_string)
                if  hash_string_hamming_distance >= ideal_hamming_distance:
                    dictionary_of_ids_and_duplicate_ids[emote].append(second_emote)

    return dictionary_of_ids_and_duplicate_ids
