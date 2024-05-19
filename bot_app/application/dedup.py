from thefuzz import process, fuzz


def deduplication(
    raw_dict: dict,
    uniqueness_ratio: int = 70
    ):
     
    cleaned_dict_plus = dict()
    total_points = 0

    for key in raw_dict:
        cleaned_dict_plus[key] = []
        for i in range(len(raw_dict[key])-1):
            for j in range(i + 1, len(raw_dict[key])):
                if fuzz.token_set_ratio(raw_dict[key][i][0], raw_dict[key][j][0]) > 100 - uniqueness_ratio:
                    raw_dict[key][j][0] = '_'

    for key in raw_dict:
        for i in range(len(raw_dict[key])):
            if raw_dict[key][i][0] != '_':
                cleaned_dict_plus[key].append(raw_dict[key][i][1])
                total_points += 1

    return cleaned_dict_plus, total_points


def deduplication_plus(raw_dict, uniq):
     
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
