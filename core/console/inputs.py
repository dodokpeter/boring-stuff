# user will be asked for selection from the string list
def select_from_list(input_message, list_of_choices, with_no_selection=False):
    list_len = len(list_of_choices)
    for i in range(list_len):
        print("Select " + str(i) + " for " + list_of_choices[i])
    index = -1
    while index < 0 or index > list_len - 1:
        index = int(input(input_message))
        if with_no_selection:
            break
    if index < 0 or index > list_len - 1:
        print("You selected nothing.")
        return None
    else:
        print("You selected: " + list_of_choices[index])
        return index


def ask_string_value(message, default):
    """Prompt for a string value. If `default` is None, the value is
    required: the "(default = ...)" suffix is omitted, and the prompt
    repeats until a non-empty answer is given."""
    if default is None:
        prompt = f"{message}: "
    else:
        prompt = f"{message} (default = {default}): "

    while True:
        user_input = input(prompt)
        if user_input:
            return user_input
        if default is not None:
            return default
