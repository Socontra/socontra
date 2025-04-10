# This module is part of the Socontra Client which facilitates the communication and interface between the agent and the Socontra Network.
# Agents use this Socontra Client to connect to the Socontra network and find, connect, interact and transact to other agents.

import threading
import json
import requests
import time

from socontra.agent_database import AgentDatabase
from sseclient import SSEClient
import config 

# Variable to store the Socontra Interface object reference so that we can redirect messages to the Socontra object.
global socontra_interface_object_ref, agent_db_object_ref
socontra_interface_object_ref = {}
agent_db_object_ref = {}


# Create a class for message responses for HTTP message requests and agent messages. This way can use response.success rather than
# reponse['success'], which I think is cleaner and easier to use.
class MessageHTTPResponse():
    def __init__(self, response):
        self.success = response['success']
        self.message = response['message']
        self.http_response=response['http_response']
        self.status_code = response['status_code']

        self.contents = {
            'success': self.success,
            'message' : self.message,
            'http_response' : self.http_response,
            'status_code' : self.status_code
        }

# Create a class for message to send - make it easier for the developer to access message components.
class Message():
    def __init__(self, sender_name, receiver_name, distribution_list, message, message_type, recipient_type, protocol, dialogue_id, 
                    task = None, proposal = None, offer = None, order = None, proposal_timeout = None, invite_offer_timeout = None, offer_timeout = None,
                    payment_required = False, human_authorization_required = False, message_id = None):
        self.sender_name = sender_name
        self.receiver_name = receiver_name
        self.distribution_list = distribution_list
        self.recipient_type = recipient_type
        self.message = message
        self.message_type= message_type
        self.protocol = protocol
        self.dialogue_id = dialogue_id
        self.message_id = message_id
        self.task = task
        self.proposal_timeout = proposal_timeout
        self.proposal = proposal
        self.invite_offer_timeout = invite_offer_timeout
        self.offer = offer
        self.offer_timeout = offer_timeout
        self.payment_required = payment_required
        self.human_authorization_required = human_authorization_required
        self.order = order

        self.contents = {
            'sender_name': self.sender_name,
            'receiver_name': self.receiver_name,
            'distribution_list': self.distribution_list,
            'recipient_type': self.recipient_type,
            'message': self.message,
            'message_type': self.message_type,
            'protocol': self.protocol,
            'dialogue_id': self.dialogue_id,
            'message_id': self.message_id,
        } if (task is None and proposal is None and offer is None) else {
            'sender_name': self.sender_name,
            'receiver_name': self.receiver_name,
            'distribution_list': self.distribution_list,
            'recipient_type': self.recipient_type,
            'message': self.message,
            'message_type': self.message_type,
            'protocol': self.protocol,
            'dialogue_id': self.dialogue_id,
            'message_id' : self.message_id,
            'task': self.task,
            'proposal_timeout': self.proposal_timeout,
            'proposal': self.proposal,
            'invite_offer_timeout': self.invite_offer_timeout,
            'offer': self.offer,
            'offer_timeout': self.offer_timeout,
            'payment_required': self.payment_required,
            'human_authorization_required': self.human_authorization_required,
            'order': self.order,
        }


def prepare_agent_api(agent_name, soc_intfce_object_ref):
    # Prepare references to agent objects so we can route massages back to the relevant agent.
    global socontra_interface_object_ref
    socontra_interface_object_ref[agent_name] = soc_intfce_object_ref
    
    # Using just an object as our database, which will save the relevant info to files.
    # On the agent side, data is not extensive or accessed often.
    global agent_db_object_ref
    agent_db_object_ref[agent_name] = AgentDatabase()


def agent_receive_messages(agent_name, clear_backlog, agent_connected):
    url = config.socontra_network_url_sse
    print('Starting agent connection to Socontra Network', agent_name)

    while True:
        try:
            # Get an access token from the Socontra Network.
            access_token = get_access_token(agent_name)

            response = requests.get(url, json={'agent_name': agent_name, 'clear_backlog': clear_backlog}, stream=True, headers=access_token)

            client = SSEClient(response)

            agent_connected['agent_connected'] = True

            for event in client.events():
                # print(agent_name, 'received message', event.data)

                message = json.loads(event.data)
                protocol_message_component = message['message']

                agent_name = protocol_message_component['receiver_name']

                global socontra_interface_object_ref

                message_type_override = message['message_type_override']

                message_category = message['message_category']

                expect_multiple_thread = threading.Thread(target=socontra_interface_object_ref[agent_name].route_message, 
                                                        args=(agent_name, protocol_message_component, message_category, message_type_override))

                expect_multiple_thread.start()
        except:
            print('Trouble connecting to the Socontra Network. Will try again soon.')
            time.sleep(2)


# Agent registration functions.

