import textwrap


# TODO: Doc
class Message:
    def __init__(self, text, colour=(255, 255, 255)):
        self.text = text
        self.colour = colour


# TODO: Doc
class MessageLog:
    def __init__(self, x, y, width, height):
        self.messages = []
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.add_message(Message("Where am I? I have to get out of here..."))

    def add_message(self, message):
        # split the messages across lines using text wrap
        new_message_lines = textwrap.wrap(message.text, self.width)

        for line in new_message_lines:
            # if the buffer is full, remove the first message to make room for the new one
            if len(self.messages) == self.height:
                del self.messages[0]

            # add the new message line as Message object
            self.messages.append(Message(line, message.colour))
