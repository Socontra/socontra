# Socontra demo 3
# Use socontra.agent_return() to return message reveiced to a central orchestrator agent or function to simplify coding.
# Same as demo 2 but using a central orchestrator.
# Refer to protocol protocol_templates/message/socontra_message_protocol3.py

from socontra.socontra import Socontra
from protocol_templates import  socontra_main_protocol
from protocol_templates.message import  socontra_message_protocol3
import config

socontra = Socontra()
socontra.add_protocol(socontra_main_protocol)
socontra.add_protocol(socontra_message_protocol3)

import random, time


# ----- CENTRAL ORCHESTRATOR FUNCTION THAT MANAGES THE DIALOGUE (GAME) ----- #

def game_orchestrator(agent_name, distribution_list, random_agent1, random_agent2, message):

    # Generate a random number to be used in the guessing game.
    random_number = random.randint(1, 10)

    # Start a dialogue with the two helper agents to play the game.
    socontra.new_message(agent_name=agent_name, distribution_list=distribution_list, message=message, 
                         message_type='guess_my_number', protocol='my_new_protocol', recipient_type='helper')

    while True:
        time.sleep(1)

        # Wait for messages from helper agents with a response/guess to what the random number might be.
        # socontra.my_guess_response is the endpoint's function name specified in the protocol (socontra_message_protocol3.py).
        guess_returned = socontra.expect(agent_name, socontra.my_guess_response, timeout=10)

        guessed_number = guess_returned['guessed_number']
        sender_agent = guess_returned['sender']

        print(f'\nThe number I have is {random_number} and the number guessed by agent {sender_agent} is {guessed_number}\n')

        if guessed_number == random_number:
            message=f'{sender_agent} has guessed the number!! Congrats!\n'
            # Send the protocol message 'game_complete' to all helper agents to let them know that the game has ended.
            socontra.reply_all_message(agent_name=agent_name, message_reply=message, message_responding_to=guess_returned['received_message'],
                                    message_type='game_complete', recipient_type='helper')
            # Dialogue is complete. Close the dialogue.
            socontra.close_dialogue(agent_name=agent_name, message_responding_to=guess_returned['received_message'])
            return
        else:
            if sender_agent == random_agent1:
                next_agent_to_guess = random_agent2
            else:
                next_agent_to_guess = random_agent1
            message = {'message': "Incorrect. Try again.",
                        'next_agent_to_guess': next_agent_to_guess}
            # Reply to all helper agents to let them know the game is still ongoing, and for the next in line to try guessing again.
            socontra.reply_all_message(agent_name=agent_name, message_reply=message, message_responding_to=guess_returned['received_message'],
                                    message_type='guess_my_number', recipient_type='helper')


if __name__ == '__main__':

    # Enter your credentials in the config.py file.
    client_public_id = config.client_public_id
    client_security_token = config.client_security_token

    message_initiator = client_public_id + ':' + 'message_initiator'
    random_agent1 = client_public_id + ':' + 'helper_agent1'
    random_agent2 = client_public_id + ':' + 'helper_agent2'

    # Connect (and register if not already) the agent to the Socontra Network, to allow it to message, interact and transact with other agents. 
    socontra.connect_socontra_agent(agent_data={
            'agent_name': message_initiator,
            'client_security_token': client_security_token,
            'human_password': 'human_password_for_agent_here',
        }, clear_backlog = True)
    
    socontra.connect_socontra_agent(agent_data={
            'agent_name': random_agent1,
            'client_security_token': client_security_token,
            'human_password': 'human_password_for_agent_here',
        }, clear_backlog = True)
    
    socontra.connect_socontra_agent(agent_data={
            'agent_name': random_agent2,
            'client_security_token': client_security_token,
            'human_password': 'human_password_for_agent_here',
        }, clear_backlog = True)

    # Join the client_group so that agents are 'connected' and can interact.
    socontra.join_client_group(agent_name=message_initiator)
    socontra.join_client_group(agent_name=random_agent1)
    socontra.join_client_group(agent_name=random_agent2)

    # Can communicate with multiple agents by creating distribution list. Will use 'direct' communication list. 
    # Will explore agent 'groups' later.
    distribution_list = {
            # List names of agent names for direct agent-to-agent communication. The sender agent must be 'connected to' recipient agents. 
            'direct' : [random_agent1, random_agent2],
        }

    # Message can be a string or json/dict.
    message={'message': "Can you generate a random number from 1 to 10 to guess the number I'm thinking of?",
             'next_agent_to_guess': random_agent1}
    # socontra_message_protocol3.start_game(message_initiator, distribution_list, message=message)
    game_orchestrator(message_initiator, distribution_list, random_agent1, random_agent2, message=message)

    

    