def agent_already_registered(agent_name, agent_data):
    # Will check if the agent has already been registered by checking if the agent exists and is stored in the local Socontra Interface 
    # database. If so, then the agent was just shut down and started again.
    if agent_db(agent_name).recreate_agent_if_exists(agent_data):

        # Create an artificial response object to send back - dont need to communicate with the Socontra Network.
        response_to_return = MessageHTTPResponse({
            'success': True,
            'message': None,
            'http_response': 'Agent already registered and created locally',
            'status_code': 200
        })
        return response_to_return
    else:
        return False


def register_new_agent(agent_name, agent_data, agent_owner_data, agent_owner_transaction_config):
    # Will register the new agent with the Socontra Network.
    # Requires a single json file with the merge of all agent_data + agent_owner_data + agent_owner_transaction_config.

    # Agent data is mandatory. SO can start with a copy of it.
    json = agent_data.copy()

    if agent_owner_data:        # Optional
        for k, v in agent_owner_data.items():
            json[k] = v
    else:
        # Even if not specified, should really provide the values as None, as already stored in this agent as default.
        for k, v in agent_db(agent_name).agent_owner_data.items():
            json[k] = v
    
    if agent_owner_transaction_config:      # Optional
        for k, v in agent_owner_transaction_config.items():
            json[k] = v
    else:
         # Even if not specified, should really provide the values as None, as already stored in this agent as default.
        for k, v in agent_db(agent_name).agent_owner_transaction_config.items():
            json[k] = v

    # lastly, need to create a password specific for this agent.
    agent_password = agent_db(agent_name).create_new_agent_password(64)
    json['agent_password'] = agent_password

    # TODO - create a human password, in case agent password is lost or for human authorization (see function recreate_agent_same_credentials()).

    # Now send a registration request.
    response = send_auth_message(agent_name, json, '/agent_auth/', 'POST')

    if response.success:
        # We need to be save this agent's unique password that allows it to access the Socontra network.
        agent_data['agent_password'] = agent_password

        # Save the agent registered data in our local database, which at the moment is just files on the local machine.
        agent_db(agent_name).store_register_agent_details(agent_data, agent_owner_data, agent_owner_transaction_config)

        response.message = 'Agent registered ok'

    # Else, if error registering (response.success == False). Must be agent with same name or client_security_token incorrect,
    # or this agent is registered but the agent's password is not available/stored on the new device. Address in next function.
    return response


def recreate_agent_same_credentials(agent_name, client_security_token):
    # This function will check if this agent already exists on the Socontra Network, 
    # ONLY IF the agent_name and client_security_token are exactly the same.
    # TODO - need 2FA. Either human password or email verification. To implement.

    new_agent_password = agent_db(agent_name).create_new_agent_password(64)

    json_message = {
        "agent_name": agent_name,
        "client_security_token": client_security_token,
        "new_password": new_agent_password
    }

    # Send the forgot password message. If the agent_name and client_security_token match, then (at the moment) the Socontra Network 
    # will provide the data to recreate the agent and allow it to access the network. Else, returns false.
    response = send_auth_message(agent_name, json_message, '/agent_auth/forgot_password', 'PUT')

    if response.success:
        # Now that the password is reset, lets get all the details about us from the agent.
        agent_db(agent_name).update_agent_password(new_agent_password, False)
        get_access_token(agent_name)        # We know we will need an access token for the request.
        response = send_auth_message(agent_name, {}, '/agent_admin/my_agent_data', 'GET')

        # Save the client_security_token encrypted.
        agent_db(agent_name).update_client_security_token(client_security_token, False)

        # response_content should have all the agent data in it. So now can store it and save the info to file.
        agent_db(agent_name).update_agent_data(response.message)

        response.http_response = 'Agent already registered and recreated via Soncontra Network.'
    else:
        print('Error connecting to the Socontra Network.', response.status_code, response.http_response)

    return response


#  ---------------- Send message to the Socontra Network.


def send_auth_message(agent_name, json_message, path, api_crud_type):
    # Send a message to the Socontra Network.
    # We have configured it for http://127.0.0.1:8000.
    # First get the agent's URL and port number.
    socontra_network_url = agent_db(agent_name).socontra_network_url
    socontra_network_path = path
    socontra_network_api_port = agent_db(agent_name).socontra_network_port

    # if path != '/agent_auth/agent_token':
        # print('sending message', json_message)

    if endpoints_that_dont_need_access_tokens(path):
        access_token = None
    else:
        access_token = agent_db(agent_name).get_socontra_access_token()

    # Send the auth request.
    res = _send_auth_request(api_crud_type, socontra_network_url, socontra_network_api_port, socontra_network_path, json_message, access_token)
    
    # If the response is 401 unauthorized, then we need a new access token.
    # Get the access token and try one more time to see if this resolves the issue.
    if res.status_code == 401 and not path == '/agent_auth/agent_token' and not endpoints_that_dont_need_access_tokens(path):

        # Get a new access token.
        access_token = get_access_token(agent_name)

        # Resend the auth message.
        if access_token:
            res = _send_auth_request(api_crud_type, socontra_network_url, socontra_network_api_port, socontra_network_path, json_message, access_token)
        else:
            return False
    
    # If there is an error on the Socontra Network, print a message and return from this function.
    if res.status_code == 500:
        print('There was an error on the Socontra Network. Action could not be completed.')
        return MessageHTTPResponse({
                'success': False,
                'http_response': res.content,
                'message': 'There was an error on the Socontra Network. Action could not be completed.',
                'status_code': res.status_code
            })
    
    try:
        response_dict = json.loads(res.content)
    except:
        response_dict = json.loads(res.detail)
    
    if 200 <= res.status_code <= 299:
       success = True
    else:
       success = False

     # Create a response object to send back.
    response_to_return = MessageHTTPResponse({
        'success': success,
        'http_response': response_dict if 'http_response' not in response_dict else response_dict['http_response'],
        'message': None if 'message_sent' not in response_dict else return_message_object(response_dict['message_sent']),
        'status_code': res.status_code
    })

    # Ensure that the next message to the Socontra Network is not instantly after this message, which can cause issues with sequence etc.
    time.sleep(0.1)

    # print('HTTP Request response:', response_to_return.contents)
    return response_to_return


