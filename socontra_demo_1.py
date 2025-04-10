# Socontra demo 1
# Connect and register agents with the Socontra Network and send messages between them.
# How Socontra works is that agents use/pass in the last message that they receive as a token to 'respond' and send messages 
# associated with the next stage/step in the protocol. The last message received comprises the agent name that you are 
# transacting with, and references both the specific dialogue (transaction) and the (previous) protocol state/stage.
# Refer protocol_templates/message/socontra_message_protocol1.py to view the protocol and how its used to exchange messages
# in this demo.

from socontra.socontra import Socontra
from protocol_templates import  socontra_main_protocol
from protocol_templates.message import  socontra_message_protocol1
import config

socontra = Socontra()
socontra.add_protocol(socontra_main_protocol)
socontra.add_protocol(socontra_message_protocol1)


if __name__ == '__main__':

    # Enter your credentials in the config.py file.
    client_public_id = config.client_public_id
    client_security_token = config.client_security_token

    message_initiator = client_public_id + ':' + 'message_initiator'
    message_receiver = client_public_id + ':' + 'message_receiver'

    # Connect (and register if not already) the agent to the Socontra Network, to allow it to message, interact and transact with other agents.
    # Credentials for each new agent to connect back to the Socontra Network are stored in folder socontra/database.
    socontra.connect_socontra_agent(agent_data={
            'agent_name': message_initiator,
            'client_security_token': client_security_token,
        }, clear_backlog = True)
    
    socontra.connect_socontra_agent(agent_data={
            'agent_name': message_receiver,
            'client_security_token': client_security_token,
        }, clear_backlog = True)

    # The agents are not connected to other agents yet, and thus cannot communicate with each other. 
    # One way to connect is by joining the client_group, which allows agents that are registered 
    # with client_public_id to freely communicate with each other.
    socontra.join_client_group(agent_name=message_initiator)
    socontra.join_client_group(agent_name=message_receiver)

    # Now that the agents are 'connected', they can send messages to each other, i.e. commence a 'dialogue' or transaction.
    # We run the demo in protocol_templates/socontra_message_protocol to exchange messages between the agents.
    # Note: even though the agents reside within this same module, they could be on the opposites side of the globe and
    #       the Socontra Network will facilitate the interaction.

    # Message can be a string or json/dict.
    message="Hi there!"
    
    # Start a dialogue between two agents message_initiator and message_receiver, as configured in the protocol
    # protocol_templates/message/socontra_message_protocol1.py
    # socontra.new_message() will send a message of message_type = 'new_message' and message_category 'message'.
    # Default recipient_type='recipient'. 
    socontra.new_message(agent_name=message_initiator, distribution_list=message_receiver, message=message, protocol='socontra')

    

    