from fuzzywuzzy import fuzz

def fuzzy_cleaning(raw_dict, uniq):

    cleaned_dict = dict()
    total_points = 0

    for key in raw_dict:
        cleaned_dict[key] = []
        for i in range(len(raw_dict[key])-1):
            for j in range(i + 1, len(raw_dict[key])):
                if fuzz.token_set_ratio(raw_dict[key][i], raw_dict[key][j]) > 100 - uniq:
                    raw_dict[key][j] = '_'

    for key in raw_dict:
        for i in range(len(raw_dict[key])):
            if raw_dict[key][i] != '_':
                cleaned_dict[key].append(raw_dict[key][i])
                total_points += 1

    return cleaned_dict, total_points

def fuzzy_cleaning_plus(raw_dict, uniq):
     
    cleaned_dict_plus = dict()
    total_points = 0

    for key in raw_dict:
        cleaned_dict_plus[key] = []
        for i in range(len(raw_dict[key])-1):
            for j in range(i + 1, len(raw_dict[key])):
                if fuzz.token_set_ratio(raw_dict[key][i][0], raw_dict[key][j][0]) > 100 - uniq:
                    raw_dict[key][j][0] = '_'

    for key in raw_dict:
        for i in range(len(raw_dict[key])):
            if raw_dict[key][i][0] != '_':
                cleaned_dict_plus[key].append(raw_dict[key][i][1])
                total_points += 1

    return cleaned_dict_plus, total_points

def list_fuzzy_cleaning(raw_list, uniq):

    total_points = 0
    cleaned_list = []

    for i in range(len(raw_list)-1):
        for j in range(i + 1, len(raw_list)):
            if fuzz.token_set_ratio(raw_list[i], raw_list[j]) > 100 - uniq:
                raw_list[j] = '_'

    for i in range(len(raw_list)):
        if raw_list[i] != '_':
            cleaned_list.append(raw_list[i])
            total_points += 1
            
    return cleaned_list, total_points, len(raw_list), len(cleaned_list)