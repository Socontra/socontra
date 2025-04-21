# See socontra_demo_3.py

import random
import config

# Create a Socontra Client for the agent. This code is required at the head of each protocol module.
# Note arguments in Protocol() to avoid error messages when receive messages with no endpoints.
from socontra.socontra import Socontra, Message, Protocol
protocol = Protocol(protocol_name='my_new_protocol', ignore_missing_endpoints=True)
socontra: Socontra = protocol.socontra
def route(*args):
    def inner_decorator(f):
        protocol.route_map[(args)] = f
        return f
    return inner_decorator


# ----- PROTOCOL ENDPOINTS ----- #
# Format is:  
# @route(message_type, message_category, protocol, recipient)
# ---OR-----
# @route(agent_name, message_type, message_category, protocol, recipient)

# agent_name = name of the agent receiving the message using this endpoint.
# message_type = describes the message, and thus the current protocol state/stage.
# message_category = 'message' - General purpose message between agents. Useful for creating new protocols for any purpose.
#                    'subscription' - Broadcasting messages to agents (one-way comms).
#                    'service' - For acheiving a task via agent-to-agent transactions for services. 
#                                Includes automated commercial transactions on behalf of agents' human users or agents themselves.
# protocol = the common protocol that the agents are using to conduct the dialogue and exchange messages.
# recipient = recipient type, e.g. in transactions for services, recipients can be 'consumer' or 'supplier' of services. 
#               Default is 'recipient' for 'message' and 'subscription' message categories, as seen below.

message_initiator = config.client_public_id + ':' + 'message_initiator'

# ------ Endpoint for the orchestrator (dialogue initiator) agent '<client_public_id>:message_initiator'.
#           Use the agent name as the first argument in the endpoint.

@route(message_initiator, 'my_guess_response', 'message', 'my_new_protocol', 'orchestrator')
# -> response: NoComms or reply message (via socontra.reply_message() or socontra.reply_all_message())
def my_guess_response(agent_name: str, received_message: Message, message_responding_to: Message):
    # Orchestrator agent receives messages with guesses of numbers from 1 to 10 until an agent guesses it correctly.

    # Use socontra.agent_return() to return the message (or any return value) to the agent that is awaiting/expecting the message.
    # The second argument is the name of this function, and remaining arguments will be converted to a dict.
    # Here we demonstrate returning multiple values, although only needed to return received_message which has all info.
    socontra.agent_return(agent_name, my_guess_response, message=received_message.message['message'], 
                          guessed_number=received_message.message['random_number'], sender=received_message.sender_name,
                          received_message=received_message)



@route(message_initiator, 'my_guess_response', 'message', 'my_new_protocol', 'add_random_numbers')
# -> response: NoComms or reply message (via socontra.reply_message() or socontra.reply_all_message())
def my_guess_response(agent_name: str, received_message: Message, message_responding_to: Message):
    # Examples of using different roles for similar messages. THis endpoint not used in demo.

    # The role above is 'orchestrator', with a purpose of finding an agent that can guess a number correctly.
    # Here, the role is 'add_random_numbers' for the same message_type = 'my_guess_response' with a different 
    # purpose of adding the random number received (not used in this demo). Later, when dealing with service type
    # messages, recipient_type  is helpful distinguishing between consumers (acquirers/buyers of services) and 
    # suppliers (providers/sellers of services, or products).

    # Add the received random number to 5.
    result = 5 + received_message.message['random_number']
    

# ------ Endpoints specific to agent '<client_public_id>:helper_agent1'. Use the agent name as the first argument in the endpoint.

global past_guesses
past_guesses = []
helper_agent1 = config.client_public_id + ':' + 'helper_agent1'

@route(helper_agent1, 'guess_my_number', 'message', 'my_new_protocol', 'helper')
# -> response: NoComms or reply message (via socontra.reply_message() or socontra.reply_all_message())
def guess_my_number_agent1(agent_name: str, received_message: Message, message_responding_to: Message=None):    
    # helper_agent1 receives a message that initiates a new dialogue to commence the game.
    msg = received_message.message['message']
    print(f'\nNew message from {received_message.sender_name} which is {msg} sent to {agent_name}\n')

    # If it is my turn to guess a number...
    if received_message.message['next_agent_to_guess'] == agent_name:
        # I am smart, I can remember past guesses.
        global past_guesses
        while True:
            my_random_number = random.randint(1, 10)
            if my_random_number not in past_guesses:
                break
        past_guesses.append(my_random_number)

        # This agent starts the game.
        message = { 'message' : f'\n{agent_name}: The random number I guessed is {str(my_random_number)}/n',
                    'random_number' : my_random_number}
        
        # Reply to the orchestrator with the guess.
        socontra.reply_message(agent_name, message_reply=message, message_responding_to=received_message,
                               message_type='my_guess_response', recipient_type='orchestrator')


@route(helper_agent1, 'game_complete', 'message', 'my_new_protocol', 'helper') 
# -> response: NoComms - end of protocol/dialogue
def game_complete_agent1(agent_name: str, received_message: Message, message_responding_to: Message):
    # helper_agent1 receives a message to end the game (and thus end the protocol).

    # Check that the message is valid for the stage of the protocol. Can only accept messages if the previous message
    # is 'my_guess_response'.
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['my_guess_response']):
        # Do nothing if incorrect message, ignore it. Sending agent will receive a protocol_error message.
        return

    print(f'\n{received_message.sender_name} sent a game completion message to {agent_name}  which is: {received_message.message}\n')

    # Close the dialogue.
    socontra.close_dialogue(agent_name, received_message)


# ------ General endpoints for all remaining agents, which in this case is just: '<client_public_id>:helper_agent2'

@route('guess_my_number', 'message', 'my_new_protocol', 'helper') 
# -> response: NoComms or reply message (via socontra.reply_message() or socontra.reply_all_message())
def guess_my_number(agent_name: str, received_message: Message, message_responding_to: Message=None):    
    # Agent agent_name receives a message that initiates a new dialogue to commence the game.

    msg = received_message.message['message']
    print(f'\nNew message from {received_message.sender_name} which is {msg} sent to {agent_name}\n')
    # If it is my turn to guess a number...
    if received_message.message['next_agent_to_guess'] == agent_name:
        # I can't remember past guesses.
        my_random_number = random.randint(1, 10)
        message = { 'message' : f'\n{agent_name}: The random number I guessed is {str(my_random_number)}/n',
                    'random_number' : my_random_number}
        
        # Reply to the orchestrator with the guess.
        socontra.reply_message(agent_name, message_reply=message, message_responding_to=received_message,
                               message_type='my_guess_response', recipient_type='orchestrator')


@route('game_complete', 'message', 'my_new_protocol', 'helper') 
# -> response: NoComms - end of protocol/dialogue
def game_complete(agent_name: str, received_message: Message, message_responding_to: Message):
    # helper_agent1 receives a message to end the game (and thus end the protocol).

    # Check that the message is valid for the stage of the protocol. Can only accept messages if the previous message
    # is 'my_guess_response'.
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['my_guess_response']):
        # Do nothing if incorrect message, ignore it. Sending agent will receive a protocol_error message.
        return

    print(f'\n{received_message.sender_name} sent a game completion message to {agent_name}  which is: {received_message.message}\n')

    # Close the dialogue.
    socontra.close_dialogue(agent_name, received_message)

