from consts import *
import json


def get_messages(uID, limit=10):
    client = Client(mail, passFb)

    userMessages = []
    before = None
    messagesCounter = 0
    messageId = 0

    while True:
        messages = client.fetchThreadMessages(thread_id=kolegiumId, limit=20, before=before)
        # Since the message come in reversed order, reverse them
        messagesCounter += 1
        if not messagesCounter % 100:
            print("Messages counter {}".format(messagesCounter))

        if not messages or messagesCounter > 3000:
            break
        before = messages[-1].timestamp
        #print(messages[-1].text, before)
        messages.reverse()
        # Prints the content of all the messages
        for message in messages:
            if message.author == uID:
                if message.text and not message.text.startswith("https"):
                    messageId += 1
                    jsonMessage = {"id": messageId, "message": message.text}
                    userMessages.append(jsonMessage)


    with open('messages_uid_{}.json'.format(uID), 'a', encoding='utf8') as file:
        json.dump(userMessages, file, ensure_ascii=False)

    try:
        client.logout()
    except:
        pass


if __name__ == "__main__":
    get_messages(ksiadzId)
