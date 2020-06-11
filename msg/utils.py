def agency_slug(agency_name):
    return '#' + ''.join(agency_name.split()) + '#'


def user_input(prompt):
    try:
        return raw_input(prompt)
    except NameError:
        return input(prompt)
