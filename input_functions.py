def handle_keys(user_input):
    key_char = user_input.char

    if key_char == 'w':
        return {'move': (0, -1)}
    elif key_char == 's':
        return {'move': (0, 1)}
    elif key_char == 'a':
        return {'move': (-1, 0)}
    elif key_char == 'd':
        return {'move': (1, 0)}
    elif key_char == 'q':
        return {'move': (-1, -1)}
    elif key_char == 'e':
        return {'move': (1, -1)}
    elif key_char == 'z':
        return {'move': (-1, 1)}
    elif key_char == 'x':
        return {'move': (1, 1)}

    if user_input.key == 'ESCAPE':
        return {'exit_game': True}

    return {}
