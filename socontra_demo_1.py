# Socontra demo 1
# Connect and register agents with the Socontra Network and send messages between them.
# Socontra use/pass in the last message that agents receive as a token to 'respond' and send the next messages 
# in the protocol. The last message received comprises: the agent (receiver name) to respond to; the ‘dialogue’ 
# that the message relates to (i.e. the specific interaction or transaction); the type (category) of message 
# and protocol used for the interaction; and the previous step or stage in the protocol that message is in response 
# to, allowing the receiving agent to validate the message and understand the meaning and expected contents of 
# the message within the context of the protocol.

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
    # Credentials for each new agent to connect back to the Socontra Network after registration are stored in folder socontra/database.
    # Agents generate their own password to connect to the Socontra Network once registered. If the password is 'lost', e.g. the agent is 
    # moved to a new device/server, then the human_password can be used to reconnect the agent by allowing it to reset its password.
    socontra.connect_socontra_agent(agent_data={
            'agent_name': message_initiator,
            'client_security_token': client_security_token,
            'human_password': 'human_password_for_agent_here',
        }, clear_backlog = True)
    
    socontra.connect_socontra_agent(agent_data={
            'agent_name': message_receiver,
            'client_security_token': client_security_token,
            'human_password': 'human_password_for_agent_here',
        }, clear_backlog = True)

    # The agents are not connected to other agents yet, and thus cannot communicate with each other. 
    # One way to connect is by joining the client_group, which allows agents that are registered 
    # with client_public_id to freely communicate with each other.
    socontra.join_client_group(agent_name=message_initiator)
    socontra.join_client_group(agent_name=message_receiver)

    # Now that the agents are 'connected', they can send messages to each other, i.e. commence a 'dialogue' or transaction.
    # Even though the agents reside within this same module, they could be on the opposites side of the globe and
    #       the Socontra Network will facilitate the interaction.

    # Message can be a string or json/dict.
    message="Hi there!"
    
    # Start a dialogue between two agents message_initiator and message_receiver, as configured in the protocol
    # protocol_templates/message/socontra_message_protocol1.py
    # socontra.new_message() will send a message of message_type = 'new_message' and message_category 'message'.
    # Default recipient_type='recipient'. 
    socontra.new_message(agent_name=message_initiator, distribution_list=message_receiver, message=message, protocol='socontra')

    

    