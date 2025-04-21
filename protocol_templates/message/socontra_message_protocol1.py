# Simple message exchange protocol.

# Create a Socontra Client for the agent. This code is required at the head of each protocol module.
from socontra.socontra import Socontra, Message, Protocol
protocol = Protocol()
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

# agent_name = name of the agent receiving the message using this endpoint (not used in this template, refer next template).
# message_type = describes the message, and thus the current protocol state/stage.
# message_category = 'message' - General purpose message between agents. Useful for creating new protocols for any purpose.
#                    'subscription' - Broadcasting messages to agents (one-way comms).
#                    'service' - For acheiving a task via agent-to-agent transactions for services. 
#                                Includes automated commercial transactions on behalf of agents' human users or agents themselves.
# protocol = the common protocol that the agents are using to conduct the dialogue and exchange messages.
# recipient = recipient type, e.g. in transactions for services, recipients can be 'consumer' or 'supplier' of services. 
#               Default is 'recipient' for 'message' and 'subscription' message categories, as seen below.

@route('new_message', 'message', 'socontra', 'recipient') 
# -> response: NoComms or reply message (via socontra.reply_message() or socontra.reply_all_message())
def receive_new_message(agent_name: str, received_message: Message):    
    # Agent agent_name receives a message that initiates a new dialogue.

    print(f'\nNew message from {received_message.sender_name} which is {received_message.message} sent to {agent_name}\n')

    # To reply, just pass in the last messages received with 'message_responding_to='.
    # The socontra.reply_message() will send a message with type 'message_response', which will be received by endpoint below.
    socontra.reply_message(agent_name=agent_name, message_reply='Thanks for the greeting.', message_responding_to=received_message)


@route('message_response', 'message', 'socontra', 'recipient') 
# -> response: NoComms or reply message (via socontra.reply_message() or socontra.reply_all_message())
def receive_message_response(agent_name: str, received_message: Message, message_responding_to: Message):
    # Agent receives a response to the last message.

    # Check that the message is valid for the stage of the protocol. Can only accept messages if the previous message
    # is 'message_new' or 'message_response' (in this simple example, this will always be the case.)
    if not socontra.protocol_validation(agent_name, received_message, message_responding_to, valid_message_types=['new_message', 'message_response']):
        # Do nothing if incorrect message, ignore it. Sending agent will receive a protocol_error message.
        return

    print(f'\n{received_message.sender_name} sent a response to {agent_name} which is {received_message.message}\n')

    # Once the dialogue is completed, the agent can close the dialogue, again by passing in the last message received. 
    # If the agent that initiated the dialogue closes the dialogue, this will prevent any more messages being exchanged 
    # for this dialogue by all agents.
    socontra.close_dialogue(agent_name=agent_name, message_responding_to=received_message)


