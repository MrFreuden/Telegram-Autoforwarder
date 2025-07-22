import asyncio
import os
from telethon.sync import TelegramClient
from telethon import errors
from dotenv import load_dotenv
load_dotenv()

class TelegramForwarder:
    def __init__(self, api_id, api_hash, phone_number):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.client = TelegramClient(f'session_{phone_number}', api_id, api_hash)

    async def connect_and_authorize(self):
        """ Подключение и авторизация аккаунта. """
        await self.client.connect()

        if not await self.client.is_user_authorized():
            print(f"Account {self.phone_number} is not authorized. Authorizing...")
            await self.client.send_code_request(self.phone_number)
            try:
                await self.client.sign_in(self.phone_number, input(f"Enter the code for {self.phone_number}: "))
            except errors.rpcerrorlist.SessionPasswordNeededError:
                password = input(f'Two-step verification is enabled for {self.phone_number}. Enter your password: ')
                await self.client.sign_in(password=password)

    async def forward_all_messages_to_channel(self, source_chat_id, destination_channel_id):
        """ Пересылка сообщений. """
        await self.connect_and_authorize()

        try:
            source_chat_entity = await self.client.get_input_entity(source_chat_id)
            print(f"Source chat entity obtained for {self.phone_number}: {source_chat_entity}")
        except Exception as e:
            print(f"Error getting input entity for source chat {source_chat_id} (Account {self.phone_number}): {e}")
            return

        try:
            last_message_id = (await self.client.get_messages(source_chat_entity, limit=1))[0].id
            print(f"Last message ID for {self.phone_number}: {last_message_id}")
        except Exception as e:
            print(f"Error getting last message ID from source chat {source_chat_id} (Account {self.phone_number}): {e}")
            return

        while True:
            print(f"Checking for messages and forwarding them (Account {self.phone_number})...")
            messages = await self.client.get_messages(source_chat_entity, min_id=last_message_id, limit=None)

            for message in reversed(messages):
                print(f"Forwarding message ID: {message.id} (Account {self.phone_number})")
                await self.client.send_message(destination_channel_id, message.text)
                print(f"Message forwarded (Account {self.phone_number})")
                last_message_id = max(last_message_id, message.id)

            await asyncio.sleep(5)  # Adjust the delay time as needed

def read_credentials(user_number):
    try:
        api_id = os.getenv(f"API_ID_USER_{user_number}")
        api_hash = os.getenv(f"API_HASH_USER_{user_number}")
        phone_number = os.getenv(f"PHONE_NUMBER_USER_{user_number}")
        source_chat_id = os.getenv(f"SOURCE_CHAT_ID_USER_{user_number}")
        destination_channel_id = os.getenv(f"DESTINATION_CHANNEL_ID_USER_{user_number}")

        missing_vars = []

        if not api_id:
            missing_vars.append("API_ID")
        if not api_hash:
            missing_vars.append("API_HASH")
        if not phone_number:
            missing_vars.append("PHONE_NUMBER")
        if not source_chat_id:
            missing_vars.append("SOURCE_CHAT_ID")
        if not destination_channel_id:
            missing_vars.append("DESTINATION_CHANNEL_ID")

        if missing_vars:
            raise ValueError(f"Missing the following environment variables for USER {user_number}: {', '.join(missing_vars)}")

        return api_id, api_hash, phone_number, int(source_chat_id), int(destination_channel_id)
    except Exception as e:
        print(f"An error occurred while reading credentials for user {user_number}: {e}")
        return None, None, None, None, None

async def main():
    api_id_1, api_hash_1, phone_number_1, source_chat_id_1, destination_channel_id_1 = read_credentials(1)
    api_id_2, api_hash_2, phone_number_2, source_chat_id_2, destination_channel_id_2 = read_credentials(2)

    if api_id_1 is None or api_hash_1 is None or phone_number_1 is None or source_chat_id_1 is None or destination_channel_id_1 is None:
        print("Exiting because credentials or chat IDs are missing for User 1.")
        return

    if api_id_2 is None or api_hash_2 is None or phone_number_2 is None or source_chat_id_2 is None or destination_channel_id_2 is None:
        print("Exiting because credentials or chat IDs are missing for User 2.")
        return    

    forwarder_1 = TelegramForwarder(api_id_1, api_hash_1, phone_number_1)
    forwarder_2 = TelegramForwarder(api_id_2, api_hash_2, phone_number_2)

    print(f"User 1 source chat ID: {source_chat_id_1}")
    print(f"User 2 source chat ID: {source_chat_id_2}")

    await asyncio.gather(
        forwarder_1.forward_all_messages_to_channel(source_chat_id_1, destination_channel_id_1),
        forwarder_2.forward_all_messages_to_channel(source_chat_id_2, destination_channel_id_2)
    )

if __name__ == "__main__":
    asyncio.run(main())
