from Bot import Bot
import fbchat
import json
import consts
import random
import os
import asyncio

if os.name == "nt":
    asyncio.DefaultEventLoopPolicy = asyncio.WindowsSelectorEventLoopPolicy


class TextBot(Bot):
    def __init__(self, username, passwd, botted_id, group_id):
        super().__init__(username, passwd)
        self.botted_id = botted_id
        self.group_id = group_id
        self.database_path = "messages_uid_{}.json".format(self.botted_id)
        self.message_database = self.get_message_database(self.database_path)

    def send_text_to_user(self, user_id, message):
        user = fbchat.User(session=self.session, id=user_id)
        user.send_text(message)
        print("Message {} has been sent to user: {}".format(message, user_id))

    async def send_text_to_group(self, group_id, message, session):
        group = fbchat.Group(session=session, id=group_id)
        await group.send_text(message)
        print("Message {} has been sent to user: {}".format(message, group_id))

    def send_text_to_yourself(self, message):
        self.send_text_to_user(self.uId, message)

    def get_messages_from_user_in_group(self, user_id, group_id):
        messageId = 0
        userMessages = []
        group = fbchat.Group(session=self.session, id=group_id)
        for message in group.fetch_messages(limit=20000):
            if message.author == user_id:
                if message.text and not message.text.startswith("https"):
                    messageId += 1
                    jsonMessage = {"id": messageId, "message": message.text}
                    userMessages.append(jsonMessage)

        self.save_database()

        return userMessages

    def read_message_database(self, db_path):
        try:
            with open(db_path, 'r', encoding='utf8') as file:
                database = json.load(file)
                return database
        except FileNotFoundError:
            print("File not found {}".format(db_path))
            return  # No database file

    def get_message_database(self, db_path):
        database = self.read_message_database(db_path)
        if not database:
            database = self.get_messages_from_user_in_group(self.botted_id, self.group_id)
        return database

    async def send_random_message_from_database(self, session):
        rand_id = random.randrange(len(self.message_database))
        message = self.message_database[rand_id]["message"]
        await self.send_text_to_group(self.group_id, message, session)

    async def on_message(self, event, session):
        # No need to try if it's a user chat
        if not isinstance(event.thread, fbchat.Group):
            return

        if event.message.text == "!xiendzobot":
            await self.send_random_message_from_database(session)
            return

        if event.message.text and "!add" in event.message.text:
            message_to_add = event.message.text.split("!add")[1].strip()
            await self.add_to_database(message_to_add, session)
            return

        if event.message.text and "!del" in event.message.text:
            message_to_del = event.message.text.split("!del")[1].strip()
            await self.del_from_database(message_to_del, session)
            return

    async def listen_to_events(self, listener, session):
        async for event in listener.listen():
            if isinstance(event, fbchat.MessageEvent):
                await self.on_message(event, session)

    def save_database(self):
        with open('messages_uid_{}.json'.format(self.botted_id), 'w', encoding='utf8') as file:
            json.dump(self.message_database, file, ensure_ascii=False)

    async def add_to_database(self, message, session):
        if self.find_record(message):
            await self.send_text_to_group(self.group_id, "Message {} already exists in db".format(message), session)
            return

        new_id = len(self.message_database)
        self.message_database.append({"id": new_id, "message": message})
        self.save_database()
        await self.send_text_to_group(self.group_id, "Message added to db: {}".format(message), session)

    def find_record(self, message):
        try:
            found_record = next(item for item in self.message_database if item["message"].lower() == message.lower())
        except StopIteration:
            found_record = None
        return found_record

    async def del_from_database(self, message, session):
        found_record = self.find_record(message)

        if not found_record:
            await self.send_text_to_group(self.group_id, "Message {} not found in db".format(message), session)
            return

        found_index = self.message_database.index(found_record)
        self.message_database.remove(found_record)
        for elem in self.message_database[found_index:]:
            elem["id"] -= 1
        self.save_database()
        await self.send_text_to_group(self.group_id, "Message deleted from db: {}".format(message), session)

    async def run(self, listener, session):
        await self.listen_to_events(listener, session)


async def main():
    ksiendzobot = TextBot(consts.mail, consts.passFb, consts.ksiadzId, consts.kolegiumId)
    session = await ksiendzobot.get_session()
    client = fbchat.Client(session=session)
    listener = fbchat.Listener(session=session, chat_on=False, foreground=False)

    listen_task = asyncio.create_task(ksiendzobot.run(listener, session))

    client.sequence_id_callback = listener.set_sequence_id

    # Call the fetch_threads API once to get the latest sequence ID
    await client.fetch_threads(limit=1).__anext__()

    # Let the listener run, otherwise the script will stop
    await listen_task


if __name__ == "__main__":
    asyncio.run(main())