def _send_auth_request(api_crud_type, socontra_network_url, socontra_network_api_port, socontra_network_path, json_message, access_token):
    
    if api_crud_type == 'POST':
        res = requests.post(socontra_network_url + ':' + str(socontra_network_api_port) + socontra_network_path, json=json_message, headers=access_token)
    elif api_crud_type == 'GET':
        res = requests.get(socontra_network_url + ':' + str(socontra_network_api_port) + socontra_network_path, json=json_message, headers=access_token)
    elif api_crud_type == 'PUT':
        res = requests.put(socontra_network_url + ':' + str(socontra_network_api_port) + socontra_network_path, json=json_message, headers=access_token)
    elif api_crud_type == 'DELETE':
        res = requests.delete(socontra_network_url + ':' + str(socontra_network_api_port) + socontra_network_path, json=json_message, headers=access_token)
    else:
        raise ValueError('ERROR - PROVIDE TYPE OF CRUD MESSAGE')
    
    return res

def endpoints_that_dont_need_access_tokens(path):
    # Will return true if path is an endpoint that does not need an access token.
    return path == '/agent_auth/' or path == '/agent_auth/agent_token' or path == '/agent_auth/forgot_password' \
        or path == '/agent_auth/activate_agent'

def get_access_token(agent_name):
    json_message = {
        'agent_name': agent_name,
        'agent_password': agent_db(agent_name).get_agent_password()
    }

    response_content = send_auth_message(agent_name, json_message, '/agent_auth/agent_token', 'POST')

    if 'access_token' in response_content.http_response:
        a_t = response_content.http_response['access_token']
        access_token = {'Authorization': f'Bearer {a_t}'}
        # Save access token.
        agent_db(agent_name).store_socontra_access_token(access_token)
        return access_token
    else:
        # error with getting access, return false.
        return False


# Get the database object for the specific agent. Need to do this because there could be multiple agents
# running off this same Socontra Client.
def agent_db(agent_name):
    global agent_db_object_ref
    if agent_name in agent_db_object_ref:
        return agent_db_object_ref[agent_name]
    else:
        raise ValueError('agent_name not found. Please check and ensure that the agent associated with agent_name is registered: ' + agent_name)
    
def is_agent_connected(agent_name):
    # Will check if the agent is connected.
    global agent_db_object_ref
    return agent_name in agent_db_object_ref


def return_message_object(json_message, message_type = None):
    # Will convert a dict message into an object message to return to the developer.
    message_type_to_use = message_type if message_type is not None else json_message['message_type']

    if 'task' not in json_message:
        return Message(
            sender_name=json_message['sender_name'],
            receiver_name=json_message['receiver_name'],
            distribution_list=json_message['distribution_list'],
            message=json_message['message'],
            message_type=message_type_to_use,
            recipient_type=json_message['recipient_type'],
            protocol=json_message['protocol'],
            dialogue_id=json_message['dialogue_id'],
            message_id = None if 'message_id' not in json_message else json_message['message_id'],
            )
    else:
        return Message(
            sender_name=json_message['sender_name'],
            receiver_name=json_message['receiver_name'],
            distribution_list=json_message['distribution_list'],
            message=json_message['message'],
            message_type=message_type_to_use,
            recipient_type=json_message['recipient_type'],
            protocol=json_message['protocol'],
            dialogue_id=json_message['dialogue_id'],
            message_id = json_message['message_id'],
            task=json_message['task'],
            proposal_timeout=json_message['proposal_timeout'],
            proposal=json_message['proposal'],
            invite_offer_timeout=json_message['invite_offer_timeout'],
            offer=json_message['offer'],
            offer_timeout=json_message['offer_timeout'],
            payment_required=json_message['payment_required'],
            human_authorization_required=json_message['human_authorization_required'],
            order=json_message['order'],
            )